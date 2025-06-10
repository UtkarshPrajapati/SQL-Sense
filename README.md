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

## 🚀 Project Showcase

A visual tour of the SQL LLM Agent, from its architecture to its user interface and the technologies that power it.

### 🏛️ System Architecture & Workflow
These diagrams illustrate the core structure and operational flow of the application.

<p align="center">
  <strong>1. High-Level System Architecture</strong><br>
  <em>This diagram shows the main components of the system, including the user interface, the FastAPI backend, the SQL database, and the Gemini LLM, and how they interact.</em>
</p>
<p align="center">
  <img src="assets/high-level-architecture.png" alt="High-Level System Architecture" width="700"/>
</p>

<p align="center">
  <strong>2. Application Workflow</strong><br>
  <em>This flowchart details the step-by-step process, from the user submitting a query to the AI generating SQL, fetching data, and returning insights.</em>
</p>
<p align="center">
  <img src="assets/data-flow-diagram.png" alt="SQL Assistant Workflow" width="700"/>
</p>

### 🗄️ Database Schema
An overview of the database structure used in this project.

<p align="center">
  <strong>Employee & Salary Schema</strong><br>
  <em>ER Diagram for the `Employees` and `Salaries` tables.</em>
</p>
<p align="center">
  <img src="assets/er-diagram-employees-salaries.png" alt="Employee and Salary ER Diagram" width="600"/>
</p>

<p align="center">
  <strong>Product Schema</strong><br>
  <em>ER Diagram for the `Product` table.</em>
</p>
<p align="center">
  <img src="assets/er-diagram-products.png" alt="Product ER Diagram" width="600"/>
</p>

### 💻 User Interface
Screenshots of the application in action.

<p align="center">
  <strong>Main Chat Interface</strong><br>
  <em>The primary UI where users interact with the SQL agent.</em>
</p>
<p align="center">
  <img src="assets/ui-initial-screen.png" alt="Main Chat Interface" width="700"/>
</p>

<p align="center">
  <strong>Query Results & Insights</strong><br>
  <em>An example of the application returning query results, generated SQL, and AI-driven insights.</em>
</p>
<p align="center">
  <img src="assets/ui-query-result.png" alt="Query Results and Insights" width="700"/>
</p>

<p align="center">
  <strong>Database Schema Viewer</strong><br>
  <em>The collapsible sidebar allows users to browse the connected database schemas and tables.</em>
</p>
<p align="center">
  <img src="assets/ui-show-databases.png" alt="Database Schema Viewer" width="700"/>
</p>

### 🛠️ Technologies Used
The core technologies and libraries that make this project possible.

<table align="center">
  <tr>
    <td align="center" width="140">
      <a href="https://www.w3.org/TR/CSS/#css" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/skills/css3-colored.svg" width="100" height="100" alt="CSS3" />
      </a>
      <br><strong>CSS3</strong>
    </td>
    <td align="center" width="140">
      <a href="https://developer.mozilla.org/en-US/docs/Glossary/HTML5" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/skills/html5-colored.svg" width="100" height="100" alt="HTML5" />
      </a>
      <br><strong>HTML5</strong>
    </td>
    <td align="center" width="140">
      <a href="https://tailwindcss.com" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/skills/tailwindcss-colored.svg" width="100" height="100" alt="TailwindCSS" />
      </a>
      <br><strong>TailwindCSS</strong>
    </td>
    <td align="center" width="140">
      <a href="https://www.python.org/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/skills/python-colored.svg" width="100" height="100" alt="Python" />
      </a>
      <br><strong>Python</strong>
    </td>
    <td align="center" width="140">
      <a href="https://fastapi.tiangolo.com/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/skills/fastapi-colored.svg" width="100" height="100" alt="Fast API" />
      </a>
      <br><strong>FastAPI</strong>
    </td>
    <td align="center" width="140">
      <a href="https://www.mysql.com/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/skills/mysql-colored.svg" width="100" height="100" alt="MySQL" />
      </a>
      <br><strong>MySQL</strong>
    </td>
    <td align="center" width="140">
      <a href="https://deepmind.google/technologies/gemini/" target="_blank" rel="noreferrer">
        <img src="https://upload.wikimedia.org/wikipedia/commons/8/8a/Google_Gemini_logo.svg" height="80" alt="Google Gemini" />
      </a>
      <br><strong>Google Gemini</strong>
    </td>
  </tr>
</table>

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