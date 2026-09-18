import json
import base64
import pyodbc

def get_db_connection(user_key='RadhaUser'):
    # 1. JSON file se config load karein
    with open('db_config.json', 'r') as f:
        config = json.load(f)

    server = config.get('server')
    database = config.get('database')
    
    # Selected user ka credentials nikaalein
    user_info = config['users'].get(user_key)
    if not user_info:
        raise ValueError(f"User '{user_key}' db_config.json me nahi mila!")

    user_id = user_info['user_id']
    # Base64 password decode kar rahe hain
    password = base64.b64decode(user_info['password']).decode('utf-8')

    # 2. Connection string for SQL Server Express
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user_id};"
        f"PWD={password};"
    )

    # 3. Connection return karein
    conn = pyodbc.connect(conn_str)
    return conn