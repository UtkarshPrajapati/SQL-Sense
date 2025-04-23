# 🤖 SQL LLM Agent: Your Intelligent Database Assistant 📊💻

Welcome to the SQL LLM Agent project! This tool combines Large Language Models (LLMs) with SQL databases to help you interact with your data using natural language, generate SQL queries, and gain insights. ✨

This app works with the help of Gemini API.
## 🌟 Overview

This project provides an intelligent interface to interact with SQL databases. Key features include:

-   **Natural Language Processing:** Ask questions in plain English, and let the LLM translate them into SQL queries. 🗣️➡️🔣
-   **SQL Query Generation:** The LLM generates optimized SQL queries based on your questions. 🧠
-   **Data Retrieval:** Execute the generated SQL and fetch the results directly from your database. 🗄️
-   **Insight Generation:** Obtain deep insights from the fetched data. 📈
- **Direct SQL Execution** : You can use `/run` command to directly execute an sql command. 
-   **Interactive Chat Interface:** A user-friendly chat interface for a seamless experience. 💬
-   **Database Schema Awareness:** Understands your database schema to formulate accurate queries. 📚

## 📁 File Descriptions

-   **`gen-data.py`:** 🔄
    -   Uses the `Faker` library to generate realistic data.
    -   Creates `employees` and `salaries` tables with appropriate sample data.
-   **`index.html`:** 🎨
    -   The front-end user interface of the project.
    -   Uses HTML, CSS, and JavaScript to create an interactive chat experience.
    -   Fetches and displays database schema dynamically.
    -   Sends and receives messages to the `/chat` API endpoint.
    -   Displays results, insights, and error messages.
-   **`requirements.txt`:** 📦
    -   Lists all the Python dependencies required to run the project.
    -   Includes libraries like `fastapi`, `mysql-connector-python`, `pydantic`, `requests`, and more.
-   **`sql_assistant.py`:** 🚀
    -   Contains the core logic of the application.
    -   Manages database connections and query execution.
    -   Integrates with the Gemini API for SQL generation and data analysis.
    -   Defines API endpoints using FastAPI.
    

    


## 🛠️ Installation Steps

1.  **Clone the Repository:**
```
    git clone <repository-url>
    cd <repository-directory>
```
2.  **Create a Virtual Environment:**
```
    python3 -m venv .venv
```
3.  **Activate the Virtual Environment:**
    -   On Linux/macOS:
```
        source .venv/bin/activate     
```
-   On Windows:
```
        .venv\Scripts\activate     
```
4.  **Install Dependencies:**
```
    pip install -r requirements.txt 
```
5.  **Set Up the Database:**
    -   Make sure you have MySQL installed and running.
    -   Update the database credentials in `gen-data.py` ( `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`).
    - Run the following to create the database: `python gen-data.py`
    - Create `.env` file with `GEMINI_API_KEY=<YOUR API KEY>`
    - You can add the MYSQL credentials here as well.

## 🚀 Usage

1.  **Start the API and UI:**
    - Run `uvicorn sql_assistant:app --reload`
    - Run the `index.html` (this is the UI) file in browser.
    - the WebApp will start at `http://localhost:8012`

2.  **Open the UI:**
    -   Open your web browser and go to `http://0.0.0.0:6969`.
    - You will be able to see all the tables with the columns.

3.  **Interact with the Agent:**
    -   Type your questions in natural language (e.g., "Show me all employees in the HR department").
    - You can run direct SQL commands by typing `/run SELECT * FROM your_table LIMIT 10;`
    - Press enter to submit.
    -   The agent will generate the SQL query, execute it, and display the results and insights.

## ⚙️ Configuration

-   **Database:** Adjust the `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` variables in the `api.py`, `gen-data.py` and `sql_assistant.py` files to match your MySQL setup.
-   **LLM:** Customize the LLM model and parameters in `sql_assistant.py` to fine-tune performance and accuracy.
-   **Gemini API**: Set the `GEMINI_API_KEY` in `.env` file

## 🤝 Contributing

Contributions are welcome! If you'd like to enhance this project, feel free to fork the repository and submit a pull request. Please follow the existing code style and include tests with your changes. 😊

## 👏 Credits

Thanks to the amazing open-source community for creating the tools and libraries that made this project possible. 🙌