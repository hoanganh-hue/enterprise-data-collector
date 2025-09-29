"""
HSCTVN Client Enhanced - Phiên bản nâng cấp hoàn chỉnh
Trích xuất đầy đủ thông tin doanh nghiệp từ hsctvn.com bao gồm địa chỉ
"""
import asyncio
import re
import json
from typing import Dict, Optional, Any
from playwright.async_api import async_playwright

class HSCTVNEnhanced:
    """Client nâng cấp để trích xuất đầy đủ thông tin doanh nghiệp"""
    
    def __init__(self):
        self.base_url = "https://hsctvn.com"
        
    async def search_company(self, tax_code: str) -> Optional[Dict[str, Any]]:
        """Tìm kiếm thông tin công ty theo mã số thuế"""
        print(f"🔍 Tìm kiếm MST: {tax_code}")
        
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # 1. Truy cập trang chủ
                print("   🌐 Truy cập hsctvn.com...")
                await page.goto(self.base_url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(2000)
                
                # 2. Tìm kiếm
                print(f"   🔍 Tìm kiếm MST {tax_code}...")
                search_input = await page.query_selector("input[name='key']")
                if not search_input:
                    print("   ❌ Không tìm thấy ô tìm kiếm")
                    return None
                
                await search_input.fill(tax_code)
                await page.wait_for_timeout(1000)
                
                # Submit form
                submit_btn = await page.query_selector("input[type='submit']")
                if submit_btn:
                    await submit_btn.click()
                else:
                    await search_input.press("Enter")
                
                # 3. Chờ kết quả
                print("   ⏳ Chờ kết quả...")
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(3000)
                
                # 4. Tìm link kết quả chính xác với MST
                result_link = await self._find_exact_result_link(page, tax_code)
                
                if result_link:
                    href = await result_link.get_attribute("href")
                    full_url = self._normalize_url(href)
                    
                    print(f"   🔗 Truy cập chi tiết: {full_url}")
                    await page.goto(full_url, timeout=30000)
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(3000)
                else:
                    print("   ⚠️ Không tìm thấy link chính xác, thử trích xuất từ trang hiện tại")
                
                # 5. Trích xuất thông tin với phương pháp cải tiến
                print("   📊 Trích xuất thông tin nâng cấp...")
                company_info = await self._extract_enhanced_info(page, tax_code)
                
                # Screenshot để debug
                await page.screenshot(path=f"enhanced_result_{tax_code}.png")
                print(f"   📸 Screenshot: enhanced_result_{tax_code}.png")
                
                return company_info
                
            except Exception as e:
                print(f"   ❌ Lỗi: {e}")
                await page.screenshot(path=f"enhanced_error_{tax_code}.png")
                return None
            finally:
                await browser.close()
    
    async def _find_exact_result_link(self, page, tax_code: str):
        """Tìm link kết quả chính xác cho MST"""
        try:
            # Tìm tất cả links trong bảng kết quả
            links = await page.query_selector_all("table a, .search-result a, a[href*='cong-ty']")
            
            for link in links:
                try:
                    href = await link.get_attribute("href")
                    text = await link.inner_text()
                    
                    # Tìm link có chứa MST trong href hoặc text
                    if href and (tax_code in href or tax_code in text):
                        if "cong-ty" in href and "danh-sach" not in href:
                            print(f"   ✅ Tìm thấy link chính xác: {href}")
                            return link
                    
                    # Hoặc tìm link trong cùng row với MST
                    parent_row = await link.evaluate_handle("""
                        element => element.closest('tr')
                    """)
                    
                    if parent_row:
                        row_text = await parent_row.inner_text()
                        if tax_code in row_text:
                            if "cong-ty" in href and "danh-sach" not in href:
                                print(f"   ✅ Tìm thấy link trong row chứa MST: {href}")
                                return link
                    
                except:
                    continue
            
            # Fallback: lấy link đầu tiên nếu có
            first_company_link = await page.query_selector("a[href*='cong-ty']:not([href*='danh-sach'])")
            if first_company_link:
                href = await first_company_link.get_attribute("href")
                print(f"   ⚠️ Sử dụng link đầu tiên: {href}")
                return first_company_link
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Lỗi tìm link: {e}")
            return None
    
    def _normalize_url(self, href: str) -> str:
        """Chuẩn hóa URL"""
        if href.startswith("/"):
            return f"{self.base_url}{href}"
        elif href.startswith("http"):
            return href
        else:
            return f"{self.base_url}/{href}"
    
    async def _extract_enhanced_info(self, page, tax_code: str) -> Dict[str, Any]:
        """Trích xuất thông tin với phương pháp nâng cấp"""
        company_info = {
            'ma_so_thue': tax_code,
            'ten_cong_ty': '',
            'dia_chi_thue': '',
            'dai_dien_phap_luat': '',
            'dien_thoai': '',
            'email': '',
            'ngay_cap': '',
            'nganh_nghe_chinh': '',
            'trang_thai': '',
            'cap_nhat_lan_cuoi': '',
            'nganh_nghe_kinh_doanh_chi_tiet': []
        }
        
        try:
            # Lấy toàn bộ text của trang để phân tích
            full_text = await page.inner_text("body")
            
            # 1. Trích xuất tên công ty từ tiêu đề
            await self._extract_company_name(page, company_info)
            
            # 2. Trích xuất thông tin từ text pattern (phương pháp mới)
            await self._extract_info_from_text_patterns(full_text, company_info)
            
            # 3. Trích xuất từ bảng (phương pháp cũ vẫn giữ để bổ sung)
            await self._extract_detailed_table_info(page, company_info)
            
            # 4. Trích xuất thông tin liên hệ
            await self._extract_contact_info(page, company_info)
            
            # 5. Trích xuất ngành nghề
            await self._extract_main_business_activity(page, company_info)
            
            # 6. Validate và làm sạch dữ liệu
            self._validate_and_clean_final(company_info, tax_code)
            
            return company_info
            
        except Exception as e:
            print(f"   ⚠️ Lỗi trích xuất: {e}")
            return company_info
    
    async def _extract_info_from_text_patterns(self, full_text: str, company_info: Dict[str, Any]):
        """Phương pháp mới: trích xuất thông tin từ text patterns"""
        try:
            lines = full_text.split('\n')
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                if not line_clean:
                    continue
                
                # Địa chỉ thuế - pattern mới
                if 'địa chỉ thuế:' in line_clean.lower():
                    address_match = re.search(r'địa chỉ thuế:\s*(.+)', line_clean, re.IGNORECASE)
                    if address_match:
                        address = address_match.group(1).strip()
                        if len(address) > 5:  # Điều kiện ít khắt khe hơn
                            company_info['dia_chi_thue'] = address
                            print(f"   ✅ Địa chỉ thuế: {address}")
                
                # Đại diện pháp luật
                elif 'đại diện pháp luật:' in line_clean.lower():
                    rep_match = re.search(r'đại diện pháp luật:\s*(.+)', line_clean, re.IGNORECASE)
                    if rep_match:
                        rep = rep_match.group(1).strip()
                        if len(rep) > 2 and not any(char.isdigit() for char in rep):
                            company_info['dai_dien_phap_luat'] = rep
                            print(f"   ✅ Đại diện pháp luật: {rep}")
                
                # Điện thoại
                elif 'điện thoại:' in line_clean.lower():
                    phone_match = re.search(r'điện thoại:\s*(.+)', line_clean, re.IGNORECASE)
                    if phone_match:
                        phone_text = phone_match.group(1).strip()
                        phone = self._extract_valid_phone(phone_text)
                        if phone and phone != company_info['ma_so_thue']:
                            company_info['dien_thoai'] = phone
                            print(f"   ✅ Điện thoại: {phone}")
                
                # Ngày cấp
                elif 'ngày cấp:' in line_clean.lower():
                    date_match = re.search(r'ngày cấp:\s*(.+)', line_clean, re.IGNORECASE)
                    if date_match:
                        date_text = date_match.group(1).strip()
                        if self._is_valid_date(date_text):
                            company_info['ngay_cap'] = date_text
                            print(f"   ✅ Ngày cấp: {date_text}")
                
                # Ngành nghề chính
                elif 'ngành nghề chính:' in line_clean.lower():
                    business_match = re.search(r'ngành nghề chính:\s*(.+)', line_clean, re.IGNORECASE)
                    if business_match:
                        business = business_match.group(1).strip()
                        if len(business) > 5:
                            company_info['nganh_nghe_chinh'] = business
                            print(f"   ✅ Ngành nghề chính: {business}")
                
                # Trạng thái  
                elif 'trạng thái:' in line_clean.lower():
                    status_match = re.search(r'trạng thái:\s*(.+)', line_clean, re.IGNORECASE)
                    if status_match:
                        status = status_match.group(1).strip()
                        company_info['trang_thai'] = status
                        print(f"   ✅ Trạng thái: {status}")
                
                # Tìm các pattern khác từ các dòng liền kề
                elif any(keyword in line_clean.lower() for keyword in ['số', 'lô', 'đường', 'phường', 'quận', 'thành phố', 'tỉnh']):
                    # Có thể là địa chỉ nếu chưa có
                    if not company_info['dia_chi_thue'] and len(line_clean) > 15:
                        # Kiểm tra xem có phải là địa chỉ không
                        if self._looks_like_address(line_clean):
                            company_info['dia_chi_thue'] = line_clean
                            print(f"   ✅ Địa chỉ (pattern): {line_clean}")
        
        except Exception as e:
            print(f"   ⚠️ Lỗi trích xuất từ text: {e}")
    
    def _looks_like_address(self, text: str) -> bool:
        """Kiểm tra xem text có giống địa chỉ không"""
        address_indicators = ['số', 'lô', 'đường', 'phường', 'quận', 'thành phố', 'tỉnh', 'xã', 'huyện']
        text_lower = text.lower()
        
        # Phải có ít nhất 2 indicator
        count = sum(1 for indicator in address_indicators if indicator in text_lower)
        
        # Không được chứa các từ không phải địa chỉ
        non_address = ['mã số thuế', 'điện thoại', 'email', 'ngày', 'năm', 'tháng']
        has_non_address = any(word in text_lower for word in non_address)
        
        return count >= 2 and not has_non_address and len(text) > 15
    
    async def _extract_company_name(self, page, company_info: Dict[str, Any]):
        """Trích xuất tên công ty từ các nguồn đáng tin cậy"""
        try:
            # Thứ tự ưu tiên: h1 -> title -> h2
            selectors = ['h1', 'title', 'h2', '.company-name', '.title']
            
            for selector in selectors:
                try:
                    if selector == 'title':
                        text = await page.title()
                    else:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.inner_text()
                        else:
                            continue
                    
                    if text and len(text.strip()) > 5:
                        # Làm sạch tên công ty
                        clean_name = self._clean_company_name(text.strip())
                        if clean_name:
                            company_info['ten_cong_ty'] = clean_name
                            print(f"   ✅ Tên công ty: {clean_name}")
                            return
                except:
                    continue
                    
        except Exception as e:
            print(f"   ⚠️ Lỗi trích xuất tên: {e}")
    
    def _clean_company_name(self, text: str) -> str:
        """Làm sạch tên công ty"""
        # Loại bỏ các tiền tố không cần thiết
        text = re.sub(r'^(Thông tin|Chi tiết|Detail|Info|Company)\s*[:]\s*', '', text, flags=re.IGNORECASE)
        
        # Loại bỏ thông tin website
        text = re.sub(r'\s*-[^-]*hsctvn[^-]*$', '', text, flags=re.IGNORECASE)
        
        # Loại bỏ thông tin số lượng hồ sơ
        text = re.sub(r'\s*\|\s*\d+[,.\s]*\d*\s*hồ sơ.*$', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    async def _extract_detailed_table_info(self, page, company_info: Dict[str, Any]):
        """Trích xuất thông tin chi tiết từ bảng (phương pháp cũ để bổ sung)"""
        try:
            main_tables = await page.query_selector_all("table")
            
            for table in main_tables:
                rows = await table.query_selector_all("tr")
                
                for row in rows:
                    cells = await row.query_selector_all("td, th")
                    if len(cells) >= 2:
                        try:
                            label_elem = cells[0]
                            value_elem = cells[1]
                            
                            label = await label_elem.inner_text()
                            value = await value_elem.inner_text()
                            
                            self._map_table_field(label.strip(), value.strip(), company_info)
                            
                        except:
                            continue
        
        except Exception as e:
            print(f"   ⚠️ Lỗi trích xuất bảng: {e}")
    
    def _map_table_field(self, label: str, value: str, company_info: Dict[str, Any]):
        """Map field từ bảng vào company_info với điều kiện ít khắt khe hơn"""
        if not label or not value or len(value) < 2:
            return
        
        label_lower = label.lower().strip()
        value_clean = value.strip()
        
        # Địa chỉ với điều kiện ít khắt khe hơn
        if any(kw in label_lower for kw in ['địa chỉ', 'address']) and len(value_clean) > 10:
            if not company_info['dia_chi_thue']:  # Chỉ set nếu chưa có
                company_info['dia_chi_thue'] = value_clean
                print(f"   ✅ Địa chỉ (bảng): {value_clean}")
        
        # Đại diện pháp luật
        elif any(kw in label_lower for kw in ['đại diện pháp luật', 'giám đốc', 'legal representative', 'director']):
            if len(value_clean) > 2 and not any(char.isdigit() for char in value_clean):
                if not company_info['dai_dien_phap_luat']:
                    company_info['dai_dien_phap_luat'] = value_clean
                    print(f"   ✅ Đại diện (bảng): {value_clean}")
        
        # Điện thoại
        elif any(kw in label_lower for kw in ['điện thoại', 'phone', 'tel', 'fax']):
            phone = self._extract_valid_phone(value_clean)
            if phone and not company_info['dien_thoai']:
                company_info['dien_thoai'] = phone
                print(f"   ✅ Điện thoại (bảng): {phone}")
    
    def _extract_valid_phone(self, text: str) -> str:
        """Trích xuất số điện thoại hợp lệ với logic chuẩn hóa"""
        if not text:
            return ""
        
        # Xóa spaces và ký tự đặc biệt
        text_clean = re.sub(r'[^\d+]', ' ', text)
        
        # Tìm pattern số điện thoại Việt Nam cụ thể
        phone_patterns = [
            # Số di động: 09x, 08x, 07x, 05x, 03x (10-11 số)
            r'(0[3579])[0-9]{8}',
            # Số cố định Hà Nội: 024 + 8 số
            r'(024)[0-9]{8}',
            # Số cố định TP.HCM: 028 + 8 số  
            r'(028)[0-9]{8}',
            # Số cố định khác: 02xx + 7-8 số
            r'(02[0-9])[0-9]{7,8}',
            # International format
            r'(\+84[3579])[0-9]{8}',
        ]
        
        found_phones = []
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text_clean)
            for match in matches:
                cleaned = re.sub(r'[^\d+]', '', match)
                
                # Kiểm tra không phải MST 
                if cleaned.startswith('010') or cleaned.startswith('011') or cleaned.startswith('012'):
                    continue
                    
                # Kiểm tra không phải năm
                if len(cleaned) == 4 and cleaned.startswith('20'):
                    continue
                
                # Kiểm tra độ dài hợp lệ
                if 9 <= len(cleaned) <= 12:
                    found_phones.append(cleaned)
        
        # Ưu tiên số di động (03, 05, 07, 08, 09)
        for phone in found_phones:
            if phone.startswith(('03', '05', '07', '08', '09')):
                return phone
        
        # Fallback: số cố định
        for phone in found_phones:
            if phone.startswith('02'):
                return phone
                
        return ""
    
    def _is_valid_date(self, text: str) -> bool:
        """Kiểm tra xem có phải ngày tháng hợp lệ không"""
        date_patterns = [
            r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}',
            r'\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    async def _extract_contact_info(self, page, company_info: Dict[str, Any]):
        """Trích xuất thông tin liên hệ từ toàn bộ trang"""
        try:
            full_text = await page.inner_text("body")
            
            # Tìm email
            if not company_info['email']:
                email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
                emails = re.findall(email_pattern, full_text)
                if emails:
                    # Lọc email hợp lệ (không phải placeholder)
                    for email in emails:
                        if not any(placeholder in email.lower() for placeholder in ['example', 'test', 'sample']):
                            company_info['email'] = email
                            print(f"   ✅ Email: {email}")
                            break
            
            # Tìm số điện thoại nếu chưa có
            if not company_info['dien_thoai']:
                phone = self._extract_valid_phone(full_text)
                if phone:
                    company_info['dien_thoai'] = phone
                    print(f"   ✅ Điện thoại từ text: {phone}")
        
        except Exception as e:
            print(f"   ⚠️ Lỗi trích xuất liên hệ: {e}")
    
    async def _extract_main_business_activity(self, page, company_info: Dict[str, Any]):
        """Trích xuất ngành nghề kinh doanh chính xác"""
        try:
            activities = []
            
            # Tìm section chứa ngành nghề của công ty hiện tại
            business_sections = await page.query_selector_all(
                "div:has-text('Ngành nghề'), section:has-text('Ngành nghề'), .business-activity"
            )
            
            for section in business_sections:
                try:
                    section_text = await section.inner_text()
                    
                    # Chỉ lấy ngành nghề liên quan đến công ty hiện tại
                    if company_info['ten_cong_ty'] and company_info['ten_cong_ty'] in section_text:
                        # Tìm các list items trong section này
                        list_items = await section.query_selector_all("li")
                        for item in list_items:
                            text = await item.inner_text()
                            if self._is_valid_business_activity(text):
                                activities.append(text.strip())
                except:
                    continue
            
            # Fallback: tìm từ tất cả li elements nhưng filter kỹ hơn
            if not activities:
                all_items = await page.query_selector_all("ul li, ol li")
                for item in all_items:
                    try:
                        text = await item.inner_text()
                        if self._is_valid_business_activity(text):
                            activities.append(text.strip())
                    except:
                        continue
            
            # Loại bỏ duplicate và giới hạn số lượng
            unique_activities = []
            for activity in activities:
                if activity not in unique_activities and len(unique_activities) < 10:
                    unique_activities.append(activity)
            
            company_info['nganh_nghe_kinh_doanh_chi_tiet'] = unique_activities
            
            if unique_activities:
                print(f"   ✅ Ngành nghề chi tiết: {len(unique_activities)} items")
        
        except Exception as e:
            print(f"   ⚠️ Lỗi trích xuất ngành nghề: {e}")
    
    def _is_valid_business_activity(self, text: str) -> bool:
        """Kiểm tra xem có phải ngành nghề kinh doanh hợp lệ không"""
        if not text or len(text.strip()) < 10 or len(text.strip()) > 300:
            return False
        
        text_lower = text.lower()
        
        # Phải chứa từ khóa kinh doanh
        business_keywords = [
            'sản xuất', 'kinh doanh', 'dịch vụ', 'bán', 'phân phối', 
            'xuất nhập khẩu', 'thương mại', 'chế tạo', 'gia công'
        ]
        
        has_business_keyword = any(keyword in text_lower for keyword in business_keywords)
        
        # Loại bỏ các dòng không phải ngành nghề
        invalid_indicators = [
            'mã số thuế', 'địa chỉ', 'điện thoại', 'email', 'website',
            'người đại diện', 'giám đốc', 'thành lập', 'vốn điều lệ'
        ]
        
        has_invalid = any(indicator in text_lower for indicator in invalid_indicators)
        
        return has_business_keyword and not has_invalid
    
    def _validate_and_clean_final(self, company_info: Dict[str, Any], original_tax_code: str):
        """Validate và làm sạch dữ liệu cuối cùng"""
        # Đảm bảo MST đúng
        if not company_info['ma_so_thue'] or company_info['ma_so_thue'] == original_tax_code:
            company_info['ma_so_thue'] = original_tax_code
        
        # Làm sạch số điện thoại (đảm bảo không phải MST)
        if company_info['dien_thoai'] == original_tax_code:
            company_info['dien_thoai'] = ""  # Reset nếu nhầm lẫn với MST
        
        # Làm sạch tên công ty
        if company_info['ten_cong_ty']:
            company_info['ten_cong_ty'] = self._clean_company_name(company_info['ten_cong_ty'])
        
        # Làm sạch địa chỉ
        if company_info['dia_chi_thue']:
            # Loại bỏ whitespace thừa
            company_info['dia_chi_thue'] = ' '.join(company_info['dia_chi_thue'].split())
    
    def save_to_file(self, tax_code: str, data: Dict[str, Any]):
        """Lưu kết quả ra file JSON"""
        filename = f"company_enhanced_{tax_code}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"   💾 Đã lưu: {filename}")
        except Exception as e:
            print(f"   ⚠️ Lỗi lưu file: {e}")

async def test_enhanced():
    """Test phiên bản nâng cấp hoàn chỉnh"""
    tax_code = "0107634707"
    client = HSCTVNEnhanced()
    
    print(f"🧪 TEST PHIÊN BẢN NÂNG CẤP HOÀN CHỈNH - MST: {tax_code}")
    print("=" * 70)
    
    result = await client.search_company(tax_code)
    
    if result:
        print("\n" + "=" * 70)
        print("📋 KẾT QUẢ TRÍCH XUẤT NÂNG CẤP:")
        print("=" * 70)
        
        for key, value in result.items():
            if value:
                if isinstance(value, list):
                    print(f"{key}: {len(value)} items")
                    for i, item in enumerate(value[:3], 1):
                        print(f"  {i}. {item}")
                    if len(value) > 3:
                        print(f"  ... và {len(value) - 3} items khác")
                else:
                    print(f"{key}: {value}")
        
        # Lưu kết quả
        client.save_to_file(tax_code, result)
        
        # Thống kê
        filled_fields = sum(1 for v in result.values() if v and str(v).strip())
        print(f"\n📊 Đã trích xuất {filled_fields}/{len(result)} trường")
        
        # Đánh giá chất lượng
        quality_score = filled_fields / len(result) * 100
        print(f"🎯 Độ đầy đủ thông tin: {quality_score:.1f}%")
        
        # Đánh giá cụ thể địa chỉ
        if result['dia_chi_thue']:
            print(f"✅ Đã trích xuất được địa chỉ: {result['dia_chi_thue']}")
        else:
            print("❌ Chưa trích xuất được địa chỉ")
            
    else:
        print("❌ Không trích xuất được thông tin")

if __name__ == "__main__":
    asyncio.run(test_enhanced())