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
    cipher_suite = Fernet(key)
    decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
    return decrypted_data

# Hash sensitive information
def hash_data(data):
    return hashlib.sha256(data.encode()).hexdigest()

# Mask sensitive information
def mask_data(data):
    return '*' * len(data)

# Example usage:
key = generate_key()
print("Generated Key:", key)

# Example sensitive data
customer_name = "John Doe"
email = "johndoe@gmail.com"

# Split email address into local and domain parts
local_part, domain_part = email.split('@')
print("Local Part:", local_part)
print("Domain Part:", domain_part)

# Hash sensitive data (local part remains visible)
hashed_name = hash_data(customer_name)
hashed_domain = hash_data(domain_part)

# Encrypt hashed domain part
encrypted_domain = encrypt_data(hashed_domain, key)

# Mask original data (local part remains visible)
masked_name = mask_data(customer_name)
masked_email = f"{masked_name}@{domain_part}"

print("Masked Email:", masked_email)

# Decrypt and verify data
decrypted_domain = decrypt_data(encrypted_domain, key)
print("Decrypted Domain:", decrypted_domain)

# Reconstruct email address with decrypted domain
decrypted_email = f"{masked_name}@{decrypted_domain}"
print("Decrypted Email:", decrypted_email)
