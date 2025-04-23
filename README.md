# 🤖 SQL LLM Agent: Your Intelligent Database Assistant 📊💻

Welcome to the SQL LLM Agent project! This tool combines Large Language Models (LLMs) with SQL databases to help you interact with your data using natural language, generate SQL queries, and gain insights. ✨

This app works with the help of Gemini API.

## 🌟 Overview

This project provides an intelligent interface to interact with SQL databases. Key features include:

-   **Natural Language Processing:** Ask questions in plain English, and let the LLM translate them into SQL queries. 🗣️➡️🔣
-   **SQL Query Generation:** The LLM generates optimized SQL queries based on your questions. 🧠
-   **Data Retrieval:** Execute the generated SQL and fetch the results directly from your database. 🗄️
-   **Insight Generation:** Obtain deep insights from the fetched data. 📈
-   **Direct SQL Execution:** You can use `/run` command to directly execute an SQL command.
-   **Interactive Chat Interface:** A user-friendly chat interface for a seamless experience. 💬
-   **Database Schema Awareness:** Understands your database schema to formulate accurate queries. 📚

## 📁 File Descriptions

-   **`gen-data.py`:** 🔄
    -   Uses the `Faker` library to generate realistic employee and salary data.
    -   Creates `employees` and `salaries` tables with appropriate sample data in MySQL.
-   **`index.html`:** 🎨
    -   The main front-end user interface of the project.
    -   Built with HTML, Tailwind CSS, Lucide icons, and marked.js for markdown rendering.
    -   Provides an interactive chat experience with natural language input.
    -   Displays database schema dynamically and shows query results and insights.
-   **`requirements.txt`:** 📦
    -   Lists all the Python dependencies required to run the project.
    -   Includes libraries like `fastapi`, `mysql-connector-python`, `pydantic`, `requests`, `google-generativeai`, and more.
-   **`sql_assistant.py`:** 🚀
    -   Contains the core application logic using FastAPI.
    -   Manages MySQL database connections and query execution.
    -   Integrates with the Gemini API for SQL generation from natural language and data insight generation.
    -   Defines API endpoints for the UI, schema fetching, and chat interaction.


## 🛠️ Installation Steps

1.  **Clone the Repository:**
```
    git clone https://github.com/UtkarshPrajapati/SQL-Sense.git
    cd SQL-Sense
```
2.  **Create a Virtual Environment:**
```
    python3 -m venv .venv
```
3.  **Activate the Virtual Environment:**
    - On Windows:
```
    .venv\Scripts\activate     
```
4.  **Install Dependencies:**
```
    pip install -r requirements.txt 
```
5.  **Set Up the Database:**
    -   Make sure you have MySQL installed and running.
    -   Update the database credentials in `.env` ( `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`,`GEMINI_API_KEY`).
    -   Run the following to create the database and insert sample data: `python gen-data.py`

## 🚀 Usage

1.  **Start the WebApp:**
    -   You can start the services manually:
        - Run `uvicorn sql_assistant:app --reload`
        - Open `http://127.0.0.1:8000` in a browser for the main UI.
2.  **Interact with the Agent:**
    -   Type your questions in natural language (e.g., "Show me all employees in the HR department").
    -   Use `/run` command to execute direct SQL queries (e.g., `/run SELECT * FROM employees LIMIT 10;`).
    -   View query results, insights, and database schema dynamically.

## ⚙️ Configuration

-   **Database:** Adjust the `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` variables in the `.env` file.
-   **LLM and Gemini API:** Set the `GEMINI_API_KEY` in the `.env` file.

## 🤝 Contributing

Contributions are welcome! If you'd like to enhance this project, feel free to fork the repository and submit a pull request. Please follow the existing code style and include tests with your changes. 😊

## 👏 Credits

Thanks to the amazing open-source community for creating the tools and libraries that made this project possible. 🙌