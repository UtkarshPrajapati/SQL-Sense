"""
Automated tests for the DataFlow backend (sql_assistant.py).
"""
import pytest
import httpx
from unittest import mock
import os
import uuid

# Ensure the app is loaded before importing FastAPI TestClient
# This might require adjusting PYTHONPATH or how the app instance is obtained
# For now, assuming sql_assistant can be imported and `app` is available.
from sql_assistant import app, SessionData, session_backend, cookie

# For mocking database and Gemini responses
MOCK_DB_CONNECTION = mock.Mock()
MOCK_DB_CURSOR = mock.Mock()
MOCK_GEMINI_CLIENT = mock.Mock()
MOCK_GEMINI_MODELS = mock.Mock() # Mock for gemini_client.models
MOCK_GEMINI_GENERATE_CONTENT_RESPONSE = mock.Mock()

# Test client for FastAPI
# client = TestClient(app) # httpx.AsyncClient is preferred for async FastAPI apps

@pytest.fixture(scope="function")
def client():
    """
    Provides an asynchronous test client for the FastAPI application.
    Includes session setup for each test.
    """
    async def _client_wrapper():
        # Create a new session for each test
        session_id = uuid.uuid4()
        initial_data = SessionData(history=[])
        await session_backend.create(session_id, initial_data)

        # Set the session cookie for the client
        # httpx.AsyncClient handles cookies automatically if set in headers or by server
        # For direct cookie setting:
        cookies = {cookie.cookie_name: str(session_id)}

        async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
            ac.cookies.update(cookies) # Set cookies for the client
            yield ac
    return _client_wrapper


# Mock environment variables before sql_assistant is imported by other modules
# This is tricky because sql_assistant loads .env on import.
# We will mock the os.getenv calls within sql_assistant for more direct control.

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mocks environment variables for testing."""
    monkeypatch.setenv("MYSQL_HOST", "test_host")
    monkeypatch.setenv("MYSQL_USER", "test_user")
    monkeypatch.setenv("MYSQL_PASSWORD", "test_password")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test_secret_key_for_sessions")
    # This ensures that when sql_assistant.py is loaded by the test runner,
    # it sees these mocked values.

@pytest.fixture(autouse=True)
def mock_external_services():
    """
    Mocks external services like database and Gemini API.
    Applied automatically to all tests.
    """
    # Reset mocks before each test
    MOCK_DB_CONNECTION.reset_mock()
    MOCK_DB_CURSOR.reset_mock()
    MOCK_GEMINI_CLIENT.reset_mock()
    MOCK_GEMINI_MODELS.reset_mock()
    MOCK_GEMINI_GENERATE_CONTENT_RESPONSE.reset_mock()

    # Default behavior for mocks (can be overridden in specific tests)
    MOCK_DB_CONNECTION.cursor.return_value = MOCK_DB_CURSOR
    MOCK_DB_CURSOR.fetchall.return_value = []
    MOCK_DB_CURSOR.description = []
    MOCK_DB_CURSOR.fetchmany.return_value = []

    MOCK_GEMINI_CLIENT.models = MOCK_GEMINI_MODELS # Attach the models mock
    MOCK_GEMINI_MODELS.generate_content.return_value = MOCK_GEMINI_GENERATE_CONTENT_RESPONSE
    MOCK_GEMINI_GENERATE_CONTENT_RESPONSE.text = "SELECT * FROM mock_table;"
    MOCK_GEMINI_GENERATE_CONTENT_RESPONSE.prompt_feedback = None # No blocking by default

    # Patch the actual functions/classes used by the application
    # Patching 'mysql.connector.connect'
    patch_db_connect = mock.patch('mysql.connector.connect', return_value=MOCK_DB_CONNECTION)

    # Patching 'google.genai.Client'
    # The actual client is genai.Client, and then client.models.generate_content is called.
    patch_gemini_client_constructor = mock.patch('google.genai.Client', return_value=MOCK_GEMINI_CLIENT)

    # Patching 'sql_assistant.fetch_all_tables_and_columns'
    # This is an internal function, so we patch it within the module.
    patch_fetch_schema = mock.patch('sql_assistant.fetch_all_tables_and_columns')

    # Patching 'sql_assistant.execute_sql_query'
    patch_execute_sql = mock.patch('sql_assistant.execute_sql_query')

    # Start the patches
    # Patches need to be started and stopped for each test or test session.
    # Using them as context managers or with start/stop is common.
    # For autouse fixtures, we can start them and add a finalizer to stop them.

    started_patches = {
        "db_connect": patch_db_connect.start(),
        "gemini_client": patch_gemini_client_constructor.start(),
        "fetch_schema": patch_fetch_schema.start(),
        "execute_sql": patch_execute_sql.start(),
    }

    # Configure the default return values for the patched internal functions
    # These are function-level mocks, so they are directly usable.
    started_patches["fetch_schema"].return_value = {"mock_db": {"mock_table": ["col1", "col2"]}}
    # Default: (results, column_names, column_types_str, status_code, error_message)
    started_patches["execute_sql"].return_value = ([], [], "", 1, None)


    yield started_patches # Provide the started mocks to the test if needed

    # Stop all patches after the test
    for p in started_patches.values():
        p.stop()

# Placeholder test to ensure setup is working
# This will be removed/replaced with actual tests.
@pytest.mark.asyncio
async def test_placeholder_async(client):
    """A placeholder test to ensure the async client and mocks can be initialized."""
    test_client_instance = None
    async for instance in client(): # Iterate to get the client instance from the async generator
        test_client_instance = instance
        break # We only need one instance

    assert test_client_instance is not None
    response = await test_client_instance.get("/")
    assert response.status_code == 200
    # Further checks can be added here if needed

# --- Tests for /chat endpoint ---

@pytest.mark.asyncio
async def test_chat_plain_english_to_sql_execution(client, mock_external_services):
    """Test plain-English to SQL conversion and successful execution."""
    async for ac in client():
        # Mock Gemini to return a safe SELECT query
        mock_external_services["gemini_client"].models.generate_content.return_value.text = "SELECT name FROM users;"
        # Mock SQL execution to return some data
        mock_external_services["execute_sql"].return_value = (
            [("Alice",), ("Bob",)], # results
            ["name"],                # columns
            "name: VARCHAR",         # col_types
            1,                       # status_code (SELECT success)
            None                     # error_message
        )
        # Mock schema fetching
        mock_external_services["fetch_schema"].return_value = {"db1": {"users": ["id", "name"]}}

        response = await ac.post("/chat", json={"message": "Show me all user names"})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "result"
        assert data["query"] == "SELECT name FROM users;"
        assert data["results"] == [["Alice",], ["Bob",]]
        assert data["columns"] == ["name"]
        assert "insights" in data

        # Check if history was updated (simplified check)
        # This requires peeking into the session_backend, which can be complex.
        # For now, we trust the endpoint logic. A more direct check would involve
        # retrieving the session data from session_backend after the call.

@pytest.mark.asyncio
async def test_chat_conversational_query(client, mock_external_services):
    """Test handling of conversational queries like 'hello'."""
    async for ac in client():
        # Mock Gemini to indicate a conversational query
        mock_external_services["gemini_client"].models.generate_content.return_value.text = "Error: This is a conversational query."
        # Mock the secondary Gemini call for a conversational response

        # We need to make sure the mock is configured for multiple calls if generate_sql_with_gemini and get_conversational_response_with_gemini are called
        # For simplicity, let's assume the first call is for SQL generation, second for conversational.
        mock_gemini_responses = [
            mock.Mock(text="Error: This is a conversational query.", prompt_feedback=None), # For generate_sql_with_gemini
            mock.Mock(text="Hello there! How can I help you today?", prompt_feedback=None)  # For get_conversational_response_with_gemini
        ]
        mock_external_services["gemini_client"].models.generate_content.side_effect = mock_gemini_responses


        response = await ac.post("/chat", json={"message": "Hello"})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "info"
        assert data["content"] == "Hello there! How can I help you today?"

        # Check that generate_sql_with_gemini was called, then get_conversational_response_with_gemini
        assert mock_external_services["gemini_client"].models.generate_content.call_count == 2

@pytest.mark.asyncio
async def test_chat_run_sql_command_safe(client, mock_external_services):
    """Test /run <SQL> command for a safe SELECT query."""
    async for ac in client():
        mock_sql_query = "SELECT id FROM products;"
        mock_external_services["execute_sql"].return_value = (
            [(1,), (2,)], ["id"], "id: INT", 1, None
        )

        response = await ac.post("/chat", json={"message": f"/run {mock_sql_query}"})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "result"
        assert data["query"] == mock_sql_query
        assert data["results"] == [[1,], [2,]]

        # Ensure Gemini was NOT called for SQL generation
        mock_external_services["gemini_client"].models.generate_content.assert_not_called()
        # Ensure execute_sql_query was called with the exact query
        mock_external_services["execute_sql"].assert_called_once_with(mock_sql_query)

@pytest.mark.asyncio
async def test_chat_gemini_fails_to_generate_sql(client, mock_external_services):
    """Test error handling when Gemini API fails to generate SQL."""
    async for ac in client():
        mock_external_services["gemini_client"].models.generate_content.return_value.text = "Error: AI model failed."

        response = await ac.post("/chat", json={"message": "Some complex query"})

        assert response.status_code == 200 # The endpoint itself handles the error gracefully
        data = response.json()
        assert data["type"] == "error"
        assert "Error: AI model failed." in data["content"]

@pytest.mark.asyncio
async def test_chat_sql_execution_error(client, mock_external_services):
    """Test error handling for SQL execution errors."""
    async for ac in client():
        mock_sql_query = "SELECT * FROM non_existent_table;"
        mock_external_services["gemini_client"].models.generate_content.return_value.text = mock_sql_query
        mock_external_services["execute_sql"].return_value = (
            None, None, None, 3, "SQL Error: Table not found"
        )
        # Mock the Gemini call for error explanation
        # This is the second call to generate_content in the /chat flow if SQL fails
        mock_gemini_error_explanation = "AI says: The table might not exist."

        # Setup side_effect for multiple calls: 1. SQL gen, 2. Error explanation
        mock_external_services["gemini_client"].models.generate_content.side_effect = [
            mock.Mock(text=mock_sql_query, prompt_feedback=None), # For generate_sql_with_gemini
            mock.Mock(text=mock_gemini_error_explanation, prompt_feedback=None) # For get_error_explanation_with_gemini
        ]

        response = await ac.post("/chat", json={"message": "Query that will fail"})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "error"
        assert "Query failed to execute" in data["content"]
        assert "SQL Error: Table not found" in data["content"]
        assert data["ai_explanation"] == mock_gemini_error_explanation

        assert mock_external_services["gemini_client"].models.generate_content.call_count == 2
        mock_external_services["execute_sql"].assert_called_once_with(mock_sql_query)

@pytest.mark.asyncio
async def test_chat_block_high_risk_query_drop_table(client, mock_external_services):
    """Test security blocking for high-risk 'DROP TABLE' query via /run command."""
    async for ac in client():
        # No need to mock Gemini as /run bypasses it.
        # The get_query_risk_level function will be called internally.
        response = await ac.post("/chat", json={"message": "/run DROP TABLE users;"})

        assert response.status_code == 200 # Endpoint handles it, doesn't crash
        data = response.json()
        assert data["type"] == "error"
        assert "blocked for security reasons" in data["content"]
        assert "ai_explanation" in data # Should have the canned explanation

        # Ensure execute_sql_query was NOT called
        mock_external_services["execute_sql"].assert_not_called()

@pytest.mark.asyncio
async def test_chat_block_high_risk_query_generated_alter(client, mock_external_services):
    """Test security blocking for high-risk 'ALTER TABLE' query generated by AI."""
    async for ac in client():
        mock_external_services["gemini_client"].models.generate_content.return_value.text = "ALTER TABLE users ADD COLUMN email VARCHAR(255);"

        response = await ac.post("/chat", json={"message": "Add an email column to users"})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "error"
        assert "blocked for security reasons" in data["content"]

        mock_external_services["execute_sql"].assert_not_called()

# --- Tests for /reset_chat endpoint ---

@pytest.mark.asyncio
async def test_reset_chat_clears_history(client, mock_external_services):
    """Test that /reset_chat clears the session's chat history."""
    async for ac in client():
        # 1. Add something to history via the /chat endpoint first
        # Mock Gemini to return a simple response for history population
        mock_external_services["gemini_client"].models.generate_content.return_value.text = "Error: This is a conversational query."
        # Mock the secondary Gemini call for a conversational response
        mock_gemini_responses = [
            mock.Mock(text="Error: This is a conversational query.", prompt_feedback=None),
            mock.Mock(text="Initial message in history.", prompt_feedback=None)
        ]
        mock_external_services["gemini_client"].models.generate_content.side_effect = mock_gemini_responses

        await ac.post("/chat", json={"message": "Populate history"})
        # At this point, the session associated with `ac` should have some history.

        # 2. Call /reset_chat
        reset_response = await ac.post("/reset_chat")
        assert reset_response.status_code == 200
        reset_data = reset_response.json()
        assert reset_data["status"] == "success"
        assert "Chat history has been reset" in reset_data["message"]

        # 3. Verify history is cleared by making another chat call that depends on history (or by inspecting session)
        # For simplicity, let's send a message and see if the AI (mocked) gets an empty history.
        # Reset side_effect for Gemini mock for the next call
        mock_external_services["gemini_client"].models.generate_content.side_effect = None # Clear side_effect
        mock_external_services["gemini_client"].models.generate_content.return_value.text = "SELECT * FROM test" # Default SQL gen
        mock_external_services["execute_sql"].return_value = ([], [], "", 1, None) # Default SQL exec

        # Re-configure the mock for generate_sql_with_gemini to capture the history it receives.
        # The `history` argument to `generate_sql_with_gemini` is the second positional argument
        # if `self` is the first (for methods), or first if it's a standalone function.
        # In sql_assistant.py, generate_sql_with_gemini receives (user_query, schema, history).
        # So, `history` is at index 2 of `args` for the mock call.

        # We need to inspect the arguments passed to the *mocked* `generate_sql_with_gemini`
        # which is `mock_external_services["gemini_client"].models.generate_content`
        # The actual `generate_sql_with_gemini` function constructs a prompt that includes history.
        # So, we check the `contents` argument to `gemini_client.models.generate_content`.

        # Reset the primary mock for a clean check
        mock_external_services["gemini_client"].models.generate_content.reset_mock()
        mock_external_services["gemini_client"].models.generate_content.return_value.text = "SELECT * FROM after_reset;"


        await ac.post("/chat", json={"message": "After reset"})

        # The `contents` arg to `generate_content` is `history + [{"role": "user", "parts": [{"text": system_prompt}]}]`
        # If history was cleared, the `contents` list should only contain the new user prompt.
        # The `history` part of `contents` should be empty.
        # The call_args for `generate_content` can be inspected.
        # The first call to generate_content in the /chat endpoint (generate_sql_with_gemini)
        # will receive the history.

        # Get the arguments of the first call to generate_content
        # (assuming it was called once after reset)
        call_args = mock_external_services["gemini_client"].models.generate_content.call_args
        assert call_args is not None, "Gemini generate_content was not called after reset"

        passed_contents = call_args.kwargs.get('contents')
        assert passed_contents is not None, "Contents not passed to generate_content"

        # `passed_contents` is `history + [{"role": "user", "parts": [...]}]`.
        # If session history was cleared, the `history` part here should be empty.
        # So, `passed_contents` should have length 1 (just the system_prompt part).
        assert len(passed_contents) == 1, f"History not cleared. Contents length: {len(passed_contents)}"
        assert passed_contents[0]["role"] == "user" # It's the system_prompt effectively
        assert "After reset" in passed_contents[0]["parts"][0]["text"]

@pytest.mark.asyncio
async def test_reset_chat_on_new_session(client):
    """Test /reset_chat on a session that has no prior history (should still succeed)."""
    async for ac in client():
        # Session is new, created by the client fixture, history is empty.
        reset_response = await ac.post("/reset_chat")
        assert reset_response.status_code == 200
        reset_data = reset_response.json()
        assert reset_data["status"] == "success"
        assert "Chat history has been reset" in reset_data["message"]

        # Optionally, verify history remains empty by calling /chat as in the previous test.
        # This part is largely redundant if the above test passes, but good for completeness.
        # (Code similar to the verification part of test_reset_chat_clears_history)

@pytest.mark.asyncio
async def test_chat_confirm_medium_risk_query_insert(client, mock_external_services):
    """Test confirmation flow for medium-risk 'INSERT' query generated by AI."""
    async for ac in client():
        mock_sql_query = "INSERT INTO users (name) VALUES ('Charlie');"
        mock_external_services["gemini_client"].models.generate_content.return_value.text = mock_sql_query

        response = await ac.post("/chat", json={"message": "Add user Charlie"})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "confirm_execution"
        assert data["query"] == mock_sql_query
        assert "may modify your data" in data["message"]

        mock_external_services["execute_sql"].assert_not_called()

@pytest.mark.asyncio
async def test_chat_missing_message_field(client):
    """Test request validation for missing 'message' field."""
    async for ac in client():
        response = await ac.post("/chat", json={}) # Missing "message"

        assert response.status_code == 422 # Unprocessable Entity
        data = response.json()
        assert "detail" in data
        assert any("message" in error["loc"] and "Field required" in error["msg"] for error in data["detail"])

@pytest.mark.asyncio
async def test_chat_fetch_schema_fails(client, mock_external_services):
    """Test /chat when fetching schema fails before AI query generation."""
    async for ac in client():
        mock_external_services["fetch_schema"].return_value = {
            "error": {"schema": ["Database connection failed"]}
        }
        # Gemini should not be called if schema fails

        response = await ac.post("/chat", json={"message": "Show me users"})

        assert response.status_code == 200 # Endpoint handles error gracefully
        data = response.json()
        assert data["type"] == "error"
        assert "Could not fetch database schema" in data["content"]
        assert "Database connection failed" in data["content"]

        mock_external_services["gemini_client"].models.generate_content.assert_not_called()
        mock_external_services["execute_sql"].assert_not_called()

# --- Tests for /schema endpoint ---

@pytest.mark.asyncio
async def test_get_schema_success(client, mock_external_services):
    """Test successful schema retrieval."""
    async for ac in client():
        expected_schema = {
            "db1": {"table1": ["colA", "colB"]},
            "db2": {"table2": ["colX", "colY"], "table3": ["colZ"]}
        }
        mock_external_services["fetch_schema"].return_value = expected_schema

        response = await ac.get("/schema")

        assert response.status_code == 200
        data = response.json()
        assert data["schema"] == expected_schema

        mock_external_services["fetch_schema"].assert_called_once()

# --- Tests for /config and /config_status endpoints ---

@pytest.mark.asyncio
async def test_get_config_status(client, mock_env_vars): # mock_env_vars to ensure globals are set
    """Test retrieval of current configuration status."""
    async for ac in client():
        # Values from mock_env_vars
        expected_host = "test_host"
        expected_user = "test_user"
        expected_password_set = True # Since "test_password" is non-empty
        expected_gemini_key_set = True # Since "test_gemini_key" is non-empty

        # Need to ensure the global variables in sql_assistant are updated based on mock_env_vars
        # This happens upon import of sql_assistant, which pytest handles.
        # For this test, we might need to re-import or directly mock the global vars
        # if they are not reflecting mock_env_vars correctly.
        # However, load_dotenv in sql_assistant runs on import.
        # The `mock_env_vars` fixture sets environment variables *before* the module is loaded by tests.
        # So, MYSQL_HOST etc. in sql_assistant should have the test values.

        with mock.patch('sql_assistant.MYSQL_HOST', expected_host), \
             mock.patch('sql_assistant.MYSQL_USER', expected_user), \
             mock.patch('sql_assistant.MYSQL_PASSWORD', "test_password"), \
             mock.patch('sql_assistant.GEMINI_API_KEY', "test_gemini_key"):

            response = await ac.get("/config_status")

            assert response.status_code == 200
            data = response.json()
            assert data["mysql_host"] == expected_host
            assert data["mysql_user"] == expected_user
            assert data["mysql_password_set"] == expected_password_set
            assert data["gemini_api_key_set"] == expected_gemini_key_set


@pytest.mark.asyncio
@mock.patch('sql_assistant.update_env_file') # Mock file system interaction
async def test_update_config_success(mock_update_env_file, client, mock_external_services):
    """Test successful update of configuration."""
    async for ac in client():
        new_config = {
            "mysql_host": "new_host",
            "mysql_user": "new_user",
            "mysql_password": "new_password",
            "gemini_api_key": "new_gemini_key"
        }

        # Mock successful DB connection test
        mock_external_services["db_connect"].return_value.close.return_value = None # mysql.connector.connect().close()
        # Mock successful Gemini API test
        # The real test is `genai.Client(api_key=...).models.generate_content(...)`
        # Our `mock_external_services["gemini_client"]` is the result of `genai.Client()`
        mock_external_services["gemini_client"].models.generate_content.return_value.text = "ping_response"

        response = await ac.post("/config", json=new_config)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["mysql_connection"] == "success"
        assert data["gemini_api"] == "success"
        assert "Configuration updated" in data["message"]

        mock_update_env_file.assert_called_once()

        # Verify that sql_assistant's global vars were updated (requires inspecting them or another /config_status call)
        # This is a bit indirect. A direct assertion on os.environ or global vars would be better if feasible.
        # For now, we trust `update_environment` is called and works.
        # Let's also check that initialize_gemini_api was called if gemini key changed
        # This requires a mock on initialize_gemini_api
        with mock.patch('sql_assistant.initialize_gemini_api') as mock_init_gemini:
            await ac.post("/config", json=new_config) # Call again to check side effects
            mock_init_gemini.assert_called()


@pytest.mark.asyncio
@mock.patch('sql_assistant.update_env_file')
async def test_update_config_mysql_fails(mock_update_env_file, client, mock_external_services):
    """Test config update when MySQL connection test fails."""
    async for ac in client():
        config_data = {
            "mysql_host": "bad_host", "mysql_user": "user",
            "mysql_password": "pw", "gemini_api_key": "key"
        }
        # Mock DB connection failure
        mock_external_services["db_connect"].side_effect = Exception("MySQL connection error")
        # Gemini success
        mock_external_services["gemini_client"].models.generate_content.return_value.text = "ping_response"

        response = await ac.post("/config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success" # Overall update is success, but connection status shows failure
        assert "failed: MySQL connection error" in data["mysql_connection"]
        assert data["gemini_api"] == "success"
        mock_update_env_file.assert_called_once()

@pytest.mark.asyncio
@mock.patch('sql_assistant.update_env_file')
async def test_update_config_gemini_fails(mock_update_env_file, client, mock_external_services):
    """Test config update when Gemini API key validation fails."""
    async for ac in client():
        config_data = {
            "mysql_host": "host", "mysql_user": "user",
            "mysql_password": "pw", "gemini_api_key": "bad_key"
        }
        # Mock DB success
        mock_external_services["db_connect"].return_value.close.return_value = None
        # Mock Gemini failure
        # The call is genai.Client(api_key=...).models.generate_content(...)
        # We need the constructor mock `mock_external_services["gemini_client_constructor"]` if we need to mock Client() itself
        # But `mock_external_services["gemini_client"]` is the *instance* of the client.
        # So, if Client() construction is fine but generate_content fails:
        mock_external_services["gemini_client"].models.generate_content.side_effect = Exception("Gemini API error")

        response = await ac.post("/config", json=config_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["mysql_connection"] == "success"
        assert "failed: Gemini API error" in data["gemini_api"]
        mock_update_env_file.assert_called_once()

@pytest.mark.asyncio
@mock.patch('sql_assistant.update_env_file')
async def test_update_config_empty_values_use_defaults(mock_update_env_file, client, mock_external_services):
    """Test that empty config values use defaults and are reported correctly."""
    async for ac in client():
        # Send empty strings for all fields
        empty_config = {
            "mysql_host": "", "mysql_user": "",
            "mysql_password": "", "gemini_api_key": ""
        }

        # Mock successful connections for default values
        mock_external_services["db_connect"].return_value.close.return_value = None
        # For Gemini, an empty key means "not_provided", no API call.
        # So, the `generate_content` mock shouldn't be hit for the Gemini test if key is empty.
        # We might need to adjust the mock setup for `initialize_gemini_api` if it's called.

        response = await ac.post("/config", json=empty_config)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["mysql_connection"] == "success" # Assuming defaults connect
        assert data["gemini_api"] == "not_provided" # Correct for empty key

        mock_update_env_file.assert_called_once()

        # Check that the global variables in sql_assistant were updated to defaults
        # This requires inspecting them, e.g. by calling /config_status
        # Or by directly checking os.environ IF update_environment correctly sets them
        # Let's assume 'localhost', 'root', 'root' are defaults
        # And that initialize_gemini_api is called
        with mock.patch('sql_assistant.initialize_gemini_api') as mock_init_gemini, \
             mock.patch('sql_assistant.MYSQL_HOST', "localhost"), \
             mock.patch('sql_assistant.MYSQL_USER', "root"), \
             mock.patch('sql_assistant.MYSQL_PASSWORD', "root"), \
             mock.patch('sql_assistant.GEMINI_API_KEY', ""):

            status_response = await ac.get("/config_status")
            status_data = status_response.json()

            assert status_data["mysql_host"] == "localhost"
            assert status_data["mysql_user"] == "root"
            assert status_data["mysql_password_set"] == True # Default "root" is non-empty
            assert status_data["gemini_api_key_set"] == False # Default "" is empty

            # Call config again to check initialize_gemini_api with empty key
            await ac.post("/config", json=empty_config)
            # initialize_gemini_api should be called even if the key is empty to reset the state
            assert mock_init_gemini.call_count > 0 # Called at least once due to the second post

# --- Tests for /execute_confirmed_sql endpoint ---

@pytest.mark.asyncio
async def test_execute_confirmed_sql_success_dml(client, mock_external_services):
    """Test successful execution of a confirmed DML query (e.g., INSERT)."""
    async for ac in client():
        confirmed_query = "INSERT INTO products (name) VALUES ('Test Product');"
        # Mock execute_sql_query for DML success
        mock_external_services["execute_sql"].return_value = (
            None, None, None, 2, None # DML success
        )

        response = await ac.post("/execute_confirmed_sql", json={"query": confirmed_query})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "info"
        assert f"Query executed successfully:\n\n```sql\n{confirmed_query}\n```" in data["content"]

        mock_external_services["execute_sql"].assert_called_once_with(confirmed_query)
        # TODO: Verify history update if applicable for confirmed DML

@pytest.mark.asyncio
async def test_execute_confirmed_sql_success_select(client, mock_external_services):
    """Test successful execution of a confirmed SELECT query."""
    async for ac in client():
        confirmed_query = "SELECT * FROM customers WHERE id = 1;"
        mock_external_services["execute_sql"].return_value = (
            [(1, "Test Customer")], ["id", "name"], "id:INT, name:VARCHAR", 1, None # SELECT success
        )

        response = await ac.post("/execute_confirmed_sql", json={"query": confirmed_query})

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "result"
        assert data["query"] == confirmed_query
        assert data["results"] == [[1, "Test Customer"]]
        assert data["columns"] == ["id", "name"]
        assert "insights" in data # Default insight message for confirmed queries

        mock_external_services["execute_sql"].assert_called_once_with(confirmed_query)
        # TODO: Verify history update

@pytest.mark.asyncio
async def test_execute_confirmed_sql_execution_fails(client, mock_external_services):
    """Test error handling if the confirmed query fails during execution."""
    async for ac in client():
        confirmed_query = "UPDATE non_existent_table SET col = 1;"
        db_error_message = "SQL Error: Table 'non_existent_table' doesn't exist"
        ai_explanation = "AI says: The table you tried to update does not exist."

        mock_external_services["execute_sql"].return_value = (
            None, None, None, 3, db_error_message # SQL error
        )
        # Mock the Gemini call for error explanation
        mock_external_services["gemini_client"].models.generate_content.return_value.text = ai_explanation

        response = await ac.post("/execute_confirmed_sql", json={"query": confirmed_query})

        assert response.status_code == 200 # Endpoint handles error gracefully
        data = response.json()
        assert data["type"] == "error"
        assert f"Confirmed query failed to execute:\n```sql\n{confirmed_query}\n```" in data["content"]
        assert db_error_message in data["content"]
        assert data["ai_explanation"] == ai_explanation

        mock_external_services["execute_sql"].assert_called_once_with(confirmed_query)
        # Check that get_error_explanation_with_gemini was called
        mock_external_services["gemini_client"].models.generate_content.assert_called_once()
        # Ensure fetch_all_tables_and_columns was called for context
        mock_external_services["fetch_schema"].assert_called_once()


@pytest.mark.asyncio
async def test_execute_confirmed_sql_missing_query_field(client):
    """Test request validation for missing 'query' field."""
    async for ac in client():
        response = await ac.post("/execute_confirmed_sql", json={}) # Missing "query"

        assert response.status_code == 422 # Unprocessable Entity by Pydantic
        data = response.json()
        assert "detail" in data
        assert any("query" in error["loc"] and "Field required" in error["msg"] for error in data["detail"])

@pytest.mark.asyncio
async def test_execute_confirmed_sql_empty_query_string(client, mock_external_services):
    """Test sending an empty query string."""
    async for ac in client():
        response = await ac.post("/execute_confirmed_sql", json={"query": "   "}) # Empty query

        assert response.status_code == 400 # Bad Request as per endpoint logic
        data = response.json()
        assert data["type"] == "error"
        assert "No query provided for execution" in data["content"]

        mock_external_services["execute_sql"].assert_not_called()
