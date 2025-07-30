# import sqlite3
# from typing import List, Dict, Optional, Any
# from datetime import datetime
# import pandas as pd
# from contextlib import contextmanager
#
# class DatabaseManager:
#     def __init__(self, db_path: str = "permits.db"):
#         self.db_path = db_path
#         self.initialize_database()
#
#     @contextmanager
#     def get_connection(self):
#         """Context manager for database connections"""
#         conn = sqlite3.connect(self.db_path)
#         conn.row_factory = sqlite3.Row
#         try:
#             yield conn
#         finally:
#             conn.close()
#
#     # def initialize_database(self):
#     #     """Initialize database tables"""
#     #     with self.get_connection() as conn:
#     #         # Main permits table with city column
#     #         conn.execute('''
#     #             CREATE TABLE IF NOT EXISTS permits (
#     #                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#     #                 city TEXT NOT NULL,
#     #                 permit_num TEXT NOT NULL,
#     #                 address TEXT,
#     #                 contractor_name TEXT,
#     #                 valuation REAL,
#     #                 permit_fee REAL,
#     #                 date_issued TEXT,
#     #                 neighborhood TEXT,
#     #                 class TEXT,
#     #                 units INTEGER,
#     #                 description TEXT,
#     #                 status TEXT,
#     #                 created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
#     #                 updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
#     #                 UNIQUE(city, permit_num)
#     #             )
#     #         ''')
#     #
#     #         # Settings table
#     #         conn.execute('''
#     #             CREATE TABLE IF NOT EXISTS settings (
#     #                 key TEXT PRIMARY KEY,
#     #                 value TEXT,
#     #                 updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
#     #             )
#     #         ''')
#     #
#     #         # City configurations table
#     #         conn.execute('''
#     #             CREATE TABLE IF NOT EXISTS city_configs (
#     #                 city TEXT PRIMARY KEY,
#     #                 display_name TEXT,
#     #                 timezone TEXT,
#     #                 scraper_class TEXT,
#     #                 last_scraped DATETIME,
#     #                 is_active BOOLEAN DEFAULT TRUE
#     #             )
#     #         ''')
#     #
#     #         # Create indexes for performance
#     #         conn.execute('CREATE INDEX IF NOT EXISTS idx_permits_city ON permits(city)')
#     #         conn.execute('CREATE INDEX IF NOT EXISTS idx_permits_date ON permits(date_issued)')
#     #         conn.execute('CREATE INDEX IF NOT EXISTS idx_permits_contractor ON permits(contractor_name)')
#     #         conn.execute('CREATE INDEX IF NOT EXISTS idx_permits_valuation ON permits(valuation)')
#     #
#     #         conn.commit()
#
#     def initialize_database(self):
#         with self.get_connection() as conn:
#             conn.execute('''
#                 CREATE TABLE IF NOT EXISTS permits (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     city TEXT NOT NULL,
#                     permit_num TEXT NOT NULL,
#                     permit_type TEXT,
#                     description TEXT,
#                     applied_date TEXT,
#                     issued_date TEXT,
#                     current_status TEXT,
#                     applicant_name TEXT,
#                     applicant_address TEXT,
#                     contractor_name TEXT,
#                     contractor_address TEXT,
#                     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
#                     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
#                     UNIQUE(city, permit_num)
#                 )
#             ''')
#             conn.commit()
#
#     def get_available_cities(self) -> List[str]:
#         """Get list of cities with permits data"""
#         with self.get_connection() as conn:
#             cursor = conn.execute('SELECT DISTINCT city FROM permits ORDER BY city')
#             return [row['city'] for row in cursor.fetchall()]
#
#     # def insert_permits(self, city: str, permits_data: List[Dict]) -> int:
#     #     """Insert permits for a specific city"""
#     #     if not permits_data:
#     #         return 0
#     #
#     #     inserted_count = 0
#     #     with self.get_connection() as conn:
#     #         for permit in permits_data:
#     #             try:
#     #                 # Check if permit already exists
#     #                 existing = conn.execute(
#     #                     'SELECT 1 FROM permits WHERE city = ? AND permit_num = ?',
#     #                     (city, permit.get('permit_num'))
#     #                 ).fetchone()
#     #
#     #                 if existing:
#     #                     continue
#     #
#     #                 # Insert new permit
#     #                 conn.execute('''
#     #                     INSERT INTO permits (
#     #                         city, permit_num, address, contractor_name, valuation,
#     #                         permit_fee, date_issued, neighborhood, class, units,
#     #                         description, status
#     #                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#     #                 ''', (
#     #                     city,
#     #                     permit.get('permit_num'),
#     #                     permit.get('address'),
#     #                     permit.get('contractor_name'),
#     #                     permit.get('valuation'),
#     #                     permit.get('permit_fee'),
#     #                     permit.get('date_issued'),
#     #                     permit.get('neighborhood'),
#     #                     permit.get('class'),
#     #                     permit.get('units'),
#     #                     permit.get('description'),
#     #                     permit.get('status')
#     #                 ))
#     #
#     #                 inserted_count += 1
#     #
#     #             except Exception as e:
#     #                 print(f"Error inserting permit {permit.get('permit_num')}: {e}")
#     #                 continue
#     #
#     #         conn.commit()
#     #
#     #     return inserted_count
#
#     def insert_permits(self, city: str, permits_data: List[Dict]) -> int:
#         """Insert permits for a specific city"""
#         if not permits_data:
#             return 0
#
#         inserted_count = 0
#         with self.get_connection() as conn:
#             for permit in permits_data:
#                 try:
#                     existing = conn.execute(
#                         'SELECT 1 FROM permits WHERE city = ? AND permit_num = ?',
#                         (city, permit.get('permit_num'))
#                     ).fetchone()
#
#                     if existing:
#                         continue
#
#                     conn.execute('''
#                         INSERT INTO permits (
#                             city, permit_num, permit_type, description,
#                             applied_date, issued_date, current_status,
#                             applicant_name, applicant_address,
#                             contractor_name, contractor_address
#                         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                     ''', (
#                         city,
#                         permit.get('Permit Num'),
#                         permit.get('Permit Type Desc'),
#                         permit.get('Description'),
#                         permit.get('Applied Date'),
#                         permit.get('Issued Date'),
#                         permit.get('current_status'),
#                         permit.get('Applicant Name'),
#                         permit.get('Applicant Address'),
#                         permit.get('Contractor Name'),
#                         permit.get('Contractor Address')
#                     ))
#
#                     inserted_count += 1
#
#                 except Exception as e:
#                     print(f"❌ Error inserting permit {permit.get('permit_num')}: {e}")
#                     continue
#
#             conn.commit()
#
#         return inserted_count
#
#     def search_permits(self, city: Optional[str] = None, query: Optional[str] = None,
#                       contractor: Optional[str] = None, min_valuation: Optional[float] = None,
#                       max_valuation: Optional[float] = None, page: int = 1,
#                       limit: int = 20) -> Dict[str, Any]:
#         """Search permits with filters"""
#
#         with self.get_connection() as conn:
#             sql = '''
#                 SELECT city, permit_num, address, contractor_name ,
#                        permit_fee, date_issued, neighborhood, class, units,
#                        description, status
#                 FROM permits
#                 WHERE 1=1
#             '''
#             params = []
#
#             # Add filters
#             if city:
#                 sql += ' AND city = ?'
#                 params.append(city)
#
#             if query:
#                 sql += ' AND (address LIKE ? OR permit_num LIKE ? OR contractor_name LIKE ?)'
#                 params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
#
#             if contractor:
#                 sql += ' AND contractor_name LIKE ?'
#                 params.append(f'%{contractor}%')
#
#             # if min_valuation is not None:
#             #     sql += ' AND valuation >= ?'
#             #     params.append(min_valuation)
#             #
#             # if max_valuation is not None:
#             #     sql += ' AND valuation <= ?'
#             #     params.append(max_valuation)
#
#             # Get total count
#             count_sql = f'SELECT COUNT(*) FROM ({sql})'
#             total_count = conn.execute(count_sql, params).fetchone()[0]
#
#             # Add pagination
#             sql += ' ORDER BY date_issued DESC LIMIT ? OFFSET ?'
#             params.extend([limit, (page - 1) * limit])
#
#             # Execute query
#             cursor = conn.execute(sql, params)
#             permits = [dict(row) for row in cursor.fetchall()]
#
#             return {
#                 'permits': permits,
#                 'total': total_count,
#                 'page': page,
#                 'limit': limit,
#                 'pages': (total_count + limit - 1) // limit
#             }
#
#     def get_city_stats(self, city: str) -> Dict[str, Any]:
#         """Get statistics for a specific city"""
#         with self.get_connection() as conn:
#             stats = {}
#
#             # Total permits
#             stats['total_permits'] = conn.execute(
#                 'SELECT COUNT(*) FROM permits WHERE city = ?', (city,)
#             ).fetchone()[0]
#
#             # Total valuation
#             #stats['total_valuation'] = conn.execute(
#                # 'SELECT COALESCE(SUM(valuation), 0) FROM permits WHERE city = ? AND valuation > 0',
#                # (city,)
#             #).fetchone()[0]
#
#             # Average valuation
#             # stats['avg_valuation'] = conn.execute(
#             #     'SELECT COALESCE(AVG(valuation), 0) FROM permits WHERE city = ? AND valuation > 0',
#             #     (city,)
#             # ).fetchone()[0]
#
#             # Unique contractors
#             # stats['unique_contractors'] = conn.execute(
#             #     'SELECT COUNT(DISTINCT contractor_name) FROM permits WHERE city = ? AND contractor_name IS NOT NULL',
#             #     (city,)
#             # ).fetchone()[0]
#
#             return stats
#
#     def get_overall_stats(self) -> Dict[str, Any]:
#         """Get overall statistics across all cities"""
#         with self.get_connection() as conn:
#             stats = {}
#
#             stats['total_permits'] = conn.execute('SELECT COUNT(*) FROM permits').fetchone()[0]
#             # stats['total_valuation'] = conn.execute(
#             #     'SELECT COALESCE(SUM(valuation), 0) FROM permits WHERE valuation > 0'
#             # ).fetchone()[0]
#             # stats['avg_valuation'] = conn.execute(
#             #     'SELECT COALESCE(AVG(valuation), 0) FROM permits WHERE valuation > 0'
#             # ).fetchone()[0]
#             # stats['unique_contractors'] = conn.execute(
#             #     'SELECT COUNT(DISTINCT contractor_name) FROM permits WHERE contractor_name IS NOT NULL'
#             # ).fetchone()[0]
#             stats['cities_count'] = conn.execute(
#                 'SELECT COUNT(DISTINCT city) FROM permits'
#             ).fetchone()[0]
#
#             return stats
#
#     def get_recent_permits(self, city: Optional[str] = None, limit: int = 10) -> List[Dict]:
#         """Get recent permits"""
#         with self.get_connection() as conn:
#             if city:
#                 cursor = conn.execute('''
#                     SELECT city, permit_num, address, contractor_name, valuation, date_issued
#                     FROM permits
#                     WHERE city = ?
#                     ORDER BY date_issued DESC
#                     LIMIT ?
#                 ''', (city, limit))
#             else:
#                 cursor = conn.execute('''
#                     SELECT city, permit_num, address, contractor_name, valuation, date_issued
#                     FROM permits
#                     ORDER BY date_issued DESC
#                     LIMIT ?
#                 ''', (limit,))
#
#             return [dict(row) for row in cursor.fetchall()]
#
#     def get_top_contractors(self, city: Optional[str] = None, limit: int = 10) -> List[Dict]:
#         """Get top contractors by valuation"""
#         with self.get_connection() as conn:
#             if city:
#                 cursor = conn.execute('''
#                     SELECT contractor_name, COUNT(*) as permit_count,
#                            COALESCE(SUM(valuation), 0) as total_valuation
#                     FROM permits
#                     WHERE city = ? AND contractor_name IS NOT NULL AND valuation > 0
#                     GROUP BY contractor_name
#                     LIMIT ?
#                 ''', (city, limit))
#             else:
#                 cursor = conn.execute('''
#                     SELECT contractor_name, COUNT(*) as permit_count
#                     FROM permits
#                     WHERE contractor_name IS NOT NULL AND valuation > 0
#                     GROUP BY contractor_name
#                     ORDER BY total_valuation DESC
#                     LIMIT ?
#                 ''', (limit,))
#
#             return [dict(row) for row in cursor.fetchall()]
#
#     def get_permit_by_id(self, permit_id: str) -> Optional[Dict]:
#         """Get permit by ID (permit_num)"""
#         with self.get_connection() as conn:
#             cursor = conn.execute(
#                 'SELECT * FROM permits WHERE permit_num = ?',
#                 (permit_id,)
#             )
#             result = cursor.fetchone()
#             return dict(result) if result else None
#
#     def update_schedule_settings(self, hour: int, minute: int, cities: List[str]):
#         """Update scheduling settings"""
#         with self.get_connection() as conn:
#             conn.execute(
#                 'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
#                 ('scrape_hour', str(hour))
#             )
#             conn.execute(
#                 'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
#                 ('scrape_minute', str(minute))
#             )
#             conn.execute(
#                 'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
#                 ('scrape_cities', ','.join(cities))
#             )
#             conn.commit()


# file: db_manager.py

import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path: str = "permits.db"):
        self.db_path = db_path
        self.initialize_database()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def initialize_database(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS permits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    permit_num TEXT NOT NULL,
                    permit_type TEXT,
                    description TEXT,
                    applied_date TEXT,
                    issued_date TEXT,
                    current_status TEXT,
                    applicant_name TEXT,
                    applicant_address TEXT,
                    contractor_name TEXT,
                    contractor_address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(city, permit_num)
                )
            ''')
            conn.commit()

    def insert_permits(self, city: str, permits_data: List[Dict]) -> int:
        if not permits_data:
            return 0
        inserted_count = 0
        with self.get_connection() as conn:
            for permit in permits_data:
                try:
                    existing = conn.execute(
                        'SELECT 1 FROM permits WHERE city = ? AND permit_num = ?',
                        (city, permit.get('Permit Num'))
                    ).fetchone()
                    if existing:
                        continue
                    conn.execute('''
                        INSERT INTO permits (
                            city, permit_num, permit_type, description,
                            applied_date, issued_date, current_status,
                            applicant_name, applicant_address,
                            contractor_name, contractor_address
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        city,
                        permit.get('Permit Num'),
                        permit.get('Permit Type Desc'),
                        permit.get('Description'),
                        permit.get('Applied Date'),
                        permit.get('Issued Date'),
                        permit.get('current_status'),
                        permit.get('Applicant Name'),
                        permit.get('Applicant Address'),
                        permit.get('Contractor Name'),
                        permit.get('Contractor Address')
                    ))
                    inserted_count += 1
                except Exception as e:
                    print(f"❌ Error inserting permit {permit.get('Permit Num')}: {e}")
            conn.commit()
        return inserted_count

    # def search_permits(self, city: Optional[str] = None, query: Optional[str] = None,
    #                    contractor: Optional[str] = None, page: int = 1, limit: int = 20) -> Dict[str, Any]:
    #     with self.get_connection() as conn:
    #         sql = '''
    #             SELECT city, permit_num, permit_type, description,
    #                    applied_date, issued_date, current_status,
    #                    applicant_name, applicant_address,
    #                    contractor_name, contractor_address
    #             FROM permits
    #             WHERE 1=1
    #         '''
    #         params = []
    #         if city:
    #             sql += ' AND city = ?'
    #             params.append(city)
    #         if query:
    #             sql += ' AND (permit_num LIKE ? OR description LIKE ? OR contractor_name LIKE ?)'
    #             params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
    #         if contractor:
    #             sql += ' AND contractor_name LIKE ?'
    #             params.append(f'%{contractor}%')
    #         count_sql = f'SELECT COUNT(*) FROM ({sql})'
    #         total_count = conn.execute(count_sql, params).fetchone()[0]
    #         sql += ' ORDER BY issued_date DESC LIMIT ? OFFSET ?'
    #         params.extend([limit, (page - 1) * limit])
    #         cursor = conn.execute(sql, params)
    #         permits = [dict(row) for row in cursor.fetchall()]
    #         return {
    #             'permits': permits,
    #             'total': total_count,
    #             'page': page,
    #             'limit': limit,
    #             'pages': (total_count + limit - 1) // limit
    #         }
    def search_permits(
            self,
            city: Optional[str] = None,
            query: Optional[str] = None,
            contractor: Optional[str] = None,
            min_valuation: Optional[float] = None,
            max_valuation: Optional[float] = None,
            page: int = 1,
            limit: int = 20
    ) -> Dict[str, Any]:
        with self.get_connection() as conn:
            sql = '''
                  SELECT city, \
                         permit_num, \
                         permit_type, \
                         description,
                         applied_date, \
                         issued_date, \
                         current_status,
                         applicant_name, \
                         applicant_address,
                         contractor_name, \
                         contractor_address
                  FROM permits
                  WHERE 1 = 1 \
                  '''
            params = []

            if city:
                sql += ' AND city = ?'
                params.append(city)
            if query:
                sql += ' AND (permit_num LIKE ? OR description LIKE ? OR contractor_name LIKE ?)'
                params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
            if contractor:
                sql += ' AND contractor_name LIKE ?'
                params.append(f'%{contractor}%')
            if min_valuation is not None:
                sql += ' AND valuation >= ?'
                params.append(min_valuation)
            if max_valuation is not None:
                sql += ' AND valuation <= ?'
                params.append(max_valuation)

            # Note: you need a valuation column in your permits table for these to work.

            count_sql = f'SELECT COUNT(*) FROM ({sql})'
            total_count = conn.execute(count_sql, params).fetchone()[0]

            sql += ' ORDER BY issued_date DESC LIMIT ? OFFSET ?'
            params.extend([limit, (page - 1) * limit])

            cursor = conn.execute(sql, params)
            permits = [dict(row) for row in cursor.fetchall()]

            return {
                'permits': permits,
                'total': total_count,
                'page': page,
                'limit': limit,
                'pages': (total_count + limit - 1) // limit
            }

    def get_available_cities(self) -> List[str]:
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT DISTINCT city FROM permits ORDER BY city')
            return [row['city'] for row in cursor.fetchall()]

    def get_city_stats(self, city: str) -> Dict[str, Any]:
        with self.get_connection() as conn:
            stats = {}
            stats['total_permits'] = conn.execute(
                'SELECT COUNT(*) FROM permits WHERE city = ?', (city,)
            ).fetchone()[0]
            return stats

    def get_overall_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            stats = {}
            stats['total_permits'] = conn.execute('SELECT COUNT(*) FROM permits').fetchone()[0]
            stats['cities_count'] = conn.execute('SELECT COUNT(DISTINCT city) FROM permits').fetchone()[0]
            return stats

    def get_recent_permits(self, city: Optional[str] = None, limit: int = 10) -> List[Dict]:
        with self.get_connection() as conn:
            if city:
                cursor = conn.execute('''
                    SELECT city, permit_num, permit_type, issued_date,
                           contractor_name, applicant_name
                    FROM permits
                    WHERE city = ?
                    ORDER BY issued_date DESC
                    LIMIT ?
                ''', (city, limit))
            else:
                cursor = conn.execute('''
                    SELECT city, permit_num, permit_type, issued_date,
                           contractor_name, applicant_name
                    FROM permits
                    ORDER BY issued_date DESC
                    LIMIT ?
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_top_contractors(self, city: Optional[str] = None, limit: int = 10) -> List[Dict]:
        with self.get_connection() as conn:
            if city:
                cursor = conn.execute('''
                    SELECT contractor_name, COUNT(*) as permit_count
                    FROM permits
                    WHERE city = ? AND contractor_name IS NOT NULL
                    GROUP BY contractor_name
                    ORDER BY permit_count DESC
                    LIMIT ?
                ''', (city, limit))
            else:
                cursor = conn.execute('''
                    SELECT contractor_name, COUNT(*) as permit_count
                    FROM permits
                    WHERE contractor_name IS NOT NULL
                    GROUP BY contractor_name
                    ORDER BY permit_count DESC
                    LIMIT ?
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_permit_by_id(self, permit_id: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM permits WHERE permit_num = ?',
                (permit_id,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None

    def update_schedule_settings(self, hour: int, minute: int, cities: List[str]):
        with self.get_connection() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
            conn.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                ('scrape_hour', str(hour))
            )
            conn.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                ('scrape_minute', str(minute))
            )
            conn.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                ('scrape_cities', ','.join(cities))
            )
            conn.commit()
