"""
Database manager for Enterprise Data Collector
SQLite database operations
Author: MiniMax Agent
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class DatabaseManager:
    """Database manager for SQLite operations"""
    
    def __init__(self, db_path: str = "Database/enterprise_data.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Create database directory if not exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Enhanced Companies table for v2.0
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Companies (
                        ma_so_thue TEXT PRIMARY KEY,
                        ten_cong_ty TEXT NOT NULL,
                        ten_giao_dich TEXT,
                        ten_tieng_anh TEXT,
                        nguoi_dai_dien TEXT,
                        chuc_vu_dai_dien TEXT,
                        dai_dien_phap_luat TEXT,
                        dien_thoai TEXT,
                        dien_thoai_dai_dien TEXT,
                        fax TEXT,
                        email TEXT,
                        website TEXT,
                        dia_chi_dang_ky TEXT,
                        dia_chi_thue TEXT,
                        tinh_thanh_pho TEXT,
                        quan_huyen TEXT,
                        phuong_xa TEXT,
                        nganh_nghe_kinh_doanh_chinh TEXT,
                        nganh_nghe_khac TEXT,
                        loai_hinh_doanh_nghiep TEXT,
                        tinh_trang_hoat_dong TEXT,
                        so_giay_phep_kinh_doanh TEXT,
                        ngay_cap_giay_phep DATE,
                        ngay_hoat_dong DATE,
                        ngay_thay_doi_gan_nhat DATE,
                        co_quan_cap_phep TEXT,
                        so_quyet_dinh TEXT,
                        von_dieu_le TEXT,
                        von_dang_ky TEXT,
                        cap_nhat_lan_cuoi TEXT,
                        trang_thai_hsctvn TEXT,
                        data_source TEXT DEFAULT 'api',
                        raw_json_api TEXT,
                        raw_json_hsctvn TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_tinh_trang ON Companies(tinh_trang_hoat_dong)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_nganh_nghe ON Companies(nganh_nghe_kinh_doanh_chinh)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_tinh_thanh ON Companies(tinh_thanh_pho)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_data_source ON Companies(data_source)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON Logs(timestamp)')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def company_exists(self, tax_code: str) -> bool:
        """Check if company exists in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM Companies WHERE ma_so_thue = ?', (tax_code,))
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Failed to check company existence: {e}")
            return False
    
    def insert_company(self, company_data: Dict[str, Any]) -> bool:
        """Insert new company record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare fields and values
                fields = list(company_data.keys())
                placeholders = ', '.join(['?' for _ in fields])
                
                sql = f'''
                    INSERT INTO Companies ({', '.join(fields)})
                    VALUES ({placeholders})
                '''
                
                cursor.execute(sql, list(company_data.values()))
                conn.commit()
                
                self.logger.debug(f"Company {company_data.get('ma_so_thue')} inserted successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to insert company: {e}")
            return False
    
    def update_company(self, tax_code: str, company_data: Dict[str, Any]) -> bool:
        """Update existing company record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare update fields
                update_fields = []
                update_values = []
                
                for field, value in company_data.items():
                    if field not in ['ma_so_thue', 'created_at']:  # Skip PK and created_at
                        update_fields.append(f'{field} = ?')
                        update_values.append(value)
                
                update_values.append(tax_code)  # For WHERE clause
                
                sql = f'''
                    UPDATE Companies 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE ma_so_thue = ?
                '''
                
                cursor.execute(sql, update_values)
                conn.commit()
                
                self.logger.debug(f"Company {tax_code} updated successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update company {tax_code}: {e}")
            return False
    
    def save_company(self, company_data: Dict[str, Any]) -> bool:
        """Save company (insert or update)"""
        tax_code = company_data.get('ma_so_thue')
        if not tax_code:
            self.logger.error("Cannot save company without tax code")
            return False
        
        if self.company_exists(tax_code):
            return self.update_company(tax_code, company_data)
        else:
            return self.insert_company(company_data)
    
    def get_company(self, tax_code: str) -> Optional[Dict[str, Any]]:
        """Get company by tax code"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM Companies WHERE ma_so_thue = ?', (tax_code,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get company {tax_code}: {e}")
            return None
    
    def get_companies(
        self, 
        tinh_trang: Optional[str] = None,
        nganh_nghe: Optional[str] = None,
        tinh_thanh_pho: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get companies with filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build query
                conditions = []
                params = []
                
                if tinh_trang:
                    conditions.append('tinh_trang_hoat_dong = ?')
                    params.append(tinh_trang)
                
                if nganh_nghe:
                    conditions.append('nganh_nghe_kinh_doanh_chinh LIKE ?')
                    params.append(f'%{nganh_nghe}%')
                
                if tinh_thanh_pho:
                    conditions.append('tinh_thanh_pho LIKE ?')
                    params.append(f'%{tinh_thanh_pho}%')
                
                where_clause = ''
                if conditions:
                    where_clause = 'WHERE ' + ' AND '.join(conditions)
                
                limit_clause = ''
                if limit:
                    limit_clause = f'LIMIT {limit}'
                
                sql = f'''
                    SELECT * FROM Companies 
                    {where_clause}
                    ORDER BY updated_at DESC
                    {limit_clause}
                '''
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get companies: {e}")
            return []
    
    def log_message(self, level: str, message: str):
        """Log message to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO Logs (level, message) VALUES (?, ?)',
                    (level, message)
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to log to database: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total companies
                cursor.execute('SELECT COUNT(*) FROM Companies')
                stats['total_companies'] = cursor.fetchone()[0]
                
                # By status
                cursor.execute('''
                    SELECT tinh_trang_hoat_dong, COUNT(*) 
                    FROM Companies 
                    WHERE tinh_trang_hoat_dong IS NOT NULL AND tinh_trang_hoat_dong != ''
                    GROUP BY tinh_trang_hoat_dong
                ''')
                stats['by_status'] = dict(cursor.fetchall())
                
                # By data source
                cursor.execute('''
                    SELECT data_source, COUNT(*) 
                    FROM Companies 
                    GROUP BY data_source
                ''')
                stats['by_data_source'] = dict(cursor.fetchall())
                
                # By province (top 10)
                cursor.execute('''
                    SELECT tinh_thanh_pho, COUNT(*) 
                    FROM Companies 
                    WHERE tinh_thanh_pho IS NOT NULL AND tinh_thanh_pho != ''
                    GROUP BY tinh_thanh_pho
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                ''')
                stats['top_provinces'] = dict(cursor.fetchall())
                
                # Recent additions
                cursor.execute('''
                    SELECT DATE(created_at), COUNT(*)
                    FROM Companies
                    WHERE created_at >= DATE('now', '-7 days')
                    GROUP BY DATE(created_at)
                    ORDER BY DATE(created_at) DESC
                ''')
                stats['recent_additions'] = dict(cursor.fetchall())
                
                # Total logs
                cursor.execute('SELECT COUNT(*) FROM Logs')
                stats['total_logs'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {}
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """Clean up old log entries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM Logs 
                    WHERE timestamp < DATE('now', '-{} days')
                '''.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old log entries")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup logs: {e}")
            return 0
    
    def close(self):
        """Close database connections"""
        # SQLite connections are per-thread and auto-close
        pass