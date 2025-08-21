import sqlite3
import hashlib

# Hash sensitive information
def hash_data(data):
    return hashlib.sha256(data.encode()).hexdigest()

# Mask sensitive information
def mask_data(data):
    return '*' * len(data)

# Create a SQLite database connection
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# Create table
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                salary REAL)''')

# Sample data
sample_data = [
    ('Alice', 'alice@example.com', '123-456-7890', 50000.0),
    ('Bob', 'bob@example.com', '987-654-3210', 60000.0)
]

# Insert sample data into the table
cursor.executemany('INSERT INTO users (name, email, phone, salary) VALUES (?, ?, ?, ?)', sample_data)

# Commit changes
conn.commit()

# User role (for demonstration purposes)
user_role = 'admin'  # Change to 'user' to simulate a non-admin user

# Retrieve and display data based on user role
cursor.execute('SELECT * FROM users')
rows = cursor.fetchall()

for row in rows:
    if user_role != 'admin':
        print(f"Name: {row[1]}, Email: {row[2]}, Phone: {row[3]}, Salary: {row[4]}")
    else:
        masked_email = mask_data(row[2])
        masked_phone = mask_data(row[3])
        masked_name = mask_data(row[1])
        print(f"Name: {masked_name}, Email: {masked_email}, Phone: {masked_phone}, Salary: *****")

# Close connection
conn.close()
