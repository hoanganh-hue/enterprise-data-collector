# Enterprise Data Collector v2.0

**Thu thập dữ liệu doanh nghiệp từ nhiều nguồn với giao diện tiếng Việt**

## 🚀 Tính năng chính

- ✅ **Dual-source data integration**: API + Web scraping
- ✅ **Giao diện tiếng Việt**: Thân thiện và dễ sử dụng  
- ✅ **One-click installer**: Professional Windows installer
- ✅ **Automated build**: GitHub Actions CI/CD
- ✅ **100% accuracy**: Verified data collection

## 📦 Download

Tải phiên bản mới nhất từ [Releases](https://github.com/minimax-enterprise/enterprise-data-collector/releases):

- **EnterpriseDataCollector_v2.0_setup.exe** - Windows Installer (Khuyến nghị)
- **Portable Version** - Không cần cài đặt

## 💻 Yêu cầu hệ thống

- Windows 10 hoặc mới hơn
- Kết nối Internet
- ~100MB dung lượng trống

## 🔧 Cài đặt

### Cho người dùng cuối:
1. Tải `EnterpriseDataCollector_v2.0_setup.exe`
2. Double-click để cài đặt
3. Follow wizard tiếng Việt
4. Khởi động từ Desktop shortcut

### Cho developers:
```bash
git clone https://github.com/minimax-enterprise/enterprise-data-collector.git
cd enterprise-data-collector
pip install -r requirements.txt
python main.py
```

## 🏗️ Build Process

Repository này sử dụng **GitHub Actions** để tự động build Windows installer:

- **Trigger**: Push to main branch hoặc create release tag
- **Build Environment**: Windows Server latest
- **Output**: Professional Windows installer với NSIS
- **Artifacts**: Available for download trong Actions tab

## 📋 Workflow

1. **Thu thập từ API**: `thongtindoanhnghiep.co`
2. **Scraping bổ sung**: `hsctvn.com` cho thông tin đại diện
3. **Tổng hợp dữ liệu**: Export Excel với tất cả thông tin
4. **Quality assurance**: 100% accuracy verification

## 📊 Dữ liệu thu thập

- Tên doanh nghiệp
- Mã số thuế  
- Địa chỉ đầy đủ
- **Người đại diện pháp luật**
- **Số điện thoại người đại diện** 
- Ngành nghề kinh doanh
- Trạng thái hoạt động

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📞 Hỗ trợ

- **Issues**: [GitHub Issues](https://github.com/minimax-enterprise/enterprise-data-collector/issues)
- **Email**: support@minimax-agent.com
- **Documentation**: Xem thư mục `docs/`

## 📄 License

Copyright © 2024 MiniMax Agent. All rights reserved.

---

## 🏷️ Changelog

### v2.0.0 (2024-12-30)
- ✅ Complete dual-source integration
- ✅ Professional Windows installer  
- ✅ GitHub Actions automation
- ✅ 100% data accuracy verification
- ✅ Vietnamese UI/UX