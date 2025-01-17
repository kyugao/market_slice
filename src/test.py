from adata import stock

from utils.five_min_kline_service import five_min_amount_history

# print(stock.info.get_plate_east(stock_code='300274'))
print(five_min_amount_history(code='BK1031'))