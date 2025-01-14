from typing import Callable
from adata import stock
from pandas import DataFrame
# concept_list result sample
# 	concept_code	index_code	name	source
# 0	BK0623	BK0623	海洋经济	东方财富
# 1	BK0501	BK0501	次新股	东方财富
# 2	BK0971	BK0971	注册制次新股	东方财富
# 3	BK1122	BK1122	血氧仪	东方财富
# 全局变量,用于缓存概念列表数据

class ConceptDataUtil:
    _concept_list = None

    def concept_list():
        if ConceptDataUtil._concept_list is None:
            df = stock.info.all_concept_code_east()
            ConceptDataUtil._concept_list = df
        return ConceptDataUtil._concept_list

    def get_concept_name(concept_code: str):
        df = ConceptDataUtil.concept_list()
        return df[df['concept_code'] == concept_code]['name'].values[0]

if __name__ == "__main__":
    print(ConceptDataUtil.concept_list())

