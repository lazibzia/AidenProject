import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import contextmanager
from sqlmodel import create_engine, Session

DATABASE_URL = "sqlite:///permits.db"  # or your actual DB URL
#engine = create_engine(DATABASE_URL, echo=True)
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False, "timeout": 10}  # Wait up to 10s
)

def get_session():
    with Session(engine) as session:
        yield session

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
                    permit_class_mapped TEXT,
                    work_class TEXT,
                    description TEXT,
                    applied_date TEXT,
                    issued_date TEXT,
                    current_status TEXT,
                    applicant_name TEXT,
                    applicant_address TEXT,
                    contractor_name TEXT,
                    contractor_address TEXT,
                    contractor_company_name TEXT,
                    contractor_phone TEXT,
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
                            city, permit_num, permit_type, permit_class_mapped,
                            work_class, description, applied_date, issued_date,
                            current_status, applicant_name, applicant_address,
                            contractor_name, contractor_address,
                            contractor_company_name, contractor_phone
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        city,
                        permit.get('Permit Num'),
                        permit.get('Permit Type Desc'),
                        permit.get('Permit Class Mapped'),
                        permit.get('Work Class'),
                        permit.get('Description'),
                        permit.get('Applied Date'),
                        permit.get('Issued Date'),
                        permit.get('current_status'),
                        permit.get('Applicant Name'),
                        permit.get('Applicant Address'),
                        permit.get('Contractor Name'),
                        permit.get('Contractor Address'),
                        permit.get('Contractor Company Name'),
                        permit.get('Contractor Phone')
                    ))
                    inserted_count += 1

                except Exception as e:
                    print(f"❌ Error inserting permit {permit.get('Permit Num')}: {e}")
                    continue

            conn.commit()
        return inserted_count

    def search_permits(self, city: Optional[str] = None, query: Optional[str] = None,
                      contractor: Optional[str] = None, work_class: Optional[str] = None,
                      permit_class: Optional[str] = None, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        with self.get_connection() as conn:
            sql = '''
                SELECT 
                    city, permit_num, permit_type, permit_class_mapped,
                    work_class, description, applied_date, issued_date,
                    current_status, applicant_name, applicant_address,
                    contractor_name, contractor_address,
                    contractor_company_name, contractor_phone
                FROM permits
                WHERE 1=1
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
                
            if work_class:
                sql += ' AND work_class = ?'
                params.append(work_class)
                
            if permit_class:
                sql += ' AND permit_class_mapped = ?'
                params.append(permit_class)

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
            
            # Add stats for permit classes
            permit_classes = conn.execute('''
                SELECT permit_class_mapped, COUNT(*) as count 
                FROM permits 
                WHERE city = ? AND permit_class_mapped IS NOT NULL
                GROUP BY permit_class_mapped
            ''', (city,)).fetchall()
            stats['permit_classes'] = {row['permit_class_mapped']: row['count'] for row in permit_classes}
            
            # Add stats for work classes
            work_classes = conn.execute('''
                SELECT work_class, COUNT(*) as count 
                FROM permits 
                WHERE city = ? AND work_class IS NOT NULL
                GROUP BY work_class
            ''', (city,)).fetchall()
            stats['work_classes'] = {row['work_class']: row['count'] for row in work_classes}
            
            return stats

    def get_overall_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            stats = {}
            stats['total_permits'] = conn.execute('SELECT COUNT(*) FROM permits').fetchone()[0]
            stats['cities_count'] = conn.execute('SELECT COUNT(DISTINCT city) FROM permits').fetchone()[0]
            
            # Add overall permit class stats
            permit_classes = conn.execute('''
                SELECT permit_class_mapped, COUNT(*) as count 
                FROM permits 
                WHERE permit_class_mapped IS NOT NULL
                GROUP BY permit_class_mapped
            ''').fetchall()
            stats['permit_classes'] = {row['permit_class_mapped']: row['count'] for row in permit_classes}
            
            # Add overall work class stats
            work_classes = conn.execute('''
                SELECT work_class, COUNT(*) as count 
                FROM permits 
                WHERE work_class IS NOT NULL
                GROUP BY work_class
            ''').fetchall()
            stats['work_classes'] = {row['work_class']: row['count'] for row in work_classes}
            
            return stats

    def get_recent_permits(self, city: Optional[str] = None, limit: int = 10) -> List[Dict]:
        with self.get_connection() as conn:
            if city:
                cursor = conn.execute('''
                    SELECT 
                        city, permit_num, permit_type, issued_date,
                        contractor_name, contractor_company_name, work_class
                    FROM permits
                    WHERE city = ?
                    ORDER BY issued_date DESC
                    LIMIT ?
                ''', (city, limit))
            else:
                cursor = conn.execute('''
                    SELECT 
                        city, permit_num, permit_type, issued_date,
                        contractor_name, contractor_company_name, work_class
                    FROM permits
                    ORDER BY issued_date DESC
                    LIMIT ?
                ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_top_contractors(self, city: Optional[str] = None, limit: int = 10) -> List[Dict]:
        with self.get_connection() as conn:
            if city:
                cursor = conn.execute('''
                    SELECT 
                        contractor_name, 
                        contractor_company_name,
                        COUNT(*) as permit_count
                    FROM permits
                    WHERE city = ? AND contractor_name IS NOT NULL
                    GROUP BY contractor_name, contractor_company_name
                    ORDER BY permit_count DESC
                    LIMIT ?
                ''', (city, limit))
            else:
                cursor = conn.execute('''
                    SELECT 
                        contractor_name,
                        contractor_company_name,
                        COUNT(*) as permit_count
                    FROM permits
                    WHERE contractor_name IS NOT NULL
                    GROUP BY contractor_name, contractor_company_name
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