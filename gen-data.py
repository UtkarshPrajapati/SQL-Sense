import mysql.connector
from faker import Faker
import random
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "SQLLLM")

fake = Faker('en_IN')

def create_tables_if_not_exist():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()

        create_employee_table_query = """
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INT PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            date_of_birth DATE,
            department VARCHAR(50)
        )
        """
        cursor.execute(create_employee_table_query)

        create_salary_table_query = """
        CREATE TABLE IF NOT EXISTS salaries (
            employee_id INT,
            full_name VARCHAR(100),
            salary INT,
            departments VARCHAR(50),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        )
        """
        cursor.execute(create_salary_table_query)

        conn.commit()
        print("Tables created or already exist")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        cursor.close()
        conn.close()


def generate_employee_data(num_records):
    employees = []
    for _ in range(num_records):
        employee_id = fake.unique.random_int(min=1000, max=9999)
        first_name = fake.first_name()
        last_name = fake.last_name()
        date_of_birth = fake.date_of_birth(
            minimum_age=22, maximum_age=60).strftime('%Y-%m-%d')
        department = random.choice(
            ['HR', 'Finance', 'Engineering', 'Sales', 'Marketing'])
        employees.append((employee_id, first_name, last_name,
                         date_of_birth, department))
    return employees


def generate_salary_data(employees):
    salaries = []
    for employee in employees:
        employee_id = employee[0]
        full_name = f"{employee[1]} {employee[2]}"
        salary = random.randint(15000, 2000000)
        department = employee[4]
        salaries.append((employee_id, full_name, salary, department))
    return salaries


def insert_data_into_mysql(employees, salaries):
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()
        
        employee_query = """
        INSERT INTO employees (employee_id, first_name, last_name, date_of_birth, department)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        first_name=VALUES(first_name),
        last_name=VALUES(last_name),
        date_of_birth=VALUES(date_of_birth),
        department=VALUES(department)
        """
        cursor.executemany(employee_query, employees)

        salary_query = """
        INSERT INTO salaries (employee_id, full_name, salary, departments)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        full_name=VALUES(full_name),
        salary=VALUES(salary),
        departments=VALUES(departments)
        """
        cursor.executemany(salary_query, salaries)

        conn.commit()
        print("Data inserted successfully")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        cursor.close()
        conn.close()


create_tables_if_not_exist()

num_records = 1000
employees_data = generate_employee_data(num_records)
salaries_data = generate_salary_data(employees_data)

insert_data_into_mysql(employees_data, salaries_data)
