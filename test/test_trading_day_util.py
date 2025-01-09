import unittest
from datetime import datetime
from loguru import logger
from utils.trading_day_util import TradingDayUtil

class TestTradingDayUtil(unittest.TestCase):
    """交易日期工具类测试"""
    
    def setUp(self):
        """测试前置设置"""
        logger.info("\n=== 开始测试 ===")
    
    def tearDown(self):
        """测试后置处理"""
        logger.info("=== 测试结束 ===\n")
    
    def test_get_trading_days(self):
        """测试获取最近交易日方法"""
        logger.info("测试获取最近交易日...")
        
        # 获取最近交易日
        latest_day = TradingDayUtil.get_trading_days()
            
        logger.info(f"获取到的最近交易日: {latest_day}")
    
    def test_get_previous_trading_days(self):
        """测试获取过去n个交易日方法"""
        logger.info("测试获取过去n个交易日...")
        
        # 获取过去n个交易日
        previous_days = TradingDayUtil.get_previous_trading_days()
            
        logger.info(f"获取到的前5个交易日: {previous_days}")

    def test_get_latest_trading_day(self):
        """测试获取最近交易日方法"""
        logger.info("测试获取最后一个交易日...")
        
        # 获取最近交易日
        latest_day = TradingDayUtil.get_latest_trading_day()
        
        logger.info(f"获取到的最近交易日: {latest_day}")

if __name__ == '__main__':
    unittest.main() 