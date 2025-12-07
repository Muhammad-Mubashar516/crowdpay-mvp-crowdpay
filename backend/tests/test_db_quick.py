#!/usr/bin/env python3
"""
Quick test after database setup
"""

from dotenv import load_dotenv
import os
from supabase import create_client


def test_after_setup():
    load_dotenv()
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
    
    # Test that tables exist
    tables_to_test = ['payment_links', 'contributions', 'webhook_events']
    
    for table in tables_to_test:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            print(f'Table {table} exists and is accessible')
        except Exception as e:
            print(f'Table {table} error: {e}')
    
    # Test inserting sample data
    try:
        link_data = {
            'slug': 'test-campaign-' + os.urandom(4).hex(),
            'title': 'Test Campaign',
            'description': 'This is a test',
            'goal_kes': 10000.00
        }
        
        result = supabase.table('payment_links').insert(link_data).execute()
        print(f'Sample data inserted: {result.data[0]["slug"]}')
        
    except Exception as e:
        print(f'Failed to insert test data: {e}')

if __name__ == "__main__":
    test_after_setup()
