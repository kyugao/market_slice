import sys
from PyQt5 import QtWidgets
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)
from src.widgets.trading_volume_chart_widget import TradingVolumeChartWidget

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建中央Widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # 创建并添加交易量图表Widget
        self.volume_chart = TradingVolumeChartWidget()
        layout.addWidget(self.volume_chart)

def main():
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()