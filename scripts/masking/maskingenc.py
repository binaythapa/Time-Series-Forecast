import sqlite3
from cryptography.fernet import Fernet
import hashlib

# Generate a secure encryption key
def generate_key():
    return Fernet.generate_key()

# Encrypt data
def encrypt_data(data, key):
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(data.encode())
    return encrypted_data

# Decrypt data
def decrypt_data(encrypted_data, key):
    try:
        cipher_suite = Fernet(key)
        decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
        return decrypted_data
    except Exception as e:
        print("Error during decryption:", e)
        return None

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

# Encryption key
key = generate_key()

# User role (for demonstration purposes)
user_role = 'admin'  # Change to 'user' to simulate a non-admin user

# Retrieve and display data based on user role
cursor.execute('SELECT * FROM users')
rows = cursor.fetchall()

for row in rows:
    if user_role == 'admin':
        # Decrypt name
        decrypted_name = decrypt_data(row[1], key)
        print(f"Name: {decrypted_name}, Email: {row[2]}, Phone: {row[3]}, Salary: {row[4]}")
    else:
        # Mask email and phone, decrypt name
        masked_email = mask_data(row[2])
        masked_phone = mask_data(row[3])
        decrypted_name = decrypt_data(row[1], key)
        if decrypted_name:
            print(f"Name: {decrypted_name}, Email: {masked_email}, Phone: {masked_phone}, Salary: *****")
        else:
            print("Error: Unable to decrypt name.")

# Close connection
conn.close()
