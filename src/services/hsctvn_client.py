import asyncio
import re
import json
import logging
from typing import Dict, Optional, Any
from playwright.async_api import async_playwright

# Configure logging
logger = logging.getLogger(__name__)

class HSCTVNEnhanced:
    """Client nâng cấp để trích xuất đầy đủ thông tin doanh nghiệp"""
    
    def __init__(self):
        self.base_url = "https://hsctvn.com"
        
    async def search_company(self, tax_code: str) -> Optional[Dict[str, Any]]:
        """Tìm kiếm thông tin công ty theo mã số thuế"""
        logger.info(f"🔍 Tìm kiếm MST: {tax_code}")
        
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=\'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\'
            )
            page = await context.new_page()
            
            try:
                # 1. Truy cập trang chủ
                logger.info("   🌐 Truy cập hsctvn.com...")
                await page.goto(self.base_url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(2000)
                
                # 2. Tìm kiếm
                logger.info(f"   🔍 Tìm kiếm MST {tax_code}...")
                search_input = await page.query_selector("input[name=\'key\']")
                if not search_input:
                    logger.error("   ❌ Không tìm thấy ô tìm kiếm")
                    return None
                
                await search_input.fill(tax_code)
                await page.wait_for_timeout(1000)
                
                # Submit form
                submit_btn = await page.query_selector("input[type=\'submit\']")
                if submit_btn:
                    await submit_btn.click()
                else:
                    await search_input.press("Enter")
                
                # 3. Chờ kết quả
                logger.info("   ⏳ Chờ kết quả...")
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(3000)
                
                # 4. Tìm link kết quả chính xác với MST
                result_link = await self._find_exact_result_link(page, tax_code)
                
                if result_link:
                    href = await result_link.get_attribute("href")
                    full_url = self._normalize_url(href)
                    
                    logger.info(f"   🔗 Truy cập chi tiết: {full_url}")
                    await page.goto(full_url, timeout=30000)
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_timeout(3000)
                else:
                    logger.warning("   ⚠️ Không tìm thấy link chính xác, thử trích xuất từ trang hiện tại")
                
                # 5. Trích xuất thông tin với phương pháp cải tiến
                logger.info("   📊 Trích xuất thông tin nâng cấp...")
                company_info = await self._extract_enhanced_info(page, tax_code)
                
                # Debug information
                self._debug_extracted_info(company_info, tax_code)

                # Screenshot để debug
                screenshot_path = f"enhanced_result_{tax_code}.png"
                await page.screenshot(path=screenshot_path)
                logger.info(f"   📸 Screenshot: {screenshot_path}")
                
                return company_info
                
            except Exception as e:
                logger.error(f"   ❌ Lỗi: {e}")
                error_screenshot_path = f"enhanced_error_{tax_code}.png"
                await page.screenshot(path=error_screenshot_path)
                logger.error(f"   📸 Error Screenshot: {error_screenshot_path}")
                return None
            finally:
                await browser.close()
    
    async def _find_exact_result_link(self, page, tax_code: str):
        """Tìm link kết quả chính xác cho MST"""
        try:
            # Tìm tất cả links trong bảng kết quả
            links = await page.query_selector_all("table a, .search-result a, a[href*=\'cong-ty\']")
            
            for link in links:
                try:
                    href = await link.get_attribute("href")
                    text = await link.inner_text()
                    
                    # Tìm link có chứa MST trong href hoặc text
                    if href and (tax_code in href or tax_code in text):
                        if "cong-ty" in href and "danh-sach" not in href:
                            logger.info(f"   ✅ Tìm thấy link chính xác: {href}")
                            return link
                    
                    # Hoặc tìm link trong cùng row với MST
                    parent_row = await link.evaluate_handle("""
                        element => element.closest(\'tr\')
                    """)
                    
                    if parent_row:
                        row_text = await parent_row.inner_text()
                        if tax_code in row_text:
                            if "cong-ty" in href and "danh-sach" not in href:
                                logger.info(f"   ✅ Tìm thấy link trong row chứa MST: {href}")
                                return link
                    
                except:
                    continue
            
            # Fallback: lấy link đầu tiên nếu có
            first_company_link = await page.query_selector("a[href*=\'cong-ty\']:not([href*=\'danh-sach\'])")
            if first_company_link:
                href = await first_company_link.get_attribute("href")
                logger.warning(f"   ⚠️ Sử dụng link đầu tiên: {href}")
                return first_company_link
            
            return None
            
        except Exception as e:
            logger.warning(f"   ⚠️ Lỗi tìm link: {e}")
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
            \'ma_so_thue\': tax_code,
            \'ten_cong_ty\': \'\',
            \'dia_chi_thue\': \'\',
            \'dai_dien_phap_luat\': \'\',
            \'dien_thoai\': \'\',
            \'email\': \'\',
            \'ngay_cap\': \'\',
            \'nganh_nghe_chinh\': \'\',
            \'trang_thai\': \'\',
            \'cap_nhat_lan_cuoi\': \'\',
            \'nganh_nghe_kinh_doanh_chi_tiet\': []
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
            logger.warning(f"   ⚠️ Lỗi trích xuất: {e}")
            return company_info
    
    def has_meaningful_data(self, hsctvn_data: Dict[str, Any]) -> bool:
        """
        Kiểm tra dữ liệu HSCTVN có thực sự hữu ích hay không.
        Yêu cầu ít nhất 2 trường quan trọng: tên công ty và địa chỉ.
        """
        required_fields = ['ten_cong_ty', 'dia_chi_thue']
        meaningful_count = sum(1 for field in required_fields
                              if field in hsctvn_data and hsctvn_data[field])
        return meaningful_count >= 2

    def _calculate_quality_score(self, company_info: Dict[str, Any]) -> int:
        """
        Tính toán điểm chất lượng dữ liệu trích xuất.
        """
        score = 0
        if company_info.get('ten_cong_ty'):
            score += 30
        if company_info.get('dia_chi_thue'):
            score += 30
        if company_info.get('dai_dien_phap_luat'):
            score += 15
        if company_info.get('dien_thoai'):
            score += 10
        if company_info.get('email'):
            score += 5
        if company_info.get('ngay_cap'):
            score += 5
        if company_info.get('nganh_nghe_chinh'):
            score += 5
        return score

    def _debug_extracted_info(self, company_info: Dict[str, Any], tax_code: str):
        """
        In chi tiết thông tin đã extract được từ HSCTVN.
        Đánh giá chất lượng dữ liệu và ghi log chi tiết.
        """
        logger.info(f"=== DEBUG HSCTVN cho MST: {tax_code} ===")
        for key, value in company_info.items():
            logger.info(f"{key}: {value} ({'Có dữ liệu' if value else 'Trống'})")
        quality_score = self._calculate_quality_score(company_info)
        logger.info(f"Quality Score: {quality_score}/100")

    async def _extract_info_from_text_patterns(self, full_text: str, company_info: Dict[str, Any]):
        """Phương pháp mới: trích xuất thông tin từ text patterns"""
        try:
            lines = full_text.split('\n')
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                if not line_clean:
                    continue
                
                # Địa chỉ thuế - pattern mới
                if \'địa chỉ thuế:\' in line_clean.lower():
                    address_match = re.search(r\'địa chỉ thuế:\s*(.+)\\' , line_clean, re.IGNORECASE)
                    if address_match:
                        address = address_match.group(1).strip()
                        if len(address) > 5:  # Điều kiện ít khắt khe hơn
                            company_info[\'dia_chi_thue\'] = address
                            logger.info(f"   ✅ Địa chỉ thuế: {address}")
                
                # Đại diện pháp luật
                elif \'đại diện pháp luật:\' in line_clean.lower():
                    rep_match = re.search(r\'đại diện pháp luật:\s*(.+)\\' , line_clean, re.IGNORECASE)
                    if rep_match:
                        rep = rep_match.group(1).strip()
                        if len(rep) > 2 and not any(char.isdigit() for char in rep):
                            company_info[\'dai_dien_phap_luat\'] = rep
                            logger.info(f"   ✅ Đại diện pháp luật: {rep}")
                
                # Điện thoại
                elif \'điện thoại:\' in line_clean.lower():
                    phone_match = re.search(r\'điện thoại:\s*(.+)\\' , line_clean, re.IGNORECASE)
                    if phone_match:
                        phone_text = phone_match.group(1).strip()
                        phone = self._extract_valid_phone(phone_text)
                        if phone and phone != company_info[\'ma_so_thue\']:
                            company_info[\'dien_thoai\'] = phone
                            logger.info(f"   ✅ Điện thoại: {phone}")
                
                # Ngày cấp
                elif \'ngày cấp:\' in line_clean.lower():
                    date_match = re.search(r\'ngày cấp:\s*(.+)\\' , line_clean, re.IGNORECASE)
                    if date_match:
                        date_text = date_match.group(1).strip()
                        if self._is_valid_date(date_text):
                            company_info[\'ngay_cap\'] = date_text
                            logger.info(f"   ✅ Ngày cấp: {date_text}")
                
                # Ngành nghề chính
                elif \'ngành nghề chính:\' in line_clean.lower():
                    business_match = re.search(r\'ngành nghề chính:\s*(.+)\\' , line_clean, re.IGNORECASE)
                    if business_match:
                        business = business_match.group(1).strip()
                        if len(business) > 5:
                            company_info[\'nganh_nghe_chinh\'] = business
                            logger.info(f"   ✅ Ngành nghề chính: {business}")
                
                # Trạng thái  
                elif \'trạng thái:\' in line_clean.lower():
                    status_match = re.search(r\'trạng thái:\s*(.+)\\' , line_clean, re.IGNORECASE)
                    if status_match:
                        status = status_match.group(1).strip()
                        company_info[\'trang_thai\'] = status
                        logger.info(f"   ✅ Trạng thái: {status}")
                
                # Tìm các pattern khác từ các dòng liền kề
                elif any(keyword in line_clean.lower() for keyword in [\'số\', \'lô\', \'đường\', \'phường\', \'quận\', \'thành phố\', \'tỉnh\']):
                    # Có thể là địa chỉ nếu chưa có
                    if not company_info[\'dia_chi_thue\'] and len(line_clean) > 15:
                        # Kiểm tra xem có phải là địa chỉ không
                        if self._looks_like_address(line_clean):
                            company_info[\'dia_chi_thue\'] = line_clean
                            logger.info(f"   ✅ Địa chỉ (pattern): {line_clean}")
        
        except Exception as e:
            logger.warning(f"   ⚠️ Lỗi trích xuất từ text: {e}")
    
    def _looks_like_address(self, text: str) -> bool:
        """Kiểm tra xem text có giống địa chỉ không"""
        address_indicators = [\'số\', \'lô\', \'đường\', \'phường\', \'quận\', \'thành phố\', \'tỉnh\', \'xã\', \'huyện\']
        text_lower = text.lower()
        
        # Phải có ít nhất 2 indicator
        count = sum(1 for indicator in address_indicators if indicator in text_lower)
        
        # Không được chứa các từ không phải địa chỉ
        non_address = [\'mã số thuế\', \'điện thoại\', \'email\', \'ngày\', \'năm\', \'tháng\']
        has_non_address = any(word in text_lower for word in non_address)
        
        return count >= 2 and not has_non_address and len(text) > 15
    
    async def _extract_company_name(self, page, company_info: Dict[str, Any]):
        """Trích xuất tên công ty từ các nguồn đáng tin cậy"""
        try:
            # Thứ tự ưu tiên: h1 -> title -> h2
            selectors = [\'h1\', \'title\', \'h2\', \'.company-name\', \'.title\']
            
            for selector in selectors:
                try:
                    if selector == \'title\':
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
                            company_info[\'ten_cong_ty\'] = clean_name
                            logger.info(f"   ✅ Tên công ty: {clean_name}")
                            return
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"   ⚠️ Lỗi trích xuất tên: {e}")
    
    def _clean_company_name(self, text: str) -> str:
        """Làm sạch tên công ty"""
        # Loại bỏ các tiền tố không cần thiết
        text = re.sub(r\'^(Thông tin|Chi tiết|Detail|Info|Company)\s*[:]\s*\', \'\', text, flags=re.IGNORECASE)
        
        # Loại bỏ thông tin website
        text = re.sub(r\'\s*-[^-]*hsctvn[^-]*$\' , \'\', text, flags=re.IGNORECASE)
        
        # Loại bỏ thông tin số lượng hồ sơ
        text = re.sub(r\'\s*\|\s*\d+[,.\s]*\d*\s*hồ sơ.*$\' , \'\', text, flags=re.IGNORECASE)
        
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
            logger.warning(f"   ⚠️ Lỗi trích xuất bảng: {e}")
    
    def _map_table_field(self, label: str, value: str, company_info: Dict[str, Any]):
        """Map field từ bảng vào company_info với điều kiện ít khắt khe hơn"""
        if not label or not value or len(value) < 2:
            return
        
        label_lower = label.lower().strip()
        value_clean = value.strip()
        
        # Địa chỉ với điều kiện ít khắt khe hơn
        if any(kw in label_lower for kw in [\'địa chỉ\', \'address\']) and len(value_clean) > 10:
            if not company_info[\'dia_chi_thue\']:  # Chỉ set nếu chưa có
                company_info[\'dia_chi_thue\'] = value_clean
                logger.info(f"   ✅ Địa chỉ (bảng): {value_clean}")
        
        # Đại diện pháp luật
        elif any(kw in label_lower for kw in [\'đại diện pháp luật\', \'giám đốc\', \'legal representative\', \'director\']):
            if len(value_clean) > 2 and not any(char.isdigit() for char in value_clean):
                if not company_info[\'dai_dien_phap_luat\']:
                    company_info[\'dai_dien_phap_luat\'] = value_clean
                    logger.info(f"   ✅ Đại diện pháp luật (bảng): {value_clean}")
        
        # Điện thoại
        elif any(kw in label_lower for kw in [\'điện thoại\', \'phone\', \'tel\']):
            phone = self._extract_valid_phone(value_clean)
            if phone and phone != company_info[\'ma_so_thue\']:
                if not company_info[\'dien_thoai\']:
                    company_info[\'dien_thoai\'] = phone
                    logger.info(f"   ✅ Điện thoại (bảng): {phone}")
        
        # Email
        elif any(kw in label_lower for kw in [\'email\']):
            if self._is_valid_email(value_clean):
                if not company_info[\'email\']:
                    company_info[\'email\'] = value_clean
                    logger.info(f"   ✅ Email (bảng): {value_clean}")
        
        # Ngày cấp
        elif any(kw in label_lower for kw in [\'ngày cấp\', \'ngày thành lập\', \'ngày đăng ký\', \'date of issue\']):
            if self._is_valid_date(value_clean):
                if not company_info[\'ngay_cap\']:
                    company_info[\'ngay_cap\'] = value_clean
                    logger.info(f"   ✅ Ngày cấp (bảng): {value_clean}")
        
        # Ngành nghề chính
        elif any(kw in label_lower for kw in [\'ngành nghề chính\', \'lĩnh vực hoạt động\', \'main business\']):
            if len(value_clean) > 5:
                if not company_info[\'nganh_nghe_chinh\']:
                    company_info[\'nganh_nghe_chinh\'] = value_clean
                    logger.info(f"   ✅ Ngành nghề chính (bảng): {value_clean}")
        
        # Trạng thái
        elif any(kw in label_lower for kw in [\'trạng thái\', \'status\']):
            if len(value_clean) > 2:
                if not company_info[\'trang_thai\']:
                    company_info[\'trang_thai\'] = value_clean
                    logger.info(f"   ✅ Trạng thái (bảng): {value_clean}")

    async def _extract_contact_info(self, page, company_info: Dict[str, Any]):
        """Trích xuất thông tin liên hệ từ các thẻ p, div"""
        try:
            content_div = await page.query_selector(".content") # Hoặc selector chứa thông tin chính
            if content_div:
                text_content = await content_div.inner_text()
                
                # Phone
                phone_match = re.search(r\'Điện thoại:\s*([\d\s\.\-]+)\' , text_content)
                if phone_match:
                    phone = self._extract_valid_phone(phone_match.group(1))
                    if phone and not company_info[\'dien_thoai\']:
                        company_info[\'dien_thoai\'] = phone
                        logger.info(f"   ✅ Điện thoại (content): {phone}")
                
                # Email
                email_match = re.search(r\'Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\', text_content)
                if email_match:
                    if self._is_valid_email(email_match.group(1)) and not company_info[\'email\']:
                        company_info[\'email\'] = email_match.group(1)
                        logger.info(f"   ✅ Email (content): {company_info[\'email\']}")
        except Exception as e:
            logger.warning(f"   ⚠️ Lỗi trích xuất liên hệ: {e}")

    async def _extract_main_business_activity(self, page, company_info: Dict[str, Any]):
        """Trích xuất ngành nghề chính và chi tiết"""
        try:
            # Ngành nghề chính
            main_business_elem = await page.query_selector("p:has-text(\'Ngành nghề chính:\') strong")
            if main_business_elem:
                main_business = await main_business_elem.inner_text()
                if main_business and not company_info[\'nganh_nghe_chinh\']:
                    company_info[\'nganh_nghe_chinh\'] = main_business.strip()
                    logger.info(f"   ✅ Ngành nghề chính (selector): {main_business.strip()}")
            
            # Ngành nghề kinh doanh chi tiết (từ bảng)
            detail_table = await page.query_selector("table.table-bordered") # Selector cho bảng ngành nghề chi tiết
            if detail_table:
                rows = await detail_table.query_selector_all("tr")
                detailed_activities = []
                for row in rows[1:]: # Bỏ qua header
                    cols = await row.query_selector_all("td")
                    if len(cols) > 1:
                        activity = await cols[1].inner_text() # Cột thứ 2 thường là tên ngành nghề
                        if activity.strip():
                            detailed_activities.append(activity.strip())
                if detailed_activities:
                    company_info[\'nganh_nghe_kinh_doanh_chi_tiet\'] = detailed_activities
                    logger.info(f"   ✅ Ngành nghề chi tiết: {detailed_activities[:3]}...")

        except Exception as e:
            logger.warning(f"   ⚠️ Lỗi trích xuất ngành nghề: {e}")

    def _validate_and_clean_final(self, company_info: Dict[str, Any], tax_code: str):
        """
        Kiểm tra và làm sạch dữ liệu cuối cùng.
        """
        # Đảm bảo mã số thuế luôn đúng
        company_info[\'ma_so_thue\'] = tax_code

        # Làm sạch các trường rỗng
        for key, value in company_info.items():
            if isinstance(value, str):
                company_info[key] = value.strip()
            elif isinstance(value, list):
                company_info[key] = [item.strip() for item in value if item.strip()]

        # Loại bỏ các trường không cần thiết hoặc không có dữ liệu
        keys_to_remove = [key for key, value in company_info.items() if not value and key != 'nganh_nghe_kinh_doanh_chi_tiet']
        for key in keys_to_remove:
            del company_info[key]

        # Nếu ngành nghề chi tiết rỗng, xóa nó
        if not company_info.get('nganh_nghe_kinh_doanh_chi_tiet'):
            company_info.pop('nganh_nghe_kinh_doanh_chi_tiet', None)

    def _extract_valid_phone(self, text: str) -> Optional[str]:
        """
        Trích xuất số điện thoại hợp lệ từ chuỗi.
        """
        phone_numbers = re.findall(r\'\b(0\d{9,10}|\+84\d{9,10})\b\', text)
        if phone_numbers:
            return phone_numbers[0]
        return None

    def _is_valid_email(self, email: str) -> bool:
        """
        Kiểm tra định dạng email hợp lệ.
        """
        return re.match(r\'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$\' , email) is not None

    def _is_valid_date(self, date_str: str) -> bool:
        """
        Kiểm tra định dạng ngày tháng hợp lệ (DD/MM/YYYY hoặc DD-MM-YYYY).
        """
        return re.match(r\'^(?:\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})$\', date_str) is not None


# Example Usage (for testing purposes)
async def main():
    logging.basicConfig(level=logging.INFO)
    client = HSCTVNEnhanced()

    tax_codes = ["0100109106", "0100109106-001", "0100109106-002", "0100109106-003"]

    for tax_code in tax_codes:
        company_info = await client.search_company(tax_code)
        if company_info:
            logger.info(f"\n--- Kết quả trích xuất cho MST {tax_code} ---")
            for key, value in company_info.items():
                logger.info(f"{key}: {value}")
        else:
            logger.info(f"\n--- Không tìm thấy thông tin cho MST {tax_code} ---")

if __name__ == "__main__":
    asyncio.run(main())
