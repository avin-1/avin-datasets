import os
from openai import OpenAI
import sqlite3
from dotenv import load_dotenv

# ---------- Load Hugging Face token ----------
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN missing in .env")

# ---------- Connect to SQLite database ----------
DB_PATH = "ecom.db"
conn = sqlite3.connect(DB_PATH)

def fetch_schema() -> str:
    """Return a text description of all tables/columns in the SQLite DB."""
    cur = conn.cursor()
    cur.execute("""
        SELECT m.name as table_name, p.name as column_name, p.type as data_type
        FROM sqlite_master m
        JOIN pragma_table_info(m.name) p
        WHERE m.type='table'
        ORDER BY table_name
    """)
    schema = ""
    for t, c, d in cur.fetchall():
        schema += f"Table {t}: column {c} ({d})\n"
    cur.close()
    return schema

# ---------- OpenAI Client with Hugging Face Router ----------
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

def ask_db(nl_query: str):
    """
    Takes a natural language query, generates an SQL query using an LLM via the
    OpenAI client, executes it, and returns the result.
    """
    db_schema = fetch_schema()

    # The prompt is constructed as a message for the chat completions API
    messages = [
        {
            "role": "system",
            "content": f"""You are a SQL expert. You are given a database schema and a natural language question. Your task is to write a single, correct SQLite SQL query that answers the question. DO NOT include any explanation, prose, or extra text. Only output the SQL query.
            Database schema: {db_schema}"""
        },
        {
            "role": "user",
            "content": nl_query
        }
    ]

    # Use the correct model name for Hugging Face Inference API
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        temperature=0.0,
        max_tokens=200
    )

    sql_query = completion.choices[0].message.content.strip()

    # Ensure the query is properly terminated with a semicolon
    if not sql_query.endswith(';'):
        sql_query += ';'

    print("Generated SQL:", sql_query)
    cur = conn.cursor()
    cur.execute(sql_query)
    rows = cur.fetchall()
    cur.close()
    return rows

if __name__ == "__main__":
    # Note: Ensure you have already created and populated your 'ecom.db' file.
    while True:
        q = input("\nAsk in plain English (or 'exit'): ")
        if q.lower().startswith("exit"):
            break
        try:
            print("Result:", ask_db(q))
        except Exception as e:
            print("Error:", e)