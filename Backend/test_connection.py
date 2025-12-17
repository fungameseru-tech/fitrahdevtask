import os
from dotenv import load_dotenv
import psycopg2

# Load environment - try both paths
load_dotenv(os.path.join('..', '.env.local'))
load_dotenv('.env.local')

# Get database URL
db_url = os.getenv('DATABASE_URL')

if not db_url:
    print("❌ DATABASE_URL not found in environment")
    print("\n💡 Make sure Neon Local Connect extension is running!")
    print("   Or use direct connection:")
    db_url = "postgresql://neondb_owner:npg_EnVuj8G4bmek@ep-hidden-thunder-adyxhuf2-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
    print(f"   Using direct Neon URL...")

print(f"\nTesting connection to: {db_url[:60]}...")

try:
    # Test connection
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    
    print("✅ Connection successful!")
    print(f"PostgreSQL version: {version[0][:50]}...")
    
    # Check if tables exist
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    
    if tables:
        print(f"\n📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("\n⚠️  No tables found. Need to run migrations.")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
