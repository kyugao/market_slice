from loguru import logger
import pandas as pd
import requests
from utils.trading_day_util import TradingDayUtil

def five_min_sh_amount_history(days: int = 5):
    limit = days * 48
    prevTradeDays = TradingDayUtil.get_previous_trading_days(inDays = 1)
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.000001&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=5&fqt=1&end={prevTradeDays[-1]}&lmt={limit}&_=1736309467992"
    logger.debug(f"请求五分钟K线数据：{url}")
    res_json = requests.request('get', url, headers={}, proxies={}).json()
    print(f"获取到的五分钟K线数据：{res_json}")
    result = pd.DataFrame(item.split(',') for item in res_json['data']['klines'])
    result.columns = ['trade_time', 'volume', 'amount']
    result.set_index('trade_time', inplace=True)
    return result

def five_min_sh_amount_latest():
    limit = 48
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.000001&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=5&fqt=1&end=20500101&lmt={limit}&_=1736309467992"
    res_json = requests.request('get', url, headers={}, proxies={}).json()
    # print(f"获取到的五分钟K线数据：{res_json}")
    result = pd.DataFrame(item.split(',') for item in res_json['data']['klines'])
    result.columns = ['trade_time', 'volume', 'amount']
    result.set_index('trade_time', inplace=True)
    # 获取最后一天的日期
    last_date = result.index.str[:10].max()
    # 筛选最后一天的数据
    result = result[result.index.str[:10] == last_date]
    logger.debug(f"[DEBUG] 获取到的五分钟K线数据: \n{result}")
    return result

def five_min_sz_amount_history(days: int = 5):
    limit = days * 48
    prevTradeDays = TradingDayUtil.get_previous_trading_days(inDays = 1)
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=0.399001&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=5&fqt=1&end={prevTradeDays[-1]}&lmt={limit}&_=1736309467992"
    logger.debug(f"请求五分钟K线数据：{url}")
    res_json = requests.request('get', url, headers={}, proxies={}).json()
    print(f"获取到的五分钟K线数据：{res_json}")
    result = pd.DataFrame(item.split(',') for item in res_json['data']['klines'])
    result.columns = ['trade_time', 'volume', 'amount']
    result.set_index('trade_time', inplace=True)
    return result


def five_min_sz_amount_latest():
    limit = 48
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=0.399001&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=5&fqt=1&end=20500101&lmt={limit}&_=1736309467992"
    res_json = requests.request('get', url, headers={}, proxies={}).json()
    # print(f"获取到的五分钟K线数据：{res_json}")
    result = pd.DataFrame(item.split(',') for item in res_json['data']['klines'])
    result.columns = ['trade_time', 'volume', 'amount']
    result.set_index('trade_time', inplace=True)
    # 获取最后一天的日期
    last_date = result.index.str[:10].max()
    # 筛选最后一天的数据
    result = result[result.index.str[:10] == last_date]
    logger.debug(f"[DEBUG] 获取到的五分钟K线数据: \n{result.sample()}")
    return result
# stock:   https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&beg=0&end=20500101&ut=fa5fd1943c7b386f172d6893dbfba10b&rtntype=6&secid=0.300274&klt=5&fqt=1&cb=jsonp1737095273936
# concept: https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.{code}&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=5&fqt=1&end={prevTradeDays[-1]}&lmt={limit}&_=1736309467992


def five_min_amount_history(code: str, days: int = 5):
    limit = days * 48
    prevTradeDays = TradingDayUtil.get_previous_trading_days(inDays = 1)
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.{code}&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=5&fqt=1&end={prevTradeDays[-1]}&lmt={limit}&_=1736309467992"
    logger.debug(f"请求五分钟K线数据：{url}")
    res_json = requests.request('get', url, headers={}, proxies={}).json()
    # print(f"获取到的五分钟K线数据：{res_json}")
    result = pd.DataFrame(item.split(',') for item in res_json['data']['klines'])
    result.columns = ['trade_time', 'volume', 'amount']
    result.set_index('trade_time', inplace=True)
    return result

def five_min_amount_latest(code: str):
    limit = 48
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.{code}&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=5&fqt=1&end=20500101&lmt={limit}&_=1736309467992"
    res_json = requests.request('get', url, headers={}, proxies={}).json()
    # print(f"获取到的五分钟K线数据：{res_json}")
    result = pd.DataFrame(item.split(',') for item in res_json['data']['klines'])
    result.columns = ['trade_time', 'volume', 'amount']
    result.set_index('trade_time', inplace=True)
    # 获取最后一天的日期
    last_date = result.index.str[:10].max()
    # 筛选最后一天的数据
    result = result[result.index.str[:10] == last_date]
    logger.debug(f"[DEBUG] 获取到的五分钟K线数据: \n{result.tail(10)}")
    return result
