import os
import logging
import json
from typing import List, Dict, Any, Tuple, Optional

import mysql.connector
from mysql.connector import FieldType
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import functools

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Logging Configuration - moved to the top
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration with defaults
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "SQLLLM")

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = "gemini-2.0-flash"

# Variable to track if Gemini API is initialized
gemini_initialized = False

# Path to .env file
ENV_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

# Function to initialize Gemini API
def initialize_gemini_api():
    global gemini_initialized
    try:
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            gemini_initialized = True
            logger.info("Gemini API initialized successfully")
            return True
        else:
            logger.warning("GEMINI_API_KEY not found. Some features will be limited.")
            gemini_initialized = False
            return False
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {e}")
        gemini_initialized = False
        return False

# Initialize Gemini API on startup
initialize_gemini_api()

# ADDED: Decorator to check Gemini API initialization
def ensure_gemini_initialized(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not gemini_initialized:
            # Log the issue, the function itself will return an error message string
            logger.warning(f"Gemini API not initialized. Call to {func.__name__} will be skipped.")
            # Depending on the function's expected return type, you might return a specific error object/string.
            # For these functions, they are expected to return a string, so we return an error string.
            return "Error: Gemini API not configured. Please set up your API key in the configuration."
        return func(*args, **kwargs)
    return wrapper

# Function to update environment variables and .env file
def update_environment(config_data):
    """Updates environment variables and .env file with new configurations."""
    global MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, GEMINI_API_KEY
    
    # Define default values for each configuration
    defaults = {
        "mysql_host": "localhost",
        "mysql_user": "root",
        "mysql_password": "root",
        "mysql_database": "SQLLLM",
        "gemini_api_key": ""
    }
    
    # Update environment variables with non-empty values or defaults
    if "mysql_host" in config_data and config_data["mysql_host"]:
        MYSQL_HOST = config_data["mysql_host"]
    else:
        MYSQL_HOST = defaults["mysql_host"]
    os.environ["MYSQL_HOST"] = MYSQL_HOST
    
    if "mysql_user" in config_data and config_data["mysql_user"]:
        MYSQL_USER = config_data["mysql_user"]
    else:
        MYSQL_USER = defaults["mysql_user"]
    os.environ["MYSQL_USER"] = MYSQL_USER
    
    if "mysql_password" in config_data and config_data["mysql_password"]:
        MYSQL_PASSWORD = config_data["mysql_password"]
    else:
        MYSQL_PASSWORD = defaults["mysql_password"]
    os.environ["MYSQL_PASSWORD"] = MYSQL_PASSWORD
    
    if "mysql_database" in config_data and config_data["mysql_database"]:
        MYSQL_DATABASE = config_data["mysql_database"]
    else:
        MYSQL_DATABASE = defaults["mysql_database"]
    os.environ["MYSQL_DATABASE"] = MYSQL_DATABASE
    
    if "gemini_api_key" in config_data and config_data["gemini_api_key"]:
        GEMINI_API_KEY = config_data["gemini_api_key"]
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
        # Reinitialize Gemini API with new key
        initialize_gemini_api()
    
    # Update .env file
    update_env_file(config_data, defaults)
    
    logger.info("Environment variables updated with new configuration")

# Function to update .env file
def update_env_file(config_data, defaults):
    """Updates .env file with new configuration data."""
    try:
        # Create a new .env file if it doesn't exist
        if not os.path.exists(ENV_FILE_PATH):
            with open(ENV_FILE_PATH, "w") as env_file:
                env_file.write(f"MYSQL_HOST={config_data.get('mysql_host', defaults['mysql_host'])}\n")
                env_file.write(f"MYSQL_USER={config_data.get('mysql_user', defaults['mysql_user'])}\n")
                env_file.write(f"MYSQL_PASSWORD={config_data.get('mysql_password', defaults['mysql_password'])}\n")
                env_file.write(f"MYSQL_DATABASE={config_data.get('mysql_database', defaults['mysql_database'])}\n")
                env_file.write(f"GEMINI_API_KEY={config_data.get('gemini_api_key', defaults['gemini_api_key'])}\n")
                logger.info("Created .env file with new configuration")
        else:
            # Read existing .env file
            try:
                with open(ENV_FILE_PATH, "r") as env_file:
                    lines = env_file.readlines()
            except Exception as e:
                logger.error(f"Error reading .env file: {e}")
                # If reading fails, create a new file
                with open(ENV_FILE_PATH, "w") as env_file:
                    env_file.write(f"MYSQL_HOST={config_data.get('mysql_host', defaults['mysql_host'])}\n")
                    env_file.write(f"MYSQL_USER={config_data.get('mysql_user', defaults['mysql_user'])}\n")
                    env_file.write(f"MYSQL_PASSWORD={config_data.get('mysql_password', defaults['mysql_password'])}\n")
                    env_file.write(f"MYSQL_DATABASE={config_data.get('mysql_database', defaults['mysql_database'])}\n")
                    env_file.write(f"GEMINI_API_KEY={config_data.get('gemini_api_key', defaults['gemini_api_key'])}\n")
                    logger.info("Created new .env file after read failure")
                return
                
            # Update existing lines or add new ones
            updated_lines = []
            updated_keys = {"MYSQL_HOST": False, "MYSQL_USER": False, "MYSQL_PASSWORD": False, 
                          "MYSQL_DATABASE": False, "GEMINI_API_KEY": False}
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):  # Preserve comments and blank lines
                    updated_lines.append(line + "\n")
                    continue
                
                if "=" not in line:  # Skip malformed lines
                    updated_lines.append(line + "\n")
                    continue
                    
                key, _ = line.split("=", 1)
                key = key.strip()
                
                if key == "MYSQL_HOST":
                    updated_lines.append(f"MYSQL_HOST={config_data.get('mysql_host', defaults['mysql_host'])}\n")
                    updated_keys["MYSQL_HOST"] = True
                elif key == "MYSQL_USER":
                    updated_lines.append(f"MYSQL_USER={config_data.get('mysql_user', defaults['mysql_user'])}\n")
                    updated_keys["MYSQL_USER"] = True
                elif key == "MYSQL_PASSWORD":
                    updated_lines.append(f"MYSQL_PASSWORD={config_data.get('mysql_password', defaults['mysql_password'])}\n")
                    updated_keys["MYSQL_PASSWORD"] = True
                elif key == "MYSQL_DATABASE":
                    updated_lines.append(f"MYSQL_DATABASE={config_data.get('mysql_database', defaults['mysql_database'])}\n")
                    updated_keys["MYSQL_DATABASE"] = True
                elif key == "GEMINI_API_KEY":
                    updated_lines.append(f"GEMINI_API_KEY={config_data.get('gemini_api_key', defaults['gemini_api_key'])}\n")
                    updated_keys["GEMINI_API_KEY"] = True
                else:
                    updated_lines.append(line + "\n")  # Preserve other environment variables
            
            # Add any missing keys
            for key, updated in updated_keys.items():
                if not updated:
                    if key == "MYSQL_HOST":
                        updated_lines.append(f"MYSQL_HOST={config_data.get('mysql_host', defaults['mysql_host'])}\n")
                    elif key == "MYSQL_USER":
                        updated_lines.append(f"MYSQL_USER={config_data.get('mysql_user', defaults['mysql_user'])}\n")
                    elif key == "MYSQL_PASSWORD":
                        updated_lines.append(f"MYSQL_PASSWORD={config_data.get('mysql_password', defaults['mysql_password'])}\n")
                    elif key == "MYSQL_DATABASE":
                        updated_lines.append(f"MYSQL_DATABASE={config_data.get('mysql_database', defaults['mysql_database'])}\n")
                    elif key == "GEMINI_API_KEY":
                        updated_lines.append(f"GEMINI_API_KEY={config_data.get('gemini_api_key', defaults['gemini_api_key'])}\n")
            
            # Write updated .env file
            with open(ENV_FILE_PATH, "w") as env_file:
                env_file.writelines(updated_lines)
                logger.info("Updated .env file with new configuration")
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")

# --- Database Interaction ---

# MODIFY get_db_connection to accept optional db_name
def get_db_connection(db_name: Optional[str] = None):
    """
    Establishes a connection to the MySQL server.
    Connects to a specific database if db_name is provided.
    """
    try:
        conn_params = {
            'host': MYSQL_HOST,
            'user': MYSQL_USER,
            'password': MYSQL_PASSWORD,
            'pool_name': "mypool", # Optional: Use connection pooling
            'pool_size': 5,       # Optional: Pool size
            'auth_plugin': 'mysql_native_password'
        }
        if db_name:
            conn_params['database'] = db_name

        conn = mysql.connector.connect(**conn_params)
        logger.info(f"DB connection established (Database: {db_name or 'None'})")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Database connection error (connecting to {db_name or 'server'}): {err}")
        # Don't raise HTTPException here directly, let caller handle None return or raise
        # raise HTTPException(status_code=500, detail=f"Database connection failed: {err}")
        return None # Return None on connection failure
def execute_sql_query(query: str) -> Tuple[Optional[List[Tuple]], Optional[List[str]], Optional[str], int, Optional[str]]:
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
    results: Optional[List[Tuple]] = None # Initialize results
    column_names: Optional[List[str]] = None
    column_types_str: Optional[str] = None

    try:
        # Connect WITHOUT specifying a default database
        conn = get_db_connection(db_name=None)
        if not conn:
            # Handle connection failure
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
            if cursor.description: # Check if description exists (it might not for some SHOW commands)
                column_names = [i[0] for i in cursor.description]
                # Ensure FieldType is imported or defined
                from mysql.connector.constants import FieldType
                col_dtypes = [[i[0], FieldType.get_info(i[1])] for i in cursor.description]
                column_types_str = 'Column : Dtype\n' + '\n'.join(f'{k}: {v}' for k, v in col_dtypes)
            else:
                column_names = ["Result"] # Default column name if description is unavailable
                column_types_str = "Column : Dtype\nResult: <unknown>"
                # Adjust results structure if needed based on the specific SHOW command
                # Check if results is not None and not empty before accessing results[0]
                if results and isinstance(results[0], (str, int, float, bytes)): # Added bytes type
                     results = [(r,) for r in results] # Wrap single values in tuples

            # conn is guaranteed to be non-None here due to the check above
            conn.commit() # Necessary even for SELECT with some configurations/engines
            # results is guaranteed to be a list (possibly empty) by fetchmany
            result_count = len(results) if results is not None else 0
            logger.info(f"Query executed successfully, fetched {result_count} rows.")
            return results, column_names, column_types_str, 1, None
        else:
            # conn is guaranteed to be non-None here
            conn.commit()
            logger.info("Non-SELECT/SHOW query executed successfully.")
            return None, None, None, 2, None # Success for non-select queries

    except mysql.connector.Error as e:
        logger.error(f"SQL Error executing query '{query}': {e}")
        error_message = f"SQL Error: {e}"
        # Rollback changes if an error occurs during non-select queries
        if conn:
            try:
                conn.rollback()
            except mysql.connector.Error as rb_err:
                logger.error(f"Error during rollback: {rb_err}")
        return None, None, None, 3, error_message
    except Exception as e:
        logger.error(f"Unexpected error executing query '{query}': {e}", exc_info=True)
        error_message = f"Unexpected Error: {e}"
        # Rollback changes if an unexpected error occurs
        if conn:
             try:
                 conn.rollback()
             except mysql.connector.Error as rb_err:
                 logger.error(f"Error during rollback: {rb_err}")
        return None, None, None, 3, error_message
    finally:
        if cursor:
            cursor.close()
        # Check conn exists and is connected before closing
        if conn and conn.is_connected():
            conn.close()
            logger.info("DB connection closed.")


# REWRITE fetch_all_tables_and_columns to fetch from multiple databases
def fetch_all_tables_and_columns() -> Dict[str, Dict[str, List[str]]]:
    """
    Fetches all non-system databases, their tables, and columns.
    Returns: Dict[db_name, Dict[table_name, List[column_name]]]
    """
    schema_info: Dict[str, Dict[str, List[str]]] = {}
    conn = None
    cursor = None
    # Exclude system databases
    system_databases = {'information_schema', 'mysql', 'performance_schema', 'sys'}

    try:
        # Connect without specifying a database
        conn = get_db_connection(db_name=None)
        if not conn:
             logger.error("Failed to get DB connection for schema fetching.")
             return {"error": {"schema": ["Failed to connect to the database server."]}}

        cursor = conn.cursor()

        # Get all databases
        cursor.execute("SHOW DATABASES;")
        fetch_result = cursor.fetchall()
        if fetch_result is None:
            logger.warning("No databases returned from SHOW DATABASES query.")
            return {}
        databases = [row[0] for row in fetch_result if row[0] not in system_databases]

        if not databases:
            logger.warning("No user databases found.")
            return {} # Return empty if no relevant databases

        # Get tables and columns for each relevant database
        for db_name in databases:
            schema_info[db_name] = {}
            try:
                cursor.execute(f"SHOW TABLES FROM `{db_name}`;")
                fetch_result = cursor.fetchall()
                if fetch_result is None:
                    logger.warning(f"No tables returned for database {db_name}.")
                    tables = []
                else:
                    tables = [row[0] for row in fetch_result]

                for table_name in tables:
                    try:
                        cursor.execute(f"SHOW COLUMNS FROM `{db_name}`.`{table_name}`;")
                        fetch_result = cursor.fetchall()
                        if fetch_result is None:
                            logger.warning(f"No columns returned for table {db_name}.{table_name}.")
                            columns = []
                        else:
                            columns = [column[0] for column in fetch_result]
                        schema_info[db_name][table_name] = columns
                    except mysql.connector.Error as e:
                        logger.warning(f"Could not fetch columns for table {db_name}.{table_name}: {e}")
                        schema_info[db_name][table_name] = [f"Error fetching columns: {e}"]

            except mysql.connector.Error as e:
                 logger.warning(f"Could not fetch tables for database {db_name}: {e}")
                 # Add an error placeholder for the database if tables couldn't be listed
                 schema_info[db_name] = {"error": [f"Error fetching tables: {e}"]}

        logger.info(f"Fetched schema for {len(databases)} databases.")
        return schema_info

    except mysql.connector.Error as e:
        logger.error(f"SQL Error fetching database list: {e}")
        return {"error": {"schema": [f"SQL Error fetching databases: {e}"]}} # Indicate error in schema structure
    except Exception as e:
        logger.error(f"Error fetching schema: {e}", exc_info=True)
        return {"error": {"schema": [f"Unexpected error fetching schema: {str(e)}"]}}
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# --- Gemini API Interaction ---

# MODIFY schema_string generation in generate_sql_with_gemini
@ensure_gemini_initialized
def generate_sql_with_gemini(user_query: str, schema: Dict[str, Dict[str, List[str]]]) -> Optional[str]:
    """Generates an SQL query using the Gemini API based on user input and multi-DB schema."""
    # Check if Gemini API is initialized - REMOVED, HANDLED BY DECORATOR
    # if not gemini_initialized:
    #     return "Error: Gemini API not configured. Please set up your API key in the configuration."
        
    schema_string = ""
    if not schema or "error" in schema: # Check for top-level error
         schema_string = "Could not fetch schema. Please ensure database connection is correct."
    else:
        for db_name, tables in schema.items():
            schema_string += f"\nDatabase: `{db_name}`\n"
            if isinstance(tables, dict): # Check if it's a dictionary of tables or an error list
                if not tables:
                     schema_string += "  (No tables found or accessible)\n"
                elif "error" in tables:
                     schema_string += f"  Error fetching tables: {tables['error']}\n"
                else:
                    for table_name, columns in tables.items():
                        col_string = ', '.join([f"`{c}`" for c in columns])
                        schema_string += f"  - Table: `{table_name}`: Columns: {col_string}\n"
            else:
                 # Handle case where schema[db_name] might be an error list itself (though unlikely with current fetch logic)
                 schema_string += f"  Error retrieving table details for this database.\n"


    prompt = f"""You are an expert SQL assistant. Given the following database schema across potentially multiple databases and a user question, generate the most appropriate SQL query to answer the question.

Database Schema:
{schema_string}

User Question: "{user_query}"

Instructions:
- Analyze the user question and the schema carefully.
- If querying a table, use the fully qualified name (e.g., `database_name`.`table_name`) unless the query context makes the database obvious or only one database exists. Prefer qualified names for clarity.
- Generate only **one single** SQL statement. Do not include multiple statements separated by semicolons (`;`).
- Do not include any explanations, introductory text, backticks (```sql), or markdown formatting.
- Ensure the query is syntactically correct for MySQL.
- If the question cannot be answered with the given schema or is ambiguous, respond with "Error: Cannot answer question with available schema."

SQL Query:"""

    # --- rest of the function remains the same ---
    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)

        # Clean up potential markdown formatting just in case
        sql_query = response.text.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip() # Remove leading/trailing whitespace

        logger.info(f"Gemini generated SQL: {sql_query}")
        if sql_query.lower().startswith("error:"):
             logger.warning(f"Gemini indicated an error: {sql_query}")
             # Return the error message from Gemini
             return sql_query # Return the error string itself

        # Basic validation (prevent obviously non-SQL responses)
        # Allow for USE statement as well
        if not any(kw in sql_query.lower() for kw in ["select", "insert", "update", "delete", "show", "create", "alter", "drop", "use"]):
             logger.warning(f"Generated text doesn't look like SQL: {sql_query}")
             return "Error: Generated text does not appear to be a valid SQL query." # Return an error string

        return sql_query

    except Exception as e:
        logger.error(f"Error calling Gemini API for SQL generation: {e}", exc_info=True)
        return "Error: Failed to communicate with the AI model for SQL generation." # Return an error string

@ensure_gemini_initialized
def get_insights_with_gemini(original_query: str, sql_query: str, results: List[Tuple], columns: List[str], col_types: str) -> str:
    """Generates insights on the data using the Gemini API."""
    # Check if Gemini API is initialized - REMOVED, HANDLED BY DECORATOR
    # if not gemini_initialized:
    #     return "Insights not available: Gemini API not configured."
        
    if not results:
        return "No results to analyze."

    # Limit results sent to Gemini to avoid exceeding token limits
    results_preview = json.dumps(results[:20], indent=2, default=str) # Send first 20 rows as JSON

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

    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)
        logger.info("Gemini generated insights.")
        return response.text
    except Exception as e:
        logger.error(f"Error calling Gemini API for insights: {e}", exc_info=True)
        return "Error generating insights from the AI model."

# ADD New function for conversational responses
@ensure_gemini_initialized
def get_conversational_response_with_gemini(user_message: str) -> str:
    """Gets a conversational response from Gemini."""
    # Check if Gemini API is initialized - REMOVED, HANDLED BY DECORATOR
    # if not gemini_initialized:
    #     return "I'm sorry, but the Gemini API is not configured. Please set up your API key in the configuration."
        
    logger.info(f"Getting conversational response for: {user_message}")
    prompt = f"""You are a helpful assistant. Respond conversationally and politely to the following user message. Do not attempt to generate SQL or refer to databases unless the user explicitly asks about them in this message.

User Message: "{user_message}"

Assistant Response:"""

    try:
        # Use the same model or potentially a different one optimized for chat if needed
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)
        # Add basic safety check
        if response.prompt_feedback and response.prompt_feedback.block_reason:
             logger.warning(f"Conversational response blocked. Reason: {response.prompt_feedback.block_reason}")
             return "I cannot provide a response to that topic."

        return response.text.strip()

    except Exception as e:
        logger.error(f"Error calling Gemini API for conversational response: {e}", exc_info=True)
        return "I'm having trouble responding right now. Please try again later."

# ADDED: New Gemini function for explaining SQL errors
@ensure_gemini_initialized
def get_error_explanation_with_gemini(original_user_query: Optional[str], failed_sql_query: str, error_message: str) -> str:
    """Generates a user-friendly explanation for an SQL error using Gemini."""
    # if not gemini_initialized: # Handled by decorator
    #     return "AI explanation unavailable: Gemini API not configured."

    prompt_context = f"User's original request (if available): \"{original_user_query}\"\n"
    if not original_user_query:
        prompt_context = "The user was attempting to execute a specific SQL query.\n"

    prompt = f"""You are an expert SQL troubleshooting assistant.

The following SQL query failed:
```sql
{failed_sql_query}
```

The database returned this error message:
{error_message}

{prompt_context}
Instructions:
- Explain the error message in simple, easy-to-understand terms in 5-10 sentences maximum.
- What are the common reasons for this specific error?
- What should the user check or try to resolve this issue?
- If the error indicates the table is not insertable (e.g., it's a view), explain what that means.
- Format your response clearly using Markdown. Start with "### AI Troubleshooting Suggestion".
- Do not repeat the SQL query or the raw error message unless it's for specific emphasis within your explanation.

Explanation:"""

    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            logger.warning(f"Error explanation response blocked. Reason: {response.prompt_feedback.block_reason}")
            return "AI explanation could not be generated for this error due to content restrictions."
        logger.info("Gemini generated SQL error explanation.")
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error calling Gemini API for SQL error explanation: {e}", exc_info=True)
        return "Error generating AI explanation for the SQL error."

# --- FastAPI Application ---

app = FastAPI(title="SQL Assistant with Gemini")

# Mount static files (for CSS, JS if needed later)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=".") # Expect index.html in the same directory

class ChatRequest(BaseModel):
    message: str

# Add ConfigRequest model
class ConfigRequest(BaseModel):
    mysql_host: str
    mysql_user: str
    mysql_password: str
    gemini_api_key: str

# ADDED: Model for confirmed execution request
class ConfirmedExecutionRequest(BaseModel):
    query: str

# ADDED: Helper function to identify modifying queries
def is_modifying_query(sql_query: str) -> bool:
    """Checks if the SQL query is likely to modify data or structure."""
    query_lower = sql_query.strip().lower()
    # Common keywords for DML and DDL that modify data/structure
    # Excludes SELECT, SHOW, DESCRIBE, EXPLAIN, USE (USE changes session state but isn't data destructive)
    modifying_keywords = [
        "insert", "update", "delete", "create", "alter", "drop", "truncate",
        "replace", "merge", "upsert" # Added more comprehensive keywords
    ]
    # Ensure we don't misclassify SELECT ... INTO OUTFILE or similar if not intended.
    # For now, simple keyword check is the goal.
    # Avoid flagging common clauses within SELECTs if they share a keyword (less likely with this list).
    return any(keyword in query_lower for keyword in modifying_keywords)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/schema", response_class=JSONResponse)
async def get_schema():
    """API endpoint to fetch the current database schema."""
    schema = fetch_all_tables_and_columns()
    if "error" in schema:
         # Return a specific error status if schema fetching failed critically
         # For now, returning 200 but with error content
         return JSONResponse(content={"schema": schema}, status_code=200)
    return JSONResponse(content={"schema": schema})

# Add config endpoint
@app.post("/config", response_class=JSONResponse)
async def update_config(config_request: ConfigRequest):
    """Updates application configuration."""
    try:
        # Apply defaults for empty values
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
        
        # Test MySQL connection
        try:
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
            
        # Test Gemini API key
        original_key = GEMINI_API_KEY
        gemini_status = "success"
        
        try:
            # Temporarily set the new key
            os.environ["GEMINI_API_KEY"] = gemini_api_key
            genai.configure(api_key=gemini_api_key)
            test_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
            # Try a simple test generation
            test_response = test_model.generate_content("Hello")
            if test_response.text:
                gemini_status = "success"
            else:
                gemini_status = "failed: no response"
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API with new key: {e}")
            gemini_status = f"failed: {e}"
            # Restore the original key
            os.environ["GEMINI_API_KEY"] = original_key
            initialize_gemini_api()
        
        # Update environment and .env file with new config
        update_environment(config_data)
        
        return JSONResponse(content={
            "status": "success",
            "mysql_connection": mysql_status,
            "gemini_api": gemini_status,
            "message": "Configuration updated and applied immediately. No restart required.",
            "restart_needed": False
        })
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return JSONResponse(
            content={"status": "error", "message": f"Failed to update configuration: {str(e)}"},
            status_code=500
        )

@app.post("/chat", response_class=JSONResponse)
async def handle_chat(chat_request: ChatRequest):
    """Handles user messages, interacts with DB and Gemini."""
    user_message = chat_request.message.strip()
    response_data: Dict[str, Any] = {"type": "error", "content": "An unexpected error occurred."}
    query_to_run = None # Initialize query_to_run
    schema = None # Initialize schema
    generated_sql_for_confirmation = None # To hold SQL that needs confirmation

    try:
        if user_message.lower().startswith("/run "):
            # Direct SQL execution
            query_to_run = user_message[5:].strip() # Get query after "/run "
            if not query_to_run:
                response_data = {"type": "error", "content": "No query provided after /run command."}
                return JSONResponse(content=response_data)
        else:
            # Natural language query -> Attempt SQL Generation FIRST
            logger.info(f"Processing natural language query: {user_message}")
            schema = fetch_all_tables_and_columns() # Fetch schema once
            if "error" in schema:
                 error_msg = "Could not fetch database schema to process your request."
                 if schema.get("error", {}).get("schema"):
                     error_msg += f" Error: {', '.join(schema['error']['schema'])}"
                 response_data = {"type": "error", "content": error_msg}
                 return JSONResponse(content=response_data)

            generated_sql = generate_sql_with_gemini(user_message, schema)

            # --- MODIFICATION START: Check for specific error to fallback ---
            specific_sql_error = "Error: Cannot answer question with available schema."
            if generated_sql == specific_sql_error:
                logger.info(f"SQL generation returned '{specific_sql_error}'. Falling back to conversational response.")
                conversational_response = get_conversational_response_with_gemini(user_message)
                response_data = {"type": "info", "content": conversational_response}
                return JSONResponse(content=jsonable_encoder(response_data))
            # --- MODIFICATION END ---

            # If it wasn't the specific error, proceed with SQL path checks
            elif not generated_sql:
                response_data = {"type": "error", "content": "The AI model could not generate an SQL query for your request. Please try rephrasing or check model availability."}
                return JSONResponse(content=response_data)
            elif generated_sql.lower().startswith("error:"): # Handle other specific errors from generation
                 response_data = {"type": "error", "content": generated_sql}
                 return JSONResponse(content=response_data)
            else:
                # --- NEW: Check if generated SQL is modifying ---
                if is_modifying_query(generated_sql):
                    logger.info(f"Generated modifying SQL, requires confirmation: {generated_sql}")
                    response_data = {
                        "type": "confirm_execution",
                        "query": generated_sql,
                        "message": "The AI generated the following query which may modify your data or database structure. Please review and confirm execution:"
                    }
                    return JSONResponse(content=jsonable_encoder(response_data))
                else:
                    # If SQL was generated successfully and is not modifying, assign it to be run
                    query_to_run = generated_sql
        
        # If we have a query_to_run (either from /run or non-modifying AI gen)
        if query_to_run:
            # --- Logic to handle plain "SHOW TABLES;" (remains the same) ---
            if query_to_run.strip().lower() == 'show tables;':
                logger.info("Detected plain 'SHOW TABLES;' query. Checking database context...")
                # Use schema fetched earlier if available
                current_schema = schema or fetch_all_tables_and_columns()
                user_databases = [
                    db for db, tables in current_schema.items()
                    if db != 'error' and db not in {'information_schema', 'mysql', 'performance_schema', 'sys'} and isinstance(tables, dict) and 'error' not in tables
                ]
                if len(user_databases) == 1:
                    db_to_use = user_databases[0]
                    logger.info(f"Found single user database '{db_to_use}'. Prepending USE statement.")
                    query_to_run = f"USE `{db_to_use}`; {query_to_run}"
                elif len(user_databases) > 1:
                    logger.warning("Multiple user databases exist. Cannot execute plain 'SHOW TABLES;'.")
                    response_data = {
                        "type": "error",
                        "content": f"Please specify which database's tables you want to see. Multiple databases found: {', '.join(user_databases)}. \\nTry 'show tables from database_name;' or ask like 'what tables are in {user_databases[0]}?'."
                    }
                    return JSONResponse(content=jsonable_encoder(response_data))
                else:
                    logger.warning("No user databases found to execute 'SHOW TABLES;' against.")
                    response_data = { "type": "error", "content": "No user databases found or accessible. Cannot show tables." }
                    return JSONResponse(content=jsonable_encoder(response_data))

            # --- Execution logic (remains largely the same) ---
            logger.info(f"Executing final query: {query_to_run}")
            results, columns, col_types, status, db_error = execute_sql_query(query_to_run)
            
            if status == 3: # SQL Error
                 error_content = f"SQL Error: {db_error or 'Query execution failed.'}"
                 ai_explanation = ""
                 # Add context for generated SQL if it was the one that failed
                 if 'generated_sql' in locals() and generated_sql == query_to_run:
                     error_content = f"Generated SQL failed to execute:\n```sql\n{generated_sql}\n```\nError: {db_error or 'Unknown SQL execution error.'}"
                     ai_explanation = get_error_explanation_with_gemini(original_user_query=user_message, failed_sql_query=generated_sql, error_message=str(db_error))
                 elif 'generated_sql' in locals() and query_to_run.endswith(generated_sql): # Check if it's the modified version
                     error_content = f"Generated SQL (modified with USE) failed to execute:\n```sql\n{query_to_run}\n```\nError: {db_error or 'Unknown SQL execution error.'}"
                     # Passing user_message, as it was the origin for the generated_sql part
                     ai_explanation = get_error_explanation_with_gemini(original_user_query=user_message, failed_sql_query=query_to_run, error_message=str(db_error))
                 else: # For /run commands or other cases
                     error_content = f"Query failed to execute:\n```sql\n{query_to_run}\n```\nError: {db_error or 'Unknown SQL execution error.'}"
                     # For /run, the original query *is* the query_to_run. No separate user_message for AI context.
                     ai_explanation = get_error_explanation_with_gemini(original_user_query=None, failed_sql_query=query_to_run, error_message=str(db_error))
                 response_data = {"type": "error", "content": error_content, "ai_explanation": ai_explanation}

            elif status == 2: # DML/DDL Success
                response_data = {"type": "info", "content": f"Query executed successfully:\n\n```sql\n{query_to_run}\n```"}
            elif status == 1: # SELECT/SHOW Success
                 insights = ""
                 if results is not None and columns and col_types:
                     original_user_intent = user_message
                     if user_message.lower().startswith("/run "): original_user_intent = f"Direct execution: {user_message[5:].strip()}"
                     insights = get_insights_with_gemini(original_query=original_user_intent, sql_query=query_to_run, results=results, columns=columns, col_types=col_types)
                 response_data = {"type": "result", "query": query_to_run, "columns": columns, "results": results, "insights": insights }
            else: # Should not happen
                 response_data = {"type": "error", "content": "Unknown query execution status."}
        else:
             # This path is reached if AI generation resulted in a query requiring confirmation,
             # and that confirmation response was already sent.
             # Or if /run was empty and handled, or if generate_sql_with_gemini returned an error that was handled.
             # No further action needed here as the response should have been sent.
             # If response_data is still default, it means an unhandled path.
             if response_data.get("content") == "An unexpected error occurred.":
                 logger.error("Reached end of handler without a query to execute or a confirmation response being sent.")
                 response_data = {"type": "error", "content": "Could not determine an action for your message."}

        return JSONResponse(content=jsonable_encoder(response_data))
    
    except HTTPException as http_exc:
        logger.error(f"HTTP Exception: {http_exc.detail}")
        # Re-raise HTTPException to let FastAPI handle it
        raise http_exc
    except Exception as e:
        logger.critical(f"Unhandled error in /chat endpoint: {e}", exc_info=True)
        # Return a generic server error response
        response_data = {"type": "error", "content": f"An internal server error occurred: {e}"}
        return JSONResponse(content=response_data, status_code=500)

# ADDED: New endpoint for executing confirmed SQL
@app.post("/execute_confirmed_sql", response_class=JSONResponse)
async def handle_confirmed_sql(request: ConfirmedExecutionRequest):
    query_to_run = request.query.strip()
    response_data: Dict[str, Any] = {"type": "error", "content": "An unexpected error occurred."}

    if not query_to_run:
        response_data = {"type": "error", "content": "No query provided for execution."}
        return JSONResponse(content=response_data, status_code=400)

    try:
        logger.info(f"Executing user-confirmed query: {query_to_run}")
        results, columns, col_types, status, db_error = execute_sql_query(query_to_run)

        if status == 3: # SQL Error
            error_content = f"Confirmed query failed to execute:\n```sql\n{query_to_run}\n```\nError: {db_error or 'Unknown SQL execution error.'}"
            # For confirmed SQL, original user query is not directly available here.
            # We can pass the SQL itself as the context for the error explanation.
            ai_explanation = get_error_explanation_with_gemini(original_user_query=f"User confirmed execution of the following SQL", failed_sql_query=query_to_run, error_message=str(db_error))
            response_data = {"type": "error", "content": error_content, "ai_explanation": ai_explanation}
        elif status == 2: # DML/DDL Success
            response_data = {"type": "info", "content": f"Query executed successfully:\n\n```sql\n{query_to_run}\n```"}
        elif status == 1: # SELECT/SHOW Success (unlikely for confirmed DML/DDL, but handle robustly)
            # insights = "" # Decided not to generate insights here for simplicity
            # if results is not None and columns and col_types:
            # insights = get_insights_with_gemini(original_query=f"Confirmed execution of: {query_to_run}", sql_query=query_to_run, results=results, columns=columns, col_types=col_types)
            response_data = {
                "type": "result", # Keep type as result for consistency if it's a SELECT
                "query": query_to_run,
                "columns": columns,
                "results": results,
                "insights": "Query executed. Insights are typically generated for natural language queries leading to SELECT."
            }
        else: # Should not happen
            response_data = {"type": "error", "content": "Unknown query execution status."}

        return JSONResponse(content=jsonable_encoder(response_data))

    except Exception as e:
        logger.critical(f"Unhandled error in /execute_confirmed_sql endpoint: {e}", exc_info=True)
        response_data = {"type": "error", "content": f"An internal server error occurred: {e}"}
        return JSONResponse(content=response_data, status_code=500)


# --- Main Execution ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting SQL Assistant server...")
    # Start the server even if Gemini API key is missing - we can set it later
    uvicorn.run(app, host="0.0.0.0", port=8012)