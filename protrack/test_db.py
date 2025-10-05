import psycopg2

try:
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres.zkpaqrzwoffzumhbeyfj",
        password="dmsL62VTD1LL6QDY",
        host="aws-1-us-east-2.pooler.supabase.com",
        port="6543"
    )
    print("✓ Connection successful!")
    conn.close()
except Exception as e:
    print(f"✗ Connection failed: {e}")