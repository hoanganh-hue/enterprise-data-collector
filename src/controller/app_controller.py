"""
Enhanced App Controller for Enterprise Data Collector v2.0
Main application controller with dual data source integration
Author: MiniMax Agent
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from pathlib import Path

from ..services import (
    ThongTinDoanhNghiepAPIClient,
    APIHelper,
    EnhancedIntegratedDataService
)
from ..models import (
    DatabaseManager,
    EnhancedCompany,
    City,
    Industry
)
from ..exporter import EnhancedExcelExporter
from ..logger import setup_dual_logger


class EnhancedAppController:
    """
    Enhanced application controller cho Enterprise Data Collector v2.0
    
    Features:
    - Dual data source integration (API + HSCTVN)
    - Enhanced database management
    - Progress tracking
    - Excel export với 31 columns
    - Comprehensive logging
    """
    
    def __init__(
        self,
        db_path: str = "Database/enterprise_data.db",
        output_dir: str = "Outputs",
        log_dir: str = "Logs",
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ):
        # Initialize database manager
        self.db_manager = DatabaseManager(db_path)
        
        # Initialize logger
        self.logger = setup_dual_logger(
            name="EnhancedController",
            level="INFO",
            log_dir=log_dir,
            db_manager=self.db_manager
        )
        
        # Initialize API client
        self.api_client = ThongTinDoanhNghiepAPIClient(logger=self.logger)
        self.api_helper = APIHelper(self.api_client)
        
        # Initialize enhanced data service
        self.data_service = EnhancedIntegratedDataService(
            api_client=self.api_client,
            db_manager=self.db_manager,
            logger=self.logger,
            progress_callback=progress_callback
        )
        
        # Initialize excel exporter
        self.excel_exporter = EnhancedExcelExporter(output_dir)
        
        # Progress callback
        self.progress_callback = progress_callback
        
        # Cache cho reference data
        self._cities_cache = None
        self._industries_cache = None
        
        self.logger.info("EnhancedAppController initialized")
    
    def get_cities(self, use_cache: bool = True) -> List[City]:
        """
        Lấy danh sách tỉnh/thành phố
        
        Args:
            use_cache: Sử dụng cache
            
        Returns:
            List of City objects
        """
        try:
            if use_cache and self._cities_cache:
                return self._cities_cache
            
            cities = self.api_client.get_cities(use_cache=use_cache)
            
            if use_cache:
                self._cities_cache = cities
            
            self.logger.info(f"Retrieved {len(cities)} cities")
            return cities
            
        except Exception as e:
            self.logger.error(f"Failed to get cities: {e}")
            return []
    
    def get_industries(self, use_cache: bool = True) -> List[Industry]:
        """
        Lấy danh sách ngành nghề
        
        Args:
            use_cache: Sử dụng cache
            
        Returns:
            List of Industry objects
        """
        try:
            if use_cache and self._industries_cache:
                return self._industries_cache
            
            industries = self.api_client.get_industries(use_cache=use_cache)
            
            if use_cache:
                self._industries_cache = industries
            
            self.logger.info(f"Retrieved {len(industries)} industries")
            return industries
            
        except Exception as e:
            self.logger.error(f"Failed to get industries: {e}")
            return []
    
    def find_city_by_name(self, name: str) -> Optional[City]:
        """
        Tìm tỉnh/thành phố theo tên
        
        Args:
            name: Tên tỉnh/thành phố
            
        Returns:
            City object hoặc None
        """
        return self.api_helper.find_city_by_name(name)
    
    def find_industry_by_name(self, name: str) -> Optional[Industry]:
        """
        Tìm ngành nghề theo tên
        
        Args:
            name: Tên ngành nghề
            
        Returns:
            Industry object hoặc None
        """
        return self.api_helper.find_industry_by_name(name)
    
    async def collect_companies(
        self,
        location_name: Optional[str] = None,
        industry_name: Optional[str] = None,
        max_companies: int = 100,
        enable_hsctvn: bool = True,
        hsctvn_delay: float = 2.0
    ) -> Dict[str, Any]:
        """
        Thu thập dữ liệu công ty enhanced
        
        Args:
            location_name: Tên tỉnh/thành phố
            industry_name: Tên ngành nghề
            max_companies: Số công ty tối đa
            enable_hsctvn: Có kích hoạt HSCTVN integration
            hsctvn_delay: Delay giữa HSCTVN requests
            
        Returns:
            Thống kê kết quả
        """
        
        self.logger.info(f"Starting collection: location={location_name}, industry={industry_name}, max={max_companies}")
        
        try:
            # Validate and convert parameters
            location_slug = None
            industry_slug = None
            
            if location_name:
                city = self.find_city_by_name(location_name)
                if city:
                    location_slug = city.slug
                    self.logger.info(f"Found city: {city.name} -> {location_slug}")
                else:
                    raise ValueError(f"City not found: {location_name}")
            
            if industry_name:
                industry = self.find_industry_by_name(industry_name)
                if industry:
                    industry_slug = industry.slug
                    self.logger.info(f"Found industry: {industry.name} -> {industry_slug}")
                else:
                    raise ValueError(f"Industry not found: {industry_name}")
            
            # Start enhanced data collection
            stats = await self.data_service.collect_enhanced_data(
                location_slug=location_slug,
                industry_slug=industry_slug,
                max_companies=max_companies,
                enable_hsctvn=enable_hsctvn,
                hsctvn_delay=hsctvn_delay
            )
            
            self.logger.info(f"Collection completed successfully: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Collection failed: {e}")
            raise
    
    def get_collected_companies(
        self,
        tinh_trang: Optional[str] = None,
        nganh_nghe: Optional[str] = None,
        tinh_thanh_pho: Optional[str] = None,
        data_source: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[EnhancedCompany]:
        """
        Lấy danh sách công ty đã thu thập
        
        Args:
            tinh_trang: Tình trạng hoạt động
            nganh_nghe: Ngành nghề
            tinh_thanh_pho: Tỉnh/thành phố
            data_source: Nguồn dữ liệu
            limit: Giới hạn số kết quả
            
        Returns:
            List of EnhancedCompany
        """
        return self.data_service.get_enhanced_companies_from_db(
            tinh_trang=tinh_trang,
            nganh_nghe=nganh_nghe,
            tinh_thanh_pho=tinh_thanh_pho,
            data_source=data_source,
            limit=limit
        )
    
    def export_to_excel(
        self,
        companies: List[EnhancedCompany],
        filename: Optional[str] = None,
        include_charts: bool = True
    ) -> str:
        """
        Xuất dữ liệu ra Excel
        
        Args:
            companies: Danh sách công ty
            filename: Tên file
            include_charts: Có bao gồm biểu đồ
            
        Returns:
            Đường dẫn file đã tạo
        """
        try:
            if not companies:
                raise ValueError("No companies to export")
            
            # Auto-generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"enhanced_companies_{timestamp}.xlsx"
            
            # Export using enhanced exporter
            output_path = self.excel_exporter.export_enhanced_companies(
                companies=companies,
                filename=filename,
                include_charts=include_charts
            )
            
            self.logger.info(f"Excel export completed: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Excel export failed: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê database
        
        Returns:
            Dictionary chứa thống kê
        """
        return self.db_manager.get_stats()
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê collection hiện tại
        
        Returns:
            Dictionary chứa thống kê
        """
        return self.data_service.get_collection_stats()
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Dọn dẹp logs cũ
        
        Args:
            days: Số ngày giữ lại
            
        Returns:
            Số logs đã xóa
        """
        return self.db_manager.cleanup_old_logs(days)
    
    def validate_collection_params(
        self,
        location_name: Optional[str] = None,
        industry_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate collection parameters
        
        Args:
            location_name: Tên tỉnh/thành phố
            industry_name: Tên ngành nghề
            
        Returns:
            Validation result
        """
        result = {
            'valid': True,
            'errors': [],
            'location_info': None,
            'industry_info': None
        }
        
        try:
            if location_name:
                city = self.find_city_by_name(location_name)
                if city:
                    result['location_info'] = {
                        'name': city.name,
                        'slug': city.slug,
                        'id': city.id
                    }
                else:
                    result['valid'] = False
                    result['errors'].append(f"Không tìm thấy tỉnh/thành phố: {location_name}")
            
            if industry_name:
                industry = self.find_industry_by_name(industry_name)
                if industry:
                    result['industry_info'] = {
                        'name': industry.name,
                        'slug': industry.slug,
                        'id': industry.id
                    }
                else:
                    result['valid'] = False
                    result['errors'].append(f"Không tìm thấy ngành nghề: {industry_name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            result['valid'] = False
            result['errors'].append(f"Lỗi validation: {e}")
            return result
    
    def test_api_connection(self) -> Dict[str, Any]:
        """
        Test API connection
        
        Returns:
            Test result
        """
        try:
            # Test by getting cities
            cities = self.get_cities(use_cache=False)
            
            if cities:
                return {
                    'success': True,
                    'message': f"Kết nối API thành công. Tìm thấy {len(cities)} tỉnh/thành phố.",
                    'cities_count': len(cities)
                }
            else:
                return {
                    'success': False,
                    'message': "Kết nối API thất bại hoặc không có dữ liệu."
                }
                
        except Exception as e:
            self.logger.error(f"API connection test failed: {e}")
            return {
                'success': False,
                'message': f"Lỗi kết nối API: {e}"
            }
    
    def close(self):
        """
        Cleanup resources
        """
        try:
            if hasattr(self, 'data_service'):
                self.data_service.close()
            
            if hasattr(self, 'api_client'):
                self.api_client.close()
            
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
            
            self.logger.info("EnhancedAppController closed")
            
        except Exception as e:
            self.logger.error(f"Error closing controller: {e}")