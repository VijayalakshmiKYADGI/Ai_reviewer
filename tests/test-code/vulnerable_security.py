import subprocess
import os

def connect_db():
    password = "password123"  # Hardcoded password
    api_key = "sk_1234567890abcdef1234567890abcdef" # Hardcoded API key
    db_url = f"mysql://user:{password}@localhost/db"
    
    # SQL Injection vulnerability
    user_input = "admin' OR '1'='1"
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    
    # Command injection
    cmd = "echo " + user_input
    os.system(cmd)
    
    # Weak cryptography
    import hashlib
    m = hashlib.md5()
    m.update(b"Faster but insecure")

def run_shell(command):
    subprocess.call(command, shell=True) # Shell=True is dangerous
