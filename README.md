# 🤖 DataFlow: Your Intelligent Database Assistant

[![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-05998b.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made with Love](https://img.shields.io/badge/Made%20with-❤-ff69b4)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#-contributing)

DataFlow bridges the gap between humans and relational data. Ask questions in plain English and instantly receive optimized SQL, live results, and AI-generated insights – all without leaving the browser. ✨

---

## 📚 Table of Contents

1. [Why DataFlow?](#-why-dataflow)
2. [Key Features](#-key-features)
3. [Project Showcase](#-project-showcase)
4. [Technologies and Core Libraries](#%EF%B8%8F-technologies-and-core-libraries)
6. [Setup and Installation](#%EF%B8%8F-setup-and-installation)
8. [How to Use](#-how-to-use)
9. [API Endpoints](#-api-endpoints)
10. [Troubleshooting & FAQ](#-troubleshooting--faq)
11. [Project Structure](#-project-structure)
12. [Contributing](#-contributing)
13. [License](#-license)
14. [Acknowledgements](#-acknowledgements)

---

## ❓ Why DataFlow?

Traditional SQL clients are great at running queries—but they assume you already *know* SQL and your schema inside-out. DataFlow removes that barrier:

* **No more context-switching.** Ask questions in plain language and stay focused on your analysis.
* **Instant productivity.** New teammates or non-technical stakeholders can explore data without a crash-course in SQL.
* **Better insights, faster.** AI-generated summaries highlight trends you might miss in raw tables.
* **Safety first.** Potentially destructive queries are intercepted and require explicit confirmation.

---

## ✨ Key Features

-   **🤖 Natural Language to SQL:** Ask questions in English; get optimized SQL queries in return.
-   **🚀 Direct SQL Execution:** A `/run` command to execute raw SQL queries for power users.
-   **📈 AI-Powered Insights:** Automatically generates summaries and suggests relevant follow-up questions from query results.
-   **💡 AI-Powered Troubleshooting:** When a query fails, the AI provides a plain-English explanation of the error and suggests a fix based on your database schema.
-   **🛡️ Advanced Security:** Intercepts potentially harmful queries. Data-modifying queries (e.g., `UPDATE`, `INSERT`) require user confirmation, while structure-altering queries (e.g., `DROP`, `ALTER`) are blocked entirely.
-   **👁️ Dynamic Schema Viewer:** An interactive, collapsible sidebar displays your database schemas, tables, and columns in real-time.
-   **⚡ Interactive Querying:** Click-to-run buttons appear on suggested SQL code blocks, allowing for one-click execution right from the chat.
-   **⚙️ On-the-Fly Configuration:** Update database credentials and API keys from the UI without needing to restart the server. Your settings are securely saved in a local `.env` file.
-   **💬 Session-Based History:** Chat history is tied to your browser session, providing a persistent and private workspace. Start a new chat anytime.
-   **🎨 Modern Material UI:** A sleek, responsive, and user-friendly chat UI built with TailwindCSS and inspired by Material Design, featuring toast notifications and a seamless user experience.

---

## 🚀 Project Showcase

A visual tour of DataFlow, from its architecture to its user interface.

<details>
<summary><strong>🏛️ System Architecture & Workflow (Click to Expand)</strong></summary>

<p align="center">
  <strong>1. High-Level System Architecture</strong><br>
  <em>The main components of the system: UI, FastAPI Backend, SQL Database, and the Gemini LLM.</em>
</p>
<p align="center">
  <img src="assets/high-level-architecture.png" alt="High-Level System Architecture" width="700"/>
</p>

<p align="center">
  <strong>2. Application Workflow</strong><br>
  <em>From user prompt to AI-generated SQL, data retrieval, and final insights.</em>
</p>
<p align="center">
  <img src="assets/data-flow-diagram.png" alt="SQL Assistant Workflow" width="700"/>
</p>

</details>

<details>
<summary><strong>🗄️ Database Schema (Click to Expand)</strong></summary>

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

</details>

<details>
<summary><strong>💻 User Interface (Click to Expand)</strong></summary>

<p align="center">
  <strong>Main Chat Interface</strong><br>
  <em>The primary UI where users interact with the SQL agent.</em>
</p>
<p align="center">
  <img src="assets/ui-initial-screen.png" alt="Main Chat Interface" width="700"/>
</p>

<p align="center">
  <strong>Query Results & Insights</strong><br>
  <em>An example of the application returning query results, generated SQL, AI-driven insights, and AI-powered troubleshooting for errors.</em>
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

</details>

---

## 🛠️ Technologies and Core Libraries

<table align="center">
  <tr>
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
      <a href="https://deepmind.google/technologies/gemini/" target="_blank" rel="noreferrer">
        <img src="https://upload.wikimedia.org/wikipedia/commons/8/8a/Google_Gemini_logo.svg" height="100" alt="Google Gemini" />
      </a>
      <br><strong>Google Gemini</strong>
    </td>
    <td align="center" width="140">
      <a href="https://www.mysql.com/" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/skills/mysql-colored.svg" width="100" height="100" alt="MySQL" />
      </a>
      <br><strong>MySQL</strong>
    </td>
    <td align="center" width="140">
      <a href="https://tailwindcss.com" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/skills/tailwindcss-colored.svg" width="100" height="100" alt="TailwindCSS" />
      </a>
      <br><strong>TailwindCSS</strong>
    </td>
    <td align="center" width="140">
      <a href="https://developer.mozilla.org/en-US/docs/Glossary/HTML5" target="_blank" rel="noreferrer">
        <img src="https://raw.githubusercontent.com/danielcranney/readme-generator/main/public/icons/skills/html5-colored.svg" width="100" height="100" alt="HTML5" />
      </a>
      <br><strong>HTML5</strong>
    </td>
  </tr>
</table>

**Backend:** Python, FastAPI, Uvicorn, Google GenAI API, MySQL Connector, Pydantic, python-dotenv, sqlparse, fastapi-sessions

**Frontend:** HTML, TailwindCSS, Marked.js, DOMPurify, Lucide Icons

---
## ⚙️ Setup and Installation

Follow these steps to get DataFlow running on your local machine.

### 1. Prerequisites

-   **Python 3.11+**
-   **Git**
-   An active **MySQL** database service.

### 2. Clone the Repository
```bash
git clone https://github.com/UtkarshPrajapati/SQL-Sense.git
cd SQL-Sense
```

### 3. Set Up Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Configure Environment Variables

It is **not strictly necessary** to create a `.env` file before starting, but it is recommended for providing your database credentials and Gemini API key.

**How it works:**
*   **No `.env` file:** The application will start with default settings (attempting to connect to MySQL on `localhost` with user `root`). You can then use the web UI's **Config** panel to enter your credentials, which will automatically create a `.env` file for you.
*   **With a `.env` file:** You can create a file named `.env` in the project root to pre-configure the application.

1.  Create a file named `.env` in the root of the project (optional).
2.  Add the keys you need. The application will use defaults for any keys that are not provided.

<details>
<summary><strong>Example `.env` structure (Click to Expand)</strong></summary>

```
# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key

# Session Management (Optional, will be auto-generated)
SESSION_SECRET_KEY=your_super_secret_key_for_sessions
```
</details>

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

### 6. (Optional) Prepare the Sample Database

This step is only necessary if you want to use the pre-defined sample data to test the application. If you intend to connect to your own existing database, you can skip this.

Run the provided script to create the necessary tables and populate them with realistic sample data.

```bash
python gen-data.py
```
This script will create two databases by default:
1.  **`SQLLLM`**: Contains `employees` and `salaries` tables.
2.  **`StoreDB`**: Contains a `products` table.

It will then populate these tables with sample data.

### 7. Run the Application
You're all set! Start the FastAPI server.
```bash
python sql_assistant.py
```
The application will be live at **http://127.0.0.1:6969**.

---

## 📖 How to Use

1.  **Open the Web Interface:** Navigate to `http://127.0.0.1:6969` in your web browser.
2.  **Configure Credentials:** Click the "Config" button to enter your MySQL and Gemini API Key details. They will be saved for future sessions.
3.  **View Schema:** Click the "View Schema" button to see the tables and columns the AI is aware of.
4.  **Ask a Question:** Type a question in plain English, like `show me all employees and their salaries`.
5.  **Execute Direct SQL:** For precise control, use the `/run` command followed by a SQL query. For example: `/run SELECT product_name, price FROM products WHERE price > 50;`
6.  **Review Results:** The application will display the generated SQL, the data results in a table, and a summary of insights derived by the AI.
7.  **One-Click Execution:** If the assistant suggests an SQL query, click the "Run Query" button that appears over the code block to execute it immediately.
8.  **Start a New Chat:** Click the "New Chat" button to clear the conversation and start fresh.

---

## 🔗 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **GET** | `/` | Serves the `index.html` single-page application and manages session creation. |
| **GET** | `/schema` | Returns JSON containing databases, tables, and columns the assistant can access. |
| **GET** | `/config_status`| Returns the public configuration status (e.g., host, user, and whether keys are set). |
| **POST** | `/config` | Body: `{ "mysql_host": "...", "mysql_user": "...", "mysql_password": "...", "gemini_api_key": "..." }` – Updates connection credentials and tests them. No restart needed. |
| **POST** | `/chat` | Body: `{ "message": "<natural-language question or /run <SQL>>" }` – Main interaction endpoint: accepts NL queries or `/run` SQL commands, returns results/insights. |
| **POST** | `/execute_confirmed_sql` | Body: `{ "query": "<SQL previously flagged for confirmation>" }` – Executes DML queries that the user has reviewed and approved. |
| **POST**| `/reset_chat` | Clears the chat history for the current user session. |

All responses are JSON and follow the shape documented in the code. Unhandled errors are returned with appropriate HTTP status codes.

---

## 🛟 Troubleshooting & FAQ

<details>
<summary><strong>The server starts but `/schema` returns an empty list</strong></summary>

**Cause:** The MySQL credentials in your `.env` file don't have permission to see user databases, or no user databases exist.

**Fix:**
1. Verify `MYSQL_USER` / `MYSQL_PASSWORD` in `.env` or via the UI Config panel.
2. Check that your user has at least `SELECT` privilege on the target databases.
3. Use the `/config` endpoint (or restart the app) after updating credentials.
</details>

<details>
<summary><strong>Gemini replies with "Error: Gemini API not configured"</strong></summary>

The `GEMINI_API_KEY` environment variable is missing or invalid.

* Obtain an API key from Google AI Studio.
* Add it to your `.env` file and/or update via the `/config` endpoint.
* Restart the backend (or let `/config` re-initialize the key).
</details>

<details>
<summary><strong>"Client does not support authentication protocol" MySQL error</strong></summary>

Your MySQL server may be using the newer `caching_sha2_password` plugin while the connector expects `mysql_native_password`. The application attempts to use `mysql_native_password` by default. If this error still occurs, you may need to update your user configuration in MySQL.

```sql
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'your_password';
FLUSH PRIVILEGES;
```

Alternatively, create a dedicated read-only user for DataFlow with compatible auth.
</details>

<details>
<summary><strong>The UI shows a loading spinner that never stops after I submit a question</strong></summary>

Check the backend logs; the LLM may be taking longer than expected or returning a safety block. Increase the `timeout` on your HTTP client if you've reverse-proxied the API.
</details>

---

## 📂 Project Structure
```
.
├── .env.example        # Environment variable template
├── .gitignore          # Files to ignore for git
├── README.md           # This file
├── assets              # Images and architectural diagrams
├── gen-data.py         # Generates and populates the database
├── index.html          # Main frontend file
├── requirements.txt    # Python dependencies
├── sql_assistant.py    # FastAPI backend logic
├── static              # Static assets for the logo
└── venv                # Virtual environment folder
```

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📜 License

Distributed under the MIT License.

---

## 👏 Acknowledgements

-   The amazing open-source community.
-   The teams behind FastAPI, Google Gemini, and Uvicorn.
-   Icons and visuals from [Lucide Icons](https://lucide.dev/) and [SVG Repo](https://www.svgrepo.com/).
