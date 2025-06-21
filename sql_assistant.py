import os
import logging
import json
from typing import List, Dict, Any, Tuple, Optional
import mysql.connector
import sqlparse
from mysql.connector import FieldType
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import functools
import uuid
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration with defaults
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "SQLLLM")

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = "gemini-2.5-flash-lite-preview-06-17"
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", str(uuid.uuid4()))

# Variable to track if Gemini API is initialized
gemini_initialized = False
# Global Gemini Client
gemini_client: Optional[genai.client.Client] = None

# In-memory store for chat history (a list of message dictionaries)
MAX_HISTORY_LENGTH = 20 # Max number of user/model turn pairs to keep

# Path to .env file
ENV_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

# --- Session Management Setup ---
class SessionData(BaseModel):
    history: List[Dict[str, Any]] = []

cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="session_id",
    identifier="general_verifier",
    auto_error=True,
    secret_key=SESSION_SECRET_KEY, 
    cookie_params=cookie_params,
)

session_backend = InMemoryBackend[uuid.UUID, SessionData]()

class SessionManager(SessionVerifier[uuid.UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[uuid.UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True

session_verifier = SessionManager(
    identifier="general_verifier",
    auto_error=True,
    backend=session_backend,
    auth_http_exception=HTTPException(status_code=403, detail="Invalid session"),
)

# --- Chat History Management (Now operates on a session) ---

def add_to_history(session_data: SessionData, role: str, text: str):
    """
    Adds a message to the chat history for a given session and truncates it.
    """
    session_data.history.append({"role": role, "parts": [{"text": text}]})

    # Truncate history if it becomes too long
    if len(session_data.history) > MAX_HISTORY_LENGTH * 2:
        session_data.history = session_data.history[2:]
        logger.info(f"Chat history truncated. New length: {len(session_data.history)}")

def clear_chat_history():
    """Clears the global chat history."""
    global chat_history_store
    chat_history_store = []
    logger.info("Chat history has been cleared.")

# Function to initialize Gemini API
def initialize_gemini_api():
    """
    Initializes the Gemini API and validates the key by making a test call.
    """
    global gemini_initialized, gemini_client
    try:
        if GEMINI_API_KEY:
            # The new SDK uses a client object for all interactions.
            gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            # Test the key by making a lightweight, non-streaming call
            gemini_client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents="ping",
                config={
                    "max_output_tokens": 1
                }
            )
            gemini_initialized = True
            logger.info("Gemini API initialized and validated successfully")
            return True
        else:
            logger.warning("GEMINI_API_KEY not found. Some features will be limited.")
            gemini_initialized = False
            gemini_client = None
            return False
    except Exception as e:
        logger.error(f"Failed to initialize or validate Gemini API key: {e}")
        gemini_initialized = False
        gemini_client = None
        return False

# Initialize Gemini API on startup
initialize_gemini_api()

# Function to update environment variables and .env file
def update_environment(config_data):
    """Updates environment variables and .env file with new configurations."""
    global MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, GEMINI_API_KEY
    
    defaults = {
        "mysql_host": "localhost",
        "mysql_user": "root",
        "mysql_password": "root",
        "mysql_database": "SQLLLM",
        "gemini_api_key": "" # Explicitly empty for API key default handling
    }
    
    # Update global Python variables and os.environ
    # If config_data provides a value, use it. Otherwise, use the default.
    MYSQL_HOST = config_data["mysql_host"] if config_data.get("mysql_host") else defaults["mysql_host"]
    os.environ["MYSQL_HOST"] = MYSQL_HOST
    
    MYSQL_USER = config_data["mysql_user"] if config_data.get("mysql_user") else defaults["mysql_user"]
    os.environ["MYSQL_USER"] = MYSQL_USER
    
    MYSQL_PASSWORD = config_data["mysql_password"] if config_data.get("mysql_password") else defaults["mysql_password"]
    os.environ["MYSQL_PASSWORD"] = MYSQL_PASSWORD
    
    MYSQL_DATABASE = config_data["mysql_database"] if config_data.get("mysql_database") else defaults["mysql_database"]
    os.environ["MYSQL_DATABASE"] = MYSQL_DATABASE
    
    # For Gemini API key, allow an empty string from config_data to be set
    if "gemini_api_key" in config_data:
        GEMINI_API_KEY = config_data["gemini_api_key"]
    else:
        GEMINI_API_KEY = defaults["gemini_api_key"] # Should not happen if key always in config_data
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    if config_data.get("gemini_api_key") or defaults["gemini_api_key"]:
        initialize_gemini_api() # Reinitialize if key is set or was previously set and now defaulted
    
    update_env_file() # Call without arguments
    logger.info("Environment variables updated with new configuration")

# Function to update .env file
def update_env_file(): # Removed config_data and defaults parameters
    """Updates .env file with the current global configuration values."""
    global MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, GEMINI_API_KEY, SESSION_SECRET_KEY
    try:
        env_values_to_write = {
            "MYSQL_HOST": MYSQL_HOST,
            "MYSQL_USER": MYSQL_USER,
            "MYSQL_PASSWORD": MYSQL_PASSWORD,
            "MYSQL_DATABASE": MYSQL_DATABASE,
            "GEMINI_API_KEY": GEMINI_API_KEY,
            "SESSION_SECRET_KEY": SESSION_SECRET_KEY
        }

        if not os.path.exists(ENV_FILE_PATH):
            with open(ENV_FILE_PATH, "w") as env_file:
                for key, value in env_values_to_write.items():
                    env_file.write(f"{key}={value}\n")
                logger.info("Created .env file with new configuration")
        else:
            try:
                with open(ENV_FILE_PATH, "r") as env_file:
                    lines = env_file.readlines()
            except Exception as e:
                logger.error(f"Error reading .env file: {e}, recreating file.")
                with open(ENV_FILE_PATH, "w") as env_file:
                    for key, value in env_values_to_write.items():
                        env_file.write(f"{key}={value}\n")
                    logger.info("Created new .env file after read failure")
                return
                
            updated_lines = []
            managed_keys_updated = {key: False for key in env_values_to_write}
            
            for line in lines:
                line_strip = line.strip()
                if not line_strip or line_strip.startswith("#"):  # Preserve comments and blank lines
                    updated_lines.append(line)
                    continue
                
                if "=" not in line_strip:  # Skip malformed lines
                    updated_lines.append(line)
                    continue
                    
                key, _ = line_strip.split("=", 1)
                key_stripped = key.strip()
                
                if key_stripped in env_values_to_write:
                    updated_lines.append(f"{key_stripped}={env_values_to_write[key_stripped]}\n")
                    managed_keys_updated[key_stripped] = True
                else:
                    updated_lines.append(line)  # Preserve other unrelated env variables
            
            # Add any of our managed keys that weren't in the file originally
            for key, value in env_values_to_write.items():
                if not managed_keys_updated[key]:
                    updated_lines.append(f"{key}={value}\n")
            
            with open(ENV_FILE_PATH, "w") as env_file:
                env_file.writelines(updated_lines)
                logger.info("Updated .env file with new configuration")
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")

# --- Database Interaction ---

def get_db_connection(db_name: Optional[str] = None):
    """
    Establishes a connection to the MySQL server.
    Connects to a specific database if db_name is provided.
    Returns the connection object or None if connection fails.
    """
    try:
        conn_params = {
            'host': MYSQL_HOST,
            'user': MYSQL_USER,
            'password': MYSQL_PASSWORD,
            'pool_name': "mypool", 
            'pool_size': 5,
            'auth_plugin': 'mysql_native_password'
        }
        if db_name:
            conn_params['database'] = db_name

        conn = mysql.connector.connect(**conn_params)
        logger.info(f"DB connection established (Database: {db_name or 'None'})")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error (connecting to {db_name or 'server'}): {err}")
        return None 

def execute_sql_query(query: str) -> Tuple[Optional[List[Any]], Optional[List[str]], Optional[str], int, Optional[str]]:
    """
    Executes an SQL query against the database.

    Args:
        query: The SQL query string to execute.

    Returns:
        A tuple containing:
        - results: List of result tuples (or None).
        - column_names: List of column names (or None).
        - column_types_str: String describing column names and types (or None).
        - status_code: 1 (SELECT/SHOW success), 2 (Other DML/DDL success), 3 (Error).
        - error_message: Error details if status_code is 3.
    """
    logger.info(f"Executing Query: {query}")
    conn = None
    cursor = None
    results: Optional[List[Any]] = None
    column_names: Optional[List[str]] = None
    column_types_str: Optional[str] = None

    try:
        conn = get_db_connection(db_name=None) # Connect WITHOUT specifying a default database
        if not conn:
            error_message = "SQL Error: Failed to connect to the database server for query execution."
            logger.error(error_message)
            return None, None, None, 3, error_message

        cursor = conn.cursor(buffered=True)

        # --- SECURITY WARNING ---
        # Executing arbitrary SQL generated by an LLM or user input is a
        # significant security risk. In a production environment, you MUST:
        # 1. Sanitize and validate the query.
        # 2. Use parameterized queries where possible.
        # 3. Limit database user permissions (e.g., read-only access).
        # 4. Consider query allow-listing or blocking certain commands.
        # This example executes the query directly for simplicity, but DO NOT deploy like this.
        cursor.execute(query)

        query_lower = query.strip().lower()
        if query_lower.startswith("select") or query_lower.startswith("show"):
            results = cursor.fetchmany(100) # Limit results for display
            if cursor.description: 
                column_names = [i[0] for i in cursor.description]
                from mysql.connector.constants import FieldType # Ensure FieldType is imported
                col_dtypes = [[i[0], FieldType.get_info(i[1])] for i in cursor.description]
                column_types_str = 'Column : Dtype\n' + '\n'.join(f'{k}: {v}' for k, v in col_dtypes)
            else:
                column_names = ["Result"] 
                column_types_str = "Column : Dtype\nResult: <unknown>"
                if results and isinstance(results[0], (str, int, float, bytes)): 
                     results = [(r,) for r in results] # Wrap single values in tuples

            conn.commit() # Necessary even for SELECT with some configurations/engines
            result_count = len(results) if results is not None else 0
            logger.info(f"Query executed successfully, fetched {result_count} rows.")
            return results, column_names, column_types_str, 1, None
        else:
            conn.commit()
            logger.info("Non-SELECT/SHOW query executed successfully.")
            return None, None, None, 2, None # Success for non-select queries

    except mysql.connector.Error as e:
        logger.error(f"SQL Error executing query '{query}': {e}")
        error_message = f"SQL Error: {e}"
        if conn: # Rollback changes if an error occurs during non-select queries
            try:
                conn.rollback()
            except mysql.connector.Error as rb_err:
                logger.error(f"Error during rollback: {rb_err}")
        return None, None, None, 3, error_message
    except Exception as e:
        logger.error(f"Unexpected error executing query '{query}': {e}", exc_info=True)
        error_message = f"Unexpected Error: {e}"
        if conn: # Rollback changes if an unexpected error occurs
             try:
                 conn.rollback()
             except mysql.connector.Error as rb_err:
                 logger.error(f"Error during rollback: {rb_err}")
        return None, None, None, 3, error_message
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected(): # Check conn exists and is connected before closing
            conn.close()
            logger.info("DB connection closed.")

def fetch_all_tables_and_columns() -> Dict[str, Dict[str, Any]]:
    """
    Fetches all non-system databases, their tables, and columns.
    Returns: Dict[db_name, Dict[table_name, List[column_name]]]
    Returns an error structure if connection or queries fail.
    """
    schema_info: Dict[str, Dict[str, Any]] = {}
    conn = None
    cursor = None
    system_databases = {'information_schema', 'mysql', 'performance_schema', 'sys'} # Exclude system databases

    try:
        conn = get_db_connection(db_name=None) # Connect without specifying a database
        if not conn:
             logger.error("Failed to get DB connection for schema fetching.")
             return {"error": {"schema": ["Failed to connect to the database server."]}}

        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES;") # Get all databases
        fetch_result = cursor.fetchall()
        if not fetch_result:
            logger.warning("No databases returned from SHOW DATABASES query.")
            return {}
        databases = [str(row[0]) for row in fetch_result if row[0] not in system_databases] # type: ignore

        if not databases:
            logger.warning("No user databases found.")
            return {} 

        for db_name in databases: # Get tables and columns for each relevant database
            schema_info[db_name] = {}
            try:
                cursor.execute(f"SHOW TABLES FROM `{db_name}`;")
                fetch_result = cursor.fetchall()
                if fetch_result is None:
                    logger.warning(f"No tables returned for database {db_name}.")
                    tables = []
                else:
                    tables = [str(row[0]) for row in fetch_result] # type: ignore

                for table_name in tables:
                    try:
                        cursor.execute(f"SHOW COLUMNS FROM `{db_name}`.`{table_name}`;")
                        fetch_result = cursor.fetchall()
                        if fetch_result is None:
                            logger.warning(f"No columns returned for table {db_name}.{table_name}.")
                            columns = []
                        else:
                            columns = [str(column[0]) for column in fetch_result] # type: ignore
                        schema_info[db_name][table_name] = columns
                    except mysql.connector.Error as e:
                        logger.warning(f"Could not fetch columns for table {db_name}.{table_name}: {e}")
                        schema_info[str(db_name)][str(table_name)] = [f"Error fetching columns: {e}"]

            except mysql.connector.Error as e:
                 logger.warning(f"Could not fetch tables for database {db_name}: {e}")
                 schema_info[str(db_name)] = {"error": [f"Error fetching tables: {e}"]} # Add an error placeholder

        logger.info(f"Fetched schema for {len(databases)} databases.")
        return schema_info

    except mysql.connector.Error as e:
        logger.error(f"SQL Error fetching database list: {e}")
        return {"error": {"schema": [f"SQL Error fetching databases: {e}"]}} 
    except Exception as e:
        logger.error(f"Error fetching schema: {e}", exc_info=True)
        return {"error": {"schema": [f"Unexpected error fetching schema: {str(e)}"]}}
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# --- Gemini API Interaction ---

# Decorator to check Gemini API initialization
def ensure_gemini_initialized(func):
    """Decorator to ensure Gemini API is initialized before calling the wrapped function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not gemini_initialized:
            logger.warning(f"Gemini API not initialized. Call to {func.__name__} will be skipped.")
            # Functions decorated are expected to return a string, so return an error string.
            return "Error: Gemini API not configured. Please set up your API key in the configuration."
        return func(*args, **kwargs)
    return wrapper

@ensure_gemini_initialized
def generate_sql_with_gemini(user_query: str, schema: Dict[str, Dict[str, List[str]]], history: List[Dict[str, Any]]) -> Optional[str]:
    """Generates an SQL query using the Gemini API based on user input and multi-DB schema."""
    schema_string = ""
    if not schema or "error" in schema: 
         schema_string = "Could not fetch schema. Please ensure database connection is correct."
    else:
        for db_name, tables in schema.items():
            schema_string += f"\nDatabase: `{db_name}`\n"
            if isinstance(tables, dict): 
                if not tables:
                     schema_string += "  (No tables found or accessible)\n"
                elif "error" in tables:
                     schema_string += f"  Error fetching tables: {tables['error']}\n"
                else:
                    for table_name, columns in tables.items():
                        col_string = ', '.join([f"`{c}`" for c in columns])
                        schema_string += f"  - Table: `{table_name}`: Columns: {col_string}\n"
            else:
                 schema_string += f"  Error retrieving table details for this database.\n"

    # The system instruction or initial prompt part
    system_prompt = f"""You are an expert SQL assistant. Given the following database schema across potentially multiple databases and a user question, generate the most appropriate SQL query to answer the question.

Database Schema:
{schema_string}

User Question: "{user_query}"

Instructions:
- Your **only** task is to generate a single, executable MySQL query to answer the user's question based on the schema.
- **Always** attempt to generate a query. Do not engage in conversation or ask for clarification.
- If the user asks for a relationship between tables, generate a `JOIN` query. When using a `JOIN`, do not use `SELECT *`. Instead, select specific, useful columns from both tables to show the relationship.
- If the user asks to create a table, make reasonable assumptions for column types (e.g., VARCHAR(255) for text, INT for IDs).
- If querying a table, use the fully qualified name (e.g., `database_name`.`table_name`).
- Generate only **one single** SQL statement. Do not include multiple statements or comments.
- Do not include any explanations, introductory text, backticks (```sql), or markdown formatting.
- If the user's request is impossible to answer with a SQL query (e.g., it's a greeting like "hello"), then and only then, respond with the exact text: "Error: This is a conversational query."

SQL Query:"""

    # Combine the history with the new system prompt
    # The API expects the 'contents' to be a list of these dictionaries.
    request_contents = history + [{"role": "user", "parts": [{"text": system_prompt}]}]

    try:
        # The new SDK uses client.models.generate_content
        if not gemini_client:
            return "Error: Gemini client not initialized."
            
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=request_contents
        )

        if not hasattr(response, 'text') or not response.text:
            logger.warning(f"Gemini returned no text for SQL generation from user query: {user_query}")
            return "Error: The AI model did not return a response."

        sql_query = response.text.strip() # Clean up potential markdown formatting
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip() 

        logger.info(f"Gemini generated SQL: {sql_query}")
        if sql_query.lower().startswith("error:"):
             logger.warning(f"Gemini indicated an error: {sql_query}")
             return sql_query 

        # Basic validation
        if not any(kw in sql_query.lower() for kw in ["select", "insert", "update", "delete", "show", "create", "alter", "drop", "use"]):
             logger.warning(f"Generated text doesn't look like SQL: {sql_query}")
             return "Error: Generated text does not appear to be a valid SQL query."

        return sql_query

    except Exception as e:
        logger.error(f"Error calling Gemini API for SQL generation: {e}", exc_info=True)
        return "Error: Failed to communicate with the AI model for SQL generation."

@ensure_gemini_initialized
def get_insights_with_gemini(original_query: str, sql_query: str, results: List[Any], columns: List[str], col_types: str, history: List[Dict[str, Any]]) -> str:
    """Generates insights on the data using the Gemini API."""
    if not results:
        return "No results to analyze."

    results_preview = json.dumps(results[:20], indent=2, default=str) # Limit results sent to Gemini

    # The main prompt for this specific task
    prompt = f"""You are a data analyst assistant. A user asked the following question:
"{original_query}"

The following SQL query was executed to fetch data:
```sql
{sql_query}
```

The query returned the following data (showing up to 20 rows):
Columns and Types:
{col_types}

Results (JSON format):
{results_preview}

Instructions:
- Provide concise, insightful observations based *only* on the provided data sample.
- Do not invent data or make assumptions beyond what's shown.
- Suggest 1-2 potential follow-up questions or SQL queries the user might be interested in, based on these results and the original question.
- Format your response clearly using Markdown. Start with "### Data Insights" and then "### Suggested Follow-up".

Analysis:"""

    # Combine history with the new prompt
    request_contents = history + [{"role": "user", "parts": [{"text": prompt}]}]

    try:
        if not gemini_client:
            return "Error: Gemini client not initialized."

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=request_contents
        )
        logger.info("Gemini generated insights.")
        return response.text if response.text else "No insights could be generated from the data."
    except Exception as e:
        logger.error(f"Error calling Gemini API for insights: {e}", exc_info=True)
        return "Error generating insights from the AI model."

@ensure_gemini_initialized
def get_conversational_response_with_gemini(user_message: str, history: List[Dict[str, Any]]) -> str:
    """Gets a conversational response from Gemini for non-SQL related queries."""
    logger.info(f"Getting conversational response for: {user_message}")
    
    # Construct the final prompt for the API call
    prompt = f"""You are a helpful assistant. Respond conversationally and politely to the following user message. Do not attempt to generate SQL or refer to databases unless the user explicitly asks about them in this message.

User Message: "{user_message}"

Assistant Response:"""

    # Combine history with the new prompt
    request_contents = history + [{"role": "user", "parts": [{"text": prompt}]}]

    try:
        if not gemini_client:
            return "Error: Gemini client not initialized."
            
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=request_contents
        )
        if response.prompt_feedback and response.prompt_feedback.block_reason:
             logger.warning(f"Conversational response blocked. Reason: {response.prompt_feedback.block_reason}")
             return "I cannot provide a response to that topic."

        return response.text.strip() if response.text else "I am unable to provide a response at this time."

    except Exception as e:
        logger.error(f"Error calling Gemini API for conversational response: {e}", exc_info=True)
        return "I'm having trouble responding right now. Please try again later."

@ensure_gemini_initialized
def get_error_explanation_with_gemini(original_user_query: Optional[str], failed_sql_query: str, error_message: str, schema: Optional[Dict[str, Any]] = None, history: List[Dict[str, Any]] = []) -> str:
    """Generates a user-friendly explanation for an SQL error using Gemini."""
    prompt_context = f"User's original request (if available): \"{original_user_query}\"\n"
    if not original_user_query:
        prompt_context = "The user was attempting to execute a specific SQL query.\n"

    schema_context = ""
    if schema:
        schema_string = ""
        if not schema or "error" in schema:
            schema_string = "Could not fetch schema."
        else:
            for db_name, tables in schema.items():
                schema_string += f"\nDatabase: `{db_name}`\n"
                if isinstance(tables, dict):
                    if not tables:
                        schema_string += "  (No tables found or accessible)\n"
                    elif "error" in tables:
                        schema_string += f"  Error fetching tables: {tables['error']}\n"
                    else:
                        for table_name, columns in tables.items():
                            col_string = ', '.join([f"`{c}`" for c in columns])
                            schema_string += f"  - Table: `{table_name}`: Columns: {col_string}\n"
                else:
                    schema_string += f"  Error retrieving table details for this database.\n"
        schema_context = f"""
For context, here is the database schema the query was run against:
{schema_string}
"""

    prompt = f"""You are an expert SQL troubleshooting assistant.

The following SQL query failed:
```sql
{failed_sql_query}
```

The database returned this error message:
{error_message}

{prompt_context}
{schema_context}
Instructions:
- Explain the error message in simple, easy-to-understand terms in 5-10 sentences maximum.
- **Use the provided database schema to give a specific, actionable suggestion.** For example, if a column name is wrong, suggest the correct one from the schema.
- What are the common reasons for this specific error?
- What should the user check or try to resolve this issue?
- If the error indicates the table is not insertable (e.g., it's a view), explain what that means.
- Format your response clearly using Markdown. Start with "### AI Troubleshooting Suggestion".
- Do not repeat the SQL query or the raw error message unless it's for specific emphasis within your explanation.

Explanation:"""

    # Combine history with the new prompt
    request_contents = history + [{"role": "user", "parts": [{"text": prompt}]}]

    try:
        if not gemini_client:
            return "Error: Gemini client not initialized."
            
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=request_contents
        )
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            logger.warning(f"Error explanation response blocked. Reason: {response.prompt_feedback.block_reason}")
            return "AI explanation could not be generated for this error due to content restrictions."
        logger.info("Gemini generated SQL error explanation.")
        return response.text.strip() if response.text else "An AI explanation could not be generated for this error."
    except Exception as e:
        logger.error(f"Error calling Gemini API for SQL error explanation: {e}", exc_info=True)
        return "Error generating AI explanation for the SQL error."

def get_query_risk_level(sql_query: str) -> int:
    """
    Classifies a query into a risk level based on its type. This is a primary safeguard
    to prevent accidental or malicious database structure changes.

    Returns:
        0: Read-only (safe to execute immediately).
        1: Data-modifying (requires user confirmation).
        2: Structure-modifying or potentially unsafe (should be blocked).
    """
    # Whitelists for different statement types identified by sqlparse
    read_only_types = ["SELECT", "USE"]
    data_modifying_types = ["INSERT", "UPDATE", "DELETE", "CREATE"]
    # Any DDL or DCL is considered structure-modifying and high-risk
    structure_modifying_types = ["ALTER", "DROP", "TRUNCATE", "GRANT", "REVOKE", "RENAME"]

    # Quick check for common safe commands that sqlparse might label as 'UNKNOWN'
    query_upper = sql_query.strip().upper()
    if any(query_upper.startswith(kw) for kw in ["SHOW", "DESCRIBE", "EXPLAIN"]):
        return 0

    try:
        parsed_statements = sqlparse.parse(sql_query)
        if not parsed_statements:
            logger.warning("Could not parse SQL query. Flagging as high-risk for safety.")
            return 2  # Fail-closed: If parsing fails, assume it's unsafe.

        # If there are multiple statements, we block it for safety to prevent complex attacks.
        if len(parsed_statements) > 1:
            logger.warning(f"Detected multiple SQL statements. Blocking for security: {sql_query}")
            return 2

        if not parsed_statements or len(parsed_statements) == 0:
            logger.warning("No SQL statements parsed. Flagging as high-risk for safety.")
            return 2

        try:
            stmt = parsed_statements[0]
            stmt_type = stmt.get_type()
            stmt_upper = str(stmt).strip().upper()
        except Exception as e:
            logger.error(f"Error accessing parsed SQL statement: {e}. Flagging as high-risk.")
            return 2

        if stmt_type in structure_modifying_types:
            logger.warning(f"Detected structure-modifying query (by type '{stmt_type}'). Blocking.")
            return 2

        if stmt_type in data_modifying_types:
            return 1

        if stmt_type in read_only_types:
            # Secondary check for dangerous clauses sometimes found in SELECT statements
            if "INTO OUTFILE" in stmt_upper or "INTO DUMPFILE" in stmt_upper:
                logger.warning(f"Detected potentially harmful 'SELECT...INTO' clause. Blocking.")
                return 2
            return 0

        # If the type is UNKNOWN or something else not on our lists, we block it.
        logger.warning(f"Detected query with unclassified type '{stmt_type}'. Blocking for safety.")
        return 2

    except Exception as e:
        logger.error(f"Failed to parse SQL query for security check: {e}. Flagging as high-risk.")
        return 2 # If any other exception occurs during parsing, fail-closed.

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str


class ConfigRequest(BaseModel):
    mysql_host: str
    mysql_user: str
    mysql_password: str
    gemini_api_key: str


class PublicConfig(BaseModel):
    mysql_host: str
    mysql_user: str
    mysql_password_set: bool
    gemini_api_key_set: bool


class ConfirmedExecutionRequest(BaseModel):
    query: str


# --- FastAPI Application ---

app = FastAPI(title="SQL Assistant with Gemini")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=".") # Expect index.html in the root directory

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serves the main HTML page and ensures a session cookie is set
    for the first-time visitor.
    """
    response = templates.TemplateResponse("index.html", {"request": request})

    # If no session cookie is present on the incoming request, create one.
    if "session_id" not in request.cookies:
        session_id = uuid.uuid4()
        initial_data = SessionData()
        # Add the welcome message to the history for this new session - REMOVED
        # add_to_history(initial_data, "model", "Hello! I'm your SQL assistant. How can I help you with your databases today?")
        await session_backend.create(session_id, initial_data)
        cookie.attach_to_response(response, session_id)

    return response

@app.get("/config_status", response_model=PublicConfig)
async def get_config_status():
    """API endpoint to fetch the current, non-sensitive configuration status."""
    return PublicConfig(
        mysql_host=MYSQL_HOST,
        mysql_user=MYSQL_USER,
        mysql_password_set=bool(MYSQL_PASSWORD), # True if password is not an empty string
        gemini_api_key_set=bool(GEMINI_API_KEY)  # True if key is not an empty string
    )

@app.get("/schema", response_class=JSONResponse)
async def get_schema():
    """API endpoint to fetch the current database schema."""
    schema = fetch_all_tables_and_columns()
    if "error" in schema:
         # Returning 200 but with error content for client-side handling
         return JSONResponse(content={"schema": schema}, status_code=200)
    return JSONResponse(content={"schema": schema})

@app.post("/reset_chat", response_class=JSONResponse)
async def reset_chat(session_id: uuid.UUID = Depends(cookie)):
    """API endpoint to clear the server-side chat history for the current session."""
    # Create a new, empty session data object
    new_session_data = SessionData()
    # Replace the old session data with the new empty one
    await session_backend.update(session_id, new_session_data)
    logger.info(f"Chat history for session {session_id} has been reset.")
    return JSONResponse(content={"status": "success", "message": "Chat history has been reset."})

@app.post("/config", response_class=JSONResponse)
async def update_config(config_request: ConfigRequest):
    """Updates application configuration and tests connections."""
    try:
        mysql_host = config_request.mysql_host if config_request.mysql_host else "localhost"
        mysql_user = config_request.mysql_user if config_request.mysql_user else "root"
        mysql_password = config_request.mysql_password if config_request.mysql_password else "root"
        gemini_api_key = config_request.gemini_api_key if config_request.gemini_api_key else ""
        
        config_data = {
            "mysql_host": mysql_host,
            "mysql_user": mysql_user,
            "mysql_password": mysql_password,
            "gemini_api_key": gemini_api_key
        }
        
        mysql_status = "failed: unknown"
        try: # Test MySQL connection
            conn = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                auth_plugin='mysql_native_password'
            )
            conn.close()
            mysql_status = "success"
        except mysql.connector.Error as err:
            logger.error(f"Failed to connect with new MySQL credentials: {err}")
            mysql_status = f"failed: {err}"
            
        gemini_status = "failed: unknown"
        original_key = GEMINI_API_KEY
        try: # Test Gemini API key
            if gemini_api_key:
                # Use the new SDK's client for testing
                test_client = genai.Client(api_key=gemini_api_key)
                test_response = test_client.models.generate_content(
                    model=GEMINI_MODEL_NAME,
                    contents="ping",
                    config={
                        "max_output_tokens": 1
                    }
                )
                if test_response.text:
                    gemini_status = "success"
                else:
                    gemini_status = "failed: no response"
            else:
                gemini_status = "not_provided"
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API with new key: {e}")
            gemini_status = f"failed: {e}"
            # Restore the original key if test failed
            os.environ["GEMINI_API_KEY"] = original_key
            if original_key: initialize_gemini_api() 
        
        update_environment(config_data) # Update environment and .env file
        
        return JSONResponse(content={
            "status": "success",
            "mysql_connection": mysql_status,
            "gemini_api": gemini_status,
            "message": "Configuration updated. Check connection statuses.",
            "restart_needed": False 
        })
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return JSONResponse(
            content={"status": "error", "message": f"Failed to update configuration: {str(e)}"},
            status_code=500
        )

@app.post("/chat", response_class=JSONResponse)
async def handle_chat(chat_request: ChatRequest, session_id: uuid.UUID = Depends(cookie), session_data: SessionData = Depends(session_verifier)):
    """Handles user messages, directs to SQL generation or conversational response, and executes SQL."""
    user_message = chat_request.message.strip()
    response_data: Dict[str, Any] = {"type": "error", "content": "An unexpected error occurred."}
    query_to_run: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None 
    
    # Use a copy of the session history for this request to avoid modifying it mid-process
    history = list(session_data.history)

    try:
        # Step 1: Determine the query to run, either from a /run command or by generating it.
        if user_message.lower().startswith("/run "):
            query_to_run = user_message[5:].strip()
            if not query_to_run:
                response_data = {"type": "error", "content": "No query provided after /run command."}
                return JSONResponse(content=response_data)
        else:
            logger.info(f"Processing natural language query: {user_message}")
            schema = fetch_all_tables_and_columns()
            if "error" in schema:
                error_msg = "Could not fetch database schema to process your request."
                if schema.get("error", {}).get("schema"):
                    error_msg += f" Error: {', '.join(schema['error']['schema'])}"
                response_data = {"type": "error", "content": error_msg}
                return JSONResponse(content=response_data)

            generated_sql = generate_sql_with_gemini(user_message, schema, history)
            model_response_text = ""

            if generated_sql and generated_sql.strip().lower().startswith("error: this is a conversational query"):
                logger.info("AI determined this is a conversational query. Replying with a generic message.")
                model_response_text = get_conversational_response_with_gemini(user_message, history)
                response_data = {"type": "info", "content": model_response_text}
                
                # CORRECTED LOGIC: Add to history only on success
                add_to_history(session_data, "user", user_message)
                add_to_history(session_data, "model", model_response_text)
                await session_backend.update(session_id, session_data) # Persist the change

                return JSONResponse(content=jsonable_encoder(response_data))

            if not generated_sql or generated_sql.lower().startswith("error:"):
                error_message = generated_sql if generated_sql else "The AI model could not generate an SQL query. Please try rephrasing."
                response_data = {"type": "error", "content": error_message}
                return JSONResponse(content=response_data)
            
            query_to_run = generated_sql.strip()
            # DO NOT add to history here yet. Wait for execution result.

        # Step 2: Centralized security check for the determined query
        risk_level = get_query_risk_level(query_to_run)

        if risk_level == 2: # Block structure-modifying or unsafe queries
            logger.warning(f"Blocking high-risk query: {query_to_run}")
            response_data = {
                "type": "error",
                "content": "This action was blocked for security reasons.",
                "ai_explanation": "The submitted query was identified as potentially altering database structure (e.g., using `CREATE`, `DROP`, `ALTER`) or containing other unsafe patterns. For safety, only data manipulation (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) and simple `SHOW` commands are processed."
            }
            return JSONResponse(content=jsonable_encoder(response_data))

        elif risk_level == 1: # Require confirmation for data-modifying queries
            logger.info(f"Query requires confirmation: {query_to_run}")
            response_data = {
                "type": "confirm_execution",
                "query": query_to_run,
                "message": "You are attempting to run the following query which may modify your data. Please review and confirm execution:"
            }
            return JSONResponse(content=jsonable_encoder(response_data))
        
        # Step 3: If query is safe (risk_level == 0), proceed with execution.
        
        # Special handling for plain 'SHOW TABLES;' to add context
        if query_to_run.strip().lower() == 'show tables;':
            logger.info("Detected plain 'SHOW TABLES;' query. Checking database context...")
            current_schema = schema or fetch_all_tables_and_columns()
            user_databases = [
                db for db, tables in current_schema.items()
                if db != 'error' and db not in {'information_schema', 'mysql', 'performance_schema', 'sys'} and isinstance(tables, dict) and 'error' not in tables
            ]
            if len(user_databases) == 1:
                db_to_use = user_databases[0]
                logger.info(f"Found single user database '{db_to_use}'. Rewriting query.")
                query_to_run = f"SHOW TABLES FROM `{db_to_use}`;"

            elif len(user_databases) > 1:
                logger.warning("Multiple user databases exist. Cannot execute plain 'SHOW TABLES;'.")
                response_data = {
                    "type": "error",
                    "content": f"Please specify which database's tables you want to see. Multiple databases found: {', '.join(user_databases)}. \nTry 'show tables from database_name;' or ask like 'what tables are in {user_databases[0]}?'."
                }
                return JSONResponse(content=jsonable_encoder(response_data))
            else: # No user databases found
                logger.warning("No user databases found to execute 'SHOW TABLES;' against.")
                response_data = { "type": "error", "content": "No user databases found or accessible. Cannot show tables." }
                return JSONResponse(content=jsonable_encoder(response_data))
        
        # --- Direct execution for safe (risk_level == 0) queries ---
        logger.info(f"Executing safe, final query: {query_to_run}")
        results, columns, col_types, status, db_error = execute_sql_query(query_to_run)
        
        if status == 3: # SQL Error
            if schema is None:
                logger.info("Fetching schema for error context.")
                schema = fetch_all_tables_and_columns()

            # Determine original intent for better AI explanation
            original_intent = user_message if not user_message.lower().startswith("/run ") else None
            
            error_content = f"Query failed to execute:\n```sql\n{query_to_run}\n```\nError: {db_error or 'Unknown SQL execution error.'}"
            ai_explanation = get_error_explanation_with_gemini(original_user_query=original_intent, failed_sql_query=query_to_run, error_message=str(db_error), schema=schema, history=history)
            response_data = {"type": "error", "content": error_content, "ai_explanation": ai_explanation}
            # FAILED, so we don't add to history.

        elif status == 2: # DML/DDL Success (Should not be reached from this endpoint anymore)
            response_data = {"type": "info", "content": f"Query executed successfully:\n\n```sql\n{query_to_run}\n```"}
        elif status == 1: # SELECT/SHOW Success
            insights = ""
            # CORRECTED LOGIC: Add user message and generated SQL to history now.
            add_to_history(session_data, "user", user_message)
            add_to_history(session_data, "model", query_to_run)

            if results is not None and columns and col_types:
                original_user_intent = user_message
                if user_message.lower().startswith("/run "): original_user_intent = f"Direct execution: {user_message[5:].strip()}"
                insights = get_insights_with_gemini(original_query=original_user_intent, sql_query=query_to_run, results=results, columns=columns, col_types=col_types, history=history)
            response_data = {"type": "result", "query": query_to_run, "columns": columns, "results": results, "insights": insights }
            
            # If insights were generated, add them as a separate model response for better context
            if insights:
                add_to_history(session_data, "model", insights)
            
            await session_backend.update(session_id, session_data) # Persist changes

        else: 
            response_data = {"type": "error", "content": "Unknown query execution status."}

        return JSONResponse(content=jsonable_encoder(response_data))
    
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        raise http_exc # Re-raise HTTPException to let FastAPI handle it
    except Exception as e:
        logger.critical(f"Unhandled error in /chat endpoint: {e}", exc_info=True)
        response_data = {"type": "error", "content": f"An internal server error occurred: {e}"}
        return JSONResponse(content=response_data, status_code=500)

@app.post("/execute_confirmed_sql", response_class=JSONResponse)
async def handle_confirmed_sql(request: ConfirmedExecutionRequest, session_id: uuid.UUID = Depends(cookie), session_data: SessionData = Depends(session_verifier)):
    """Executes a SQL query that has been confirmed by the user."""
    query_to_run = request.query.strip()
    response_data: Dict[str, Any] = {"type": "error", "content": "An unexpected error occurred."}
    history = list(session_data.history)

    if not query_to_run:
        response_data = {"type": "error", "content": "No query provided for execution."}
        return JSONResponse(content=response_data, status_code=400)

    try:
        logger.info(f"Executing user-confirmed query: {query_to_run}")
        results, columns, col_types, status, db_error = execute_sql_query(query_to_run)
        
        if status == 3: # SQL Error
            error_content = f"Confirmed query failed to execute:\n```sql\n{query_to_run}\n```\nError: {db_error or 'Unknown SQL execution error.'}"
            schema = fetch_all_tables_and_columns()
            ai_explanation = get_error_explanation_with_gemini(original_user_query=f"User confirmed execution of the following SQL", failed_sql_query=query_to_run, error_message=str(db_error), schema=schema, history=history)
            response_data = {"type": "error", "content": error_content, "ai_explanation": ai_explanation}
        elif status == 2: # DML/DDL Success
            response_data = {"type": "info", "content": f"Query executed successfully:\n\n```sql\n{query_to_run}\n```"}
            # CORRECTED LOGIC: Add successful DML query to history
            add_to_history(session_data, "model", query_to_run) # The user prompt is already in history
            await session_backend.update(session_id, session_data)

        elif status == 1: # SELECT/SHOW Success (less likely for confirmed DML/DDL, but handle robustly)
            response_data = {
                "type": "result", 
                "query": query_to_run,
                "columns": columns,
                "results": results,
                "insights": "Query executed. Insights are typically generated for natural language queries leading to SELECT."
            }
            # CORRECTED LOGIC: Also add this to history
            add_to_history(session_data, "model", query_to_run)
            await session_backend.update(session_id, session_data)
        else: 
            response_data = {"type": "error", "content": "Unknown query execution status."}

        return JSONResponse(content=jsonable_encoder(response_data))

    except Exception as e:
        logger.critical(f"Unhandled error in /execute_confirmed_sql endpoint: {e}", exc_info=True)
        response_data = {"type": "error", "content": f"An internal server error occurred: {e}"}
        return JSONResponse(content=response_data, status_code=500)

@app.on_event("startup")
async def startup_event():
    """Initializes a new session for the root endpoint, as it won't have a cookie yet."""
    # This is a workaround to ensure the very first visit gets a session.
    session_id = uuid.uuid4()
    initial_data = SessionData()
    # Pre-populate the first session with a welcome message - REMOVED
    # add_to_history(initial_data, "model", "Hello! I'm your SQL assistant. How can I help you with your databases today?")
    await session_backend.create(session_id, initial_data)
    # The frontend will receive this session_id via the response from "/"
    
    # We need a way to pass this to the root response. A simple global might suffice for this narrow case.
    # A better approach might involve a middleware that creates sessions if they don't exist.
    app.state.initial_session_id = session_id

# --- Main Execution ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting SQL Assistant server...")
    # Add a welcome message to the history on startup - REMOVED
    # clear_chat_history() - REMOVED
    # add_to_history("model", "Hello! I'm your SQL assistant. How can I help you with your databases today?") - REMOVED
    # Start the server even if Gemini API key is missing; it can be set later via /config
    uvicorn.run(app, host="0.0.0.0", port=8012)