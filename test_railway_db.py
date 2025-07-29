#!/usr/bin/env python3

"""
Test script to verify ODBC connection to SQL Server
Run this locally to test before deploying to Railway
"""

import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_db_connection():
    """Test database connection"""
    try:
        # Database configuration
        server = os.getenv('SQL_SERVER_HOST', 'sqlserverdb.cgt0oi2i2k3f.us-east-1.rds.amazonaws.com')
        database = os.getenv('SQL_SERVER_DATABASE', 'FIDS_DEV')
        username = os.getenv('SQL_SERVER_USERNAME', 'admin')
        password = os.getenv('SQL_SERVER_PASSWORD', 'Admin12345!')
        
        print(f"🔄 Testing connection to {server}/{database}...")
        
        # Build connection string
        connection_string = (
            f'DRIVER={{ODBC Driver 18 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password};'
            f'TrustServerCertificate=yes;'
        )
        
        # Test connection
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM flights")
        row_count = cursor.fetchone()[0]
        
        print(f"✅ Connection successful!")
        print(f"📊 Total flights in database: {row_count}")
        
        # Test sample query
        cursor.execute("SELECT TOP 3 airline, flight, destination FROM flights ORDER BY id")
        rows = cursor.fetchall()
        
        print("\n📋 Sample flights:")
        for row in rows:
            print(f"   {row[1]} - {row[0]} to {row[2]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 FIDS Database Connection Test")
    print("=" * 40)
    
    success = test_db_connection()
    
    if success:
        print("\n✅ All tests passed! Ready for Railway deployment.")
    else:
        print("\n❌ Tests failed. Please check your database configuration.")
        exit(1)
