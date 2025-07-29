import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def test_railway_connection():
    """Test connection from Railway environment"""
    try:
        server = os.getenv('SQL_SERVER_HOST')
        database = os.getenv('SQL_SERVER_DATABASE') 
        username = os.getenv('SQL_SERVER_USERNAME')
        password = os.getenv('SQL_SERVER_PASSWORD')
        
        print(f"🔄 Testing from Railway to: {server}/{database}")
        print(f"   Username: {username}")
        
        # Try with increased timeout
        connection_string = (
            f'DRIVER={{ODBC Driver 18 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password};'
            f'TrustServerCertificate=yes;'
            f'Connection Timeout=30;'  # Increase timeout
            f'Login Timeout=30;'
        )
        
        print("🔗 Attempting connection...")
        conn = pyodbc.connect(connection_string)
        
        print("✅ Connection successful!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"📊 SQL Server Version: {version[:50]}...")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == '__main__':
    test_railway_connection()
