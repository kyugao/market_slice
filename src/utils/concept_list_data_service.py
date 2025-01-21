from enum import Enum
from typing import Callable
from adata import stock
from loguru import logger
import pandas as pd
import requests
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
class BKType(Enum):
    Region = 1
    Industry = 2
    Concept = 3

    def get_cn_name(self):
        """根据枚举值返回对应的中文名称"""
        if self.value == 1:
            return "地域"
        elif self.value == 2:
            return "行业"
        elif self.value == 3:
            return "概念"
        else:
            return "未知类型"

class BKUtil:
    concept_list = None
    industry_list = None
    region_list = None
    bk_list = None

    @staticmethod
    def get_bk_list():
        if BKUtil.bk_list is None:
            BKUtil.concept_list = BKUtil.get_concept_list()
            BKUtil.industry_list = BKUtil.get_industry_list()
            BKUtil.region_list = BKUtil.get_region_list()
            # 添加概念列表
            BKUtil.concept_list['bk_type'] = BKType.Concept.get_cn_name()
            # 添加行业列表
            BKUtil.industry_list['bk_type'] = BKType.Industry.get_cn_name()
            # 添加地域列表
            BKUtil.region_list['bk_type'] = BKType.Region.get_cn_name()
            # 合并
            BKUtil.bk_list = pd.concat([BKUtil.concept_list, BKUtil.industry_list, BKUtil.region_list])
        return BKUtil.bk_list
    
    @staticmethod
    def get_bk_name(bk_code: str):
        if BKUtil.bk_list is None:
            BKUtil.get_bk_list()
        return BKUtil.bk_list.loc[bk_code]['bk_name']
        
    # 东财地域列表
    # https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A1%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=1&pz=500
    def get_region_list():
        if BKUtil.region_list is None:
            url = f"https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A1%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=1&pz=100"
            res_json = requests.request('get', url, headers={}, proxies={}).json()
            result = pd.DataFrame()
            for num, row in res_json['data']['diff'].items():
                result = pd.concat([result, pd.DataFrame(row, index=[0])], ignore_index=True)
            result.columns = ['bk_code', 'bk_prefix', 'bk_name']
            result.set_index('bk_code', inplace=True)
            BKUtil.region_list = result
        return BKUtil.region_list

    # 东财概念列表
    # https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A3%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=2&pz=20
    def get_concept_list():
        if BKUtil.concept_list is None:
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
            result.columns = ['bk_code', 'bk_prefix', 'bk_name']
            result.set_index('bk_code', inplace=True)
            result = result.sort_index(ascending=True)  # 按bk_code升序排序
            BKUtil.concept_list = result
        return BKUtil.concept_list

    # 东财行业列表
    # https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A2%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=1&pz=500
    def get_industry_list():
        if BKUtil.industry_list is None:
            url = f"https://push2.eastmoney.com/api/qt/clist/get?fs=m%3A90%2Bt%3A2%2Bf%3A!50&fields=f12%2Cf13%2Cf14&pn=1&pz=500"
            res_json = requests.request('get', url, headers={}, proxies={}).json()
            
            result = pd.DataFrame()
            for num, row in res_json['data']['diff'].items():
                result = pd.concat([result, pd.DataFrame(row, index=[0])], ignore_index=True)
            result.columns = ['bk_code', 'bk_prefix', 'bk_name']
            result.set_index('bk_code', inplace=True)
            BKUtil.industry_list = result
        return BKUtil.industry_list
