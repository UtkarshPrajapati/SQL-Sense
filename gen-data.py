import mysql.connector
from faker import Faker
import random
from dotenv import load_dotenv
import os
from decimal import Decimal # Import Decimal for price

load_dotenv()

# Original Database Config
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE_MAIN = os.getenv("MYSQL_DATABASE", "SQLLLM") # Renamed for clarity

# --- NEW: Second Database Config ---
MYSQL_DATABASE_STORE = os.getenv("MYSQL_DATABASE_STORE", "StoreDB") # New DB name

fake = Faker('en_IN') # Using Indian locale, adjust if needed

# === Functions for Main Database (SQLLLM) ===

def create_database_if_not_exist(db_name):
    """Creates a database if it doesn't exist."""
    conn = None
    cursor = None
    try:
        # Connect without specifying the database
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            auth_plugin='mysql_native_password' # Explicitly set auth plugin if needed
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci") # Added charset/collation
        print(f"Database '{db_name}' created or already exists.")
    except mysql.connector.Error as err:
        print(f"Error creating database {db_name}: {err}")
        exit(1) # Exit if database creation fails
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_main_tables_if_not_exist():
    """Creates tables in the main database (SQLLLM)."""
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE_MAIN,
            auth_plugin='mysql_native_password'
        )
        cursor = conn.cursor()

        # Keep existing Employee table
        create_employee_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{MYSQL_DATABASE_MAIN}`.employees (
            employee_id INT PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            date_of_birth DATE,
            department VARCHAR(50)
        )
        """
        cursor.execute(create_employee_table_query)

        # Keep existing Salary table
        create_salary_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{MYSQL_DATABASE_MAIN}`.salaries (
            employee_id INT,
            full_name VARCHAR(100),
            salary INT,
            departments VARCHAR(50),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        )
        """
        cursor.execute(create_salary_table_query)

        conn.commit()
        print(f"Tables in '{MYSQL_DATABASE_MAIN}' created or already exist")

    except mysql.connector.Error as err:
        print(f"Error creating tables in {MYSQL_DATABASE_MAIN}: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def generate_employee_data(num_records):
    """Generates sample employee data."""
    employees = []
    for _ in range(num_records):
        employee_id = fake.unique.random_int(min=1000, max=9999)
        first_name = fake.first_name()
        last_name = fake.last_name()
        date_of_birth = fake.date_of_birth(
            minimum_age=22, maximum_age=60).strftime('%Y-%m-%d')
        department = random.choice(
            ['HR', 'Finance', 'Engineering', 'Sales', 'Marketing', 'Operations']) # Added one more dept
        employees.append((employee_id, first_name, last_name,
                         date_of_birth, department))
    # Reset unique generator in case script is run multiple times in same session
    fake.unique.clear()
    return employees


def generate_salary_data(employees):
    """Generates salary data based on employee data."""
    salaries = []
    for employee in employees:
        employee_id = employee[0]
        full_name = f"{employee[1]} {employee[2]}"
        # More realistic salary range based on department
        base_salary = random.randint(15000, 80000)
        if employee[4] == 'Engineering':
            salary = base_salary * random.uniform(1.5, 3.0)
        elif employee[4] == 'Sales':
             salary = base_salary * random.uniform(1.2, 2.5) + random.randint(0, 50000) # Commission
        elif employee[4] == 'Finance':
             salary = base_salary * random.uniform(1.3, 2.8)
        else:
            salary = base_salary * random.uniform(1.0, 1.8)
        salary = int(salary) # Convert to integer salary
        department = employee[4]
        salaries.append((employee_id, full_name, salary, department))
    return salaries


def insert_main_data_into_mysql(employees, salaries):
    """Inserts employee and salary data into the main database."""
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE_MAIN,
             auth_plugin='mysql_native_password'
        )
        cursor = conn.cursor()

        employee_query = f"""
        INSERT INTO `{MYSQL_DATABASE_MAIN}`.employees (employee_id, first_name, last_name, date_of_birth, department)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        first_name=VALUES(first_name),
        last_name=VALUES(last_name),
        date_of_birth=VALUES(date_of_birth),
        department=VALUES(department)
        """
        cursor.executemany(employee_query, employees)
        print(f"Inserted/Updated {len(employees)} records into employees table.")

        salary_query = f"""
        INSERT INTO `{MYSQL_DATABASE_MAIN}`.salaries (employee_id, full_name, salary, departments)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        full_name=VALUES(full_name),
        salary=VALUES(salary),
        departments=VALUES(departments)
        """
        # Ensure foreign key constraints might require deleting old salaries first if employee_id changes
        # For simplicity here, we assume employee_ids remain consistent or new ones are added.
        # In a real scenario, handle updates/deletions more carefully.
        # Let's attempt to delete existing salary records for the employee IDs being inserted first
        # This avoids potential foreign key issues if an employee record was deleted/re-added
        if salaries:
             employee_ids_to_update = [s[0] for s in salaries]
             format_strings = ','.join(['%s'] * len(employee_ids_to_update))
             # Check if table exists before deleting
             cursor.execute(f"SHOW TABLES LIKE 'salaries'")
             if cursor.fetchone():
                 delete_query = f"DELETE FROM `{MYSQL_DATABASE_MAIN}`.salaries WHERE employee_id IN ({format_strings})"
                 cursor.execute(delete_query, tuple(employee_ids_to_update))
                 print(f"Attempted cleanup of existing salary records for {len(employee_ids_to_update)} employees.")

        cursor.executemany(salary_query, salaries)
        print(f"Inserted {len(salaries)} records into salaries table.")


        conn.commit()
        print(f"Data inserted successfully into {MYSQL_DATABASE_MAIN}")

    except mysql.connector.Error as err:
        print(f"Error inserting data into {MYSQL_DATABASE_MAIN}: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# === NEW: Functions for Store Database (StoreDB) ===

def create_store_tables_if_not_exist():
    """Creates tables in the store database (StoreDB)."""
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE_STORE, # Connect to the Store DB
            auth_plugin='mysql_native_password'
        )
        cursor = conn.cursor()

        # Create Products table
        create_products_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{MYSQL_DATABASE_STORE}`.products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            product_name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            price DECIMAL(10, 2),
            stock_quantity INT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_products_table_query)

        conn.commit()
        print(f"Tables in '{MYSQL_DATABASE_STORE}' created or already exist")

    except mysql.connector.Error as err:
        print(f"Error creating tables in {MYSQL_DATABASE_STORE}: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def generate_product_data(num_records):
    """Generates sample product data."""
    products = []
    categories = ['Electronics', 'Clothing', 'Home Goods', 'Books', 'Groceries', 'Toys', 'Sports']
    for _ in range(num_records):
        # product_id is AUTO_INCREMENT, so we don't generate it
        product_name = fake.catch_phrase() # Using catch_phrase for variety
        category = random.choice(categories)
        # Generate price as Decimal for precision
        price = Decimal(random.uniform(5.00, 2500.00)).quantize(Decimal('0.01'))
        stock_quantity = random.randint(0, 500)
        # Note: product_id is not included here as it's auto-generated by the DB
        products.append((product_name, category, price, stock_quantity))
    return products

def insert_product_data(products):
    """Inserts product data into the store database."""
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE_STORE, # Connect to the Store DB
            auth_plugin='mysql_native_password'
        )
        cursor = conn.cursor()

        # As product_id is auto-increment and primary key, simple INSERT is usually fine.
        # If you needed to update based on, say, product_name, the query would be different.
        # For this demo, we'll just insert. Re-running might add duplicates if table wasn't cleared.
        # Consider adding a UNIQUE constraint on product_name if duplicates are undesirable.
        product_query = f"""
        INSERT INTO `{MYSQL_DATABASE_STORE}`.products (product_name, category, price, stock_quantity)
        VALUES (%s, %s, %s, %s)
        """
        # ON DUPLICATE KEY UPDATE could be added if a unique key (like product_name) existed and you wanted updates.
        # Example (requires UNIQUE KEY on product_name):
        # ON DUPLICATE KEY UPDATE
        # category=VALUES(category),
        # price=VALUES(price),
        # stock_quantity=VALUES(stock_quantity)

        # Let's clear the table before inserting to ensure fresh data each run for the demo
        # This is destructive, use with caution!
        print(f"Clearing existing data from products table in {MYSQL_DATABASE_STORE}...")
        cursor.execute(f"TRUNCATE TABLE `{MYSQL_DATABASE_STORE}`.products;") # Faster than DELETE for full clear

        cursor.executemany(product_query, products)
        print(f"Inserted {len(products)} records into products table.")

        conn.commit()
        print(f"Data inserted successfully into {MYSQL_DATABASE_STORE}")

    except mysql.connector.Error as err:
        print(f"Error inserting data into {MYSQL_DATABASE_STORE}: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# --- Main script execution ---
print("Starting data generation process...")

# 1. Create Databases
create_database_if_not_exist(MYSQL_DATABASE_MAIN)
create_database_if_not_exist(MYSQL_DATABASE_STORE)

# 2. Create Tables in respective databases
create_main_tables_if_not_exist()
create_store_tables_if_not_exist()

# 3. Generate Data
num_employee_records = 500 # Reduced for potentially faster runs
num_product_records = 200  # Generate fewer products
print(f"Generating {num_employee_records} employee/salary records...")
employees_data = generate_employee_data(num_employee_records)
salaries_data = generate_salary_data(employees_data)

print(f"Generating {num_product_records} product records...")
products_data = generate_product_data(num_product_records)

# 4. Insert Data into respective databases
insert_main_data_into_mysql(employees_data, salaries_data)
insert_product_data(products_data)

print("Data generation process finished.")