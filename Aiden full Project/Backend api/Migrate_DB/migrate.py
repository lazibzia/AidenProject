# migrate_database.py
"""
Migration script to convert your existing Denver-only database 
to the new multi-city structure.
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os
import shutil
from typing import Dict, Any

class DatabaseMigrator:
    def __init__(self, old_db_path: str = "old_permits.db", new_db_path: str = "permits.db"):
        self.old_db_path = old_db_path
        self.new_db_path = new_db_path
    
    def migrate(self):
        """Run the complete migration process"""
        print("🔄 Starting database migration...")
        
        # Step 1: Backup existing database
        self._backup_database()
        
        # Step 2: Create new database structure
        self._create_new_database()
        
        # Step 3: Migrate existing data
        self._migrate_existing_data()
        
        # Step 4: Verify migration
        self._verify_migration()
        
        print("✅ Migration completed successfully!")
    
    def _backup_database(self):
        """Create a backup of the existing database"""
        if os.path.exists(self.old_db_path):
            backup_path = f"{self.old_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.old_db_path, backup_path)
            print(f"📦 Database backed up to: {backup_path}")
        else:
            print("⚠️  No existing database found to backup")
    
    def _create_new_database(self):
        """Create the new multi-city database structure"""
        print("🏗️  Creating new database structure...")
        
        from database.db_manager import DatabaseManager
        db_manager = DatabaseManager(self.new_db_path)
        # Database is automatically initialized in the constructor
        
        print("✅ New database structure created")
    
    def _migrate_existing_data(self):
        """Migrate data from old database to new structure"""
        if not os.path.exists(self.old_db_path):
            print("⚠️  No existing database found - skipping data migration")
            return
        
        print("📊 Migrating existing Denver permits data...")
        
        # Connect to old database
        old_conn = sqlite3.connect(self.old_db_path)
        old_conn.row_factory = sqlite3.Row
        
        # Connect to new database
        new_conn = sqlite3.connect(self.new_db_path)
        new_conn.row_factory = sqlite3.Row
        
        try:
            # Check if old table exists
            old_cursor = old_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='residential_permits'"
            )
            
            if not old_cursor.fetchone():
                print("⚠️  No 'residential_permits' table found in old database")
                return
            
            # Get all records from old database
            old_cursor = old_conn.execute("SELECT * FROM residential_permits")
            old_records = old_cursor.fetchall()
            
            print(f"📋 Found {len(old_records)} existing records to migrate")
            
            # Migrate each record
            migrated_count = 0
            
            for record in old_records:
                try:
                    # Convert old record to new format
                    new_record = self._convert_record_format(record)
                    
                    # Insert into new database
                    new_conn.execute('''
                        INSERT OR REPLACE INTO permits (
                            city, permit_num, address, contractor_name, valuation,
                            permit_fee, date_issued, neighborhood, class, units,
                            description, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        'denver',  # All existing records are Denver
                        new_record.get('permit_num'),
                        new_record.get('address'),
                        new_record.get('contractor_name'),
                        new_record.get('valuation'),
                        new_record.get('permit_fee'),
                        new_record.get('date_issued'),
                        new_record.get('neighborhood'),
                        new_record.get('class'),
                        new_record.get('units'),
                        new_record.get('description'),
                        new_record.get('status', 'Active')
                    ))
                    
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"❌ Error migrating record {record.get('permit_num', 'unknown')}: {e}")
                    continue
            
            new_conn.commit()
            print(f"✅ Successfully migrated {migrated_count} records")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            new_conn.rollback()
            
        finally:
            old_conn.close()
            new_conn.close()
    
    def _convert_record_format(self, old_record: sqlite3.Row) -> Dict[str, Any]:
        """Convert old record format to new format"""
        
        # Map old column names to new format
        # Adjust these mappings based on your actual old database schema
        return {
            'permit_num': old_record.get('permit_num'),
            'address': old_record.get('address'),
            'contractor_name': old_record.get('contractor_name'),
            'valuation': old_record.get('valuation'),
            'permit_fee': old_record.get('permit_fee'),
            'date_issued': old_record.get('date_issued'),
            'neighborhood': old_record.get('neighborhood'),
            'class': old_record.get('class'),
            'units': old_record.get('units'),
            'description': old_record.get('description', ''),
            'status': 'Active'
        }
    
    def _verify_migration(self):
        """Verify the migration was successful"""
        print("🔍 Verifying migration...")
        
        if not os.path.exists(self.new_db_path):
            print("❌ New database not found!")
            return
        
        conn = sqlite3.connect(self.new_db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            # Check total records
            cursor = conn.execute("SELECT COUNT(*) as count FROM permits")
            total_count = cursor.fetchone()['count']
            
            # Check Denver records
            cursor = conn.execute("SELECT COUNT(*) as count FROM permits WHERE city = 'denver'")
            denver_count = cursor.fetchone()['count']
            
            # Check unique cities
            cursor = conn.execute("SELECT DISTINCT city FROM permits")
            cities = [row['city'] for row in cursor.fetchall()]
            
            print(f"📊 Migration verification:")
            print(f"   Total records: {total_count}")
            print(f"   Denver records: {denver_count}")
            print(f"   Cities: {', '.join(cities)}")
            
            if total_count > 0:
                print("✅ Migration verification successful!")
            else:
                print("⚠️  No records found in new database")
                
        except Exception as e:
            print(f"❌ Verification failed: {e}")
        
        finally:
            conn.close()

# # ===== EXAMPLE USAGE SCRIPT =====
# # example_usage.py
# """
# Example script showing how to use the new multi-city system
# """
#
# import asyncio
# from database.db_manager import DatabaseManager
# from scrapers.scraper_manager import ScraperManager
# from datetime import datetime, timedelta
#
# async def example_usage():
#     """Example of using the new multi-city system"""
#
#     print("🚀 Multi-City Permits System Example")
#     print("=" * 50)
#
#     # Initialize components
#     db_manager = DatabaseManager()
#     scraper_manager = ScraperManager()
#
#     # 1. Get available cities
#     print("\n1. Available Cities:")
#     cities = db_manager.get_available_cities()
#     print(f"   {cities}")
#
#     # 2. Get overall statistics
#     print("\n2. Overall Statistics:")
#     stats = db_manager.get_overall_stats()
#     for key, value in stats.items():
#         print(f"   {key}: {value}")
#
#     # 3. Get city-specific statistics
#     if 'denver' in cities:
#         print("\n3. Denver Statistics:")
#         denver_stats = db_manager.get_city_stats('denver')
#         for key, value in denver_stats.items():
#             print(f"   {key}: {value}")
#
#     # 4. Search permits
#     print("\n4. Recent Permits Search:")
#     results = db_manager.search_permits(limit=5)
#     print(f"   Found {results['total']} permits")
#     for permit in results['permits'][:3]:  # Show first 3
#         print(f"   - {permit['city']}: {permit['permit_num']} - {permit['address']}")
#
#     # 5. City-specific search
#     print("\n5. Denver-specific Search:")
#     denver_results = db_manager.search_permits(city='denver', limit=5)
#     print(f"   Found {denver_results['total']} Denver permits")
#
#     # 6. Scraping example (commented out to avoid actual scraping)
#     # print("\n6. Scraping Example:")
#     # today = datetime.today().date()
#     # permits = scraper_manager.scrape_city('denver', today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
#     # print(f"   Scraped {len(permits)} permits")
#
#     print("\n✅ Example completed!")