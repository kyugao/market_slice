import sys
from PyQt5 import QtWidgets, uic, QtCore, QtGui
# from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from loguru import logger
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from utils.concept_list_data_service import ConceptDataUtil
from widgets.contract_trading_volume_chart_widget import ContractTradingVolumeChartWidget
from widgets.index_trading_volume_chart_widget import IndexTradingVolumeChartWidget
from widgets.concept_list_widget import ConceptListWidget

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
        uic.loadUi('./src/ui/main.ui', self)
        font_path = './src/assets/LXGWWenKai-Regular.ttf'
        fm.fontManager.addfont(font_path)
        font_props=fm.FontProperties(fname=font_path)
        # 获得字体名
        font_name=font_props.get_name()
        # 优先使用自定义的字体，不满足的则 fallback 到 sans-serif
        plt.rcParams['font.family']=[font_name, 'sans-serif']
        # （可选）还可以单独设置数学公式字体，这里用 matplotlib 默认的字体
        plt.rcParams["mathtext.fontset"]='cm'
        # 初始化echarts图表
        self.init_echarts()
        
        # 初始化UI控件
        self.init_ui_controls()
        
        # Connect resize event to update chart size
        self.headerFrame.installEventFilter(self)
        self.mainLeftFrame.installEventFilter(self)
        logger.debug("[INIT] 主窗口初始化完成")

    def init_echarts(self):
        """初始化index_echarts图表"""
        # 创建单个WebEngine视图
        # browser = QWebEngineView()
        # browser2 = QWebEngineView()
        # self.browsers = {'headerChart': browser, "mainleftChart": browser2}
        
        # 直接创建和设置布局
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # layout.addWidget(browser)
        
        # 一次性设置WebEngine属性
        # settings = browser.settings()
        # settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        
        # 设置背景色和布局
        # browser.page().setBackgroundColor(QtCore.Qt.white)
        self.headerFrame.setLayout(layout)
        
        # 直接创建和设置布局
        layout2 = QtWidgets.QVBoxLayout()
        layout2.setContentsMargins(0, 0, 0, 0)
        layout2.setSpacing(0)
        # layout2.addWidget(browser)
        
        # 一次性设置WebEngine属性
        # settings2 = browser2.settings()
        # settings2.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        
        # 设置背景色和布局
        # browser2.page().setBackgroundColor(QtCore.Qt.white)
        self.mainLeftFrame.setLayout(layout2)


    def init_ui_controls(self):
        """初始化UI控件"""
        logger.debug("[INIT] 开始初始化UI控件...")
        
        logger.debug("[INIT] 初始化UI指数成交额组件...")
        # 创建交易量图表Widget
        self.index_chart = IndexTradingVolumeChartWidget()
        
        # 获取headerFrame的布局
        header_layout = self.headerFrame.layout()
        
        # 将交易量图表添加到headerFrame布局中
        header_layout.addWidget(self.index_chart)
        
        logger.debug("[INIT] 已将指数交易量图表添加到headerFrame")

        
        logger.debug("[INIT] 初始化UI概念板块成交额组件...")
        # 创建交易量图表Widget
        self.mainLeftChart = ContractTradingVolumeChartWidget()
        
        # 获取headerFrame的布局
        mainLeft_layout = self.mainLeftFrame.layout()
        
        # 将交易量图表添加到headerFrame布局中
        mainLeft_layout.addWidget(self.mainLeftChart)
        
        logger.debug("[INIT] 已将个股交易量图表添加到mainLeft_layout")

        
        logger.debug("[INIT] 初始化UI概念板块列表组件...")
        # 检查布局是否存在
        # contractListLayout = self.contractListView.layout()
        layout2 = QtWidgets.QVBoxLayout()
        layout2.setContentsMargins(0, 0, 0, 0)
        layout2.setSpacing(0)
            
        # 创建并添加ConceptListWidget
        self.concept_list = ConceptListWidget()
        layout2.addWidget(self.concept_list)
        
        self.contractListView.setLayout(layout2)
        self.concept_list.concept_selected.connect(self.on_concept_selected)
        self.on_concept_selected(ConceptDataUtil.concept_list().iloc[0]['concept_code'])
        logger.info("[INIT] UI controls initialized")

    def on_concept_selected(self, concept_code: str):
        """处理概念选择事件"""
        logger.info(f"[EVENT] 选中概念: {concept_code}")
        name = ConceptDataUtil.get_concept_name(concept_code)
        self.mainLeftChart.update_symbol(concept_code, name)

    def cleanup_threads(self):
        """清理所有运行的线程"""
        # 停止数据服务线程
        if hasattr(self, 'history_service'):
            self.history_service._is_running = False
            self.history_service.quit()
            self.history_service.wait()
        
        if hasattr(self, 'trading_day_service'):
            self.trading_day_service._is_running = False 
            self.trading_day_service.quit()
            self.trading_day_service.wait()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 清理图表组件的线程
        self.index_chart.cleanup_threads()
        self.mainLeftChart.cleanup_threads()
        event.accept()

# 程序入口
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    window.cleanup_threads()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()