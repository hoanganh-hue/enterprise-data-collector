"""
Geographical models for Enterprise Data Collector
City, District, Ward data structures
Author: MiniMax Agent
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class City:
    """Tỉnh/Thành phố"""
    id: int
    name: str
    slug: str
    code: Optional[str] = None
    type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'code': self.code,
            'type': self.type
        }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


@dataclass
class District:
    """Quận/Huyện"""
    id: int
    name: str
    slug: str
    city_id: int
    code: Optional[str] = None
    type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'city_id': self.city_id,
            'code': self.code,
            'type': self.type
        }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


@dataclass
class Ward:
    """Phường/Xã"""
    id: int
    name: str
    slug: str
    district_id: int
    code: Optional[str] = None
    type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'district_id': self.district_id,
            'code': self.code,
            'type': self.type
        }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"