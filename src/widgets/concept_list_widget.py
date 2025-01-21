from datetime import datetime
import time
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QLineEdit
from PyQt5.QtCore import pyqtSignal, Qt, QSortFilterProxyModel, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from loguru import logger
from utils.concept_list_data_service import BKUtil

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
        
        # 添加搜索框
        self.init_search_box()
        
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
        
    def init_search_box(self):
        """初始化搜索框"""
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("输入关键词搜索...")
        self.search_box.textChanged.connect(self.filter_table)
        self.layout.addWidget(self.search_box)
        
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
        self.model.setHorizontalHeaderLabels(['板块代码', '板块名称', '板块类型'])

        # 创建代理模型用于过滤
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(0)  # 默认按板块名称过滤
        
        self.table_view.setModel(self.proxy_model)
        # 连接选择变化信号
        self.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        # 添加到布局
        self.layout.addWidget(self.table_view)
    
    def filter_table(self, text):
        """根据搜索框内容过滤表格"""
        self.proxy_model.setFilterFixedString(text)
        
    def load_concept_data(self):
        """加载概念数据"""
        try:
            # 获取概念列表数据
            concept_data = BKUtil.get_bk_list()
            concept_data.sort_index(ascending=True)
            logger.debug(f"[LOAD] 获取到的概念列表数据：\n{concept_data}")
            
            # 清空现有数据
            self.model.removeRows(0, self.model.rowCount())
            # 对concept_data数据排序, 使用index升序

            # 添加新数据
            for index, row in concept_data.iterrows():
                code_item = QStandardItem(index)  # 使用index作为板块代码
                name_item = QStandardItem(row['bk_name'])  # 使用bk_name作为板块名称
                type_item = QStandardItem(str(row['bk_type']))  # 使用bk_type作为板块类型
                code_item.setEditable(False)
                name_item.setEditable(False)
                type_item.setEditable(False)
                # 设置列宽自适应内容
                self.table_view.resizeColumnsToContents()
                self.model.appendRow([code_item, name_item, type_item])
                
            logger.info(f"[LOAD] 已加载 {len(concept_data)} 条概念数据")
            
        except Exception as e:
            logger.exception("[ERROR] 加载概念数据失败")
            raise
    

    def on_selection_changed(self, selected, deselected):
        """处理选择变化事件"""
        indexes = selected.indexes()
        if indexes:
            # 通过proxy_model获取选中行的concept_code
            proxy_index = indexes[0]
            source_index = self.proxy_model.mapToSource(proxy_index)
            concept_code = self.model.data(
                self.model.index(source_index.row(), 0)  # 第一列是concept_code
            )
            logger.info(f"[EVENT] 选中概念: {concept_code}")

            # 使用QTimer实现异步延迟
            QTimer.singleShot(500, lambda: self.handle_selection_async(concept_code))

    def handle_selection_async(self, concept_code):
        """异步处理选中逻辑"""
        try:
            current_timetag = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            logger.debug(f"[TIMESTAMP] 异步处理时间: {current_timetag}")
            
            # 检查是否仍然选中相同的行
            indexes = self.table_view.selectedIndexes()
            if indexes:
                proxy_index = indexes[0]
                source_index = self.proxy_model.mapToSource(proxy_index)
                current_code = self.model.data(
                    self.model.index(source_index.row(), 0)
                )
                
                if current_code == concept_code:
                    logger.debug(f"[TIMESTAMP] 选中项一致，发送信号: {concept_code}")
                    self.concept_selected.emit(concept_code)
                else:
                    logger.debug(f"[TIMESTAMP] 选中项已改变，跳过发送: {current_code} != {concept_code}")
            else:
                logger.debug("[TIMESTAMP] 当前无选中项，跳过发送")
                
        except Exception as e:
            logger.exception(f"[ERROR] 异步处理选中逻辑时出错: {str(e)}")
    


    def get_selected_concept(self) -> str:
        """获取当前选中的概念代码"""
        indexes = self.table_view.selectedIndexes()
        if indexes:
            return self.model.data(self.model.index(indexes[0].row(), 0))
        return None
