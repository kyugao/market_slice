import sys
from PyQt5.QtCore import QCoreApplication
from pathlib import Path

# 添加src目录到Python路径
project_root = str(Path(__file__).parent.parent)
sys.path.append(str(Path(project_root) / 'src'))

from services.history_data_service import HistoryDataService
import pandas as pd
from datetime import datetime
import logging

def setup_logger():
    """配置日志"""
    logger = logging.getLogger('TestHistoryData')
    logger.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    
    return logger

class HistoryDataTester:
    def __init__(self):
        self.logger = setup_logger()
        self.app = QCoreApplication(sys.argv)
        self.service = HistoryDataService()
        
        # 连接信号
        self.service.history_ready.connect(self.on_history_ready)
        self.service.error_occurred.connect(self.on_error)
        
    def on_history_ready(self, df: pd.DataFrame):
        """处理历史数据"""
        self.logger.info("\n=== 收到历史数据 ===")
        
        if df is None or df.empty:
            self.logger.error("历史数据为空!")
            return
            
        # 1. 基本信息检查
        self.logger.info("\n1. 基本信息:")
        self.logger.info(f"数据形状: {df.shape}")
        self.logger.info(f"列名: {df.columns.tolist()}")
        
        # 2. 数据完整性检查
        self.logger.info("\n2. 数据完整性检查:")
        required_fields = ["time", "code", "open", "close", "high", "low", "volume", "amount"]
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            self.logger.warning(f"缺失字段: {missing_fields}")
        else:
            self.logger.info("所有必需字段都存在")
            
        # 3. 时间范围检查
        self.logger.info("\n3. 时间范围检查:")
        self.logger.info(f"起始时间: {df['time'].min()}")
        self.logger.info(f"结束时间: {df['time'].max()}")
        self.logger.info(f"总交易日数: {df['time'].dt.date.nunique()}")
        
        # 4. 股票代码检查
        self.logger.info("\n4. 股票代码检查:")
        unique_codes = df['code'].unique()
        self.logger.info(f"股票代码列表: {unique_codes}")
        for code in unique_codes:
            code_data = df[df['code'] == code]
            self.logger.info(f"\n{code} 统计信息:")
            self.logger.info(f"数据条数: {len(code_data)}")
            self.logger.info(f"时间范围: {code_data['time'].min()} 到 {code_data['time'].max()}")
            self.logger.info(f"交易日数: {code_data['time'].dt.date.nunique()}")
        
        # 5. 数据质量检查
        self.logger.info("\n5. 数据质量检查:")
        # 检查空值
        null_counts = df.isnull().sum()
        if null_counts.any():
            self.logger.warning("发现空值:")
            self.logger.warning(null_counts[null_counts > 0])
        else:
            self.logger.info("数据完整，没有空值")
            
        # 检查数据类型
        self.logger.info("\n数据类型:")
        self.logger.info(df.dtypes)
        
        # 6. 数据预览
        self.logger.info("\n6. 数据预览:")
        self.logger.info("\n前5行数据:")
        self.logger.info(df.head())
        
        # 7. 基本统计信息
        self.logger.info("\n7. 基本统计信息:")
        numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount']
        self.logger.info(df[numeric_cols].describe())
        
    def on_error(self, error_msg: str):
        """处理错误"""
        self.logger.error(f"错误: {error_msg}")
        
    def run_test(self):
        """运行测试"""
        self.logger.info("开始测试历史数据初始化...")
        
        try:
            # 直接调用初始化方法
            self.service._init_history_data()
            
        except Exception as e:
            self.logger.error(f"测试过程中发生错误: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            self.logger.info("测试完成")

def main():
    tester = HistoryDataTester()
    tester.run_test()

if __name__ == '__main__':
    main() 