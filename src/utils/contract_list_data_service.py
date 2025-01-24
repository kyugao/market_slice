from enum import Enum
from loguru import logger
import pandas as pd
import requests
from threading import Lock
# concept_list result sample
# 	concept_code	index_code	name	source
# 0	BK0623	BK0623	海洋经济	东方财富
# 1	BK0501	BK0501	次新股	东方财富
# 2	BK0971	BK0971	注册制次新股	东方财富
# 3	BK1122	BK1122	血氧仪	东方财富
# 全局变量,用于缓存概念列表数据

# 东财fs说明
# m: 板块
# t: 类型（1:地域，2:行业，3:概念）

# 创建一个枚举，名为板块类型，值分别为1,2,3，对应地域，行业，概念
class ContractType(Enum):
    Region = 1
    Industry = 2
    Concept = 3
    Stock = 4

    def get_cn_name(self):
        """根据枚举值返回对应的中文名称"""
        if self.value == 1:
            return "地域"
        elif self.value == 2:
            return "行业"
        elif self.value == 3:
            return "概念"
        elif self.value == 4:
            return "股票"
        else:
            return "未知类型"

class ContractUtil:
    concept_list = None
    industry_list = None
    region_list = None
    stock_list = None
    contract_list = None
    lock = Lock()

    def init_data():
        ContractUtil.concept_list = ContractUtil.get_concept_list()
        ContractUtil.industry_list = ContractUtil.get_industry_list()
        ContractUtil.region_list = ContractUtil.get_region_list()
        ContractUtil.stock_list = ContractUtil.get_stock_list()
        # 添加概念列表
        ContractUtil.concept_list['contract_type'] = ContractType.Concept.get_cn_name()
        # 添加行业列表
        ContractUtil.industry_list['contract_type'] = ContractType.Industry.get_cn_name()
        # 添加地域列表
        ContractUtil.region_list['contract_type'] = ContractType.Region.get_cn_name()
        # 添加地域列表
        ContractUtil.stock_list['contract_type'] = ContractType.Stock.get_cn_name()
        # 合并
        ContractUtil.contract_list = pd.concat([ContractUtil.concept_list, ContractUtil.industry_list, ContractUtil.region_list, ContractUtil.stock_list])

    @staticmethod
    def get_contract_data():
        # 下面if逻辑执行时，为多线程同步调用，只有一个线程能进入
        return ContractUtil.contract_list
    
    @staticmethod
    def get_contract_name(bk_code: str):
        if ContractUtil.contract_list is None:
            ContractUtil.get_contract_data()
        return ContractUtil.contract_list.loc[bk_code]['name']
    
    @staticmethod
    def get_contract_prefix(bk_code: str):
        if ContractUtil.contract_list is None:
            ContractUtil.get_contract_data()
        return ContractUtil.contract_list.loc[bk_code]['prefix']
    
    # 东财股票数据列表
    # https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A0%2Bt%3A6%2Cm%3A0%2Bt%3A80%2Cm%3A1%2Bt%3A2%2Cm%3A1%2Bt%3A23%2Cm%3A0%2Bt%3A81%2Bs%3A2048&fields=f12%2Cf13%2Cf14&pn=1&pz=8000
    def get_stock_list():
        url = "https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A0%2Bt%3A6%2Cm%3A0%2Bt%3A80%2Cm%3A1%2Bt%3A2%2Cm%3A1%2Bt%3A23%2Cm%3A0%2Bt%3A81%2Bs%3A2048&fields=f12%2Cf13%2Cf14&pn=1&pz=8000"
        res_json = requests.request('get', url, headers={}, proxies={}).json()
        result = pd.DataFrame()
        for num, row in res_json['data']['diff'].items():
            result = pd.concat([result, pd.DataFrame(row, index=[0])], ignore_index=True)
        result.columns = ['code', 'prefix', 'name']
        result.set_index('code', inplace=True)
        return result
        
    # 东财地域列表
    # https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A1%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=1&pz=500
    def get_region_list():
        url = f"https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A1%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=1&pz=100"
        res_json = requests.request('get', url, headers={}, proxies={}).json()
        result = pd.DataFrame()
        for num, row in res_json['data']['diff'].items():
            result = pd.concat([result, pd.DataFrame(row, index=[0])], ignore_index=True)
        result.columns = ['code', 'prefix', 'name']
        result.set_index('code', inplace=True)
        return result
    
    # 东财概念列表
    # https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A3%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=2&pz=20
    def get_concept_list():
        url = f"https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A3%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=1&pz=600"
        res_json = requests.request('get', url, headers={}, proxies={}).json()
        
        result = pd.DataFrame()
        # res_json['data']['diff'] 数据格式参考 {'0': {'f12': 'BK0534', 'f13': 90, 'f14': '成渝特区'}, '1': {'f12': 'BK0535', 'f13': 90, 'f14': 'QFII重仓'}, '2': {'f12': 'BK0536', 'f13': 90, 'f14': '一带一路'}}
        for num, row in res_json['data']['diff'].items():
            # row 是json键值对数据，参考{'f12': 'BK0577', 'f13': 90, 'f14': '核能核电'}
            # 将row添加到result中
            result = pd.concat([result, pd.DataFrame(row, index=[0])], ignore_index=True)
            # result = result.append(row, ignore_index=True)
            # result = result.append(row, ignore_index=True)
        # 创建一个result对象，以key为column，value为value
        result.columns = ['code', 'prefix', 'name']
        result.set_index('code', inplace=True)
        result = result.sort_index(ascending=True)  # 按bk_code升序排序
        return result

    # 东财行业列表
    # https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A2%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=1&pz=500
    def get_industry_list():
        url = f"https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A2%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=1&pz=500"
        res_json = requests.request('get', url, headers={}, proxies={}).json()
        
        result = pd.DataFrame()
        for num, row in res_json['data']['diff'].items():
            result = pd.concat([result, pd.DataFrame(row, index=[0])], ignore_index=True)
        result.columns = ['code', 'prefix', 'name']
        result.set_index('code', inplace=True)
        return result
