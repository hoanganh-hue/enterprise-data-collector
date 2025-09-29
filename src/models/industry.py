"""
Industry models for Enterprise Data Collector
Industry data structures
Author: MiniMax Agent
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Industry:
    """Ngành nghề kinh doanh"""
    id: int
    name: str
    slug: str
    code: Optional[str] = None
    parent_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'code': self.code,
            'parent_id': self.parent_id
        }
    
    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"
    
    @property
    def is_parent(self) -> bool:
        """Kiểm tra xem có phải ngành nghề cha không"""
        return self.parent_id is None
    
    def get_display_name(self) -> str:
        """Lấy tên hiển thị với code nếu có"""
        if self.code:
            return f"{self.code} - {self.name}"
        return self.name