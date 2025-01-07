from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from pyecharts import options as opts
from pyecharts.charts import Line
import pandas as pd
from loguru import logger

from services.history_data_service import HistoryDataService
from services.trading_day_data_service import TradingDayDataService

class TradingVolumeChartWidget(QtWidgets.QWidget):
    """交易量图表Widget"""
    
    def __init__(self, parent=None, symbols=None):
        super().__init__(parent)
        logger.debug("[INIT] 开始初始化交易量图表Widget...")
        
        # 设置大小策略
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        
        # 初始化订阅的指数列表
        self.default_symbols = ['000001.SH', '399001.SZ']  # 上证指数和深证成指
        if symbols:
            self.symbols = list(set(self.default_symbols + symbols))
            logger.info(f"使用自定义订阅列表: {self.symbols}")
        else:
            self.symbols = self.default_symbols.copy()
            logger.info(f"使用默认订阅列表: {self.symbols}")
        
        # 创建布局
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 初始化图表
        self.init_chart()
        
        # 初始化数据服务
        self.init_services()
        
        # 初始化数据属性
        self.history_data = None
        self.line = None
        
        logger.debug("[INIT] 交易量图表Widget初始化完成")
        
    def init_chart(self):
        """初始化图表"""
        # 创建WebEngine视图
        self.browser = QWebEngineView()
        
        # 设置WebEngine属性
        settings = QWebEngineSettings.defaultSettings()
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        
        # 设置背景色
        self.browser.page().setBackgroundColor(QtCore.Qt.white)
        
        # 添加到布局
        self.layout.addWidget(self.browser)
        
    def init_services(self):
        """初始化数据服务"""
        # 创建服务实例
        self.history_service = HistoryDataService(symbols=self.symbols)
        self.trading_day_service = TradingDayDataService()
        
        # 连接信号
        self.history_service.history_daily_amount_ready.connect(self.on_history_daily_amount_ready)
        self.trading_day_service.data_ready.connect(self.on_trading_day_data_ready)
        
        # 启动服务
        self.history_service.start()
        self.trading_day_service.start()
        
    def create_line_chart(self, times, ave5, max5, min5, today_amount):
        """创建折线图"""
        line = (
            Line()
            .add_xaxis(times)
            .add_yaxis("AVE5", ave5, color="green")
            .add_yaxis("MAX5", max5, color="red")
            .add_yaxis("MIN5", min5, color="blue")
            .add_yaxis("TODAY", today_amount, color="black")
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
        
    def on_history_daily_amount_ready(self, history_data: pd.DataFrame):
        """处理历史数据就绪信号"""
        logger.debug("[SIGNAL] Received: history_daily_amount_ready")
        self.history_data = history_data
        self.update_chart([])  # 初始显示时today_amount为空列表
        
    def on_trading_day_data_ready(self, trading_data: pd.DataFrame):
        """处理实时数据就绪信号"""
        logger.debug("[SIGNAL] Received: trading_day_data_ready")
        if self.history_data is not None:
            self.update_chart(trading_data['sum_amount'].tolist())
            
    def update_chart(self, today_amount):
        """更新图表"""
        if self.history_data is None:
            return
            
        # 创建图表
        chart = self.create_line_chart(
            times=self.history_data.index.str[8:13].tolist(),
            ave5=self.history_data['AVE5'].tolist(),
            max5=self.history_data['MAX5'].tolist(),
            min5=self.history_data['MIN5'].tolist(),
            today_amount=today_amount
        )
        
        # 设置图表大小
        size = self.size()
        chart.width = f"{size.width()}px"
        chart.height = f"{size.height()}px"
        
        # 保存图表引用
        self.line = chart
        
        # 渲染图表
        chart.render("temp_chart.html")
        self.browser.load(QtCore.QUrl.fromLocalFile(
            str(QtCore.QDir.current().absoluteFilePath("temp_chart.html"))
        ))
        
    def resizeEvent(self, event):
        """处理大小改变事件"""
        super().resizeEvent(event)
        logger.debug(f"[RESIZE] Widget大小变化: {self.size()}")
        self.update_chart_size()
        
    def update_chart_size(self):
        """更新图表大小"""
        if self.line is None:
            return
            
        size = self.size()
        current_width = f"{size.width()}px"
        current_height = f"{size.height()}px"
        
        # 检查大小是否真的改变
        if getattr(self.line, 'width', None) != current_width or \
           getattr(self.line, 'height', None) != current_height:
            
            logger.debug(f"[CHART] 更新图表大小: {current_width} x {current_height}")
            
            # 更新图表大小
            self.line.width = current_width
            self.line.height = current_height
            
            # 重新渲染图表
            self.line.render("temp_chart.html")
            
            # 重新加载图表
            self.browser.load(QtCore.QUrl.fromLocalFile(
                str(QtCore.QDir.current().absoluteFilePath("temp_chart.html"))
            ))
            
            # 更新浏览器大小
            self.browser.setMinimumSize(size)
            
    def resizeEvent(self, event):
        """处理大小改变事件"""
        super().resizeEvent(event)
        logger.debug(f"[RESIZE] Widget大小变化: {self.size()}")
        self.update_chart_size()
        
    def update_chart_size(self):
        """更新图表大小"""
        if self.line is None:
            return
            
        size = self.size()
        current_width = f"{size.width()}px"
        current_height = f"{size.height()}px"
        
        # 检查大小是否真的改变
        if getattr(self.line, 'width', None) != current_width or \
           getattr(self.line, 'height', None) != current_height:
            
            logger.debug(f"[CHART] 更新图表大小: {current_width} x {current_height}")
            
            # 更新图表大小
            self.line.width = current_width
            self.line.height = current_height
            
            # 重新渲染图表
            self.line.render("temp_chart.html")
            
            # 重新加载图表
            self.browser.load(QtCore.QUrl.fromLocalFile(
                str(QtCore.QDir.current().absoluteFilePath("temp_chart.html"))
            ))
            
            # 更新浏览器大小
            self.browser.setMinimumSize(size)
            
    def update_chart(self, today_amount):
        """更新图表"""
        if self.history_data is None:
            return
            
        # 创建图表
        chart = self.create_line_chart(
            times=self.history_data.index.str[8:12].tolist(),
            ave5=self.history_data['AVE5'].tolist(),
            max5=self.history_data['MAX5'].tolist(),
            min5=self.history_data['MIN5'].tolist(),
            today_amount=today_amount
        )
        
        # 设置图表大小
        size = self.size()
        chart.width = f"{size.width()}px"
        chart.height = f"{size.height()}px"
        
        # 保存图表引用
        self.line = chart
        
        # 渲染图表
        chart.render("temp_chart.html")
        self.browser.load(QtCore.QUrl.fromLocalFile(
            str(QtCore.QDir.current().absoluteFilePath("temp_chart.html"))
        )) 