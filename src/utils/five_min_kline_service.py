from loguru import logger
import pandas as pd
import requests
from utils.trading_day_util import TradingDayUtil

def five_min_sh_amount_history(days: int = 5):
    return min_amount_history('000001', '1', 5)

def five_min_sh_amount_latest():
    return min_amount_latest('000001', '1', 5)

def five_min_sz_amount_history(days: int = 5):
    return min_amount_history('399001', '0', 5)


def five_min_sz_amount_latest():
    return min_amount_latest('399001', '0', 5)

def five_min_amount_history(code: str, prefix: str, days: int = 5):
    return min_amount_history(code, prefix, days)

def five_min_amount_latest(code: str, prefix: str):
    return min_amount_latest(code, prefix, 5)

def min_amount_history(code: str, prefix: str, ktype: int, days: int = 5):
    limit = days * 48
    prevTradeDays = TradingDayUtil.get_previous_trading_days(inDays = 1)
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={prefix}.{code}&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=5&fqt=1&end={prevTradeDays[-1]}&lmt={limit}&_=1736309467992"
    logger.debug(f"请求五分钟K线数据：{url}")
    res_json = requests.request('get', url, headers={}, proxies={}).json()
    print(f"获取到的五分钟K线数据：{res_json}")
    result = pd.DataFrame(item.split(',') for item in res_json['data']['klines'])
    result.columns = ['trade_time', 'volume', 'amount']
    result.set_index('trade_time', inplace=True)
    return result

def min_amount_latest(code: str, prefix: str, ktype: int):
    limit = int(240/ktype)
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={prefix}.{code}&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt={ktype}&fqt=1&end=20990101&lmt={limit}&_=1736309467992"
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