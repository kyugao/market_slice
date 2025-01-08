from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
from loguru import logger
from constants import TRADING_TIME_POINT_5M
from trading_day_util import TradingDayUtil
from xtquant.xtdata import download_history_data, get_market_data_ex
from datetime import datetime, time

class TradingDayDataService(QThread):
    data_ready = pyqtSignal(pd.DataFrame)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        """初始化交易日数据服务
        
        Args:
            trading_day (str, optional): 交易日期，格式为YYYYMMDD。
                                       如果为None，则使用当前日期。
        """
        super().__init__()
        logger.debug("[INIT] TradingDayDataService starting...")
        
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
        
        logger.debug(f"[INIT] Created trading data frame with shape: {self.trading_data.shape}")
        logger.debug(f"[INIT] Trading data sample: \n{self.trading_data}")
        
        self._is_running = True
        self.symbols = ['000001.SH', '399001.SZ']  # 默认订阅的指数
        self.fields = ["amount"]
        self.period = "5m"  # 5分钟K线周期
        
        logger.debug("[INIT] TradingDayDataService initialized")

    def run(self):
        logger.debug("[THREAD] TradingDayDataService thread started")
        self.update_trading_data()
        logger.debug("[THREAD] TradingDayDataService retrieve trading data at first time")
        # 时间索引%H%M%S
        time_index = ["093501", "094001", "094501", "095001", "095501", "100001", "100501", "101001", "101501", "102001", "102501", "103001", "103501", "104001", "104501", "105001", "105501", "110001", "110501", "111001", "111501", "112001", "112501", "113001", "113501", "114001", "114501", "115001", "115501", "130001", "130501", "131001", "131501", "132001", "132501", "133001", "133501", "134001", "134501", "135001", "135501", "140001", "140501", "141001", "141501", "142001", "142501", "143001", "143501", "144001", "144501", "145001", "145501", "150001"]
        while self._is_running:
            try:
                # 获取当前时间
                current_time = datetime.now()
                current_time_str = current_time.strftime("%H%M%S")
                logger.debug(f"[THREAD] 当前时间: {current_time_str}")
                
                # 找到下一个需要执行的时间点
                next_time = None
                for t in time_index:
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
            download_history_data(self.symbols[0], self.period)
            download_history_data(self.symbols[1], self.period)
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
                logger.info(f"[INIT] 初始化交易数据: {symbol}\n{df}")
                field = 'sh_amount' if symbol == '000001.SH' else 'sz_amount'
                # 遍历每个时间点的数据
                for index, row in df.iterrows():
                    current_time = datetime.now().strftime("%H%M%S")
                    logger.debug(f"[UPDATE] 当前时间: {current_time}, 数据时间点: {index[-6:]}")
                    # 如果数据时间点大于当前时间,则跳出循环
                    if index[-6:] > current_time:
                        logger.debug(f"[UPDATE] 数据时间点 {index[-6:]} 大于当前时间 {current_time}, 跳过更新")
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
                        logger.debug(f"[UPDATE] Updated SH amount for {index}: {amount:.2f}")
                # 转换为亿元单位
                display_data = self.trading_data.where(cond=self.trading_data['sum_amount'] > 0).copy()
                display_data[['sh_amount', 'sz_amount', 'sum_amount']] = display_data[['sh_amount', 'sz_amount', 'sum_amount']] / 100000000
                logger.info(f"[UPDATE] 更新交易数据完成(单位:亿元): \n{display_data}")
            # 发出数据更新信号
            self.data_ready.emit(display_data)
            logger.debug("[SIGNAL] 已发出数据更新信号")
        except Exception as e:
            logger.exception("[ERROR] Thread execution failed")
            self.error_occurred.emit(f"线程执行失败: {str(e)}") 
