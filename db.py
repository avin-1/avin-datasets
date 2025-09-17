import os
from dotenv import load_dotenv
import sqlite3
from langchain_huggingface import HuggingFaceEndpoint
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from models import Base, Customer, Employee, Department, Product, Inventory, Order, OrderItem, Payment
import datetime

# ---------- Load Hugging Face token from .env ----------
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN missing in .env")

# ---------- Database Setup ----------
DB_PATH = "ecom.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

def create_and_populate_db():
    """Create the database and populate it with sample data."""
    Base.metadata.create_all(engine)
    session = Session()

    # Check if data already exists
    if session.query(Customer).first():
        print("Database already populated.")
        session.close()
        return

    # Sample Data
    customers = [
        Customer(name='Alice', email='alice@example.com', city='Mumbai', signup_date=datetime.date(2024, 2, 12)),
        Customer(name='Bob', email='bob@example.com', city='Delhi', signup_date=datetime.date(2024, 5, 21))
    ]

    employees = [
        Employee(name='Jane', role='Sales Rep', hire_date=datetime.date(2023, 3, 10), salary=65000),
        Employee(name='Mark', role='Manager', hire_date=datetime.date(2022, 7, 1), salary=90000)
    ]

    departments = [
        Department(name='Electronics', manager_id=2),
        Department(name='Home Appliances', manager_id=2)
    ]

    products = [
        Product(name='Laptop', category='Computers', price=80000, department_id=1),
        Product(name='Microwave', category='Kitchen', price=15000, department_id=2)
    ]

    inventory = [
        Inventory(product_id=1, stock_level=10, last_update=datetime.datetime(2025, 9, 1, 10, 0)),
        Inventory(product_id=2, stock_level=25, last_update=datetime.datetime(2025, 9, 1, 10, 0))
    ]

    orders = [
        Order(customer_id=1, employee_id=1, order_date=datetime.datetime(2025, 9, 10, 15, 30), status='Shipped')
    ]

    order_items = [
        OrderItem(order_id=1, product_id=1, quantity=1, unit_price=80000)
    ]

    payments = [
        Payment(order_id=1, amount=80000, payment_date=datetime.datetime(2025, 9, 11, 9, 0), method='Credit Card')
    ]

    session.add_all(customers)
    session.add_all(employees)
    session.add_all(departments)
    session.add_all(products)
    session.add_all(inventory)
    session.add_all(orders)
    session.add_all(order_items)
    session.add_all(payments)

    session.commit()
    session.close()
    print("Database ecom.db created and populated with sample data.")

def fetch_db_schema() -> str:
    """Return a text description of all tables/columns in the database."""
    inspector = inspect(engine)
    schema_str = ""
    for table_name in inspector.get_table_names():
        schema_str += f"Table {table_name}:\n"
        for column in inspector.get_columns(table_name):
            schema_str += f"  - {column['name']} ({column['type']})\n"
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

    with engine.connect() as connection:
        result = connection.execute(text(sql_query))
        rows = result.fetchall()
        return rows

if __name__ == "__main__":
    create_and_populate_db()