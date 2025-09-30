"""
Enhanced Integrated Data Service for Enterprise Data Collector v2.0
Service tích hợp để quản lý thu thập dữ liệu từ 2 nguồn: API + HSCTVN
Author: MiniMax Agent
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import time

from .api_client import ThongTinDoanhNghiepAPIClient
from .hsctvn_client import HSCTVNEnhanced
from ..models.enhanced_company import EnhancedCompany
from ..models.database import DatabaseManager
from ..logger import get_logger


class EnhancedIntegratedDataService:
    """
    Enhanced service cho việc thu thập và tích hợp dữ liệu từ 2 nguồn
    
    Features:
    - Thu thập từ thongtindoanhnghiep.co API
    - Tích hợp với hsctvn.com scraping
    - Database management với 31 fields
    - Progress tracking cho cả 2 giai đoạn
    - Error handling và recovery
    """
    
    def __init__(
        self,
        api_client: ThongTinDoanhNghiepAPIClient,
        db_manager: DatabaseManager,
        logger: Optional[logging.Logger] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ):
        self.api_client = api_client
        self.db_manager = db_manager
        self.hsctvn_client = HSCTVNEnhanced()
        self.logger = logger or get_logger()
        self.progress_callback = progress_callback
        
        # Stats tracking
        self.stats = {
            'total_processed': 0,
            'api_success': 0,
            'hsctvn_success': 0,
            'dual_source_success': 0,
            'new_records': 0,
            'updated_records': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _report_progress(self, message: str, current: int, total: int):
        """Report progress via callback and logging"""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        
        self.logger.info(f"Progress: {message} ({current}/{total})")
    
    async def collect_enhanced_data(
        self,
        location_slug: Optional[str] = None,
        industry_slug: Optional[str] = None,
        max_companies: Optional[int] = None,
        page_size: int = 20,
        enable_hsctvn: bool = True,
        hsctvn_delay: float = 2.0
    ) -> Dict[str, Any]:
        """
        Thu thập dữ liệu enhanced từ 2 nguồn
        
        Args:
            location_slug: Slug địa lý
            industry_slug: Slug ngành nghề
            max_companies: Giới hạn số công ty
            page_size: Số công ty mỗi page
            enable_hsctvn: Có kích hoạt HSCTVN scraping không
            hsctvn_delay: Delay giữa các HSCTVN requests (giây)
            
        Returns:
            Dictionary chứa thống kê kết quả
        """
        
        # Reset stats
        self.stats = {
            'total_processed': 0,
            'api_success': 0,
            'hsctvn_success': 0,
            'dual_source_success': 0,
            'new_records': 0,
            'updated_records': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'end_time': None
        }
        
        self.logger.info(f"Starting enhanced data collection: location={location_slug}, industry={industry_slug}, max={max_companies}")
        self.db_manager.log_message('INFO', f"Started enhanced collection: location={location_slug}, industry={industry_slug}")
        
        try:
            # Giai đoạn 1: Thu thập từ API chính
            companies = await self._collect_from_api(
                location_slug=location_slug,
                industry_slug=industry_slug,
                max_companies=max_companies,
                page_size=page_size
            )
            
            if not companies:
                self.logger.warning("No companies found from API")
                return self.stats
            
            # Giai đoạn 2: Tích hợp với HSCTVN (nếu được kích hoạt)
            if enable_hsctvn:
                await self._integrate_hsctvn_data(companies, hsctvn_delay)
            
            # Giai đoạn 3: Lưu vào database
            await self._save_enhanced_companies(companies)
            
            # Finalize stats
            self.stats['end_time'] = datetime.now()
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            self.stats['duration_seconds'] = duration
            
            self.logger.info(f"Enhanced collection completed: {self.stats}")
            self.db_manager.log_message('INFO', f"Enhanced collection completed: {len(companies)} companies")
            
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Enhanced collection failed: {e}")
            self.db_manager.log_message('ERROR', f"Enhanced collection failed: {e}")
            raise
    
    async def _collect_from_api(
        self,
        location_slug: Optional[str],
        industry_slug: Optional[str],
        max_companies: Optional[int],
        page_size: int
    ) -> List[EnhancedCompany]:
        """
        Thu thập dữ liệu từ API chính
        """
        self.logger.info("Phase 1: Collecting data from main API...")
        
        companies = []
        page = 1
        
        while True:
            self._report_progress(
                f"Searching page {page} from API...", 
                len(companies), 
                max_companies or 1000
            )
            
            # Search companies
            search_result = self.api_client.search_companies(
                location_slug=location_slug,
                industry_slug=industry_slug,
                page=page,
                page_size=page_size
            )
            
            if not search_result.items:
                self.logger.info("No more companies found from API")
                break
            
            # Get details for each company
            for i, company_summary in enumerate(search_result.items):
                current_count = len(companies) + 1
                
                # Check limits
                if max_companies and current_count > max_companies:
                    break
                
                self._report_progress(
                    f"Getting details: {company_summary.ma_so_thue}",
                    current_count,
                    max_companies or search_result.total_count
                )
                
                try:
                    # Get company detail from API
                    company_detail = self.api_client.get_company_detail(company_summary.ma_so_thue)
                    
                    if company_detail:
                        # Convert to EnhancedCompany
                        enhanced_company = EnhancedCompany.from_api_data(company_detail.to_dict())
                        companies.append(enhanced_company)
                        
                        self.stats['api_success'] += 1
                        self.logger.debug(f"API data collected: {company_summary.ma_so_thue}")
                    else:
                        self.logger.warning(f"No details found for {company_summary.ma_so_thue}")
                        self.stats['errors'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Error getting details for {company_summary.ma_so_thue}: {e}")
                    self.stats['errors'] += 1
                
                # Rate limiting
                time.sleep(0.5)
            
            # Check stopping conditions
            if max_companies and len(companies) >= max_companies:
                break
                
            if not search_result.has_next:
                break
            
            page += 1
        
        self.stats['total_processed'] = len(companies)
        self.logger.info(f"Phase 1 completed: {len(companies)} companies from API")
        return companies
    
    async def _integrate_hsctvn_data(self, companies: List[EnhancedCompany], delay: float):
        """
        Tích hợp dữ liệu từ HSCTVN
        """
        self.logger.info(f"Phase 2: Integrating HSCTVN data for {len(companies)} companies...")
        
        for i, company in enumerate(companies, 1):
            self._report_progress(
                f"HSCTVN integration: {company.ma_so_thue}",
                i,
                len(companies)
            )
            
            try:
                # Get data from HSCTVN
                hsctvn_data = await self.hsctvn_client.search_company(company.ma_so_thue)
                
                # Chỉ count success nếu có dữ liệu thực sự hữu ích
                if hsctvn_data and self.hsctvn_client.has_meaningful_data(hsctvn_data):
                    company.integrate_hsctvn_data(hsctvn_data)
                    self.stats['hsctvn_success'] += 1
                    
                    # Count as dual source if both sources have data
                    if company.data_source == "dual":
                        self.stats['dual_source_success'] += 1
                    
                    self.logger.debug(f"HSCTVN data integrated: {company.ma_so_thue}")
                    self.logger.info(f"HSCTVN data validated successfully for {company.ma_so_thue}")
                else:
                    self.logger.warning(f"HSCTVN data validation failed for {company.ma_so_thue}")
                    
            except Exception as e:
                self.logger.error(f"Error integrating HSCTVN data for {company.ma_so_thue}: {e}")
                self.stats['errors'] += 1
            
            # Rate limiting for HSCTVN
            await asyncio.sleep(delay)
        
        self.logger.info(f"Phase 2 completed: {self.stats['hsctvn_success']} successful HSCTVN integrations")
    
    async def _save_enhanced_companies(self, companies: List[EnhancedCompany]):
        """
        Lưu enhanced companies vào database
        """
        self.logger.info(f"Phase 3: Saving {len(companies)} enhanced companies to database...")
        
        for i, company in enumerate(companies, 1):
            self._report_progress(
                f"Saving: {company.ma_so_thue}",
                i,
                len(companies)
            )
            
            try:
                company_dict = company.to_dict()
                
                # Check if exists
                if self.db_manager.company_exists(company.ma_so_thue):
                    if self.db_manager.update_company(company.ma_so_thue, company_dict):
                        self.stats['updated_records'] += 1
                        self.logger.debug(f"Updated company: {company.ma_so_thue}")
                else:
                    if self.db_manager.insert_company(company_dict):
                        self.stats['new_records'] += 1
                        self.logger.debug(f"Inserted new company: {company.ma_so_thue}")
                        
            except Exception as e:
                self.logger.error(f"Error saving company {company.ma_so_thue}: {e}")
                self.stats['errors'] += 1
        
        self.logger.info(f"Phase 3 completed: {self.stats['new_records']} new, {self.stats['updated_records']} updated")
    
    def get_enhanced_companies_from_db(
        self,
        tinh_trang: Optional[str] = None,
        nganh_nghe: Optional[str] = None,
        tinh_thanh_pho: Optional[str] = None,
        data_source: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[EnhancedCompany]:
        """
        Lấy enhanced companies từ database với filters
        
        Args:
            tinh_trang: Tình trạng hoạt động
            nganh_nghe: Ngành nghề
            tinh_thanh_pho: Tỉnh/thành phố
            data_source: Nguồn dữ liệu (api, hsctvn, dual)
            limit: Giới hạn số kết quả
            
        Returns:
            List of EnhancedCompany objects
        """
        
        try:
            # Build query conditions
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
            
            if data_source:
                conditions.append('data_source = ?')
                params.append(data_source)
            
            # Get raw data
            raw_companies = self.db_manager.get_companies(
                tinh_trang=tinh_trang,
                nganh_nghe=nganh_nghe,
                tinh_thanh_pho=tinh_thanh_pho,
                limit=limit
            )
            
            # Convert to EnhancedCompany objects
            enhanced_companies = []
            for raw_data in raw_companies:
                try:
                    # Create EnhancedCompany from database data
                    company = EnhancedCompany(
                        ma_so_thue=raw_data.get('ma_so_thue', ''),
                        ten_cong_ty=raw_data.get('ten_cong_ty', ''),
                        ten_giao_dich=raw_data.get('ten_giao_dich', ''),
                        ten_tieng_anh=raw_data.get('ten_tieng_anh', ''),
                        nguoi_dai_dien=raw_data.get('nguoi_dai_dien', ''),
                        chuc_vu_dai_dien=raw_data.get('chuc_vu_dai_dien', ''),
                        dai_dien_phap_luat=raw_data.get('dai_dien_phap_luat', ''),
                        dien_thoai=raw_data.get('dien_thoai', ''),
                        dien_thoai_dai_dien=raw_data.get('dien_thoai_dai_dien', ''),
                        fax=raw_data.get('fax', ''),
                        email=raw_data.get('email', ''),
                        website=raw_data.get('website', ''),
                        dia_chi_dang_ky=raw_data.get('dia_chi_dang_ky', ''),
                        dia_chi_thue=raw_data.get('dia_chi_thue', ''),
                        tinh_thanh_pho=raw_data.get('tinh_thanh_pho', ''),
                        quan_huyen=raw_data.get('quan_huyen', ''),
                        phuong_xa=raw_data.get('phuong_xa', ''),
                        nganh_nghe_kinh_doanh_chinh=raw_data.get('nganh_nghe_kinh_doanh_chinh', ''),
                        # Parse nganh_nghe_khac from JSON string
                        nganh_nghe_khac=self._parse_json_field(raw_data.get('nganh_nghe_khac', '')),
                        loai_hinh_doanh_nghiep=raw_data.get('loai_hinh_doanh_nghiep', ''),
                        tinh_trang_hoat_dong=raw_data.get('tinh_trang_hoat_dong', ''),
                        so_giay_phep_kinh_doanh=raw_data.get('so_giay_phep_kinh_doanh', ''),
                        ngay_cap_giay_phep=raw_data.get('ngay_cap_giay_phep'),
                        ngay_hoat_dong=raw_data.get('ngay_hoat_dong'),
                        ngay_thay_doi_gan_nhat=raw_data.get('ngay_thay_doi_gan_nhat'),
                        co_quan_cap_phep=raw_data.get('co_quan_cap_phep', ''),
                        so_quyet_dinh=raw_data.get('so_quyet_dinh', ''),
                        von_dieu_le=raw_data.get('von_dieu_le', ''),
                        von_dang_ky=raw_data.get('von_dang_ky', ''),
                        cap_nhat_lan_cuoi=raw_data.get('cap_nhat_lan_cuoi', ''),
                        trang_thai_hsctvn=raw_data.get('trang_thai_hsctvn', ''),
                        data_source=raw_data.get('data_source', 'api'),
                        raw_json_api=raw_data.get('raw_json_api', ''),
                        raw_json_hsctvn=raw_data.get('raw_json_hsctvn', ''),
                        created_at=self._parse_datetime(raw_data.get('created_at')),
                        updated_at=self._parse_datetime(raw_data.get('updated_at'))
                    )
                    enhanced_companies.append(company)
                    
                except Exception as e:
                    self.logger.error(f"Error converting raw data to EnhancedCompany: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(enhanced_companies)} enhanced companies from database")
            return enhanced_companies
            
        except Exception as e:
            self.logger.error(f"Failed to get enhanced companies from database: {e}")
            return []

    def _parse_json_field(self, json_string: str) -> List[str]:
        """Parse JSON string to list, handling errors"""
        if not json_string:
            return []
        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            self.logger.warning(f"Invalid JSON string for nganh_nghe_khac: {json_string}")
            return []

    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """
        Parse datetime string to datetime object.
        Handles multiple formats and None values.
        """
        if not dt_string:
            return None
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M:%S.%f"]:
            try:
                return datetime.strptime(dt_string, fmt)
            except ValueError:
                continue
        self.logger.warning(f"Could not parse datetime string: {dt_string}")
        return None


