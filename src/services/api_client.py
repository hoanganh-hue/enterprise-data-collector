"""
API Client for thongtindoanhnghiep.co
Enhanced client với support đầy đủ các endpoint và error handling
Author: MiniMax Agent
"""

import requests
import time
import logging
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urljoin, urlencode
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models import (
    City, District, Ward, Industry, CompanySearchResult, CompanyDetail,
    ApiResponse, PaginatedResponse
)


class ThongTinDoanhNghiepAPIClient:
    """
    Client API cho thongtindoanhnghiep.co
    
    Hỗ trợ:
    - Tất cả endpoints từ API documentation
    - Error handling và retry logic  
    - Rate limiting protection
    - Response caching
    - Logging integration
    """
    
    def __init__(
        self, 
        base_url: str = "https://thongtindoanhnghiep.co",
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        rate_limit_delay: float = 1.0,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize API client
        
        Args:
            base_url: Base URL của API
            timeout: Timeout cho requests (seconds)
            max_retries: Số lần retry khi request failed
            retry_backoff_factor: Delay factor cho retry
            rate_limit_delay: Delay giữa các requests (seconds)
            logger: Logger instance
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.logger = logger or logging.getLogger(__name__)
        
        # Setup session với retry strategy
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=retry_backoff_factor
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Default headers
        self.session.headers.update({
            'User-Agent': 'EnterpriseDataCollector/2.0 (thongtindoanhnghiep.co API Client)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # Cache cho dữ liệu ít thay đổi
        self._cache = {}
        self._last_request_time = 0
    
    def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = False,
        cache_ttl: int = 3600
    ) -> Dict[str, Any]:
        """
        Make HTTP request với error handling và rate limiting
        
        Args:
            endpoint: API endpoint (relative path)
            params: Query parameters
            use_cache: Có sử dụng cache không
            cache_ttl: Cache time-to-live (seconds)
            
        Returns:
            JSON response data
            
        Raises:
            requests.RequestException: Khi request failed
        """
        
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        # Build URL
        url = urljoin(self.base_url, endpoint)
        
        # Check cache
        cache_key = f"{url}_{urlencode(params or {})}"
        if use_cache and cache_key in self._cache:
            cached_data, cache_time = self._cache[cache_key]
            if current_time - cache_time < cache_ttl:
                self.logger.debug(f"Using cached data for {url}")
                return cached_data
        
        # Make request
        self.logger.debug(f"Making request to {url} with params: {params}")
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Update last request time
            self._last_request_time = time.time()
            
            # Parse JSON
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                raise requests.RequestException(f"Invalid JSON response: {e}")
            
            # Cache if requested
            if use_cache:
                self._cache[cache_key] = (data, current_time)
                self.logger.debug(f"Cached response for {url}")
            
            self.logger.info(f"Successfully requested {url}")
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise
    
    # =================== GEOGRAPHICAL ENDPOINTS ===================
    
    def get_cities(self, use_cache: bool = True) -> List[City]:
        """
        Lấy danh sách tất cả tỉnh/thành phố
        
        Args:
            use_cache: Sử dụng cache (default: True)
            
        Returns:
            List of City objects
        """
        try:
            data = self._make_request('/api/city', use_cache=use_cache, cache_ttl=86400)  # 24h cache
            
            cities = []
            # API returns {"LtsItem": [...], "TotalDoanhNghiep": ...}
            items = data.get('LtsItem', [])
            if isinstance(items, list):
                for item in items:
                    city = City(
                        id=item.get('ID', 0),
                        name=item.get('Title', ''),
                        slug=item.get('SolrID', '').lstrip('/'),  # Remove leading slash
                        code=item.get('code'),
                        type=item.get('Type')
                    )
                    cities.append(city)
            
            self.logger.info(f"Retrieved {len(cities)} cities")
            return cities
            
        except Exception as e:
            self.logger.error(f"Failed to get cities: {e}")
            return []
    
    def get_city_by_id(self, city_id: int, use_cache: bool = True) -> Optional[City]:
        """
        Lấy thông tin chi tiết tỉnh/thành phố theo ID
        
        Args:
            city_id: ID của tỉnh/thành phố
            use_cache: Sử dụng cache
            
        Returns:
            City object hoặc None nếu không tìm thấy
        """
        try:
            data = self._make_request(f'/api/city/{city_id}', use_cache=use_cache)
            
            return City(
                id=data.get('id', city_id),
                name=data.get('name', ''),
                slug=data.get('slug', ''),
                code=data.get('code'),
                type=data.get('type')
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get city {city_id}: {e}")
            return None
    
    def get_districts_by_city_id(self, city_id: int, use_cache: bool = True) -> List[District]:
        """
        Lấy danh sách quận/huyện theo ID tỉnh/thành phố
        
        Args:
            city_id: ID của tỉnh/thành phố
            use_cache: Sử dụng cache
            
        Returns:
            List of District objects
        """
        try:
            data = self._make_request(f'/api/city/{city_id}/district', use_cache=use_cache)
            
            districts = []
            if isinstance(data, list):
                for item in data:
                    district = District(
                        id=item.get('id', 0),
                        name=item.get('name', ''),
                        slug=item.get('slug', ''),
                        city_id=city_id,
                        code=item.get('code'),
                        type=item.get('type')
                    )
                    districts.append(district)
            
            self.logger.info(f"Retrieved {len(districts)} districts for city {city_id}")
            return districts
            
        except Exception as e:
            self.logger.error(f"Failed to get districts for city {city_id}: {e}")
            return []
    
    def get_district_by_id(self, district_id: int, use_cache: bool = True) -> Optional[District]:
        """
        Lấy thông tin chi tiết quận/huyện theo ID
        
        Args:
            district_id: ID của quận/huyện
            use_cache: Sử dụng cache
            
        Returns:
            District object hoặc None nếu không tìm thấy
        """
        try:
            data = self._make_request(f'/api/district/{district_id}', use_cache=use_cache)
            
            return District(
                id=data.get('id', district_id),
                name=data.get('name', ''),
                slug=data.get('slug', ''),
                city_id=data.get('city_id', 0),
                code=data.get('code'),
                type=data.get('type')
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get district {district_id}: {e}")
            return None
    
    def get_wards_by_district_id(self, district_id: int, use_cache: bool = True) -> List[Ward]:
        """
        Lấy danh sách phường/xã theo ID quận/huyện
        
        Args:
            district_id: ID của quận/huyện
            use_cache: Sử dụng cache
            
        Returns:
            List of Ward objects
        """
        try:
            data = self._make_request(f'/api/district/{district_id}/ward', use_cache=use_cache)
            
            wards = []
            if isinstance(data, list):
                for item in data:
                    ward = Ward(
                        id=item.get('id', 0),
                        name=item.get('name', ''),
                        slug=item.get('slug', ''),
                        district_id=district_id,
                        code=item.get('code'),
                        type=item.get('type')
                    )
                    wards.append(ward)
            
            self.logger.info(f"Retrieved {len(wards)} wards for district {district_id}")
            return wards
            
        except Exception as e:
            self.logger.error(f"Failed to get wards for district {district_id}: {e}")
            return []
    
    def get_ward_by_id(self, ward_id: int, use_cache: bool = True) -> Optional[Ward]:
        """
        Lấy thông tin chi tiết phường/xã theo ID
        
        Args:
            ward_id: ID của phường/xã
            use_cache: Sử dụng cache
            
        Returns:
            Ward object hoặc None nếu không tìm thấy
        """
        try:
            data = self._make_request(f'/api/ward/{ward_id}', use_cache=use_cache)
            
            return Ward(
                id=data.get('id', ward_id),
                name=data.get('name', ''),
                slug=data.get('slug', ''),
                district_id=data.get('district_id', 0),
                code=data.get('code'),
                type=data.get('type')
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get ward {ward_id}: {e}")
            return None
    
    # =================== INDUSTRY ENDPOINTS ===================
    
    def get_industries(self, use_cache: bool = True) -> List[Industry]:
        """
        Lấy danh sách tất cả ngành nghề kinh doanh
        
        Args:
            use_cache: Sử dụng cache (default: True)
            
        Returns:
            List of Industry objects
        """
        try:
            data = self._make_request('/api/industry', use_cache=use_cache, cache_ttl=86400)  # 24h cache
            
            industries = []
            # API returns {"LtsItem": [...], "TotalItem": ..., "TotalNganhNghe": ...}
            items = data.get('LtsItem', [])
            if isinstance(items, list):
                for item in items:
                    # Determine parent based on level structure
                    parent_id = None
                    level_codes = [item.get('Lv1'), item.get('Lv2'), item.get('Lv3'), item.get('Lv4'), item.get('Lv5')]
                    # Filter out empty levels
                    level_codes = [code for code in level_codes if code and code.strip()]
                    # If it's not a top-level industry (has more than just Lv1), it has a parent
                    if len(level_codes) > 1:
                        # This is a simplification - in a real app you'd build a proper hierarchy
                        parent_id = 1  # Placeholder
                    
                    industry = Industry(
                        id=item.get('ID', 0),
                        name=item.get('Title', ''),
                        slug=item.get('SolrID', '').lstrip('/'),  # Remove leading slash
                        code=level_codes[-1] if level_codes else None,  # Use the most specific level
                        parent_id=parent_id
                    )
                    industries.append(industry)
            
            self.logger.info(f"Retrieved {len(industries)} industries")
            return industries
            
        except Exception as e:
            self.logger.error(f"Failed to get industries: {e}")
            return []
    
    # =================== COMPANY ENDPOINTS ===================
    
    def search_companies(
        self,
        location_slug: Optional[str] = None,
        keyword: Optional[str] = None,
        industry_slug: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponse:
        """
        Tìm kiếm danh sách công ty với các filter
        
        Args:
            location_slug: Slug địa lý (vd: "ha-noi", "ha-noi/quan-hoan-kiem")
            keyword: Từ khóa tìm kiếm tên công ty
            industry_slug: Slug ngành nghề
            page: Số trang (từ 1)
            page_size: Số kết quả mỗi trang
            
        Returns:
            PaginatedResponse chứa danh sách CompanySearchResult
        """
        
        # Build parameters
        params = {
            'p': page,
            'r': page_size
        }
        
        if location_slug:
            params['l'] = location_slug
        if keyword:
            params['k'] = keyword
        if industry_slug:
            params['i'] = industry_slug
        
        try:
            data = self._make_request('/api/company', params=params)
            
            # Parse company list
            companies = []
            # API returns structure with LtsItems array (updated structure)
            company_list = data.get('LtsItems', data.get('LtsDoanhNghiep', []))
            if isinstance(company_list, list):
                for item in company_list:
                    company = CompanySearchResult(
                        ma_so_thue=item.get('MaSoThue', ''),
                        ten_cong_ty=item.get('Title', ''),
                        dia_chi=item.get('DiaChiCongTy', ''),
                        tinh_trang=item.get('TrangThaiHoatDong', ''),
                        slug=item.get('SolrID', ''),
                        ngay_cap=item.get('NgayCap'),
                        nganh_nghe=item.get('NganhNgheTitle')
                    )
                    companies.append(company)
            
            # Get pagination info from Option object
            option = data.get('Option', {})
            total_count = option.get('TotalRow', len(companies))
            current_page = option.get('CurrentPage', page)
            
            response = PaginatedResponse.from_api_data(
                items=companies,
                page=current_page,
                page_size=page_size,
                total_count=total_count
            )
            
            self.logger.info(f"Search found {total_count} companies, page {page}/{response.total_pages}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to search companies: {e}")
            return PaginatedResponse.from_api_data([], page, page_size, 0)
    
    def get_company_detail(self, tax_code: str) -> Optional[CompanyDetail]:
        """
        Lấy thông tin chi tiết công ty theo mã số thuế
        
        Args:
            tax_code: Mã số thuế của công ty
            
        Returns:
            CompanyDetail object hoặc None nếu không tìm thấy
        """
        try:
            data = self._make_request(f'/api/company/{tax_code}')
            
            company = CompanyDetail.from_api_response(data)
            self.logger.info(f"Retrieved company details for {tax_code}")
            return company
            
        except Exception as e:
            self.logger.error(f"Failed to get company details for {tax_code}: {e}")
            return None
    
    # =================== BATCH OPERATIONS ===================
    
    def get_companies_by_location_and_industry(
        self,
        location_slug: str,
        industry_slug: str,
        max_results: Optional[int] = None,
        page_size: int = 50
    ) -> List[CompanyDetail]:
        """
        Lấy tất cả công ty theo địa lý và ngành nghề (với batch processing)
        
        Args:
            location_slug: Slug địa lý
            industry_slug: Slug ngành nghề  
            max_results: Giới hạn số kết quả (None = không giới hạn)
            page_size: Số kết quả mỗi page
            
        Returns:
            List of CompanyDetail objects
        """
        companies = []
        page = 1
        
        self.logger.info(f"Starting batch collection for {location_slug} + {industry_slug}")
        
        while True:
            # Search companies
            search_result = self.search_companies(
                location_slug=location_slug,
                industry_slug=industry_slug,
                page=page,
                page_size=page_size
            )
            
            if not search_result.items:
                break
            
            # Get details for each company
            for company_summary in search_result.items:
                if max_results and len(companies) >= max_results:
                    break
                    
                detail = self.get_company_detail(company_summary.ma_so_thue)
                if detail:
                    companies.append(detail)
                    
                # Rate limiting
                time.sleep(self.rate_limit_delay)
            
            # Check if we should continue
            if max_results and len(companies) >= max_results:
                break
            
            if not search_result.has_next:
                break
                
            page += 1
            self.logger.info(f"Processed page {page-1}, collected {len(companies)} companies so far")
        
        self.logger.info(f"Batch collection completed: {len(companies)} companies")
        return companies
    
    # =================== UTILITY METHODS ===================
    
    def clear_cache(self):
        """Clear internal cache"""
        self._cache.clear()
        self.logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'cache_size': len(self._cache),
            'cache_keys': list(self._cache.keys())
        }
    
    def close(self):
        """Close session and cleanup"""
        self.session.close()
        self.logger.info("API client closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()