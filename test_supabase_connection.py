#!/usr/bin/env python
"""
Quick test script to verify Supabase credentials
Run: python test_supabase_connection.py
"""

import os
import requests
from decouple import config

def test_supabase_connection():
/*************  ✨ Windsurf Command ⭐  *************/
    """
    Tests connection to Supabase Storage API using credentials in .env file.

    Checks if SUPABASE_URL and SUPABASE_KEY are set in .env file.
    If not, prints a warning message with instructions to add them.

    Tests connection to Supabase Storage API using provided credentials.
    If successful, prints a success message and lists the buckets found.
    If not successful, prints an error message with the response status code and text.

    Returns:
        bool: True if connection is successful, False otherwise
    """
/*******  99aff64f-b274-4d7d-b613-e59c114f61df  *******/
    print("🔍 Testing Supabase Connection...")
    print("=" * 50)
    
    # Load credentials
    supabase_url = config('SUPABASE_URL', default='')
    supabase_key = config('SUPABASE_KEY', default='')
    
    # Check if credentials exist
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL or SUPABASE_KEY not found in .env file")
        print("\nAdd these to your .env file:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_KEY=your-anon-key")
        return False
    
    print(f"✅ SUPABASE_URL found: {supabase_url}")
    print(f"✅ SUPABASE_KEY found: {supabase_key[:20]}...")
    print()
    
    # Test connection to storage API
    storage_url = f"{supabase_url}/storage/v1/bucket"
    headers = {
        'Authorization': f'Bearer {supabase_key}',
        'apikey': supabase_key
    }
    
    print("📡 Testing connection to Supabase Storage API...")
    
    try:
        response = requests.get(storage_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            buckets = response.json()
            print(f"✅ Connection successful! Found {len(buckets)} bucket(s):")
            print()
            
            for bucket in buckets:
                print(f"  📦 Bucket: {bucket.get('name')}")
                print(f"     Public: {bucket.get('public', False)}")
                print(f"     ID: {bucket.get('id')}")
                print()
            
            # Check for required buckets
            bucket_names = [b.get('name') for b in buckets]
            
            if 'profilepic' not in bucket_names:
                print("⚠️  WARNING: 'profilepic' bucket not found!")
                print("   Create it in Supabase Dashboard → Storage")
                print()
            
            if 'Uploadfiles' not in bucket_names:
                print("⚠️  WARNING: 'Uploadfiles' bucket not found!")
                print("   Create it in Supabase Dashboard → Storage")
                print()
            
            print("✅ Supabase is configured correctly!")
            return True
            
        else:
            print(f"❌ Connection failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Connection timeout - check your internet connection")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    test_supabase_connection()