from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from store_proxy import StoreManager

class KlineDT(StoreManager.Base):
    __tablename__ = 'kline_dt'
    id = Column(Integer, primary_key=True)
    prefix = Column(String(8))
    code = Column(String(16))
    period = Column(String(100)) # 1min, 5min, 15min, 30min, 60m, 120m
    date = Column(DateTime)  # 记录K线日期
    time_point = Column(String(10)) # 记录K线的时间点
    amount = Column(Float) # 成交量

    __table_args__ = (
        UniqueConstraint('prefix', 'code', 'period', 'date', 'time_point', name='uix_code_period_date_time_point'),
    )