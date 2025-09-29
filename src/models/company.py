"""
Company models for Enterprise Data Collector
Basic company data structures
Author: MiniMax Agent
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


@dataclass
class CompanySearchResult:
    """Company summary từ search results"""
    ma_so_thue: str
    ten_cong_ty: str
    dia_chi: str = ""
    tinh_trang: str = ""
    slug: str = ""
    ngay_cap: Optional[str] = None
    nganh_nghe: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'ma_so_thue': self.ma_so_thue,
            'ten_cong_ty': self.ten_cong_ty,
            'dia_chi': self.dia_chi,
            'tinh_trang': self.tinh_trang,
            'slug': self.slug,
            'ngay_cap': self.ngay_cap,
            'nganh_nghe': self.nganh_nghe
        }


@dataclass
class CompanyDetail:
    """Thông tin chi tiết công ty từ API"""
    ma_so_thue: str
    ten_cong_ty: str
    ten_giao_dich: str = ""
    ten_tieng_anh: str = ""
    nguoi_dai_dien: str = ""
    chuc_vu_dai_dien: str = ""
    dia_chi: str = ""
    dien_thoai: str = ""
    fax: str = ""
    email: str = ""
    website: str = ""
    tinh_trang_hoat_dong: str = ""
    ngay_cap_phep: Optional[str] = None
    ngay_hoat_dong: Optional[str] = None
    ngay_thay_doi_gan_nhat: Optional[str] = None
    nganh_nghe_kinh_doanh_chinh: str = ""
    nganh_nghe_khac: List[str] = field(default_factory=list)
    loai_hinh_doanh_nghiep: str = ""
    von_dieu_le: str = ""
    von_dang_ky: str = ""
    tinh_thanh_pho: str = ""
    quan_huyen: str = ""
    phuong_xa: str = ""
    co_quan_cap_phep: str = ""
    so_quyet_dinh: str = ""
    raw_json: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'CompanyDetail':
        """Tạo CompanyDetail từ API response"""
        
        # Parse danh sách ngành nghề khác nếu có
        nganh_nghe_khac = []
        if 'DSNganhNgheKinhDoanh' in data:
            if isinstance(data['DSNganhNgheKinhDoanh'], list):
                nganh_nghe_khac = data['DSNganhNgheKinhDoanh']
        
        return cls(
            ma_so_thue=data.get('MaSoThue', ''),
            ten_cong_ty=data.get('Title', ''),
            ten_giao_dich=data.get('Title', ''),  # Same as title in this API
            ten_tieng_anh=data.get('TitleEn', ''),
            nguoi_dai_dien=data.get('ChuSoHuu', ''),  # Owner/representative
            chuc_vu_dai_dien='',  # Not provided in API
            dia_chi=data.get('DiaChiCongTy', ''),
            dien_thoai='',  # Not provided in basic API response
            fax='',
            email='',
            website='',
            tinh_trang_hoat_dong='Hoạt động' if not data.get('IsDelete', False) else 'Ngừng hoạt động',
            ngay_cap_phep=data.get('NgayCap'),
            ngay_hoat_dong=data.get('NgayBatDauHopDong'),
            ngay_thay_doi_gan_nhat=data.get('Updated'),
            nganh_nghe_kinh_doanh_chinh=data.get('NganhNgheTitle', ''),
            nganh_nghe_khac=nganh_nghe_khac,
            loai_hinh_doanh_nghiep=data.get('LoaiHinhTitle', ''),
            von_dieu_le=data.get('VonDieuLe', ''),
            von_dang_ky='',
            tinh_thanh_pho=data.get('TinhThanhTitle', ''),
            quan_huyen=data.get('QuanHuyenTitle', ''),
            phuong_xa=data.get('PhuongXaTitle', ''),
            co_quan_cap_phep=data.get('GiayPhepKinhDoanh_CoQuanCapTitle', ''),
            so_quyet_dinh=data.get('GiayPhepKinhDoanh', ''),
            raw_json=json.dumps(data, ensure_ascii=False),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ma_so_thue': self.ma_so_thue,
            'ten_cong_ty': self.ten_cong_ty,
            'ten_giao_dich': self.ten_giao_dich,
            'ten_tieng_anh': self.ten_tieng_anh,
            'nguoi_dai_dien': self.nguoi_dai_dien,
            'chuc_vu_dai_dien': self.chuc_vu_dai_dien,
            'dia_chi': self.dia_chi,
            'dien_thoai': self.dien_thoai,
            'fax': self.fax,
            'email': self.email,
            'website': self.website,
            'tinh_trang_hoat_dong': self.tinh_trang_hoat_dong,
            'ngay_cap_phep': self.ngay_cap_phep,
            'ngay_hoat_dong': self.ngay_hoat_dong,
            'ngay_thay_doi_gan_nhat': self.ngay_thay_doi_gan_nhat,
            'nganh_nghe_kinh_doanh_chinh': self.nganh_nghe_kinh_doanh_chinh,
            'nganh_nghe_khac': json.dumps(self.nganh_nghe_khac, ensure_ascii=False) if self.nganh_nghe_khac else '',
            'loai_hinh_doanh_nghiep': self.loai_hinh_doanh_nghiep,
            'von_dieu_le': self.von_dieu_le,
            'von_dang_ky': self.von_dang_ky,
            'tinh_thanh_pho': self.tinh_thanh_pho,
            'quan_huyen': self.quan_huyen,
            'phuong_xa': self.phuong_xa,
            'co_quan_cap_phep': self.co_quan_cap_phep,
            'so_quyet_dinh': self.so_quyet_dinh,
            'raw_json': self.raw_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __str__(self) -> str:
        return f"CompanyDetail({self.ma_so_thue}: {self.ten_cong_ty})"