from PyQt5.QtCore import QThread, pyqtSignal
from matplotlib import pyplot as plt
import numpy as np
from xtquant.xtdata import get_trading_dates, get_market_data_ex, get_market_data, download_history_data
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from trading_day_util import TradingDayUtil

class HistoryDataService(QThread):
    # 定义信号用于线程间通信
    data_ready = pyqtSignal(pd.DataFrame)  # 数据准备完成信号
    error_occurred = pyqtSignal(str)  # 错误发生信号
    history_ready = pyqtSignal(pd.DataFrame)  # 历史数据准备完成信号
    history_init_finished = pyqtSignal(pd.DataFrame, pd.DataFrame)  # 历史数据初始化完成信号
    history_daily_amount_ready = pyqtSignal(pd.DataFrame)  # 每日成交量数据准备完成信号
    latest_trading_day_ready = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        logger.info("开始初始化 HistoryDataService...")
        
        # 线程控制标志
        self._is_running = True
        
        # 初始化默认订阅的指数列表
        self.default_symbols = ['000001.SH', '399001.SZ']  # 上证指数和深证成指
        self.symbols = self.default_symbols.copy()
        logger.info(f"初始化订阅列表: {self.symbols}")
        
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
            
            # 检查每个指数的数据完整性
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
            
            # 分别获取上证和深证数据
            sh_data = market_data['000001.SH']
            sz_data = market_data['399001.SZ']
            self.history_init_finished.emit(sh_data, sz_data)
            logger.info("已发送历史数据初始化完成信号")
            
        except Exception as e:
            logger.exception(f"初始化历史数据失败: {str(e)}")
            self.error_occurred.emit(f"初始化历史数据失败: {str(e)}")

    def _init_time_range(self):
        """初始化查询时间范围"""
        now = datetime.now()
        self.current_date = now.strftime("%Y%m%d")
        logger.info(f"初始化时间范围: current_date={self.current_date}")

    def on_history_init_finished(self, shData: pd.DataFrame, szData: pd.DataFrame):
        """历史数据初始化完成后的处理
        
        Args:
            shData (pd.DataFrame): 上证指数数据
            szData (pd.DataFrame): 深证成指数据
        """
        logger.info("接收到历史数据初始化完成信号，开始后续处理...")
        
        # 创建输出数据框
        output_df = pd.DataFrame()

        # 合并上证和深证数据，计算总成交量
        for index, row in shData.iterrows():
            sh_row = row
            sz_row = szData.loc[index]
            # 将金额转换为亿元单位
            output_df.loc[index, 'totalAmount'] = (sh_row['amount'] + sz_row['amount']) / 100000000
            output_df.loc[index, 'sh_amount'] = sh_row['amount'] / 100000000
            output_df.loc[index, 'sz_amount'] = sz_row['amount'] / 100000000

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
            ma5 = []  # 5日均线
            max5 = []  # 5日最高
            min5 = []  # 5日最低
            
            for index in range(rowCount):
                totalAmount = 0
                maxAmount = 0
                minAmount = 0
                for group in groups:
                    amount = group.iloc[index, 0]  # 已经是亿元单位
                    totalAmount += amount
                    if amount > maxAmount:
                        maxAmount = amount
                    if amount < minAmount or minAmount == 0:
                        minAmount = amount
                ma5.append(round(totalAmount / len(groups), 2))  # 保留两位小数
                max5.append(round(maxAmount, 2))
                min5.append(round(minAmount, 2))
                logger.info(f"index: {index}, ma5: {ma5[index]}, max5: {max5[index]}, min5: {min5[index]}")
            
            # 添加计算结果到数据框
            daily5MinKline['MA5'] = ma5
            daily5MinKline['max5'] = max5
            daily5MinKline['min5'] = min5
            output_df = daily5MinKline
            
        logger.info(f"{date} 5m klines:\n{output_df}")
        logger.debug("[SIGNAL] Emitting history_daily_amount_ready")
        self.history_daily_amount_ready.emit(output_df)
        logger.debug("[SIGNAL] Emitted history_daily_amount_ready")

