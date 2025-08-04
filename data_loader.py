import sqlite3

conn = sqlite3.connect("dupes.db")
c = conn.cursor()

# Drop tables if they exist
c.execute("DROP TABLE IF EXISTS products")
c.execute("DROP TABLE IF EXISTS dupes")

# Create products table
c.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand TEXT NOT NULL,
    name TEXT NOT NULL,
    color TEXT,
    price REAL
)
""")

# Create dupes table
c.execute("""
CREATE TABLE dupes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_id INTEGER,
    dupe_id INTEGER,
    FOREIGN KEY(original_id) REFERENCES products(id),
    FOREIGN KEY(dupe_id) REFERENCES products(id)
)
""")

# TODO: Insert sample data from Google Sheet

conn.commit()
conn.close()
