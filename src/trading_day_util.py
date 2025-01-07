from datetime import datetime, timedelta
from loguru import logger
from xtquant.xtdata import get_trading_dates
from typing import List, Optional

class TradingDayUtil:
    """交易日期工具类"""

    @staticmethod
    def get_previous_trading_days(inDays: int = 5, callback=None) -> List[str]:
        """获取过去n个交易日
        
        Args:
            n (int): 需要获取的交易日数量
            callback (callable, optional): 回调函数，用于接收最新交易日信息
            
        Returns:
            List[str]: 交易日列表，格式为YYYYMMDD。如果获取失败返回空列表
        """
        result = TradingDayUtil.get_trading_days(inDays+1)
        return result[0:-1]
    
    @staticmethod
    def get_trading_days(n: int = 30, callback=None) -> List[str]:
        """获取过去n个交易日
        
        Args:
            n (int): 需要获取的交易日数量
            callback (callable, optional): 回调函数，用于接收最新交易日信息
            
        Returns:
            List[str]: 交易日列表，格式为YYYYMMDD。如果获取失败返回空列表
        """
        logger.info(f"开始获取过去{n}个交易日...")
        try:
            # 设置查询时间范围
            today = datetime.now()
            start_date = (today - timedelta(days=30)).strftime("%Y%m%d")  
            end_date = (today).strftime("%Y%m%d")
            
            logger.info(f"查询交易日历: start_date={start_date}, end_date={end_date}")
            
            # 获取交易日历
            trading_days = get_trading_dates(
                market='SH',
                start_time=start_date,
                end_time=end_date
            )
            
            # 如果成功获取到交易日历且有回调函数，发送最新交易日信号
            if trading_days and callback:
                latest_day = datetime.fromtimestamp(trading_days[-1]/1000).strftime('%Y%m%d')
                logger.info(f"发送最新交易日信号: {latest_day}")
                callback(latest_day)
            
            if trading_days:
                last_n_days = trading_days[-n:]
                # 将时间戳转换为日期字符串
                result = [datetime.fromtimestamp(day/1000).strftime('%Y%m%d') for day in last_n_days]
                logger.info(f"获取到的交易日: {result}")
                return result
            
            logger.warning("未获取到交易日数据")
            return []
            
        except Exception as e:
            logger.exception(f"获取交易日历失败: {str(e)}")
            return []
            
    @staticmethod
    def get_latest_trading_day() -> Optional[str]:
        """获取最近的一个交易日
        
        Returns:
            Optional[str]: 交易日期，格式为YYYYMMDD。如果获取失败返回None
        """
        logger.info("开始获取最后一个交易日...")
        trading_days = TradingDayUtil.get_trading_days(1)
        if trading_days:
            latest_day = trading_days[0]
            logger.info(f"获取到最后一个交易日: {latest_day}")
            return latest_day
            
        logger.warning("未获取到最近交易日")
        return None 