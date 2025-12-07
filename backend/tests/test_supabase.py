#!/usr/bin/env python3
"""
Test Supabase connection and database setup
Run this after setting up your database
"""

import os
from dotenv import load_dotenv
from supabase import create_client

def test_supabase_connection():
    """Test basic Supabase connection"""
    load_dotenv()
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
        return False
        
    try:
        supabase = create_client(url, key)
        print("Supabase client created successfully")
        return supabase
    except Exception as e:
        print(f"Failed to create Supabase client: {e}")
        return False

def test_tables_exist(supabase):
    """Test that required tables exist"""
    tables = ['payment_links', 'contributions', 'webhook_events']
    
    for table in tables:
        try:
            result = supabase.table(table).select("count", count="exact").execute()
            print(f"Table '{table}' exists with {result.count} records")
        except Exception as e:
            print(f"Table '{table}' error: {e}")

def test_insert_sample_data(supabase):
    """Test inserting sample data"""
    try:
        # Test payment link creation
        link_data = {
            'slug': f'test-link-{os.urandom(4).hex()}',
            'title': 'Test Crowdfunding Campaign',
            'description': 'This is a test campaign',
            'goal_kes': 10000.00,
            'visibility': 'public'
        }
        
        result = supabase.table('payment_links').insert(link_data).execute()
        if result.data:
            print(f"Sample payment link created: {result.data[0]['slug']}")
            
            # Test contribution creation
            contrib_data = {
                'link_id': result.data[0]['id'],
                'amount_kes': 1000.00,
                'payment_method': 'test',
                'donor_name': 'Test Donor',
                'status': 'pending'
            }
            
            contrib_result = supabase.table('contributions').insert(contrib_data).execute()
            if contrib_result.data:
                print(f"Sample contribution created: {contrib_result.data[0]['id']}")
            
        return True
    except Exception as e:
        print(f"Failed to insert sample data: {e}")
        return False

def main():
    print("Testing Supabase Setup\n")
    
    # Test connection
    supabase = test_supabase_connection()
    if not supabase:
        return
    
    print()
    
    # Test tables
    test_tables_exist(supabase)
    
    print()
    
    # Test data operations
    test_insert_sample_data(supabase)
    
    print("\nSupabase setup test completed!")
    print("\nNext steps:")
    print("1. Update your .env file with real Supabase credentials")
    print("2. Run the SQL scripts in Supabase SQL Editor")
    print("3. Test your Flask API endpoints")

if __name__ == "__main__":
    main()
