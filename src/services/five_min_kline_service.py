# request url reference = https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.BK0612&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=60&fqt=1&end=20500101&lmt=60&_=1736309467992

import pandas as pd
from adata.common import requests

from trading_day_util import TradingDayUtil

def five_min_amount_history(code: str, days: int = 5):
    limit = days * 48
    prevTradeDays = TradingDayUtil.get_previous_trading_days(inDays = 1)
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.{code}&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=5&fqt=1&end={prevTradeDays[-1]}&lmt={limit}&_=1736309467992"
    res_json = requests.request('get', url, headers={}, proxies={}).json()
    # print(f"获取到的五分钟K线数据：{res_json}")
    result = pd.DataFrame(item.split(',') for item in res_json['data']['klines'])
    result.columns = ['trade_time', 'volume', 'amount']
    return result

def five_min_amount_latest(code: str):
    limit = 48
    url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=90.{code}&ut=fa5fd1943c7b386f172d6893dbfba10b&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf56%2Cf57&klt=5&fqt=1&end=20500101&lmt={limit}&_=1736309467992"
    res_json = requests.request('get', url, headers={}, proxies={}).json()
    # print(f"获取到的五分钟K线数据：{res_json}")
    result = pd.DataFrame(item.split(',') for item in res_json['data']['klines'])
    result.columns = ['trade_time', 'volume', 'amount']
    return result

result = five_min_amount_history(code='BK0623')
print(result)