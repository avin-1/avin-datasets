from db import ask_db, create_and_populate_db

if __name__ == "__main__":
    # Create and populate the database if it doesn't exist
    create_and_populate_db()

    # Start the interactive loop
    while True:
        q = input("\nAsk in plain English (or 'exit'): ")
        if q.lower().startswith("exit"):
            break
        try:
            print("Result:", ask_db(q))
        except Exception as e:
            print("Error:", e)