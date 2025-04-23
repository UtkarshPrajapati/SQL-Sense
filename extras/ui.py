import gradio as gr
import requests
import asyncio
import websockets
import json
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UI_TAB_TITLE = "SQL-Sense"
# global ui, formatted_tables, available_tables_and_columns


def response(user_input, chat_history=None):
    api_url = "http://localhost:8012/sql"
    payload = {"content": user_input}

    try:
        api_response = requests.post(api_url, json=payload)
        api_response.raise_for_status()
        response_data = api_response.json()["content"]

        if isinstance(response_data, dict):
            query = response_data.get("query")
            results = response_data.get("results")
            columns = response_data.get("columns")
            insights = response_data.get("insights")

            if results and columns:
                table_html = """
                <div style='max-height: 400px; overflow-y: auto; border: 1px solid #ddd;'>
                    <table border='1' style='border-collapse: collapse; width: 100%;'>
                        <thead>
                            <tr>"""
                table_html += "".join(
                    [f"<th style='padding: 8px; text-align: left;'>{col}</th>" for col in columns])
                table_html += "</tr></thead><tbody>"
                for row in results:
                    table_html += "<tr>"
                    table_html += "".join(
                        [f"<td style='padding: 8px; text-align: left;'>{col}</td>" for col in row])
                    table_html += "</tr>"
                table_html += "</tbody></table></div>"

                return f"SQL Query: {query}<br><br>{table_html}<br><br>Data Insights: {insights}"
            else:
                return "No results found or query executed successfully."
        else:
            return response_data
    except requests.exceptions.RequestException as e:
        return f"API request failed: {str(e)}"
    except Exception as e:
        return f"Error processing request: {str(e)}"


def fetch_all_tables_and_columns():
    api_url = "http://localhost:8012/sql/tables"
    try:
        api_response = requests.get(api_url)
        api_response.raise_for_status()
        logger.info("Fetched tables and columns from API")
        return api_response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Error fetching tables: {str(e)}")
        return {"error": f"Error fetching tables: {str(e)}"}


def format_tables(tables):
    formatted_tables = "<div style='max-height: 150px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;'><ul>"
    if isinstance(tables, dict):
        for table, columns in tables.items():
            formatted_tables += f"<li>{table} ({', '.join(columns)})</li>"
    else:
        formatted_tables += "<li>Error fetching tables and columns</li>"
    formatted_tables += "</ul></div>"
    return formatted_tables


async def update_tables(websocket, path):
    global formatted_tables
    while True:
        available_tables_and_columns = fetch_all_tables_and_columns()
        formatted_tables = format_tables(available_tables_and_columns)
        await websocket.send(json.dumps({"type": "update", "description": f"Available Tables: {formatted_tables}"}))
        logger.info("Sent update to websocket clients")
        await asyncio.sleep(60)


async def websocket_listener():
    global formatted_tables
    async with websockets.connect('ws://localhost:8766') as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            if data['type'] == 'update':
                formatted_tables = data['description']
                logger.info("Received update from WebSocket and updating UI")
                # Update UI description
                ui.description = f"Available Tables: {formatted_tables}"


class ChangeHandler(FileSystemEventHandler):
    async def on_modified(self, event):
        global available_tables_and_columns, formatted_tables
        logger.info(f"Detected file modification: {event.src_path}")
        available_tables_and_columns = fetch_all_tables_and_columns()
        formatted_tables = format_tables(available_tables_and_columns)
        async with websockets.connect('ws://localhost:8766') as websocket:
            await websocket.send(json.dumps({"type": "update", "description": f"Available Tables: {formatted_tables}"}))
            logger.info(
                "Sent immediate update to websocket clients due to file modification")


def start_watcher(path):
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    logger.info("Started file watcher")


# Initial fetch of tables for description
available_tables_and_columns = fetch_all_tables_and_columns()
formatted_tables = format_tables(available_tables_and_columns)

# Gradio UI setup
ui = gr.ChatInterface(
    response,
    css="""
        footer {visibility: hidden;}
        #chatbot { flex-grow: 1 !important; overflow: auto !important;}
    """,
    chatbot=gr.Chatbot(height=600, label="SQL Sense"),
    textbox=gr.Textbox(placeholder="Ask me anything about the data.", container=False, scale=7),
    title="SQL Sense",
    description=f"Available Tables: {formatted_tables}",
    theme='ParityError/Interstellar',
    cache_examples=True,
    undo_btn=None
)

# Start WebSocket server and UI
start_server = websockets.serve(update_tables, "localhost", 8766)
asyncio.get_event_loop().run_until_complete(start_server)
logger.info("Started WebSocket server on ws://localhost:8766")

start_watcher(".")

# Start WebSocket listener to update UI
asyncio.get_event_loop().create_task(websocket_listener())


ui.launch(server_name="0.0.0.0", server_port=6969)
logger.info("Launched Gradio UI on http://0.0.0.0:6969")
