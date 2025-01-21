from adata import stock

from utils.concept_list_data_service import BKUtil

# print(stock.info.get_plate_east(stock_code='300274'))
# print(five_min_amount_history(code='BK1031'))
result = BKUtil.get_industry_list()

# 添加打印语句校验数据
print("概念列表数据前5行：")
print(result.head())
print("\n概念列表数据描述统计：")
print(result.describe())

print(result.index)
print(result.columns)