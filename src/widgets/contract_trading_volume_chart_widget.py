from datetime import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from pyecharts import options as opts
from pyecharts.charts import Line
import pandas as pd
from loguru import logger
from typing import Callable
from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
from loguru import logger
from constants import REFRESH_TIME_POINT_5M, TRADING_TIME_POINT_5M
from utils import five_min_kline_service as kline_service
from utils.trading_day_util import TradingDayUtil

class ContractTradingVolumeChartWidget(QtWidgets.QWidget):
    """交易量图表Widget"""
    
    def __init__(self, parent=None, symbol=None):
        super().__init__(parent)
        logger.debug("[INIT] 开始初始化交易量图表Widget...")
        
        # 初始化订阅的指数列表
        self.title = f'{symbol} 5分钟成交量图'
        self.symbol = symbol
        logger.info(f"使用自定义订阅列表: {self.symbol}")
        
        # 设置大小策略
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        
        # 设置最小尺寸
        self.setMinimumSize(200, 150)  # 设置一个合理的最小尺寸
        
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
        
        # 设置浏览器的大小策略
        self.browser.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        
        # 设置浏览器的最小尺寸
        self.browser.setMinimumSize(200, 150)
        
        # 添加到布局
        self.layout.addWidget(self.browser)
        
    def init_services(self):
        """初始化数据服务"""
        logger.debug("[INIT] 开始初始化数据服务...")    
        # 创建服务实例
        self.history_service = ContractHistoryDataService(symbol=self.symbol)
        self.trading_day_service = ContractTradingDayDataService(symbol=self.symbol)
        
        # 连接信号
        self.history_service.data_update_signal.connect(self.on_history_daily_amount_ready)
        self.trading_day_service.data_update_signal.connect(self.on_trading_day_data_ready)
        # 启动服务
        self.history_service.start()
        self.trading_day_service.start()
        
    def create_line_chart(self, times, ave5, max5, min5, today_amount):
        """创建折线图"""
        line = (
            Line()
            .add_xaxis(times)
            .add_yaxis("AVE5", ave5, color="rgba(0, 255, 0, 0.4)", is_symbol_show=False)
            .add_yaxis("MAX5", max5, color="rgba(255, 0, 0, 0.4)", is_symbol_show=False)  
            .add_yaxis("MIN5", min5, color="rgba(0, 0, 255, 0.4)", is_symbol_show=False)
            .add_yaxis("TODAY", today_amount, color="black")
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=self.title,
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
        # logger.debug(f"[SIGNAL] Received: history_contract_data_ready \n{history_data}")
        self.history_data = history_data
        self.update_chart()  # 初始显示时today_amount为空列表
        
    def on_trading_day_data_ready(self, trading_data: pd.DataFrame = []):
        """处理实时数据就绪信号"""
        logger.debug("[SIGNAL] Received: trading_day_data_ready")
        
        self.latest_trading_day_data = trading_data['display_amount'].tolist()
        self.update_chart()
            
    def update_chart(self):
        """更新图表"""
        logger.debug(f"[UPDATE] 更新图表")
        if self.history_data is None:
            return
            
        # 创建图表
        chart = self.create_line_chart(
            times=self.history_data.index.str[11:16].tolist(),
            ave5=self.history_data['AVE5'].tolist(),
            max5=self.history_data['MAX5'].tolist(),
            min5=self.history_data['MIN5'].tolist(),
            today_amount=self.latest_trading_day_data
        )
        
        # 设置图表大小
        size = self.size()
        chart.width = f"{size.width()}px"
        chart.height = f"{size.height()}px"
        
        # 保存图表引用
        self.line = chart
        
        # 渲染图表
        chart.render("contract_trading_volume_chart.html")
        self.browser.load(QtCore.QUrl.fromLocalFile(
            str(QtCore.QDir.current().absoluteFilePath("contract_trading_volume_chart.html"))
        ))
            
    def resizeEvent(self, event):
        """处理大小改变事件"""
        super().resizeEvent(event)
        # logger.debug(f"[RESIZE] Widget大小变化: {self.size()}")
        self.update_chart_size()
        
    def update_chart_size(self):
        """更新图表大小"""
        if self.line is None:
            return
        
        logger.debug(f"[CHART] 更新图表大小: {self.size()}")
            
        size = self.size()
        current_width = f"{size.width()}px"
        current_height = f"{size.height()}px"
        
        # 检查大小是否真的改变
        if getattr(self.line, 'width', None) != current_width or \
           getattr(self.line, 'height', None) != current_height:
            
            # logger.debug(f"[CHART] 更新图表大小: {current_width} x {current_height}")
            
            # 更新图表大小
            self.line.width = current_width
            self.line.height = current_height
            
            # 重新渲染图表
            self.line.render("contract_trading_volume_chart.html")
            
            # 重新加载图表
            self.browser.load(QtCore.QUrl.fromLocalFile(
                str(QtCore.QDir.current().absoluteFilePath("contract_trading_volume_chart.html"))
            ))
            
            # 更新浏览器大小
            self.browser.setMinimumSize(size)

class ContractTradingDayDataService(QThread):

    error_occurred = pyqtSignal(str)
    data_update_signal = pyqtSignal(pd.DataFrame)

    def __init__(self, symbol:str=None):
        """初始化交易日数据服务"""
        super().__init__()
        logger.debug("[INIT] ContractTradingDayDataService initializing...")
        
        # 创建完整的时间索引（日期+时间）
        self.trading_day = TradingDayUtil.get_latest_trading_day()
        time_index = [f"{self.trading_day}{t}" for t in TRADING_TIME_POINT_5M]
        logger.info(f"[INIT] Trading data time index: {time_index}")
        
        # 创建数据存储DataFrame
        self.trading_data = pd.DataFrame(
            index=time_index,
            columns=['amount'],
            dtype=float
        )
        # 初始化数据为0
        self.trading_data.fillna(0.0, inplace=True)
        
        logger.debug(f"[INIT] Created trading data frame with shape: {self.trading_data.shape}")
        logger.debug(f"[INIT] Trading data sample: \n{self.trading_data}")
        
        self._is_running = True
        self.symbol = symbol  # 默认订阅的合约
        self.period = "5m"  # 5分钟K线周期
        
        logger.debug("[INIT] ContractTradingDayDataService initialized")

    def run(self):
        logger.debug("[THREAD] ContractTradingDayDataService thread started")
        self.update_trading_data()
        logger.debug("[THREAD] ContractTradingDayDataService retrieve trading data at first time")
        
        while self._is_running:
            try:
                # 获取当前时间
                current_time = datetime.now()
                current_time_str = current_time.strftime("%H%M%S")
                logger.debug(f"[THREAD] ContractTradingDayDataService 当前时间: {current_time_str}")
                
                # 找到下一个需要执行的时间点
                next_time = None
                for t in REFRESH_TIME_POINT_5M:
                    if t > current_time_str:
                        next_time = t
                        break
                
                if next_time:
                    # 计算需要等待的时间
                    next_time_obj = datetime.strptime(next_time, "%H%M%S")
                    next_time_today = current_time.replace(
                        hour=next_time_obj.hour,
                        minute=next_time_obj.minute,
                        second=next_time_obj.second
                    )
                    wait_seconds = (next_time_today - current_time).total_seconds()
                    
                    logger.info(f"[THREAD] ContractTradingDayDataService 等待至下一个时间点 {next_time}, 需等待 {wait_seconds} 秒")
                    
                    # 等待到下一个时间点
                    if wait_seconds > 0:
                        self.msleep(int(wait_seconds * 1000))
                    
                    # 执行更新
                    if self._is_running:  # 再次检查是否需要继续运行
                        logger.info(f"[THREAD] 开始更新交易数据,时间点: {next_time}")
                        self.update_trading_data()
                else:
                    # 如果没有下一个时间点,说明当天交易已结束
                    logger.info("[THREAD] 当天交易时间已结束")
                    break
                    
            except Exception as e:
                logger.exception("[ERROR] 执行定时任务失败")
                self.error_occurred.emit(f"执行定时任务失败: {str(e)}")
                break

    def update_trading_data(self):
        try:
            # 获取今日交易数据
            latest_5m_trading_data = kline_service.five_min_amount_latest(self.symbol)
            logger.info(f"[DEBUG] 获取到的最新数据: {self.symbol}\n{latest_5m_trading_data}")

            # 转换为亿元单位
            for index, row in latest_5m_trading_data.iterrows():
                latest_5m_trading_data.loc[index, 'display_amount'] = round(float(row['amount']) / 100000000, 2)
            # 移除未来时间的数据
            current_time = datetime.now()
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M')
            latest_5m_trading_data = latest_5m_trading_data[latest_5m_trading_data.index <= current_time_str]
            logger.info(f"[UPDATE] =======更新交易数据完成(单位:亿元): \n{latest_5m_trading_data}")
            
            # 发出数据更新信号
            self.data_update_signal.emit(latest_5m_trading_data)
            logger.debug(f"[SIGNAL] =======已发出数据更新信号 \n{latest_5m_trading_data}")
            
        except Exception as e:
            logger.exception("[ERROR] Thread execution failed")
            self.error_occurred.emit(f"线程执行失败: {str(e)}")

class ContractHistoryDataService(QThread):
    history_init_finished = pyqtSignal(dict)  # 历史数据初始化完成信号
    def __init__(self, symbol:str=None):
        super().__init__()
        logger.info("开始初始化 ContractHistoryDataService...")
        
        # 线程控制标志
        self._is_running = True
        
        # 初始化订阅的指数列表
        self.default_symbol = '600900'  # 概念板块或个股
        if symbol:
            self.symbol = symbol
            logger.info(f"使用自定义订阅: {self.symbol}")
        else:
            self.symbol = self.default_symbol
            logger.info(f"使用默认订阅列表: {self.symbol}")
        
        logger.info("已连接历史数据初始化完成信号")
        logger.info("ContractHistoryDataService 初始化完成")


    def run(self):
        """线程入口函数"""
        # 初始化历史数据
        self._init_history_data()

    
    def _init_history_data(self):
        """初始化历史数据"""
        logger.info("开始初始化历史数据...")
        self.history_data = kline_service.five_min_amount_history(self.symbol)
        # self.history_data dataframe sample
        # <class 'pandas.core.frame.DataFrame'>
        #                   volume            amount
        # trade_time                                
        # 2025-01-02 09:35  840389  657405578.000000
        # 2025-01-02 09:40  456483  356345332.000000
        # 2025-01-02 09:45  436005  332483924.000000
        # 2025-01-02 09:50  370229  300526474.000000

        # [240 rows x 3 columns]
        grouped_df = self.history_data.groupby(self.history_data.index.astype(str).str[:10])
        groups = []
        output_df = pd.DataFrame()
        
        # 计算5日均线等指标
        for date, daily5MinKline in grouped_df:
            logger.debug(f"date: {date}, daily5MinKline:\n{daily5MinKline.head()}")
            groups.append(daily5MinKline)
            length = len(groups)
            if length > 5:
                groups.pop(0)  # 移除最早一天的数据
            elif length < 5:
                continue

            rowCount = daily5MinKline.shape[0]
            # 计算统计指标
            ave5 = []  # 5日均线
            max5 = []  # 5日最高
            min5 = []  # 5日最低
            
            for index in range(rowCount):
                totalAmount = 0
                maxAmount = 0
                minAmount = 0
                for group in groups:
                    amount = group.iloc[index, 1]  # 已经是亿元单位
                    amountNum = float(amount)
                    totalAmount += amountNum
                    if amountNum > maxAmount:
                        maxAmount = amountNum
                    if amountNum < minAmount or minAmount == 0:
                        minAmount = amountNum
                ave5.append(round(totalAmount / len(groups), 2))  # 保留两位小数
                max5.append(round(maxAmount, 2))
                min5.append(round(minAmount, 2))
                logger.debug(f"index: {index}, ave5: {ave5[index]}, max5: {max5[index]}, min5: {min5[index]}")
            
            # 添加计算结果到数据框
            daily5MinKline['AVE5'] = ave5
            daily5MinKline['MAX5'] = max5
            daily5MinKline['MIN5'] = min5
            output_df = daily5MinKline
            
        # logger.debug(f"{date} 5m klines:\n{output_df}")
        logger.debug("[SIGNAL] Emitting history_daily_amount_ready")
        # Convert values from yuan to yi yuan (100 million yuan)
        output_df['AVE5'] = (output_df['AVE5'] / 100000000).round(2)
        output_df['MAX5'] = (output_df['MAX5'] / 100000000).round(2)
        output_df['MIN5'] = (output_df['MIN5'] / 100000000).round(2)
        self.data_update_signal.emit(output_df)
        logger.debug("[SIGNAL] Emitted history_daily_amount_ready")

    error_occurred = pyqtSignal(str)
    data_update_signal = pyqtSignal(pd.DataFrame)