import os
import sys

def runtime_hook():
    if getattr(sys, 'frozen', False):
        # 运行在打包环境
        base_path = sys._MEIPASS
    else:
        # 运行在开发环境
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    # 添加模块搜索路径
    if base_path not in sys.path:
        sys.path.insert(0, base_path) 