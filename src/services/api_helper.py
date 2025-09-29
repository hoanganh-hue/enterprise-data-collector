"""
API Helper Utilities
Các utility functions để dễ dàng sử dụng ThongTinDoanhNghiepAPIClient
Author: MiniMax Agent
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import json

from .api_client import ThongTinDoanhNghiepAPIClient
from .integrated_data_service import IntegratedDataService
from ..models import CompanyDetail, City, Industry


class APIHelper:
    """
    Helper class cung cấp các utility methods để làm việc với API
    """
    
    def __init__(self, api_client: ThongTinDoanhNghiepAPIClient):
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
    
    def find_city_by_name(self, name: str, use_cache: bool = True) -> Optional[City]:
        """
        Tìm tỉnh/thành phố theo tên (không phân biệt hoa thường)
        
        Args:
            name: Tên tỉnh/thành phố (vd: "Hà Nội", "TP.HCM")
            use_cache: Sử dụng cache
            
        Returns:
            City object hoặc None
        """
        cities = self.api_client.get_cities(use_cache=use_cache)
        
        # Normalize search name
        search_name = name.lower().strip()
        
        # Các biến thể tên thường gặp
        name_variants = {
            'hà nội': ['ha noi', 'hanoi', 'thủ đô hà nội'],
            'thành phố hồ chí minh': ['tp.hcm', 'hcm', 'ho chi minh', 'saigon', 'sài gòn'],
            'đà nẵng': ['da nang', 'danang'],
            'hải phòng': ['hai phong', 'haiphong'],
            'cần thơ': ['can tho', 'cantho']
        }
        
        for city in cities:
            city_name = city.name.lower()
            
            # Exact match
            if search_name == city_name:
                return city
            
            # Check variants
            for key, variants in name_variants.items():
                if search_name in variants and key in city_name:
                    return city
                if search_name == key:
                    return city
        
        # Partial match as fallback
        for city in cities:
            if search_name in city.name.lower():
                return city
        
        return None
    
    def find_industry_by_name(self, name: str, use_cache: bool = True) -> Optional[Industry]:
        """
        Tìm ngành nghề theo tên (hỗ trợ tìm kiếm không chính xác)
        
        Args:
            name: Tên ngành nghề
            use_cache: Sử dụng cache
            
        Returns:
            Industry object hoặc None
        """
        industries = self.api_client.get_industries(use_cache=use_cache)
        
        search_name = name.lower().strip()
        
        # Exact match first
        for industry in industries:
            if search_name == industry.name.lower():
                return industry
        
        # Partial match
        for industry in industries:
            if search_name in industry.name.lower():
                return industry
        
        # Keywords match
        search_keywords = search_name.split()
        best_match = None
        max_matches = 0
        
        for industry in industries:
            industry_name = industry.name.lower()
            matches = sum(1 for keyword in search_keywords if keyword in industry_name)
            if matches > max_matches:
                max_matches = matches
                best_match = industry
        
        return best_match if max_matches > 0 else None
    
    def get_location_hierarchy(self, city_name: str) -> Dict[str, Any]:
        """
        Lấy hierarchy đầy đủ của địa lý (city -> districts -> wards)
        
        Args:
            city_name: Tên tỉnh/thành phố
            
        Returns:
            Dict chứa thông tin hierarchy
        """
        city = self.find_city_by_name(city_name)
        if not city:
            return {'error': f'City not found: {city_name}'}
        
        # Get districts
        districts = self.api_client.get_districts_by_city_id(city.id)
        
        hierarchy = {
            'city': {
                'id': city.id,
                'name': city.name,
                'slug': city.slug,
                'type': city.type
            },
            'districts': []
        }
        
        for district in districts:
            # Get wards for this district
            wards = self.api_client.get_wards_by_district_id(district.id)
            
            district_info = {
                'id': district.id,
                'name': district.name,
                'slug': district.slug,
                'type': district.type,
                'wards': [
                    {
                        'id': ward.id,
                        'name': ward.name,
                        'slug': ward.slug,
                        'type': ward.type
                    } for ward in wards
                ]
            }
            
            hierarchy['districts'].append(district_info)
        
        return hierarchy
    
    def build_location_slug(
        self, 
        city_name: str, 
        district_name: Optional[str] = None,
        ward_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Xây dựng location slug từ tên địa lý
        
        Args:
            city_name: Tên tỉnh/thành phố
            district_name: Tên quận/huyện (optional)
            ward_name: Tên phường/xã (optional)
            
        Returns:
            Location slug hoặc None nếu không tìm thấy
        """
        city = self.find_city_by_name(city_name)
        if not city:
            return None
        
        slug_parts = [city.slug]
        
        if district_name:
            districts = self.api_client.get_districts_by_city_id(city.id)
            district = None
            
            for d in districts:
                if district_name.lower() in d.name.lower():
                    district = d
                    break
            
            if not district:
                return city.slug  # Return city slug if district not found
            
            slug_parts.append(district.slug)
            
            if ward_name:
                wards = self.api_client.get_wards_by_district_id(district.id)
                ward = None
                
                for w in wards:
                    if ward_name.lower() in w.name.lower():
                        ward = w
                        break
                
                if ward:
                    slug_parts.append(ward.slug)
        
        return '/'.join(slug_parts)
    
    def validate_search_params(
        self,
        location: Optional[str] = None,
        industry: Optional[str] = None
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Validate và convert search parameters
        
        Args:
            location: Tên địa lý hoặc slug
            industry: Tên ngành nghề hoặc slug
            
        Returns:
            Tuple of (is_valid, validated_params)
        """
        validated = {}
        errors = []
        
        if location:
            # Try as slug first
            if '/' in location or location.count('-') > 0:
                validated['location_slug'] = location
            else:
                # Try to find city and build slug
                location_slug = self.build_location_slug(location)
                if location_slug:
                    validated['location_slug'] = location_slug
                else:
                    errors.append(f"Location not found: {location}")
        
        if industry:
            # Try as slug first (contains dashes)
            if '-' in industry and not ' ' in industry:
                validated['industry_slug'] = industry
            else:
                # Try to find industry
                industry_obj = self.find_industry_by_name(industry)
                if industry_obj:
                    validated['industry_slug'] = industry_obj.slug
                else:
                    errors.append(f"Industry not found: {industry}")
        
        is_valid = len(errors) == 0
        if not is_valid:
            validated['errors'] = errors
        
        return is_valid, validated
    
    def export_data_to_json(
        self,
        companies: List[CompanyDetail],
        output_file: str,
        include_raw: bool = False
    ) -> bool:
        """
        Export danh sách công ty ra file JSON
        
        Args:
            companies: List of CompanyDetail
            output_file: Đường dẫn file output
            include_raw: Có include raw API response không
            
        Returns:
            True nếu thành công
        """
        try:
            output_data = []
            
            for company in companies:
                company_data = company.to_dict()
                
                if not include_raw:
                    company_data.pop('raw_json', None)
                
                output_data.append(company_data)
            
            # Ensure output directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Exported {len(companies)} companies to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            return False
    
    def get_sample_data(self, max_companies: int = 5) -> List[CompanyDetail]:
        """
        Lấy dữ liệu mẫu cho testing
        
        Args:
            max_companies: Số lượng công ty mẫu
            
        Returns:
            List of CompanyDetail
        """
        # Get some cities and industries
        cities = self.api_client.get_cities()
        industries = self.api_client.get_industries()
        
        if not cities or not industries:
            return []
        
        # Use first city and industry
        city = cities[0]
        industry = industries[0]
        
        # Search companies
        search_result = self.api_client.search_companies(
            location_slug=city.slug,
            industry_slug=industry.slug,
            page_size=max_companies
        )
        
        # Get details for each company
        companies = []
        for company_summary in search_result.items[:max_companies]:
            detail = self.api_client.get_company_detail(company_summary.ma_so_thue)
            if detail:
                companies.append(detail)
        
        return companies


def create_api_client_with_logging(
    base_url: str = "https://thongtindoanhnghiep.co",
    log_level: str = "INFO",
    log_file: Optional[str] = None
) -> ThongTinDoanhNghiepAPIClient:
    """
    Tạo API client với logging được cấu hình sẵn
    
    Args:
        base_url: Base URL của API
        log_level: Level của logging
        log_file: File để ghi log (None = console only)
        
    Returns:
        ThongTinDoanhNghiepAPIClient instance
    """
    # Setup logging
    logger = logging.getLogger('ThongTinDoanhNghiepAPI')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)
    
    # Create API client
    return ThongTinDoanhNghiepAPIClient(
        base_url=base_url,
        logger=logger
    )


def quick_search(
    location: str,
    industry: str,
    max_results: int = 10,
    output_file: Optional[str] = None
) -> List[CompanyDetail]:
    """
    Quick search function để tìm kiếm nhanh công ty
    
    Args:
        location: Tên tỉnh/thành phố  
        industry: Tên ngành nghề
        max_results: Số lượng kết quả tối đa
        output_file: File để lưu kết quả (optional)
        
    Returns:
        List of CompanyDetail
    """
    
    # Create API client
    client = create_api_client_with_logging()
    helper = APIHelper(client)
    
    try:
        # Validate parameters
        is_valid, params = helper.validate_search_params(location, industry)
        
        if not is_valid:
            print(f"Validation errors: {params.get('errors', [])}")
            return []
        
        # Search companies
        search_result = client.search_companies(
            location_slug=params.get('location_slug'),
            industry_slug=params.get('industry_slug'),
            page_size=min(max_results, 50)
        )
        
        print(f"Found {search_result.total_count} companies, getting details for first {max_results}...")
        
        # Get details
        companies = []
        for company_summary in search_result.items[:max_results]:
            detail = client.get_company_detail(company_summary.ma_so_thue)
            if detail:
                companies.append(detail)
                print(f"✓ {detail.ma_so_thue}: {detail.ten_cong_ty}")
        
        # Export if requested
        if output_file and companies:
            helper.export_data_to_json(companies, output_file)
            print(f"Results exported to {output_file}")
        
        return companies
        
    except Exception as e:
        print(f"Search failed: {e}")
        return []
    
    finally:
        client.close()