import sqlite3

def connect_to_db():
    try:
        # connect to SQLite Database and create a cursor
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        print("DB Init")

        # Execute a query to get the SQLite version
        query = 'SELECT sqlite_version();'
        cursor.execute(query)

        # Fetch and print all results
        result = cursor.fetchall()
        print(f'SQLite Version is {result[0][0]}')

        # Close cursor after use
        cursor.close()
    except sqlite3.Error as error:
        print(f"Error occured: {error}")
    finally:
        # Ensure the database connection is closed
        if conn:
            conn.close()
            print(f"SQLite Connection closed.")

def write_to_db():
    try:
        conn = sqlite3.connect("hotel.db")
        cursor = conn.cursor()

        # Create a new table
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS hotel (
                       FIND INTEGER PRIMARY KEY NOT NULL,
                       FNAME TEXT NOT NULL,
                       COST INTEGER NOT NULL,
                       WEIGHT INTEGER
                    )
                ''')
        # Insert records
        cursor.execute("INSERT INTO hotel (FIND, FNAME, COST, WEIGHT) VALUES (1, 'Cakes', 800, 10)")
        cursor.execute("INSERT INTO hotel (FIND, FNAME, COST, WEIGHT) VALUES (2, 'Biscuits', 100, 20)")
        cursor.execute("INSERT INTO hotel (FIND, FNAME, COST, WEIGHT) VALUES (3, 'Chocos', 1000, 30)")

        conn.commit()
        print(f"Data inserted successfully.")
        cursor.close()
    except sqlite3.Error as error:
        print(f"Error while inserting data: {error}")
    finally:
        if conn:
            conn.close()
            print(f"SQLite connection closed.")

def fetch_from_db():
    conn = sqlite3.connect("hotel.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hotel")

    # fetch all records
    rows = cursor.fetchall()

    print(f"All Food Items:\n")
    for row in rows:
        print(f"Food ID: {row[0]}, Name: {row[1]}, Cost: {row[2]}, Weight: {row[3]}")
    
    cursor.close()

if __name__ == "__main__":
    # Inserting data to DB
    #write_to_db()

    # Fetching data from DB
    fetch_from_db()
    


