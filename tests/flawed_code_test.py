# Intentional flaws for AI Code Review testing
# This file contains multiple code quality, security, performance, and architecture issues

import os, sys, time  # PEP8: Multiple imports on one line

# Security: Hardcoded credentials
password = "hardcoded_password_123"
api_key = "sk-1234567890abcdefghijklmnop"
database_url = "postgresql://admin:admin123@localhost/db"

def messy_function(x, y, z):  # Quality: Missing docstring
    # Quality: Poor variable names
    a = x
    b = y
    c = z
    
    # Performance: Inefficient nested loops O(n²)
    for i in range(100):
        for j in range(100):
            time.sleep(0.001)  # Performance: Blocking sleep in loop
            if i > j:
                print(i, j)  # Quality: Print instead of logging
    
    # Security: SQL injection vulnerability
    import sqlite3
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {x}"  # SQL injection
    cursor.execute(query)
    
    return a + b + c


class GodClass:  # Architecture: God class anti-pattern
    """Class with too many responsibilities."""
    
    def __init__(self):
        self.data = []
        self.config = {}
        self.users = []
        self.products = []
    
    # Database operations
    def connect_db(self):
        pass
    
    def query_db(self):
        pass
    
    # User management
    def add_user(self, user):
        self.users.append(user)
    
    def delete_user(self, user_id):
        pass
    
    # Product management
    def add_product(self, product):
        self.products.append(product)
    
    # UI rendering
    def render_page(self):
        pass
    
    # Email sending
    def send_email(self, to, subject):
        pass
    
    # Payment processing
    def process_payment(self, amount):
        pass
    
    # Logging
    def log_event(self, event):
        print(event)  # Quality: Print instead of proper logging


def vulnerable_function(user_input):  # Security: No input validation
    """Function with security vulnerabilities."""
    
    # Security: eval() with user input
    result = eval(user_input)
    
    # Security: exec() with user input
    exec(user_input)
    
    # Security: Using pickle with untrusted data
    import pickle
    data = pickle.loads(user_input)
    
    return result


def slow_algorithm(items):  # Performance: O(n³) complexity
    """Extremely inefficient algorithm."""
    results = []
    
    for i in items:
        for j in items:
            for k in items:
                if i + j + k > 100:
                    results.append((i, j, k))
    
    return results


# Quality: Unused imports
import json
import random
import datetime

# Quality: Dead code
def unused_function():
    """This function is never called."""
    pass

# Architecture: Global state
GLOBAL_COUNTER = 0

def increment_global():  # Architecture: Modifying global state
    global GLOBAL_COUNTER
    GLOBAL_COUNTER += 1
