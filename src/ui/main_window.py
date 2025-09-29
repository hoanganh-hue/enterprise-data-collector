"""
Enhanced Main Window for Enterprise Data Collector v2.0
PyQt5 main application window with dual data source integration
Author: MiniMax Agent
"""

import sys
import asyncio
import threading
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QSpinBox, QCheckBox, QProgressBar,
    QTextEdit, QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QSplitter, QFrame, QApplication,
    QHeaderView, QStatusBar, QMenuBar, QAction, QDialog
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize
)
from PyQt5.QtGui import (
    QFont, QIcon, QPalette, QColor, QPixmap
)

from ..controller import EnhancedAppController
from ..models import EnhancedCompany, City, Industry


class CollectionWorker(QThread):
    """
    Worker thread for data collection to avoid UI freezing
    """
    
    progress_updated = pyqtSignal(str, int, int)  # message, current, total
    collection_completed = pyqtSignal(dict)  # stats
    collection_failed = pyqtSignal(str)  # error message
    
    def __init__(
        self, 
        controller: EnhancedAppController,
        location_name: str,
        industry_name: str,
        max_companies: int,
        enable_hsctvn: bool,
        hsctvn_delay: float
    ):
        super().__init__()
        self.controller = controller
        self.location_name = location_name
        self.industry_name = industry_name
        self.max_companies = max_companies
        self.enable_hsctvn = enable_hsctvn
        self.hsctvn_delay = hsctvn_delay
        self._is_running = False
    
    def run(self):
        """Run collection in separate thread"""
        self._is_running = True
        
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Set progress callback
            self.controller.progress_callback = self.progress_updated.emit
            
            # Run collection
            stats = loop.run_until_complete(
                self.controller.collect_companies(
                    location_name=self.location_name,
                    industry_name=self.industry_name,
                    max_companies=self.max_companies,
                    enable_hsctvn=self.enable_hsctvn,
                    hsctvn_delay=self.hsctvn_delay
                )
            )
            
            if self._is_running:
                self.collection_completed.emit(stats)
                
        except Exception as e:
            if self._is_running:
                self.collection_failed.emit(str(e))
        
        finally:
            # Clean up
            try:
                loop.close()
            except:
                pass
    
    def stop(self):
        """Stop collection"""
        self._is_running = False
        self.terminate()


class EnhancedMainWindow(QMainWindow):
    """
    Enhanced main window cho Enterprise Data Collector v2.0
    
    Features:
    - Modern UI design
    - Dual data source configuration
    - Real-time progress tracking
    - Enhanced data preview
    - Excel export với 31 columns
    - Comprehensive logging
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize controller
        self.controller = EnhancedAppController(
            progress_callback=self.update_progress
        )
        
        # UI state
        self.collection_worker = None
        self.current_companies = []
        
        # Initialize UI
        self.init_ui()
        self.setup_styles()
        self.load_reference_data()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Enterprise Data Collector v2.0 - Enhanced")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set window icon
        self.setWindowIcon(QIcon())
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for main content
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Configuration
        left_panel = self.create_config_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Results & Logs
        right_panel = self.create_results_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 1000])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
    
    def create_config_panel(self) -> QWidget:
        """Tạo panel cấu hình"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Collection Configuration
        config_group = QGroupBox("Cấu hình Thu thập")
        config_layout = QGridLayout(config_group)
        
        # Location selection
        config_layout.addWidget(QLabel("Tỉnh/Thành phố:"), 0, 0)
        self.location_combo = QComboBox()
        self.location_combo.setEditable(True)
        config_layout.addWidget(self.location_combo, 0, 1)
        
        # Industry selection
        config_layout.addWidget(QLabel("Ngành nghề:"), 1, 0)
        self.industry_combo = QComboBox()
        self.industry_combo.setEditable(True)
        config_layout.addWidget(self.industry_combo, 1, 1)
        
        # Max companies
        config_layout.addWidget(QLabel("Số lượng tối đa:"), 2, 0)
        self.max_companies_spin = QSpinBox()
        self.max_companies_spin.setRange(1, 1000)
        self.max_companies_spin.setValue(100)
        config_layout.addWidget(self.max_companies_spin, 2, 1)
        
        layout.addWidget(config_group)
        
        # HSCTVN Configuration
        hsctvn_group = QGroupBox("Cấu hình HSCTVN")
        hsctvn_layout = QGridLayout(hsctvn_group)
        
        # Enable HSCTVN
        self.enable_hsctvn_check = QCheckBox("Kích hoạt tích hợp HSCTVN")
        self.enable_hsctvn_check.setChecked(True)
        hsctvn_layout.addWidget(self.enable_hsctvn_check, 0, 0, 1, 2)
        
        # HSCTVN delay
        hsctvn_layout.addWidget(QLabel("Delay giữa requests (giây):"), 1, 0)
        self.hsctvn_delay_spin = QSpinBox()
        self.hsctvn_delay_spin.setRange(1, 10)
        self.hsctvn_delay_spin.setValue(2)
        hsctvn_layout.addWidget(self.hsctvn_delay_spin, 1, 1)
        
        layout.addWidget(hsctvn_group)
        
        # Control buttons
        buttons_group = QGroupBox("Thao tác")
        buttons_layout = QVBoxLayout(buttons_group)
        
        # Start collection button
        self.start_button = QPushButton("▶ Bắt đầu Thu thập")
        self.start_button.clicked.connect(self.start_collection)
        self.start_button.setMinimumHeight(40)
        buttons_layout.addWidget(self.start_button)
        
        # Stop collection button
        self.stop_button = QPushButton("⏹ Dừng Thu thập")
        self.stop_button.clicked.connect(self.stop_collection)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(40)
        buttons_layout.addWidget(self.stop_button)
        
        # Export button
        self.export_button = QPushButton("📄 Xuất Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setEnabled(False)
        self.export_button.setMinimumHeight(40)
        buttons_layout.addWidget(self.export_button)
        
        # Clear data button
        self.clear_button = QPushButton("🗑 Xóa Dữ liệu")
        self.clear_button.clicked.connect(self.clear_data)
        self.clear_button.setMinimumHeight(40)
        buttons_layout.addWidget(self.clear_button)
        
        layout.addWidget(buttons_group)
        
        # Progress section
        progress_group = QGroupBox("Tiến trình")
        progress_layout = QVBoxLayout(progress_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        # Progress label
        self.progress_label = QLabel("Sẵn sàng")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # Add stretch
        layout.addStretch()
        
        return panel
    
    def create_results_panel(self) -> QWidget:
        """Tạo panel kết quả"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Data tab
        self.create_data_tab()
        
        # Logs tab
        self.create_logs_tab()
        
        # Statistics tab
        self.create_stats_tab()
        
        return panel
    
    def create_data_tab(self):
        """Tạo tab dữ liệu"""
        data_widget = QWidget()
        layout = QVBoxLayout(data_widget)
        
        # Table for company data
        self.data_table = QTableWidget()
        layout.addWidget(self.data_table)
        
        # Setup table
        headers = [
            "Mã số thuế", "Tên công ty", "Địa chỉ", "Người đại diện",
            "Điện thoại", "Ngành nghề", "Tình trạng", "Nguồn dữ liệu"
        ]
        self.data_table.setColumnCount(len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)
        
        # Configure table
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        self.tab_widget.addTab(data_widget, "📈 Dữ liệu")
    
    def create_logs_tab(self):
        """Tạo tab logs"""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        self.tab_widget.addTab(logs_widget, "📄 Logs")
    
    def create_stats_tab(self):
        """Tạo tab thống kê"""
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        
        # Stats text area
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        layout.addWidget(self.stats_text)
        
        self.tab_widget.addTab(stats_widget, "📊 Thống kê")
    
    def create_menu_bar(self):
        """Tạo menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Export action
        export_action = QAction('&Export to Excel', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_to_excel)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        # Test API connection
        test_api_action = QAction('&Test API Connection', self)
        test_api_action.triggered.connect(self.test_api_connection)
        tools_menu.addAction(test_api_action)
        
        # Clear logs
        clear_logs_action = QAction('&Clear Logs', self)
        clear_logs_action.triggered.connect(self.clear_logs)
        tools_menu.addAction(clear_logs_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # About action
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """Tạo status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Sẵn sàng")
        self.status_bar.addWidget(self.status_label)
        
        # Database info
        self.db_info_label = QLabel("")
        self.status_bar.addPermanentWidget(self.db_info_label)
    
    def setup_styles(self):
        """Thiết lập styles cho UI"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #45a049;
            }
            
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            
            QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            
            QSpinBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            
            QTableWidget {
                gridline-color: #f0f0f0;
                background-color: white;
            }
            
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
            }
            
            QTabBar::tab {
                background: #e0e0e0;
                padding: 8px 12px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background: #4CAF50;
                color: white;
            }
        """)
    
    def load_reference_data(self):
        """Load reference data (cities, industries)"""
        try:
            # Load cities
            cities = self.controller.get_cities()
            self.location_combo.addItem("-- Chọn tỉnh/thành phố --", None)
            for city in cities:
                self.location_combo.addItem(city.name, city)
            
            # Load industries
            industries = self.controller.get_industries()
            self.industry_combo.addItem("-- Chọn ngành nghề --", None)
            for industry in industries:
                self.industry_combo.addItem(industry.name, industry)
            
            self.log_message(f"Loaded {len(cities)} cities and {len(industries)} industries")
            
        except Exception as e:
            self.show_error(f"Failed to load reference data: {e}")
    
    def start_collection(self):
        """Bắt đầu thu thập dữ liệu"""
        try:
            # Validate inputs
            location_name = self.location_combo.currentText()
            industry_name = self.industry_combo.currentText()
            
            if location_name.startswith("--") or industry_name.startswith("--"):
                self.show_error("Vui lòng chọn tỉnh/thành phố và ngành nghề")
                return
            
            # Validate parameters
            validation_result = self.controller.validate_collection_params(
                location_name=location_name,
                industry_name=industry_name
            )
            
            if not validation_result['valid']:
                errors = '\n'.join(validation_result['errors'])
                self.show_error(f"Tham số không hợp lệ:\n{errors}")
                return
            
            # Get parameters
            max_companies = self.max_companies_spin.value()
            enable_hsctvn = self.enable_hsctvn_check.isChecked()
            hsctvn_delay = self.hsctvn_delay_spin.value()
            
            # Update UI state
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.export_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_label.setText("Khởi tạo...")
            
            # Clear previous data
            self.current_companies = []
            self.data_table.setRowCount(0)
            
            # Start collection worker
            self.collection_worker = CollectionWorker(
                controller=self.controller,
                location_name=location_name,
                industry_name=industry_name,
                max_companies=max_companies,
                enable_hsctvn=enable_hsctvn,
                hsctvn_delay=hsctvn_delay
            )
            
            # Connect signals
            self.collection_worker.progress_updated.connect(self.update_progress)
            self.collection_worker.collection_completed.connect(self.on_collection_completed)
            self.collection_worker.collection_failed.connect(self.on_collection_failed)
            
            # Start worker
            self.collection_worker.start()
            
            self.log_message(f"Started collection: {location_name}, {industry_name}, max={max_companies}")
            
        except Exception as e:
            self.show_error(f"Failed to start collection: {e}")
            self.reset_ui_state()
    
    def stop_collection(self):
        """Dừng thu thập dữ liệu"""
        if self.collection_worker and self.collection_worker.isRunning():
            self.collection_worker.stop()
            self.log_message("Collection stopped by user")
        
        self.reset_ui_state()
    
    def update_progress(self, message: str, current: int, total: int):
        """Cập nhật tiến trình"""
        self.progress_label.setText(message)
        
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
        
        self.log_message(f"Progress: {message} ({current}/{total})")
    
    def on_collection_completed(self, stats: dict):
        """Xử lý khi hoàn thành thu thập"""
        try:
            # Load collected data
            self.load_collected_data()
            
            # Update stats
            self.update_stats_display(stats)
            
            # Show completion message
            total_processed = stats.get('total_processed', 0)
            dual_source = stats.get('dual_source_success', 0)
            
            message = f"Hoàn thành thu thập!\n\n" \
                     f"Tổng số công ty: {total_processed}\n" \
                     f"Tích hợp được HSCTVN: {dual_source}"
            
            QMessageBox.information(self, "Hoàn thành", message)
            
            self.log_message(f"Collection completed: {stats}")
            
        except Exception as e:
            self.show_error(f"Error processing completion: {e}")
        
        finally:
            self.reset_ui_state()
    
    def on_collection_failed(self, error_message: str):
        """Xử lý khi thu thập thất bại"""
        self.show_error(f"Thu thập thất bại:\n{error_message}")
        self.log_message(f"Collection failed: {error_message}")
        self.reset_ui_state()
    
    def reset_ui_state(self):
        """Reset UI state after collection"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Sẵn sàng")
        
        if self.current_companies:
            self.export_button.setEnabled(True)
    
    def load_collected_data(self):
        """Load collected data into table"""
        try:
            # Get collected companies
            companies = self.controller.get_collected_companies(limit=1000)
            self.current_companies = companies
            
            # Update table
            self.data_table.setRowCount(len(companies))
            
            for row, company in enumerate(companies):
                items = [
                    company.ma_so_thue,
                    company.ten_cong_ty,
                    company.dia_chi_dang_ky or company.dia_chi_thue,
                    company.nguoi_dai_dien or company.dai_dien_phap_luat,
                    company.dien_thoai or company.dien_thoai_dai_dien,
                    company.nganh_nghe_kinh_doanh_chinh,
                    company.tinh_trang_hoat_dong,
                    company.data_source
                ]
                
                for col, item in enumerate(items):
                    self.data_table.setItem(row, col, QTableWidgetItem(str(item or '')))
            
            # Auto resize columns
            self.data_table.resizeColumnsToContents()
            
            self.log_message(f"Loaded {len(companies)} companies into table")
            
        except Exception as e:
            self.show_error(f"Failed to load data: {e}")
    
    def export_to_excel(self):
        """Xuất dữ liệu ra Excel"""
        if not self.current_companies:
            self.show_error("Không có dữ liệu để xuất")
            return
        
        try:
            # Get save location
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"enhanced_companies_{timestamp}.xlsx"
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Xuất Excel",
                default_filename,
                "Excel files (*.xlsx);;All files (*.*)"
            )
            
            if filename:
                # Export
                output_path = self.controller.export_to_excel(
                    companies=self.current_companies,
                    filename=Path(filename).name,
                    include_charts=True
                )
                
                QMessageBox.information(
                    self,
                    "Xuất thành công",
                    f"Dữ liệu đã được xuất ra:\n{output_path}"
                )
                
                self.log_message(f"Exported {len(self.current_companies)} companies to {output_path}")
        
        except Exception as e:
            self.show_error(f"Failed to export: {e}")
    
    def clear_data(self):
        """Xóa dữ liệu"""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Bạn có chắc chắn muốn xóa tất cả dữ liệu?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.current_companies = []
            self.data_table.setRowCount(0)
            self.export_button.setEnabled(False)
            self.log_message("Data cleared")
    
    def test_api_connection(self):
        """Test API connection"""
        try:
            result = self.controller.test_api_connection()
            
            if result['success']:
                QMessageBox.information(self, "Kết nối thành công", result['message'])
            else:
                QMessageBox.warning(self, "Kết nối thất bại", result['message'])
            
            self.log_message(f"API test: {result['message']}")
            
        except Exception as e:
            self.show_error(f"API test failed: {e}")
    
    def clear_logs(self):
        """Xóa logs"""
        self.log_text.clear()
        self.log_message("Logs cleared")
    
    def update_stats_display(self, stats: dict):
        """Cập nhật hiển thị thống kê"""
        try:
            # Collection stats
            collection_stats = f"""Kết quả Thu thập Dữ liệu:

• Tổng số xử lý: {stats.get('total_processed', 0)}
• Thành công API: {stats.get('api_success', 0)}
• Thành công HSCTVN: {stats.get('hsctvn_success', 0)}
• Tích hợp 2 nguồn: {stats.get('dual_source_success', 0)}
• Bản ghi mới: {stats.get('new_records', 0)}
• Bản ghi cập nhật: {stats.get('updated_records', 0)}
• Lỗi: {stats.get('errors', 0)}
"""
            
            if 'duration_seconds' in stats:
                collection_stats += f"\n• Thời gian: {stats['duration_seconds']:.1f} giây"
            
            # Database stats
            db_stats = self.controller.get_database_stats()
            
            db_stats_text = f"""\n\nThống kê Database:

• Tổng số công ty: {db_stats.get('total_companies', 0)}
"""
            
            if 'by_status' in db_stats:
                db_stats_text += "\nTheo tình trạng:\n"
                for status, count in db_stats['by_status'].items():
                    db_stats_text += f"  - {status}: {count}\n"
            
            if 'by_data_source' in db_stats:
                db_stats_text += "\nTheo nguồn dữ liệu:\n"
                for source, count in db_stats['by_data_source'].items():
                    db_stats_text += f"  - {source}: {count}\n"
            
            # Update display
            self.stats_text.setText(collection_stats + db_stats_text)
            
        except Exception as e:
            self.log_message(f"Failed to update stats: {e}")
    
    def update_status(self):
        """Cập nhật status bar"""
        try:
            # Update database info
            db_stats = self.controller.get_database_stats()
            total_companies = db_stats.get('total_companies', 0)
            self.db_info_label.setText(f"Database: {total_companies} công ty")
            
        except Exception as e:
            pass  # Ignore errors in status update
    
    def show_about(self):
        """Hiển thị thông tin"""
        about_text = """Enterprise Data Collector v2.0 Enhanced

Tính năng:
• Thu thập dữ liệu từ 2 nguồn: API + HSCTVN
• Xuất Excel với 31 cột thông tin
• Giao diện thân thiện với người dùng
• Thống kê và báo cáo chi tiết

Phát triển bởi: MiniMax Agent
Phiên bản: 2.0
Năm: 2025"""
        
        QMessageBox.about(self, "Về chương trình", about_text)
    
    def log_message(self, message: str):
        """Ghi log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # Auto scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def show_error(self, message: str):
        """Hiển thị lỗi"""
        QMessageBox.critical(self, "Lỗi", message)
        self.log_message(f"ERROR: {message}")
    
    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng"""
        try:
            # Stop collection if running
            if self.collection_worker and self.collection_worker.isRunning():
                self.collection_worker.stop()
                self.collection_worker.wait(3000)  # Wait up to 3 seconds
            
            # Close controller
            self.controller.close()
            
            self.log_message("Application closed")
            
        except Exception as e:
            pass  # Ignore errors during shutdown
        
        event.accept()


def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("Enterprise Data Collector v2.0")
    app.setOrganizationName("MiniMax Agent")
    
    # Create and show main window
    window = EnhancedMainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()