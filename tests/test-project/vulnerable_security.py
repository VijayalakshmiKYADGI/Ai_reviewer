import os
import sqlite3

API_KEY = "sk-abc123hardcoded"  # B105 hardcoded password

def login(request):
    password = request.args.get('pwd')  # B105 URL param password
    user_id = request.args.get('id')
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # B608 SQL injection vulnerability
    cursor.execute(f"SELECT * FROM users WHERE id={user_id}")
    
    return cursor.fetchall()
