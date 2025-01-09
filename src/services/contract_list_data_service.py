from typing import Callable
from adata import stock
# concept_list result sample
# 	concept_code	index_code	name	source
# 0	BK0623	BK0623	海洋经济	东方财富
# 1	BK0501	BK0501	次新股	东方财富
# 2	BK0971	BK0971	注册制次新股	东方财富
# 3	BK1122	BK1122	血氧仪	东方财富
def concept_list():
    df = stock.info.all_concept_code_east()
    return df

