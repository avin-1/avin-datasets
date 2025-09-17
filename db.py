import os
from dotenv import load_dotenv
import sqlite3
from langchain_huggingface import HuggingFaceEndpoint
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

# ---------- Load Hugging Face token from .env ----------
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN missing in .env")

# ---------- Define Database Schema and Sample Data ----------
schema = """
-- === Tables ===
CREATE TABLE Customers (
    customer_id   INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE,
    city          TEXT,
    signup_date   DATE
);

CREATE TABLE Employees (
    employee_id   INTEGER PRIMARY KEY,
    name          TEXT,
    role          TEXT,
    hire_date     DATE,
    salary        REAL
);

CREATE TABLE Departments (
    department_id INTEGER PRIMARY KEY,
    name          TEXT,
    manager_id    INTEGER,
    FOREIGN KEY(manager_id) REFERENCES Employees(employee_id)
);

CREATE TABLE Products (
    product_id    INTEGER PRIMARY KEY,
    name          TEXT,
    category      TEXT,
    price         REAL,
    department_id INTEGER,
    FOREIGN KEY(department_id) REFERENCES Departments(department_id)
);

CREATE TABLE Inventory (
    inventory_id  INTEGER PRIMARY KEY,
    product_id    INTEGER,
    stock_level   INTEGER,
    last_update   DATETIME,
    FOREIGN KEY(product_id) REFERENCES Products(product_id)
);

CREATE TABLE Orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER,
    employee_id   INTEGER,
    order_date    DATETIME,
    status        TEXT,
    FOREIGN KEY(customer_id) REFERENCES Customers(customer_id),
    FOREIGN KEY(employee_id) REFERENCES Employees(employee_id)
);

CREATE TABLE OrderItems (
    order_item_id INTEGER PRIMARY KEY,
    order_id      INTEGER,
    product_id    INTEGER,
    quantity      INTEGER,
    unit_price    REAL,
    FOREIGN KEY(order_id) REFERENCES Orders(order_id),
    FOREIGN KEY(product_id) REFERENCES Products(product_id)
);

CREATE TABLE Payments (
    payment_id    INTEGER PRIMARY KEY,
    order_id      INTEGER,
    amount        REAL,
    payment_date  DATETIME,
    method        TEXT,
    FOREIGN KEY(order_id) REFERENCES Orders(order_id)
);
"""

sample_data = """
INSERT INTO Customers (name,email,city,signup_date)
VALUES ('Alice','alice@example.com','Mumbai','2024-02-12'),
       ('Bob','bob@example.com','Delhi','2024-05-21');

INSERT INTO Employees (name,role,hire_date,salary)
VALUES ('Jane','Sales Rep','2023-03-10',65000),
       ('Mark','Manager','2022-07-01',90000);

INSERT INTO Departments (name,manager_id)
VALUES ('Electronics',2), ('Home Appliances',2);

INSERT INTO Products (name,category,price,department_id)
VALUES ('Laptop','Computers',80000,1),
       ('Microwave','Kitchen',15000,2);

INSERT INTO Inventory (product_id,stock_level,last_update)
VALUES (1,10,'2025-09-01 10:00'), (2,25,'2025-09-01 10:00');

INSERT INTO Orders (customer_id,employee_id,order_date,status)
VALUES (1,1,'2025-09-10 15:30','Shipped');

INSERT INTO OrderItems (order_id,product_id,quantity,unit_price)
VALUES (1,1,1,80000);

INSERT INTO Payments (order_id,amount,payment_date,method)
VALUES (1,80000,'2025-09-11 09:00','Credit Card');
"""

# ---------- Create and populate the database ----------
DB_PATH = "ecom.db"
conn = sqlite3.connect(DB_PATH)
conn.executescript(schema)
conn.executescript(sample_data)
conn.commit()
conn.close()
print("Database ecom.db created with sample data.")

# ---------- Connect for querying and LLM setup ----------
conn = sqlite3.connect(DB_PATH)

def fetch_db_schema() -> str:
    """Return a text description of all tables/columns in the SQLite DB."""
    cur = conn.cursor()
    cur.execute("""
        SELECT m.name as table_name, p.name as column_name, p.type as data_type
        FROM sqlite_master m
        JOIN pragma_table_info(m.name) p
        WHERE m.type='table'
        ORDER BY table_name
    """)
    schema_str = ""
    for t, c, d in cur.fetchall():
        schema_str += f"Table {t}: column {c} ({d})\n"
    cur.close()
    return schema_str

# ---------- LLM endpoint with a reliable model ----------
llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    huggingfacehub_api_token=HF_TOKEN,
    temperature=0.0,
    max_new_tokens=200
)

# ---------- Prompt template for SQL generation ----------
sql_template = """
You are a SQL expert.
Your task is to write a single, correct SQLite SQL query that answers the question.
DO NOT include any explanation, prose, or extra text. Only output the SQL query.

Database schema:
{schema}

Question: {question}

SQL Query:
"""

sql_prompt = PromptTemplate(
    input_variables=["schema", "question"],
    template=sql_template
)

# ---------- Use LangChain Expression Language (LCEL) to create a chain ----------
sql_chain = sql_prompt | llm

def ask_db(nl_query: str):
    """
    Takes a natural language query, generates an SQL query,
    executes it, and returns the result.
    """
    db_schema = fetch_db_schema()
    
    sql_query = sql_chain.invoke({"schema": db_schema, "question": nl_query}).strip()

    if not sql_query.endswith(';'):
        sql_query += ';'

    print("Generated SQL:", sql_query)
    cur = conn.cursor()
    cur.execute(sql_query)
    rows = cur.fetchall()
    cur.close()
    return rows

if __name__ == "__main__":
    while True:
        q = input("\nAsk in plain English (or 'exit'): ")
        if q.lower().startswith("exit"):
            break
        try:
            print("Result:", ask_db(q))
        except Exception as e:
            print("Error:", e)