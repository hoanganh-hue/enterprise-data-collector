"""
Enhanced Company model for Enterprise Data Collector
31-field enhanced company model with dual data source integration
Author: MiniMax Agent
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


@dataclass
class EnhancedCompany:
    """Enhanced company model với 31 trường thông tin từ 2 nguồn dữ liệu"""
    
    # Core identification
    ma_so_thue: str = ""
    ten_cong_ty: str = ""
    ten_giao_dich: str = ""
    ten_tieng_anh: str = ""
    
    # Contact & representative info  
    nguoi_dai_dien: str = ""
    chuc_vu_dai_dien: str = ""
    dai_dien_phap_luat: str = ""  # From HSCTVN
    dien_thoai: str = ""
    dien_thoai_dai_dien: str = ""  # From HSCTVN
    fax: str = ""
    email: str = ""
    website: str = ""
    
    # Address information
    dia_chi_dang_ky: str = ""
    dia_chi_thue: str = ""  # From HSCTVN
    tinh_thanh_pho: str = ""
    quan_huyen: str = ""
    phuong_xa: str = ""
    
    # Business information
    nganh_nghe_kinh_doanh_chinh: str = ""
    nganh_nghe_khac: List[str] = field(default_factory=list)
    loai_hinh_doanh_nghiep: str = ""
    tinh_trang_hoat_dong: str = ""
    
    # Legal & financial info
    so_giay_phep_kinh_doanh: str = ""
    ngay_cap_giay_phep: Optional[str] = None
    ngay_hoat_dong: Optional[str] = None
    ngay_thay_doi_gan_nhat: Optional[str] = None
    co_quan_cap_phep: str = ""
    so_quyet_dinh: str = ""
    von_dieu_le: str = ""
    von_dang_ky: str = ""
    
    # Enhanced fields from HSCTVN
    cap_nhat_lan_cuoi: str = ""  # From HSCTVN
    trang_thai_hsctvn: str = ""  # From HSCTVN
    
    # Metadata
    data_source: str = "dual"  # "api", "hsctvn", "dual"
    raw_json_api: str = ""
    raw_json_hsctvn: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_api_data(cls, api_data: Dict[str, Any]) -> 'EnhancedCompany':
        """Tạo EnhancedCompany từ dữ liệu API chính"""
        
        # Parse ngành nghề khác
        nganh_nghe_khac = []
        if 'DSNganhNgheKinhDoanh' in api_data:
            if isinstance(api_data['DSNganhNgheKinhDoanh'], list):
                nganh_nghe_khac = api_data['DSNganhNgheKinhDoanh']
        
        return cls(
            ma_so_thue=api_data.get('ma_so_thue', api_data.get('MaSoThue', '')),
            ten_cong_ty=api_data.get('ten_cong_ty', api_data.get('Title', '')),
            ten_giao_dich=api_data.get('ten_giao_dich', api_data.get('Title', '')),
            ten_tieng_anh=api_data.get('ten_tieng_anh', api_data.get('TitleEn', '')),
            nguoi_dai_dien=api_data.get('nguoi_dai_dien', api_data.get('ChuSoHuu', '')),
            chuc_vu_dai_dien=api_data.get('chuc_vu_dai_dien', ''),
            dien_thoai=api_data.get('dien_thoai', ''),
            fax=api_data.get('fax', ''),
            email=api_data.get('email', ''),
            website=api_data.get('website', ''),
            dia_chi_dang_ky=api_data.get('dia_chi', api_data.get('DiaChiCongTy', '')),
            tinh_thanh_pho=api_data.get('tinh_thanh_pho', api_data.get('TinhThanhTitle', '')),
            quan_huyen=api_data.get('quan_huyen', api_data.get('QuanHuyenTitle', '')),
            phuong_xa=api_data.get('phuong_xa', api_data.get('PhuongXaTitle', '')),
            nganh_nghe_kinh_doanh_chinh=api_data.get('nganh_nghe_kinh_doanh_chinh', api_data.get('NganhNgheTitle', '')),
            nganh_nghe_khac=nganh_nghe_khac,
            loai_hinh_doanh_nghiep=api_data.get('loai_hinh_doanh_nghiep', api_data.get('LoaiHinhTitle', '')),
            tinh_trang_hoat_dong=api_data.get('tinh_trang_hoat_dong', 'Hoạt động' if not api_data.get('IsDelete', False) else 'Ngừng hoạt động'),
            so_giay_phep_kinh_doanh=api_data.get('so_giay_phep_kinh_doanh', api_data.get('GiayPhepKinhDoanh', '')),
            ngay_cap_giay_phep=api_data.get('ngay_cap_phep', api_data.get('NgayCap')),
            ngay_hoat_dong=api_data.get('ngay_hoat_dong', api_data.get('NgayBatDauHopDong')),
            ngay_thay_doi_gan_nhat=api_data.get('ngay_thay_doi_gan_nhat', api_data.get('Updated')),
            co_quan_cap_phep=api_data.get('co_quan_cap_phep', api_data.get('GiayPhepKinhDoanh_CoQuanCapTitle', '')),
            so_quyet_dinh=api_data.get('so_quyet_dinh', api_data.get('GiayPhepKinhDoanh', '')),
            von_dieu_le=api_data.get('von_dieu_le', api_data.get('VonDieuLe', '')),
            von_dang_ky=api_data.get('von_dang_ky', ''),
            data_source="api",
            raw_json_api=json.dumps(api_data, ensure_ascii=False),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def integrate_hsctvn_data(self, hsctvn_data: Dict[str, Any]):
        """Tích hợp dữ liệu từ HSCTVN vào company hiện tại"""
        
        # Ưu tiên dữ liệu từ HSCTVN cho một số trường
        if hsctvn_data.get('dai_dien_phap_luat'):
            self.dai_dien_phap_luat = hsctvn_data['dai_dien_phap_luat']
            # Nếu chưa có người đại diện từ API, dùng từ HSCTVN
            if not self.nguoi_dai_dien:
                self.nguoi_dai_dien = hsctvn_data['dai_dien_phap_luat']
        
        if hsctvn_data.get('dien_thoai'):
            self.dien_thoai_dai_dien = hsctvn_data['dien_thoai']
            # Nếu chưa có điện thoại từ API, dùng từ HSCTVN
            if not self.dien_thoai:
                self.dien_thoai = hsctvn_data['dien_thoai']
        
        if hsctvn_data.get('dia_chi_thue'):
            self.dia_chi_thue = hsctvn_data['dia_chi_thue']
            # Nếu chưa có địa chỉ từ API, dùng từ HSCTVN
            if not self.dia_chi_dang_ky:
                self.dia_chi_dang_ky = hsctvn_data['dia_chi_thue']
        
        # Các trường bổ sung khác
        if hsctvn_data.get('email') and not self.email:
            self.email = hsctvn_data['email']
        
        if hsctvn_data.get('ngay_cap') and not self.ngay_cap_giay_phep:
            self.ngay_cap_giay_phep = hsctvn_data['ngay_cap']
        
        if hsctvn_data.get('nganh_nghe_chinh') and not self.nganh_nghe_kinh_doanh_chinh:
            self.nganh_nghe_kinh_doanh_chinh = hsctvn_data['nganh_nghe_chinh']
        
        # Thông tin trạng thái từ HSCTVN
        self.trang_thai_hsctvn = hsctvn_data.get('trang_thai', '')
        self.cap_nhat_lan_cuoi = hsctvn_data.get('cap_nhat_lan_cuoi', '')
        
        # Cập nhật metadata
        self.data_source = "dual"
        self.raw_json_hsctvn = json.dumps(hsctvn_data, ensure_ascii=False)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database/export"""
        return {
            'ma_so_thue': self.ma_so_thue,
            'ten_cong_ty': self.ten_cong_ty,
            'ten_giao_dich': self.ten_giao_dich,
            'ten_tieng_anh': self.ten_tieng_anh,
            'nguoi_dai_dien': self.nguoi_dai_dien,
            'chuc_vu_dai_dien': self.chuc_vu_dai_dien,
            'dai_dien_phap_luat': self.dai_dien_phap_luat,
            'dien_thoai': self.dien_thoai,
            'dien_thoai_dai_dien': self.dien_thoai_dai_dien,
            'fax': self.fax,
            'email': self.email,
            'website': self.website,
            'dia_chi_dang_ky': self.dia_chi_dang_ky,
            'dia_chi_thue': self.dia_chi_thue,
            'tinh_thanh_pho': self.tinh_thanh_pho,
            'quan_huyen': self.quan_huyen,
            'phuong_xa': self.phuong_xa,
            'nganh_nghe_kinh_doanh_chinh': self.nganh_nghe_kinh_doanh_chinh,
            'nganh_nghe_khac': json.dumps(self.nganh_nghe_khac, ensure_ascii=False) if self.nganh_nghe_khac else '',
            'loai_hinh_doanh_nghiep': self.loai_hinh_doanh_nghiep,
            'tinh_trang_hoat_dong': self.tinh_trang_hoat_dong,
            'so_giay_phep_kinh_doanh': self.so_giay_phep_kinh_doanh,
            'ngay_cap_giay_phep': self.ngay_cap_giay_phep,
            'ngay_hoat_dong': self.ngay_hoat_dong,
            'ngay_thay_doi_gan_nhat': self.ngay_thay_doi_gan_nhat,
            'co_quan_cap_phep': self.co_quan_cap_phep,
            'so_quyet_dinh': self.so_quyet_dinh,
            'von_dieu_le': self.von_dieu_le,
            'von_dang_ky': self.von_dang_ky,
            'cap_nhat_lan_cuoi': self.cap_nhat_lan_cuoi,
            'trang_thai_hsctvn': self.trang_thai_hsctvn,
            'data_source': self.data_source,
            'raw_json_api': self.raw_json_api,
            'raw_json_hsctvn': self.raw_json_hsctvn,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_excel_row(self) -> List[Any]:
        """Convert to Excel row format (31 columns)"""
        return [
            self.ma_so_thue,
            self.ten_cong_ty,
            self.dia_chi_dang_ky or self.dia_chi_thue,
            self.nguoi_dai_dien or self.dai_dien_phap_luat,
            self.dien_thoai_dai_dien or self.dien_thoai,
            self.so_giay_phep_kinh_doanh,
            self.ngay_cap_giay_phep,
            self.tinh_thanh_pho,
            self.ten_giao_dich,
            self.ten_tieng_anh,
            self.chuc_vu_dai_dien,
            self.fax,
            self.email,
            self.website,
            self.quan_huyen,
            self.phuong_xa,
            self.nganh_nghe_kinh_doanh_chinh,
            ', '.join(self.nganh_nghe_khac) if self.nganh_nghe_khac else '',
            self.loai_hinh_doanh_nghiep,
            self.tinh_trang_hoat_dong,
            self.ngay_hoat_dong,
            self.ngay_thay_doi_gan_nhat,
            self.co_quan_cap_phep,
            self.so_quyet_dinh,
            self.von_dieu_le,
            self.von_dang_ky,
            self.dai_dien_phap_luat,
            self.dia_chi_thue,
            self.cap_nhat_lan_cuoi,
            self.trang_thai_hsctvn,
            self.data_source
        ]
    
    @staticmethod
    def get_excel_headers() -> List[str]:
        """Lấy headers cho Excel export (31 columns)"""
        return [
            'Mã số thuế',
            'Tên công ty',
            'Địa chỉ đăng ký',
            'Người đại diện',
            'Điện thoại đại diện',
            'Số giấy phép kinh doanh',
            'Ngày cấp giấy phép',
            'Tỉnh thành phố',
            'Tên giao dịch',
            'Tên tiếng Anh',
            'Chức vụ đại diện',
            'Fax',
            'Email',
            'Website',
            'Quận/Huyện',
            'Phường/Xã',
            'Ngành nghề kinh doanh chính',
            'Ngành nghề khác',
            'Loại hình doanh nghiệp',
            'Tình trạng hoạt động',
            'Ngày hoạt động',
            'Ngày thay đổi gần nhất',
            'Cơ quan cấp phép',
            'Số quyết định',
            'Vốn điều lệ',
            'Vốn đăng ký',
            'Đại diện pháp luật',
            'Địa chỉ thuế',
            'Cập nhật lần cuối',
            'Trạng thái HSCTVN',
            'Nguồn dữ liệu'
        ]
    
    def __str__(self) -> str:
        return f"EnhancedCompany({self.ma_so_thue}: {self.ten_cong_ty})"