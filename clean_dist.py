import os
import shutil
from pathlib import Path

def clean_dist():
    """清理不必要的文件"""
    dist_path = Path("dist/MarketAnalyzer")
    
    # 要删除的Qt模块
    qt_modules_to_remove = [
        "Qt5Bluetooth*", "Qt5Multimedia*", "Qt5Quick*", 
        "Qt5Sensors*", "Qt5Sql*", "Qt5Test*", "Qt5Xml*",
        "Qt53D*", "Qt5Designer*", "Qt5Location*", "Qt5Nfc*",
        "Qt5Purchasing*", "Qt5Charts*"
    ]
    
    # 要删除的PyQt5模块
    pyqt_modules_to_remove = [
        "PyQt5/Qt/qml/*", "PyQt5/Qt/plugins/sceneparsers/*",
        "PyQt5/Qt/plugins/multimedia/*", "PyQt5/Qt/plugins/sqldrivers/*"
    ]
    
    # 删除文件
    for pattern in qt_modules_to_remove + pyqt_modules_to_remove:
        for file in dist_path.glob(pattern):
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                shutil.rmtree(file)
    
    print("清理完成")

if __name__ == "__main__":
    clean_dist() 