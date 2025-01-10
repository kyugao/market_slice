from typing import Callable
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from pyecharts import options as opts
from pyecharts.charts import Line
import pandas as pd
from loguru import logger

from PyQt5.QtCore import QThread, pyqtSignal
from constants import REFRESH_TIME_POINT_5M, TRADING_TIME_POINT_5M
from xtquant.xtdata import get_market_data_ex, download_history_data
import pandas as pd
from datetime import datetime
from loguru import logger
from utils.trading_day_util import TradingDayUtil

class IndexTradingVolumeChartWidget(QtWidgets.QWidget):

    symbols = ["000001.SH", "399001.SZ"]
    title = "沪深5m成交量对比"
    """指数交易量图表Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("[INIT] 开始初始化指数5m交易量图表...")
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
        # 创建服务实例
        self.history_service = HistoryDataService(symbols=self.symbols)
        self.trading_day_service = TradingDayDataService()
        
        # 连接信号
        self.history_service.history_daily_amount_ready.connect(self.on_history_daily_amount_ready)
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
        logger.debug("[SIGNAL] Received: history_daily_amount_ready")
        self.history_data = history_data
        self.update_chart()  # 初始显示时today_amount为空列表
        
    def on_trading_day_data_ready(self, trading_data: pd.DataFrame):
        """处理实时数据就绪信号"""
        logger.debug("[SIGNAL] Received: trading_day_data_ready")
        self.latest_trading_day_data = trading_data['sum_amount'].tolist()
        self.update_chart()
            
    def update_chart(self):
        """更新图表"""
        if self.history_data is None:
            return
            
        # 创建图表
        chart = self.create_line_chart(
            times=self.history_data.index.str[8:13].tolist(),
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
        chart.render("temp_chart.html")
        self.browser.load(QtCore.QUrl.fromLocalFile(
            str(QtCore.QDir.current().absoluteFilePath("temp_chart.html"))
        ))
            
    def resizeEvent(self, event):
        """处理大小改变事件"""
        super().resizeEvent(event)
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
            
            # logger.debug(f"[CHART] 更新图表大小: {current_width} x {current_height}")
            
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

class HistoryDataService(QThread):
    # 定义信号用于线程间通信
    data_ready = pyqtSignal(pd.DataFrame)  # 数据准备完成信号
    error_occurred = pyqtSignal(str)  # 错误发生信号
    history_ready = pyqtSignal(pd.DataFrame)  # 历史数据准备完成信号
    history_init_finished = pyqtSignal(dict)  # 历史数据初始化完成信号
    history_daily_amount_ready = pyqtSignal(pd.DataFrame)  # 每日成交量数据准备完成信号
    latest_trading_day_ready = pyqtSignal(str)
    
    def __init__(self, symbols=None):
        super().__init__()
        logger.info("开始初始化 HistoryDataService...")
        
        # 线程控制标志
        self._is_running = True
        
        # 初始化订阅的指数列表
        self.default_symbols = ['000001.SH', '399001.SZ']  # 上证指数和深证成指
        if symbols:
            self.symbols = list(set(self.default_symbols + symbols))
            logger.info(f"使用自定义订阅列表: {self.symbols}")
        else:
            self.symbols = self.default_symbols.copy()
            logger.info(f"使用默认订阅列表: {self.symbols}")
        
        # 设置需要获取的数据字段
        self.fields = ["open", "close", "high", "low", "volume", "amount"]
        logger.info(f"初始化数据字段: {self.fields}")
        
        # 设置K线周期为5分钟
        self.period = "5m"
        logger.info(f"设置K线周期: {self.period}")
        
        # 历史数据缓存
        self.history_data = pd.DataFrame()
        
        # 初始化时间范围
        self._init_time_range()
        
        # 连接历史数据初始化完成信号到对应的处理函数
        self.history_init_finished.connect(self.on_history_init_finished)
        logger.info("已连接历史数据初始化完成信号")
        logger.info("HistoryDataService 初始化完成")

    def run(self):
        """线程入口函数"""
        # 初始化历史数据
        self._init_history_data()

    
    def _init_history_data(self):
        """初始化历史数据"""
        logger.info("开始初始化历史数据...")
        try:
            # 获取过去5个交易日
            self.trading_days = TradingDayUtil.get_previous_trading_days(inDays=5)
            
            if not self.trading_days:
                raise Exception("未能获取到有效的交易日期")
                
            logger.info(f"开始获取历史数据: start_time={self.trading_days[0]}, end_time={self.trading_days[-1]}")
            
            # 获取市场数据
            market_data = get_market_data_ex(
                field_list=self.fields,
                stock_list=self.symbols,
                period=self.period,
                start_time=self.trading_days[0],
                end_time=self.trading_days[-1]
            )
            
            logger.debug(f"获取到的市场数据: {market_data}")
            
            # 检查每个合约的数据完整性
            for symbol, df in market_data.items():
                logger.info(f"检查指数 {symbol} 的历史数据")
                logger.debug(f"数据概览:\n头部:\n{df.head()}\n尾部:\n{df.tail()}")

                # 检查每个交易日的数据完整性
                for trading_day in self.trading_days:
                    daily_mask = df.index.str.startswith(trading_day)
                    daily_data = df[daily_mask]
                    records_count = len(daily_data)
                    
                    logger.info(f"{symbol} 在 {trading_day} 的数据记录数: {records_count}")
                    
                    # 如果数据不完整（少于48个5分钟K线），则下载补充
                    if records_count < 48:
                        logger.warning(f"{symbol} 在 {trading_day} 数据不完整,开始补充下载")
                        download_history_data(symbol, self.period, trading_day, trading_day)
            
            # 更新历史数据缓存
            self.history_data = get_market_data_ex(
                field_list=self.fields,
                stock_list=self.symbols,
                period=self.period,
                start_time=self.trading_days[0],
                end_time=self.trading_days[-1]
            )
            
            logger.info("历史数据初始化完成")
            logger.info("准备发送历史数据初始化完成信号")
            
            self.history_init_finished.emit(self.history_data)
            logger.info("已发送历史数据初始化完成信号")
            
        except Exception as e:
            logger.exception(f"初始化历史数据失败: {str(e)}")
            self.error_occurred.emit(f"初始化历史数据失败: {str(e)}")

    def _init_time_range(self):
        """初始化查询时间范围"""
        now = datetime.now()
        self.current_date = now.strftime("%Y%m%d")
        logger.info(f"初始化时间范围: current_date={self.current_date}")

    def on_history_init_finished(self, historyData: dict):
        """历史数据初始化完成后的处理
        
        Args:
            historyData (pd.DataFrame): 合约历史数据 {symbol1: pd.DataFrame, symbol2: pd.DataFrame, ...}
        """
        logger.info("接收到历史数据初始化完成信号，开始后续处理...")
        
        # 创建输出数据框
        output_df = pd.DataFrame()
        for symbol, data in historyData.items():
            # 合并上证和深证数据，计算总成交量
            for index, row in data.iterrows():
                # 将金额转换为亿元单位
                output_df.loc[index, f'{symbol}_amount'] = row['amount'] / 100000000
        output_df["sum_amount"] = output_df.sum(axis=1)

        logger.info(f"output_df:\n{output_df.sample()}")

        # 按日期分组
        grouped_df = output_df.groupby(output_df.index.astype(str).str[:8])
        groups = []
        output_df = pd.DataFrame()
        
        # 计算5日均线等指标
        for date, daily5MinKline in grouped_df:
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
                    amount = group.iloc[index, 2]  # 已经是亿元单位
                    totalAmount += amount
                    if amount > maxAmount:
                        maxAmount = amount
                    if amount < minAmount or minAmount == 0:
                        minAmount = amount
                ave5.append(round(totalAmount / len(groups), 2))  # 保留两位小数
                max5.append(round(maxAmount, 2))
                min5.append(round(minAmount, 2))
                logger.debug(f"index: {index}, ave5: {ave5[index]}, max5: {max5[index]}, min5: {min5[index]}")
            
            # 添加计算结果到数据框
            daily5MinKline['AVE5'] = ave5
            daily5MinKline['MAX5'] = max5
            daily5MinKline['MIN5'] = min5
            output_df = daily5MinKline
            
        logger.debug(f"{date} 5m klines:\n{output_df.sample()}")
        logger.debug("[SIGNAL] Emitting history_daily_amount_ready")
        self.history_daily_amount_ready.emit(output_df)
        logger.debug("[SIGNAL] Emitted history_daily_amount_ready")


class TradingDayDataService(QThread):
    
    def __init__(self):
        """初始化交易日数据服务
        
        Args:
            trading_day (str, optional): 交易日期，格式为YYYYMMDD。
                                       如果为None，则使用当前日期。
        """
        super().__init__()
        
        # 设置交易日期
        self.trading_day = TradingDayUtil.get_latest_trading_day()
        logger.info(f"[INIT] Trading day set to: {self.trading_day}")
        
        # 创建完整的时间索引（日期+时间）
        time_index = [f"{self.trading_day}{t}" for t in TRADING_TIME_POINT_5M]
        logger.info(f"[INIT] Trading data time index: {time_index}")
        # 创建数据存储DataFrame
        self.trading_data = pd.DataFrame(
            index=time_index,
            columns=['sh_amount', 'sz_amount', 'sum_amount'],
            dtype=float
        )
        # 初始化数据为0
        self.trading_data.fillna(0.0, inplace=True)
        
        self._is_running = True
        self.symbols = ['000001.SH', '399001.SZ']  # 默认订阅的指数
        self.fields = ["amount"]
        self.period = "5m"  # 5分钟K线周期
        
        logger.debug("[INIT] TradingDayDataService initialized")

    error_occurred = pyqtSignal(str)
    data_update = "data_update"
    data_update_signal = pyqtSignal(pd.DataFrame)
    
    def emit(self, *args, **kwargs):
        """发射信号"""
        self.data_update_signal.emit(*args, **kwargs)
        logger.debug("[SIGNAL] 已发出数据更新信号")

    def run(self):
        logger.debug("[THREAD] TradingDayDataService thread started")
        self.update_trading_data()
        # 时间索引%H%M%S
        while self._is_running:
            try:
                # 获取当前时间
                current_time = datetime.now()
                current_time_str = current_time.strftime("%H%M%S")
                
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
                    
                    logger.info(f"[THREAD] 等待至下一个时间点 {next_time}, 需等待 {wait_seconds} 秒")
                    
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
            download_history_data(self.symbols[0], self.period, incrementally=True)
            download_history_data(self.symbols[1], self.period, incrementally=True)
            # 获取今日交易数据, 并初始化self.trading_data
            latest_5m_trading_data = get_market_data_ex(
                field_list=self.fields,
                stock_list=self.symbols,
                period=self.period,
                start_time=self.trading_day,
                end_time=self.trading_day
            )
            # 初始化交易数据
            for symbol, df in latest_5m_trading_data.items():
                # logger.info(f"[INIT] 初始化交易数据: {symbol}\n{df}")
                field = 'sh_amount' if symbol == '000001.SH' else 'sz_amount'
                # 遍历每个时间点的数据
                for index, row in df.iterrows():
                    current_time = datetime.now().strftime("%H%M%S")
                    # 如果数据时间点大于当前时间,则跳出循环
                    if index[-6:] > current_time:
                        break
                    # 去掉末尾秒值
                    index = index[:-2] if len(index) > 12 else index
                    # 获取当前时间
                    if index in self.trading_data.index:
                        amount = row['amount']
                        self.trading_data.loc[index, field] = amount
                        # 重新计算总和
                        self.trading_data.loc[index, 'sum_amount'] = (
                            self.trading_data.loc[index, 'sh_amount'] + 
                            self.trading_data.loc[index, 'sz_amount']
                        )
                # 转换为亿元单位
                display_data = self.trading_data.where(cond=self.trading_data['sum_amount'] > 0).copy()
                display_data[['sh_amount', 'sz_amount', 'sum_amount']] = display_data[['sh_amount', 'sz_amount', 'sum_amount']] / 100000000
                # logger.info(f"[UPDATE] 更新交易数据完成(单位:亿元): \n{display_data}")
            # 发出数据更新信号
            self.emit(display_data)
            logger.debug(f"[SIGNAL] 已发出数据更新信号")
        except Exception as e:
            logger.exception("[ERROR] Thread execution failed")
            self.error_occurred.emit(f"线程执行失败: {str(e)}") 
