from typing import Callable
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from loguru import logger

from PyQt5.QtCore import QThread, pyqtSignal
from constants import REFRESH_TIME_POINT_5M, TRADING_TIME_POINT_5M
from utils.five_min_kline_service import five_min_sh_amount_history, five_min_sz_amount_history, five_min_sh_amount_latest, five_min_sz_amount_latest
from datetime import datetime
from utils.trading_day_util import TradingDayUtil

class IndexTradingVolumeChartWidget(QtWidgets.QWidget):
    symbols = ["000001.SH", "399001.SZ"]
    title = "沪深5m成交量对比"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("[INIT] 开始初始化指数5m交易量图表...")
        
        # 设置大小策略
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        
        # 设置最小尺寸
        self.setMinimumSize(200, 150)
        
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
        
        logger.debug("[INIT] 交易量图表Widget初始化完成")
        
    def init_chart(self):
        """初始化图表"""
        # 创建Figure
        self.fig = Figure(facecolor='white')
        
        # 创建画布
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color:white;")
        
        # 添加到布局
        self.layout.addWidget(self.canvas)
        
        # 创建子图
        self.ax = self.fig.add_subplot(111)
        
    def create_line_chart(self, times, ave5, max5, min5, today_amount):
        """创建折线图"""
        # 清除现有图形
        self.ax.clear()
        
        # 绘制线条
        self.ax.plot(times, ave5, label='AVE5', color='green', alpha=0.4)
        self.ax.plot(times, max5, label='MAX5', color='red', alpha=0.4)
        self.ax.plot(times, min5, label='MIN5', color='blue', alpha=0.4)
        
        if today_amount:
            self.ax.plot(times[:len(today_amount)], today_amount, 
                        label='TODAY', color='black')
        
        # 设置标题和标签
        self.ax.set_title(self.title)
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('成交额(亿元)')
        
        # 设置图例
        self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
                      ncol=4, fancybox=True, shadow=True)
        
        # 旋转x轴标签
        self.ax.tick_params(axis='x', rotation=45)
        
        # 自动调整布局
        self.fig.tight_layout()
        
        # 重绘画布
        self.canvas.draw()
        
    def resizeEvent(self, event):
        """处理大小改变事件"""
        super().resizeEvent(event)
        self.fig.tight_layout()
        self.canvas.draw()
        
    def init_services(self):
        """初始化数据服务"""
        # 创建服务实例
        self.history_service = IndexHistoryDataService(symbols=self.symbols)
        self.trading_day_service = IndexTradingDayDataService()
        
        # 连接信号
        self.history_service.history_daily_amount_ready.connect(self.on_history_daily_amount_ready)
        self.trading_day_service.data_update_signal.connect(self.on_trading_day_data_ready)
        
        self.history_data = []
        self.latest_trading_day_data = []
        
        # 启动服务
        self.history_service.start()
        self.trading_day_service.start()
        
    def on_history_daily_amount_ready(self, history_data: pd.DataFrame):
        """处理历史数据就绪信号"""
        logger.debug("[SIGNAL] Received: history_daily_amount_ready")
        self.history_data = history_data
        self.update_chart()
        
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
        self.create_line_chart(
            times=self.history_data.index.str[11:16].tolist(),
            ave5=self.history_data['AVE5'].tolist(),
            max5=self.history_data['MAX5'].tolist(),
            min5=self.history_data['MIN5'].tolist(),
            today_amount=self.latest_trading_day_data
        )

class IndexHistoryDataService(QThread):
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
        
        # 连接历史数据初始化完成信号到对应的处理函数
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
            # 获取历史数据 sh_history_data, sz_history_data
            # 格式: trade_time, volume, amount
            # index column: trade_time
            sh_history_data = five_min_sh_amount_history(days=5)
            sz_history_data = five_min_sz_amount_history(days=5)
            
            logger.info("历史数据初始化完成")

            output_df = pd.DataFrame()
            # 以trade_time为index合并sh_history_data的amount列, 与sz_history_data的amount列 到output_df中, 分别记录为sh_amount, sz_amount
            # 在output_df中, 以trade_time为index, 以sh_amount, sz_amount为列
            # 合并上证和深证的成交额数据
            output_df = pd.DataFrame()
            output_df.index = sh_history_data.index
            output_df['sh_amount'] = sh_history_data['amount'].astype(float) / 100000000
            output_df['sz_amount'] = sz_history_data['amount'].astype(float) / 100000000
            # 计算sum_amount
            output_df['sum_amount'] = output_df['sh_amount'] + output_df['sz_amount']
            logger.info(f"output_df:\n{output_df}")

            # 按日期分组
            grouped_df = output_df.groupby(output_df.index.astype(str).str[:10])
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
            
        except Exception as e:
            logger.exception(f"初始化历史数据失败: {str(e)}")
            self.error_occurred.emit(f"初始化历史数据失败: {str(e)}")

class IndexTradingDayDataService(QThread):
    
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
                current_hour = current_time.hour
                current_minute = current_time.minute
                
                # 判断是否在交易时间内(9:00-15:01)
                if (current_hour == 9 and current_minute >= 0) or \
                   (current_hour > 9 and current_hour < 15) or \
                   (current_hour == 15 and current_minute <= 1):
                    
                    logger.debug(f"[THREAD] ContractTradingDayDataService 当前时间: {current_time_str}")
                    
                    # 执行更新
                    if self._is_running:
                        logger.info(f"[THREAD] 开始更新交易数据,时间点: {current_time_str}")
                        self.update_trading_data()
                    
                    # 等待30秒
                    self.msleep(30 * 1000)
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
            sh_latest_amount = five_min_sh_amount_latest()
            sz_latest_amount = five_min_sz_amount_latest()
            
            output_df = pd.DataFrame()
            # 以trade_time为index合并sh_history_data的amount列, 与sz_history_data的amount列 到output_df中, 分别记录为sh_amount, sz_amount
            # 在output_df中, 以trade_time为index, 以sh_amount, sz_amount为列
            # 合并上证和深证的成交额数据
            output_df = pd.DataFrame()
            output_df.index = sh_latest_amount.index
            output_df['sh_amount'] = sh_latest_amount['amount'].astype(float) / 100000000
            output_df['sz_amount'] = sz_latest_amount['amount'].astype(float) / 100000000
            
            # 计算sum_amount
            output_df['sum_amount'] = output_df['sh_amount'] + output_df['sz_amount']
            logger.info(f"output_df:\n{output_df}")

            self.emit(output_df)
            logger.debug(f"[SIGNAL] 已发出数据更新信号")
        except Exception as e:
            logger.exception("[ERROR] Thread execution failed")
            self.error_occurred.emit(f"线程执行失败: {str(e)}") 

# IndexHistoryDataService线程的测试方法
def test_index_history_data_service():
    service = IndexHistoryDataService()
    service.start()
    service.wait()
    service.terminate()
    service.quit()

if __name__ == "__main__":
    test_index_history_data_service()
