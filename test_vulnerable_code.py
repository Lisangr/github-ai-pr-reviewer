# test_vulnerable_code.py
import sqlite3

# Уязвимость 1: Захардкоженный токен (подходит под secrets-leak.md)
API_SECRET_TOKEN = "sk-proj-abcdef1234567890abcdef123456"

def get_user(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Уязвимость 2: SQL-инъекция через f-string (подходит под sql-injection.md)
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchall()