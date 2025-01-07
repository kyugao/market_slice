import sys
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from pyecharts import options as opts
from pyecharts.charts import Line
from history_data_service import HistoryDataService
from trading_day_data_service import TradingDayDataService
import pandas as pd
from loguru import logger

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
        
        # 初始化历史数据服务
        self.history_service = HistoryDataService()
        self.trading_day_data_service = TradingDayDataService()
        # 连接信号
        self.history_service.history_daily_amount_ready.connect(self.on_history_daily_amount_ready)
        logger.debug("[SIGNAL] Connected: history_daily_amount_ready -> on_history_daily_amount_ready")
        self.trading_day_data_service.data_ready.connect(self.on_trading_day_data_ready)
        logger.debug("[SIGNAL] Connected: data_ready -> on_trading_day_data_ready")
        
        # Connect resize event to update chart size
        self.headerFrame.installEventFilter(self)
        
        # Initialize line attribute
        self.line = None
        
        logger.debug("[INIT] 主窗口初始化完成")
        self.start_data_service()

    def init_echarts(self):
        """初始化echarts图表"""
        # 为每个Frame创建WebEngine视图
        self.browsers = {
            'first': QWebEngineView(),
        }
        
        # 预先创建布局对象
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 预先设置WebEngine属性
        settings = QWebEngineSettings.defaultSettings()
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        
        # 为每个Frame设置布局并禁用滚动条
        for frame, browser in zip([self.headerFrame], 
                                self.browsers.values()):
            browser.page().setBackgroundColor(QtCore.Qt.white)
            layout_copy = QtWidgets.QVBoxLayout()
            layout_copy.setContentsMargins(0, 0, 0, 0)
            layout_copy.setSpacing(0)
            layout_copy.addWidget(browser)
            frame.setLayout(layout_copy)

    def create_line_chart(self, times, ma5, max5, min5, today_amount):
        """创建折线图"""
        # 使用原始时间轴和数据,不进行采样
        line = (
            Line()
            .add_xaxis(times)
            .add_yaxis("MA5", ma5, color="green")  # 使用原始数据
            .add_yaxis("MAX5", max5, color="red")  # 使用原始数据 
            .add_yaxis("MIN5", min5, color="blue")  # 使用原始数据
            .add_yaxis("TODAY", today_amount, color="black")  # 使用原始数据
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title="5日成交量分时对比",
                    pos_left="center",
                    padding=[0, 0, 0, 40]
                ),
                xaxis_opts=opts.AxisOpts(
                    name="时间",
                    axislabel_opts=opts.LabelOpts()
                ),
                yaxis_opts=opts.AxisOpts(
                    name="成交额(亿元)", 
                    axislabel_opts=opts.LabelOpts(formatter="{value}"),
                    position="right"
                ),
                legend_opts=opts.LegendOpts(
                    pos_top="5%",
                    pos_left="center",
                    orient="horizontal"
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    formatter="{b} <br/> MA5: {c0}亿元 <br/>MAX5: {c1}亿元 <br/>MIN5: {c2}亿元 <br/>TODAY: {c3}亿元"
                )
            )
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
        )
        self.line = line
        return line

    def init_ui_controls(self):
        """初始化UI控件"""
        logger.debug("[INIT] 开始初始化UI控件...")

    def start_data_service(self):
        """启动历史数据服务"""
        logger.debug("[START] Starting background data service...")
        self.history_service.start()
        self.trading_day_data_service.start()
        logger.debug("[START] Background data service started")

    def on_trading_day_data_ready(self, trading_data: pd.DataFrame):
        logger.debug("[SIGNAL] trading_day_data_ready")
        # 创建图表
        chart = self.create_line_chart(
            times=self.history_data['time'].tolist(),
            ma5=self.history_data['MA5'].tolist(),
            max5=self.history_data['max5'].tolist(),
            min5=self.history_data['min5'].tolist(),
            today_amount=trading_data['sum_amount'].tolist()
        )
        
        # 生成HTML并显示在所有Frame中
        chart.render("temp_chart.html")
        # self.update_chart_size()
        
        # 获取Frame尺寸
        frame_size = self.headerFrame.size()
        chart.width = str(frame_size.width()) + "px"
        chart.height = str(frame_size.height()) + "px"
        
        # 为每个浏览器设置大小并加载图表
        for browser in self.browsers.values():
            browser.setMinimumSize(frame_size)
            browser.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding
            )
            browser.load(QtCore.QUrl.fromLocalFile(
                str(QtCore.QDir.current().absoluteFilePath("temp_chart.html"))
            ))
        
    def on_history_daily_amount_ready(self, history_data: pd.DataFrame):
        """处理每日成交量数据"""
        logger.debug("[SIGNAL] Received: history_daily_amount_ready")
        
        # 处理数据
        history_data['time'] = history_data.index.str[8:12]
        # 将时间格式从hhmm转换为hh:mm
        history_data['time'] = history_data['time'].apply(lambda x: f"{x[:2]}:{x[2:]}")
        
        self.history_data = history_data
        # 创建图表
        chart = self.create_line_chart(
            times=history_data['time'].tolist(),
            ma5=history_data['MA5'].tolist(),
            max5=history_data['max5'].tolist(),
            min5=history_data['min5'].tolist(),
            today_amount=[]
        )
        
        # 生成HTML并显示在所有Frame中
        chart.render("temp_chart.html")
        # self.update_chart_size()
        
        # 获取Frame尺寸
        frame_size = self.headerFrame.size()
        chart.width = str(frame_size.width()) + "px"
        chart.height = str(frame_size.height()) + "px"
        
        # 为每个浏览器设置大小并加载图表
        for browser in self.browsers.values():
            browser.setMinimumSize(frame_size)
            browser.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding
            )
            browser.load(QtCore.QUrl.fromLocalFile(
                str(QtCore.QDir.current().absoluteFilePath("temp_chart.html"))
            ))

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