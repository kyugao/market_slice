import sys
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from pyecharts import options as opts
from pyecharts.charts import Line
import pandas as pd
from loguru import logger

from services.contract_list_data_service import concept_list
from widgets.contract_trading_volume_chart_widget import ContractTradingVolumeChartWidget
from widgets.index_trading_volume_chart_widget import IndexTradingVolumeChartWidget

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
        self.mainLeftFrame.installEventFilter(self)
        
        # Initialize line attribute
        self.line = None
        
        logger.debug("[INIT] 主窗口初始化完成")

    def init_echarts(self):
        """初始化index_echarts图表"""
        # 创建单个WebEngine视图
        browser = QWebEngineView()
        browser2 = QWebEngineView()
        self.browsers = {'headerChart': browser, "mainleftChart": browser2}
        
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
        
        # 直接创建和设置布局
        layout2 = QtWidgets.QVBoxLayout()
        layout2.setContentsMargins(0, 0, 0, 0)
        layout2.setSpacing(0)
        layout2.addWidget(browser)
        
        # 一次性设置WebEngine属性
        settings2 = browser2.settings()
        settings2.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        
        # 设置背景色和布局
        browser2.page().setBackgroundColor(QtCore.Qt.white)
        self.mainLeftFrame.setLayout(layout2)


    def init_ui_controls(self):
        """初始化UI控件"""
        logger.debug("[INIT] 开始初始化UI控件...")

        # 创建交易量图表Widget
        self.index_chart = IndexTradingVolumeChartWidget()
        
        # 获取headerFrame的布局
        header_layout = self.headerFrame.layout()
        
        # 将交易量图表添加到headerFrame布局中
        header_layout.addWidget(self.index_chart)
        
        logger.debug("[INIT] 已将指数交易量图表添加到headerFrame")


        # 创建交易量图表Widget
        self.mainLeftChart = ContractTradingVolumeChartWidget(symbol='BK1184')
        
        # 获取headerFrame的布局
        mainLeft_layout = self.mainLeftFrame.layout()
        
        # 将交易量图表添加到headerFrame布局中
        mainLeft_layout.addWidget(self.mainLeftChart)
        
        logger.debug("[INIT] 已将个股交易量图表添加到mainLeft_layout")

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

    # def eventFilter(self, source, event):
    #     logger.debug(f"[EVENT] 事件类型: {event.type()}, {QtCore.QEvent.Resize}")
    #     """事件过滤器，用于监听大小改变事件"""
    #     # if event.type() == QtCore.QEvent.Resize:
    #     #     if source is self.headerFrame:
    #     #         self.index_chart.resizeEvent(event)
    #     #         # self.update_header_chart_size()
    #     #     if source is self.mainLeftFrame:
    #     #         self.mainLeftChart.resizeEvent(event)
    #         # self.update_mainleft_chart_size()
    #     return super().eventFilter(source, event)

# 程序入口
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()