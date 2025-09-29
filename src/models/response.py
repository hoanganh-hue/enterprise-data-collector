"""
API Response models for Enterprise Data Collector
Standardized response structures
Author: MiniMax Agent
"""

from dataclasses import dataclass
from typing import Generic, TypeVar, List, Optional, Dict, Any
import math

T = TypeVar('T')


@dataclass
class ApiResponse(Generic[T]):
    """Generic API response wrapper"""
    success: bool
    data: Optional[T] = None
    message: str = ""
    error_code: Optional[str] = None
    
    @classmethod
    def success_response(cls, data: T, message: str = "Success") -> 'ApiResponse[T]':
        """Tạo successful response"""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error_response(cls, message: str, error_code: Optional[str] = None) -> 'ApiResponse[None]':
        """Tạo error response"""
        return cls(success=False, message=message, error_code=error_code)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'message': self.message,
            'error_code': self.error_code
        }


@dataclass
class PaginatedResponse(Generic[T]):
    """Paginated response for list data"""
    items: List[T]
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def from_api_data(
        cls, 
        items: List[T], 
        page: int, 
        page_size: int, 
        total_count: int
    ) -> 'PaginatedResponse[T]':
        """Tạo PaginatedResponse từ dữ liệu API"""
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1
        
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'items': [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items],
            'page': self.page,
            'page_size': self.page_size,
            'total_count': self.total_count,
            'total_pages': self.total_pages,
            'has_next': self.has_next,
            'has_prev': self.has_prev
        }
    
    def get_page_info(self) -> str:
        """Lấy thông tin trang dạng text"""
        start = (self.page - 1) * self.page_size + 1
        end = min(self.page * self.page_size, self.total_count)
        return f"Showing {start}-{end} of {self.total_count} results (Page {self.page}/{self.total_pages})"
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __iter__(self):
        return iter(self.items)
    
    def __getitem__(self, index):
        return self.items[index]