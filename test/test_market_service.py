import sys
from PyQt5.QtCore import QCoreApplication
from services.history_data_service import MarketDataService
import pandas as pd
import time

class MarketServiceTester:
    def __init__(self):
        print("初始化测试环境...")
        # 创建Qt应用程序实例(无GUI)
        self.app = QCoreApplication(sys.argv)
        
        print("创建 MarketDataService 实例...")
        # 初始化行情服务
        self.market_service = MarketDataService()
        
        print("连接信号...")
        # 连接信号
        self.market_service.data_ready.connect(self.on_data_ready)
        self.market_service.error_occurred.connect(self.on_error)
        self.market_service.history_ready.connect(self.on_history_ready)
        print("信号连接完成")
        
    def on_data_ready(self, df: pd.DataFrame):
        """处理实时数据"""
        print("\n收到实时数据:")
        if df is None or df.empty:
            print("数据为空!")
            return
            
        print(f"数据形状: {df.shape}")
        print(f"时间范围: {df['time'].min()} 到 {df['time'].max()}")
        print("\n数据预览:")
        print(df.head())
        
    def on_history_ready(self, df: pd.DataFrame):
        """处理历史数据"""
        print("\n收到历史数据:")
        if df is None or df.empty:
            print("历史数据为空!")
            return
            
        print(f"数据形状: {df.shape}")
        print(f"时间范围: {df['time'].min()} 到 {df['time'].max()}")
        print("\n数据预览:")
        print(df.head())
        
        # 按股票代码分组统计
        print("\n每只股票的数据统计:")
        for code in df['code'].unique():
            code_data = df[df['code'] == code]
            print(f"\n{code}:")
            print(f"数据条数: {len(code_data)}")
            print(f"时间范围: {code_data['time'].min()} 到 {code_data['time'].max()}")
        
    def on_error(self, error_msg: str):
        """处理错误"""
        print(f"\n错误: {error_msg}")
        
    def run_test(self, test_duration=30):
        """运行测试"""
        print(f"\n开始测试 MarketDataService, 将运行 {test_duration} 秒...")
        
        # 启动行情服务
        print("启动行情服务...")
        self.market_service.start()
        print("行情服务已启动")
        
        # 运行指定时间
        start_time = time.time()
        print(f"开始等待数据, 测试将持续 {test_duration} 秒...")
        
        while time.time() - start_time < test_duration:
            self.app.processEvents()  # 处理Qt事件
            time.sleep(0.1)  # 避免CPU占用过高
            
        # 停止服务
        print("\n测试结束,正在停止服务...")
        self.market_service.stop()
        print("服务已停止")
        
def main():
    print("=== 开始测试 MarketDataService ===")
    
    # 创建测试实例
    tester = MarketServiceTester()
    
    try:
        # 运行测试30秒
        tester.run_test(30)
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"\n测试出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        # 确保正确退出
        print("正在清理资源...")
        tester.market_service.stop()
        print("测试完成")
        sys.exit()

if __name__ == '__main__':
    main() 