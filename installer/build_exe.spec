# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Enterprise Data Collector v2.0
Author: MiniMax Agent
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get the project root directory
project_root = os.path.dirname(SPECPATH)

# Define application metadata
app_name = "EnterpriseDataCollector"
app_version = "2.0"
app_description = "Enterprise Data Collector - Thu thập dữ liệu doanh nghiệp"
app_author = "MiniMax Agent"

# Collect all data files and dependencies
datas = []

# Add src directory and all its contents
src_path = os.path.join(project_root, 'src')
if os.path.exists(src_path):
    datas.append((src_path, 'src'))

# Add configuration and resource directories
for directory in ['Database', 'Outputs', 'Logs', 'docs', 'samples']:
    dir_path = os.path.join(project_root, directory)
    if os.path.exists(dir_path):
        datas.append((dir_path, directory))

# Add requirements and config files
for file in ['requirements.txt', 'pyproject.toml']:
    file_path = os.path.join(project_root, file)
    if os.path.exists(file_path):
        datas.append((file_path, '.'))

# Collect hidden imports for all dependencies
hiddenimports = [
    # Tkinter and GUI dependencies
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    
    # Async and threading
    'asyncio',
    'threading',
    'concurrent.futures',
    
    # Web scraping dependencies
    'playwright',
    'playwright.async_api',
    'beautifulsoup4',
    'bs4',
    'requests',
    'httpx',
    'urllib3',
    
    # Data processing
    'pandas',
    'openpyxl',
    'xlsxwriter',
    'numpy',
    
    # Database
    'sqlite3',
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    
    # Logging and utilities
    'logging',
    'logging.handlers',
    'json',
    'csv',
    'datetime',
    'pathlib',
    're',
    'time',
    
    # Custom modules
    'src',
    'src.ui',
    'src.ui.main_window',
    'src.controller',
    'src.services',
    'src.exporter',
    'src.logger',
    'src.models',
    'src.repository'
]

# Auto-collect submodules for major packages
try:
    hiddenimports.extend(collect_submodules('playwright'))
    hiddenimports.extend(collect_submodules('pandas'))
    hiddenimports.extend(collect_submodules('openpyxl'))
    hiddenimports.extend(collect_submodules('sqlalchemy'))
except:
    pass

# Analysis step
a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root, src_path],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'setuptools',
        'pip',
        'wheel'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='resources/app_icon.ico',
)

# Collect all files into a directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

# Create version info for Windows
version_info = f'''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({app_version.replace('.', ',')},0,0),
    prodvers=({app_version.replace('.', ',')},0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', '{app_author}'),
        StringStruct('FileDescription', '{app_description}'),
        StringStruct('FileVersion', '{app_version}'),
        StringStruct('InternalName', '{app_name}'),
        StringStruct('LegalCopyright', 'Copyright © 2024 {app_author}'),
        StringStruct('OriginalFilename', '{app_name}.exe'),
        StringStruct('ProductName', '{app_description}'),
        StringStruct('ProductVersion', '{app_version}')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
'''

# Write version info to file
with open(os.path.join(project_root, 'installer', 'version_info.txt'), 'w', encoding='utf-8') as f:
    f.write(version_info)