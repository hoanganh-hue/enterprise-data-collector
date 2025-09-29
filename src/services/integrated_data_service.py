"""
Integrated Data Service for Enterprise Data Collector
Service tích hợp để quản lý việc thu thập dữ liệu từ API với database và logging
Author: MiniMax Agent
"""

import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import sqlite3
from pathlib import Path
import json

from .api_client import ThongTinDoanhNghiepAPIClient
from ..models import CompanyDetail, City, Industry, PaginatedResponse


class IntegratedDataService:
    """
    Service tích hợp cho việc thu thập và lưu trữ dữ liệu doanh nghiệp
    
    Tính năng:
    - Tích hợp với ThongTinDoanhNghiepAPIClient
    - Quản lý database SQLite  
    - Duplicate checking
    - Progress tracking
    - Error handling và recovery
    """
    
    def __init__(
        self,
        api_client: ThongTinDoanhNghiepAPIClient,
        db_path: str = "Database/enterprise_data.db",
        logger: Optional[logging.Logger] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ):
        """
        Initialize IntegratedDataService
        
        Args:
            api_client: ThongTinDoanhNghiepAPIClient instance
            db_path: Path to SQLite database
            logger: Logger instance
            progress_callback: Callback function cho progress updates (message, current, total)
        """
        self.api_client = api_client
        self.db_path = db_path
        self.logger = logger or logging.getLogger(__name__)
        self.progress_callback = progress_callback
        
        # Create database directory if not exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Stats
        self.stats = {
            'total_processed': 0,
            'new_records': 0,
            'updated_records': 0,
            'skipped_records': 0,
            'errors': 0
        }
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Companies table with enhanced schema
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Companies (
                        ma_so_thue TEXT PRIMARY KEY,
                        ten_cong_ty TEXT NOT NULL,
                        ten_giao_dich TEXT,
                        ten_tieng_anh TEXT,
                        nguoi_dai_dien TEXT,
                        chuc_vu_dai_dien TEXT,
                        dia_chi TEXT,
                        dien_thoai TEXT,
                        fax TEXT,
                        email TEXT,
                        website TEXT,
                        tinh_trang_hoat_dong TEXT,
                        ngay_cap_phep DATE,
                        ngay_hoat_dong DATE,
                        ngay_thay_doi_gan_nhat DATE,
                        nganh_nghe_kinh_doanh_chinh TEXT,
                        nganh_nghe_khac TEXT,  -- JSON array
                        loai_hinh_doanh_nghiep TEXT,
                        von_dieu_le TEXT,
                        von_dang_ky TEXT,
                        tinh_thanh_pho TEXT,
                        quan_huyen TEXT,
                        phuong_xa TEXT,
                        co_quan_cap_phep TEXT,
                        so_quyet_dinh TEXT,
                        raw_json TEXT,  -- Full API response
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
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_tinh_trang ON Companies(tinh_trang_hoat_dong)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_nganh_nghe ON Companies(nganh_nghe_kinh_doanh_chinh)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_companies_tinh_thanh ON Companies(tinh_thanh_pho)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON Logs(timestamp)')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _report_progress(self, message: str, current: int, total: int):
        """Report progress via callback"""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        
        self.logger.info(f"Progress: {message} ({current}/{total})")
    
    def _log_to_database(self, level: str, message: str):
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
    
    def company_exists(self, tax_code: str) -> bool:
        """
        Kiểm tra xem công ty đã tồn tại trong database chưa
        
        Args:
            tax_code: Mã số thuế
            
        Returns:
            True nếu đã tồn tại
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM Companies WHERE ma_so_thue = ?', (tax_code,))
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Failed to check company existence: {e}")
            return False
    
    def save_company(self, company: CompanyDetail) -> bool:
        """
        Lưu thông tin công ty vào database
        
        Args:
            company: CompanyDetail object
            
        Returns:
            True nếu lưu thành công
        """
        try:
            company_dict = company.to_dict()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if exists
                exists = self.company_exists(company.ma_so_thue)
                
                if exists:
                    # Update existing record
                    update_fields = []
                    update_values = []
                    
                    for field, value in company_dict.items():
                        if field not in ['ma_so_thue', 'created_at']:  # Skip PK and created_at
                            update_fields.append(f'{field} = ?')
                            update_values.append(value)
                    
                    update_values.append(company.ma_so_thue)  # For WHERE clause
                    
                    sql = f'''
                        UPDATE Companies 
                        SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                        WHERE ma_so_thue = ?
                    '''
                    
                    cursor.execute(sql, update_values)
                    self.stats['updated_records'] += 1
                    action = "updated"
                    
                else:
                    # Insert new record
                    fields = list(company_dict.keys())
                    placeholders = ', '.join(['?' for _ in fields])
                    
                    sql = f'''
                        INSERT INTO Companies ({', '.join(fields)})
                        VALUES ({placeholders})
                    '''
                    
                    cursor.execute(sql, list(company_dict.values()))
                    self.stats['new_records'] += 1
                    action = "inserted"
                
                conn.commit()
                self.logger.debug(f"Company {company.ma_so_thue} {action} successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save company {company.ma_so_thue}: {e}")
            self.stats['errors'] += 1
            return False
    
    def collect_companies_by_filters(
        self,
        location_slug: Optional[str] = None,
        industry_slug: Optional[str] = None,
        max_companies: Optional[int] = None,
        page_size: int = 50,
        skip_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Thu thập dữ liệu công ty theo filter và lưu vào database
        
        Args:
            location_slug: Slug địa lý
            industry_slug: Slug ngành nghề
            max_companies: Giới hạn số công ty (None = không giới hạn)
            page_size: Số công ty mỗi page
            skip_existing: Bỏ qua những công ty đã có trong DB
            
        Returns:
            Dictionary chứa thống kê kết quả
        """
        
        # Reset stats
        self.stats = {
            'total_processed': 0,
            'new_records': 0,
            'updated_records': 0,
            'skipped_records': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        self.logger.info(f"Starting data collection: location={location_slug}, industry={industry_slug}, max={max_companies}")
        self._log_to_database('INFO', f"Started collection: location={location_slug}, industry={industry_slug}")
        
        try:
            page = 1
            collected_companies = []
            
            while True:
                # Search companies
                self._report_progress(f"Searching page {page}...", self.stats['total_processed'], max_companies or 1000)
                
                search_result = self.api_client.search_companies(
                    location_slug=location_slug,
                    industry_slug=industry_slug,
                    page=page,
                    page_size=page_size
                )
                
                if not search_result.items:
                    self.logger.info("No more companies found, stopping")
                    break
                
                # Process each company in this page
                for i, company_summary in enumerate(search_result.items):
                    current_progress = self.stats['total_processed'] + i + 1
                    
                    # Check limits
                    if max_companies and current_progress > max_companies:
                        self.logger.info(f"Reached max companies limit: {max_companies}")
                        break
                    
                    tax_code = company_summary.ma_so_thue
                    
                    # Skip if already exists (if requested)
                    if skip_existing and self.company_exists(tax_code):
                        self.stats['skipped_records'] += 1
                        self.logger.debug(f"Skipping existing company: {tax_code}")
                        continue
                    
                    # Get company details
                    self._report_progress(
                        f"Processing {tax_code}...", 
                        current_progress, 
                        max_companies or search_result.total_count
                    )
                    
                    try:
                        company_detail = self.api_client.get_company_detail(tax_code)
                        
                        if company_detail:
                            # Save to database
                            if self.save_company(company_detail):
                                collected_companies.append(company_detail)
                                self.logger.info(f"Successfully processed {tax_code}: {company_detail.ten_cong_ty}")
                            else:
                                self.logger.error(f"Failed to save {tax_code}")
                        else:
                            self.logger.warning(f"No details found for {tax_code}")
                            self.stats['errors'] += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error processing {tax_code}: {e}")
                        self.stats['errors'] += 1
                
                # Update processed count
                self.stats['total_processed'] += len(search_result.items)
                
                # Check stopping conditions
                if max_companies and self.stats['total_processed'] >= max_companies:
                    break
                    
                if not search_result.has_next:
                    break
                
                page += 1
                
                # Log progress
                self.logger.info(f"Completed page {page-1}: {self.stats}")
            
            # Final stats
            self.stats['end_time'] = datetime.now()
            self.stats['duration'] = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            self.logger.info(f"Collection completed: {self.stats}")
            self._log_to_database('INFO', f"Collection completed: {json.dumps(self.stats, default=str)}")
            
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Collection failed: {e}")
            self._log_to_database('ERROR', f"Collection failed: {e}")
            raise
    
    def get_companies_from_db(
        self,
        tinh_trang: Optional[str] = None,
        nganh_nghe: Optional[str] = None,
        tinh_thanh_pho: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lấy danh sách công ty từ database với filter
        
        Args:
            tinh_trang: Tình trạng hoạt động
            nganh_nghe: Ngành nghề
            tinh_thanh_pho: Tỉnh/thành phố
            limit: Giới hạn số kết quả
            
        Returns:
            List of company dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
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
                
                # Convert to list of dicts
                companies = [dict(row) for row in rows]
                
                self.logger.info(f"Retrieved {len(companies)} companies from database")
                return companies
                
        except Exception as e:
            self.logger.error(f"Failed to get companies from database: {e}")
            return []
    
    def get_db_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê database
        
        Returns:
            Dictionary chứa thống kê
        """
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
                    WHERE tinh_trang_hoat_dong IS NOT NULL
                    GROUP BY tinh_trang_hoat_dong
                ''')
                stats['by_status'] = dict(cursor.fetchall())
                
                # By province
                cursor.execute('''
                    SELECT tinh_thanh_pho, COUNT(*) 
                    FROM Companies 
                    WHERE tinh_thanh_pho IS NOT NULL
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
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Xóa logs cũ hơn số ngày specified
        
        Args:
            days: Số ngày để giữ logs
        """
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
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
    
    def close(self):
        """Cleanup resources"""
        if hasattr(self, 'api_client'):
            self.api_client.close()
        self.logger.info("IntegratedDataService closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()