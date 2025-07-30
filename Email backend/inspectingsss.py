import sqlite3
import os
from datetime import datetime, timedelta

# Your database paths
PERMITS_DB_PATH = r'E:\Aiden full Project\Email backend\permits.db'
CLIENTS_DB_PATH = r'E:\Aiden full Project\Email backend\database_new.db'


def debug_permits_database():
    """Debug the permits database to find why no permits are being retrieved"""

    print("🔍 DEBUGGING PERMITS DATABASE")
    print("=" * 50)

    # Check if database file exists
    if not os.path.exists(PERMITS_DB_PATH):
        print(f"❌ ERROR: Database file not found at: {PERMITS_DB_PATH}")
        return
    else:
        print(f"✅ Database file exists: {PERMITS_DB_PATH}")

    try:
        conn = sqlite3.connect(PERMITS_DB_PATH)
        cursor = conn.cursor()

        # 1. Check table structure
        print("\n📋 TABLE STRUCTURE:")
        cursor.execute("PRAGMA table_info(permits)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

        # 2. Check total number of records
        cursor.execute("SELECT COUNT(*) FROM permits")
        total_count = cursor.fetchone()[0]
        print(f"\n📊 TOTAL RECORDS: {total_count}")

        if total_count == 0:
            print("❌ No records in permits table!")
            return

        # 3. Check sample data
        print("\n📝 SAMPLE DATA (first 3 records):")
        cursor.execute("SELECT * FROM permits LIMIT 3")
        sample_records = cursor.fetchall()
        for i, record in enumerate(sample_records, 1):
            print(f"  Record {i}: {record}")

        # 4. Check date formats in issued_date column
        print("\n📅 DATE ANALYSIS:")
        cursor.execute("SELECT issued_date FROM permits WHERE issued_date IS NOT NULL LIMIT 10")
        dates = cursor.fetchall()
        print("Sample issued_date values:")
        for date_val in dates[:5]:
            print(f"  - '{date_val[0]}'")

        # 5. Test different date formats
        print("\n🔍 TESTING DATE QUERIES:")

        # Current query format (what your code uses)
        since_iso = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S.000')
        print(f"Current query date format: '{since_iso}'")

        cursor.execute("SELECT COUNT(*) FROM permits WHERE issued_date >= ?", (since_iso,))
        count_iso = cursor.fetchone()[0]
        print(f"Results with current format: {count_iso}")

        # Try simple date format
        since_simple = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        print(f"Simple date format: '{since_simple}'")

        cursor.execute("SELECT COUNT(*) FROM permits WHERE issued_date >= ?", (since_simple,))
        count_simple = cursor.fetchone()[0]
        print(f"Results with simple format: {count_simple}")

        # Try with different time periods
        for days in [7, 30, 90, 365, 3650]:
            since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM permits WHERE issued_date >= ?", (since,))
            count = cursor.fetchone()[0]
            print(f"Last {days} days: {count} permits")

        # 6. Check distinct permit types
        print("\n🏷️  PERMIT TYPES:")
        cursor.execute("SELECT permit_type, COUNT(*) FROM permits GROUP BY permit_type")
        permit_types = cursor.fetchall()
        for ptype, count in permit_types:
            print(f"  - {ptype}: {count} permits")

        # 7. Check recent permits (regardless of date format)
        print("\n📅 MOST RECENT PERMITS:")
        cursor.execute("""
            SELECT permit_num, permit_type, issued_date, applied_date 
            FROM permits 
            ORDER BY rowid DESC 
            LIMIT 5
        """)
        recent = cursor.fetchall()
        for permit in recent:
            print(f"  - {permit}")

        conn.close()

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")


def debug_clients_database():
    """Debug the clients database"""

    print("\n🔍 DEBUGGING CLIENTS DATABASE")
    print("=" * 50)

    if not os.path.exists(CLIENTS_DB_PATH):
        print(f"❌ ERROR: Database file not found at: {CLIENTS_DB_PATH}")
        return
    else:
        print(f"✅ Database file exists: {CLIENTS_DB_PATH}")

    try:
        conn = sqlite3.connect(CLIENTS_DB_PATH)
        cursor = conn.cursor()

        # Check table structure
        print("\n📋 CLIENT TABLE STRUCTURE:")
        cursor.execute("PRAGMA table_info(client)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")

        # Check clients by permit type
        print("\n👥 CLIENTS BY PERMIT TYPE:")
        cursor.execute("""
            SELECT permit_type, COUNT(*) 
            FROM client 
            WHERE email IS NOT NULL AND email != '' 
            GROUP BY permit_type
        """)
        client_types = cursor.fetchall()
        for ptype, count in client_types:
            print(f"  - {ptype}: {count} clients")

        conn.close()

    except Exception as e:
        print(f"❌ Error connecting to clients database: {e}")


if __name__ == "__main__":
    debug_permits_database()
    debug_clients_database()

    print("\n🔧 SUGGESTED FIXES:")
    print("1. Check if your issued_date format matches the query format")
    print("2. Try increasing days_back parameter (currently 30)")
    print("3. Verify permit data exists in the expected date range")
    print("4. Check if permit_type values match between permits and clients tables")