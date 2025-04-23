from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiohttp
import logging
import mysql.connector
from mysql.connector import FieldType
from typing import List, Dict

app = FastAPI()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "root"
MYSQL_DATABASE = "SQLLLM"

STREAM = False
USE_CONTEXT = False


class RequestItem(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    stream: bool
    use_context: bool


async def fetch_response(request_item: RequestItem):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post('http://103.189.172.248:11434/v1/chat/completions', json=request_item.dict()) as response:
                data = await response.json()
                print(data)
                content = data['choices'][0]['message']['content']
                return content
        except (aiohttp.ClientError, KeyError, IndexError) as e:
            logger.error(f"Error fetching response: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to fetch model response")
        except Exception as e:
            logger.critical(f"Error occured: {e}", exc_info=True)


def execute_sql_query(query: str):
    print('Executing Query:', query, 'Completed')
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor(buffered=True)
        cursor.execute(query)

        if query.strip().lower().startswith("select") or query.strip().lower().startswith("show"):
            results = cursor.fetchmany(100)
            column_names = [i[0] for i in cursor.description]
            col_dtypes = [[i[0], FieldType.get_info(
                i[1])] for i in cursor.description]
            s = 'Column : Dtype\n'
            s += '\n'.join(f'{k}: {v}' for k, v in col_dtypes)
            conn.commit()
            cursor.close()
            conn.close()
            return results, column_names, s, 1
        else:
            conn.commit()
            cursor.close()
            conn.close()
            return None, None, None, 2
    except mysql.connector.Error as e:
        cursor.close()
        conn.close()
        return None, None, None, 3


def fetch_all_tables_and_columns():
    tables_and_columns = {}
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"SHOW COLUMNS FROM {table};")
            tables_and_columns[table] = [column[0] for column in cursor.fetchall()]

        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"SQL Error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tables and columns: {str(e)}")

    return tables_and_columns


@app.post("/sql/")
async def get_response(user_message_data: dict):
    try:
        print(user_message_data,flush=True)
        user_message_content = user_message_data.get("content", "")
        if user_message_content.lower().startswith("/run"):
            query = user_message_content.replace('/run', '')
            execution_result, column_names, s, is_successful = execute_sql_query(
                query)
            if is_successful == 1:

                data_message_content = f"Here is the data from your query:\nQuery: {query}\n{s}\nResults: {execution_result[:25]}\n\nPlease provide deep insights on this data and further queries based on this data that can be used."
                request_item_with_data = RequestItem(
                    model="llama3.1",
                    messages=[
                        {"role": "system", "content": data_message_content},
                        {"role": "user", "content": user_message_content}
                    ],
                    stream=STREAM,
                    use_context=USE_CONTEXT
                )

                data_insight_response = await fetch_response(request_item_with_data)

                return {
                    "content": {
                        "query": query,
                        "results": execution_result,
                        "columns": column_names,
                        "insights": data_insight_response
                    }
                }

            if is_successful == 2:
                return {"content": "Query executed successfully but returned no results."}

            if is_successful == 3:
                return {"content": "Query Failed"}

        tables_and_columns = fetch_all_tables_and_columns()
        table_columns_info = "\n".join(
            [f"Table: {table}, Columns: {', '.join(columns)}" for table, columns in tables_and_columns.items()])

        system_message_content = f"You are an intelligent SQL assistant that understands user queries and generates appropriate SQL queries to fetch data. Here are the available tables and their columns:\n{table_columns_info}\nProvide only the SQL query in your response, nothing else. Follow the instructions STRICTLY. Nothing else except SQL Command. Give only 1 query please, not 2 or more."

        request_item = RequestItem(
            model="llama3.1",
            messages=[
                {"role": "system", "content": system_message_content},
                {"role": "user", "content": user_message_content}
            ],
            stream=STREAM,
            use_context=USE_CONTEXT
        )

        sql_query = await fetch_response(request_item)

        if sql_query.lower().startswith("select") or sql_query.lower().startswith("show"):
            sql_query = sql_query.split(';')[0]
            execution_result, column_names, s, is_successful = execute_sql_query(
                sql_query)
            if is_successful == 2:
                return {"content": "Query executed successfully but returned no results."}

            if is_successful == 3:
                request_item = RequestItem(
                    model="llama3.1",
                    messages=[
                        {"role": "system", "content": system_message_content},
                        {"role": "user", "content": user_message_content}],
                    stream=STREAM,
                    use_context=USE_CONTEXT)

                sql_query = await fetch_response(request_item)
                execution_result, column_names, s, is_successful = execute_sql_query(
                    sql_query)

            data_message_content = f"Here is the data from your query:\nQuery: {sql_query}\n{s}\nResults: {execution_result[:25]}\n\nPlease provide deep insights on this data and further sql queries based on this data that can be used ahead."
            print(data_message_content,flush=True)
            request_item_with_data = RequestItem(
                model="llama3.1",
                messages=[
                    {"role": "system", "content": data_message_content},
                    {"role": "user", "content": user_message_content}
                ],
                stream=STREAM,
                use_context=USE_CONTEXT
            )

            data_insight_response = await fetch_response(request_item_with_data)

            return {
                "content": {
                    "query": sql_query,
                    "results": execution_result,
                    "columns": column_names,
                    "insights": data_insight_response
                }
            }
        else:
            execute_sql_query(sql_query)
            return {"content": "Query executed successfully."}
    except Exception as e:
        logger.error(f"Internal server error: {e}",exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error {e}")


@app.get("/sql/tables")
async def get_tables():
    try:
        return fetch_all_tables_and_columns()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tables: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}