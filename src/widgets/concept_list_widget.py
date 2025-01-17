from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from loguru import logger
from utils.concept_list_data_service import ConceptDataUtil

class ConceptListWidget(QWidget):
    """概念列表组件"""
    
    # 定义双击信号，发送选中的concept_code
    concept_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("[INIT] 开始初始化概念列表组件...")
        
        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 初始化表格视图
        self.init_table_view()
        
        # 加载数据
        self.load_concept_data()

        # 选中第一行
        first_row_index = self.model.index(0, 0)
        self.table_view.setCurrentIndex(first_row_index)
        
        # 获取第一行的concept_code并触发选中信号
        concept_code = self.model.data(first_row_index)
        self.concept_selected.emit(concept_code)
        
        logger.debug("[INIT] 概念列表组件初始化完成")
        
    def init_table_view(self):
        """初始化表格视图"""
        self.table_view = QTableView(self)
        
        # 设置表格属性
        self.table_view.setSelectionBehavior(QTableView.SelectRows)  # 整行选择
        self.table_view.setSelectionMode(QTableView.SingleSelection)  # 单行选择
        self.table_view.setAlternatingRowColors(True)  # 交替行颜色
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)  # 禁止编辑
        self.table_view.setFocusPolicy(Qt.StrongFocus)  # 允许键盘导航
        
        # 设置表头
        self.table_view.verticalHeader().setVisible(False)  # 隐藏垂直表头
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 允许调整列宽
        self.table_view.horizontalHeader().setStretchLastSection(True)  # 最后一列自适应
        
        # 创建数据模型
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['概念代码', '概念名称'])
        self.table_view.setModel(self.model)
        
        # 连接双击信号
        self.table_view.doubleClicked.connect(self.on_double_click)
        # 连接选择变化信号
        self.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        # 添加到布局
        self.layout.addWidget(self.table_view)
        
    def load_concept_data(self):
        """加载概念数据"""
        try:
            # 获取概念列表数据
            concept_data = ConceptDataUtil.concept_list()
            logger.debug(f"[LOAD] 获取到的概念列表数据：\n{concept_data}")
            
            # 清空现有数据
            self.model.removeRows(0, self.model.rowCount())
            concept_data.sort_values(by='concept_code', inplace=True)

            
            # 添加新数据
            for index, row in concept_data.iterrows():
                code_item = QStandardItem(row['concept_code'])
                name_item = QStandardItem(row['name'])
                # 设置项目不可编辑
                code_item.setEditable(False)
                name_item.setEditable(False)
                self.model.appendRow([code_item, name_item])
                
            logger.info(f"[LOAD] 已加载 {len(concept_data)} 条概念数据")
            
        except Exception as e:
            logger.exception("[ERROR] 加载概念数据失败")
            raise
            
    def on_double_click(self, index):
        """处理双击事件"""
        if index.isValid():
            # 获取选中行的concept_code
            concept_code = self.model.data(
                self.model.index(index.row(), 0)  # 第一列是concept_code
            )
            logger.info(f"[EVENT] 双击选中概念: {concept_code}")
            # 发送选中信号
            self.concept_selected.emit(concept_code)
            
    def on_selection_changed(self, selected, deselected):
        """处理选择变化事件"""
        indexes = selected.indexes()
        if indexes:
            # 获取选中行的concept_code
            concept_code = self.model.data(
                self.model.index(indexes[0].row(), 0)  # 第一列是concept_code
            )
            logger.info(f"[EVENT] 选中概念: {concept_code}")
            # 发送选中信号
            self.concept_selected.emit(concept_code)
            
    def get_selected_concept(self) -> str:
        """获取当前选中的概念代码"""
        indexes = self.table_view.selectedIndexes()
        if indexes:
            return self.model.data(self.model.index(indexes[0].row(), 0))
        return None
