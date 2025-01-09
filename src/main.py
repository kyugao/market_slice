import sys
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from pyecharts import options as opts
from pyecharts.charts import Line
import pandas as pd
from loguru import logger

from services.concept_list_data_service import concept_list
from widgets.trading_volume_chart_widget import TradingVolumeChartWidget
from services.history_data_service import HistoryDataService
from services.trading_day_data_service import TradingDayDataService

# 配置日志
logger.add("logs/{time:YYYY-MM-DD}_app.log", 
           rotation="00:00",  # 每天零点创建新文件
           encoding="utf-8", 
           enqueue=True,  # 线程安全
           backtrace=True,  # 详细的异常追踪
           diagnose=True,  # 更详细的异常信息
           level="INFO")

class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        logger.debug("[INIT] 开始初始化主窗口...")
        
        # 加载UI
        uic.loadUi('main.ui', self)
        
        # 初始化echarts图表
        self.init_echarts()
        
        # 初始化UI控件
        self.init_ui_controls()
        
        # Connect resize event to update chart size
        self.headerFrame.installEventFilter(self)
        
        # Initialize line attribute
        self.line = None
        
        logger.debug("[INIT] 主窗口初始化完成")

    def init_echarts(self):
        """初始化echarts图表"""
        # 创建单个WebEngine视图
        browser = QWebEngineView()
        self.browsers = {'first': browser}
        
        # 直接创建和设置布局
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(browser)
        
        # 一次性设置WebEngine属性
        settings = browser.settings()
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        
        # 设置背景色和布局
        browser.page().setBackgroundColor(QtCore.Qt.white)
        self.headerFrame.setLayout(layout)

    def init_ui_controls(self):
        """初始化UI控件"""
        logger.debug("[INIT] 开始初始化UI控件...")

        # 创建交易量图表Widget
        self.volume_chart = TradingVolumeChartWidget(symbols=['000001.SH', '399001.SZ'], title="沪深5m成交量对比")
        
        # 获取headerFrame的布局
        header_layout = self.headerFrame.layout()
        
        # 将交易量图表添加到headerFrame布局中
        header_layout.addWidget(self.volume_chart)
        
        logger.debug("[INIT] 已将交易量图表添加到headerFrame")

        # 调用concept_list方法获取概念列表
        concept_data = concept_list()
        logger.debug(f"[INIT] 获取到的概念列表数据：{concept_data}")
        
        # 将数据转换为适合QTableView显示的格式
        model = QtGui.QStandardItemModel()
        model.setHorizontalHeaderLabels(['概念代码', '概念名称'])
        for index, row in concept_data.iterrows():
            model.appendRow([
                QtGui.QStandardItem(row['concept_code']),
                QtGui.QStandardItem(row['name']),
            ])
        
        # 初始化tableView并设置数据模型
        self.tableView.setModel(model)
        
        logger.debug("[INIT] 已初始化tableView并设置数据模型")

    def eventFilter(self, source, event):
        """事件过滤器，用于监听大小改变事件"""
        if event.type() == QtCore.QEvent.Resize and source is self.headerFrame:
            self.update_chart_size()
        return super().eventFilter(source, event)

    def update_chart_size(self):
        """更新图表大小"""
        if self.line is None:
            return
            
        frame_size = self.headerFrame.size()
        current_width = f"{frame_size.width()}px"
        current_height = f"{frame_size.height()}px"
        
        if self.line.width != current_width or self.line.height != current_height:
            self.line.width = current_width
            self.line.height = current_height
            self.line.render("temp_chart.html")
            
            file_path = QtCore.QDir.current().absoluteFilePath("temp_chart.html")
            url = QtCore.QUrl.fromLocalFile(str(file_path))
            
            for browser in self.browsers.values():
                browser.setMinimumSize(frame_size)
                browser.load(url)

# 程序入口
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()