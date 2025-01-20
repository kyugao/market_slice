from datetime import datetime
from loguru import logger
from typing import List
import requests
import pandas as pd

class TradingDayUtil:
    # 静态变量 trading_calendar_result
    trading_calendar_result = None
    """交易日期工具类"""

    @staticmethod
    def get_trading_calendar() -> pd.Series:
        if TradingDayUtil.trading_calendar_result is None:
            # https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.000001&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51&klt=101&fqt=1&end=20500101&lmt=60&_=1736309467992
            """获取交易日历"""
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.000001&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51&klt=101&fqt=1&end=20500101&lmt=200&_=1736309467992"
            logger.debug(f"请求市场日K线数据：{url}")
            res_json = requests.request('get', url, headers={}, proxies={}).json()
            print(f"获取到的日K线数：{res_json}")
            result = pd.DataFrame(item.split(',') for item in res_json['data']['klines'])
            result.columns = ['trade_time']
            result.set_index('trade_time', inplace=True)
            TradingDayUtil.trading_calendar_result = result.index
        return TradingDayUtil.trading_calendar_result
    
    @staticmethod
    def get_previous_trading_days(inDays: int = 5, format: str = "%Y%m%d") -> List[str]:
        """获取过去n个交易日
        
        Args:
            n (int): 需要获取的交易日数量
            callback (callable, optional): 回调函数，用于接收最新交易日信息
            
        Returns:
            List[str]: 交易日列表，格式为YYYYMMDD。如果获取失败返回空列表
        """
        calendar = TradingDayUtil.get_trading_calendar()
        results = calendar[-inDays-1:-1]
        # results = [item.strftime(format) for item in results]
        # 将YYYY-MM-DD格式转换为指定格式
        results = [datetime.strptime(date, "%Y-%m-%d").strftime(format) for date in results]
        return results
            
    @staticmethod
    def get_latest_trading_day(format: str = "%Y%m%d") -> str:
        """获取最近的一个交易日
        
        Returns:
            Optional[str]: 交易日期，格式为YYYYMMDD。如果获取失败返回None
        """
        logger.info("开始获取最后一个交易日...")
        calendar = TradingDayUtil.get_trading_calendar()
        result = datetime.strptime(calendar[-1], "%Y-%m-%d").strftime(format)
        return result

# 确保导出类
__all__ = ['TradingDayUtil']

# if __name__ == "__main__":
#     print(TradingDayUtil.get_previous_trading_days(inDays = 5))
#     print(TradingDayUtil.get_latest_trading_day())
