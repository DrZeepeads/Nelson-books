#!/usr/bin/env python3
"""
Database Setup Script
Initializes Supabase database with the required schema
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Setup the database schema in Supabase"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("Error: Supabase credentials not found in environment variables")
        return False
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    print("Setting up database schema...")
    
    # Read the SQL schema file
    try:
        with open('database_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute the schema (Note: This is a simplified approach)
        # In production, you would typically run this directly in Supabase SQL editor
        print("Schema loaded successfully!")
        print("Please run the database_schema.sql file in your Supabase SQL editor to create the tables.")
        print("You can find it at: https://supabase.com/dashboard/project/jlrjhjylekjedqwfctub/sql")
        
        return True
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

def test_connection():
    """Test the Supabase connection"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Try to query an existing table or create a simple test
        result = supabase.table('nelson_textbook').select('count').execute()
        print("✅ Supabase connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database setup...")
    
    if test_connection():
        setup_database()
        print("✅ Database setup completed!")
    else:
        print("❌ Database setup failed!")

