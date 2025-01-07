import sys
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from pyecharts import options as opts
from pyecharts.charts import Line
import pandas as pd
from loguru import logger

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

        # 创建交易量图表Widget
        self.volume_chart = TradingVolumeChartWidget()
        
        # 获取headerFrame的布局
        header_layout = self.headerFrame.layout()
        
        # 将交易量图表添加到headerFrame布局中
        header_layout.addWidget(self.volume_chart)
        
        logger.debug("[INIT] 已将交易量图表添加到headerFrame")

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