from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QLineEdit, QCheckBox, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import pyqtSignal, Qt, QSortFilterProxyModel, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from loguru import logger
from utils.contract_list_data_service import ContractUtil

class ContractListWidget(QWidget):
    """概念列表组件"""
    
    # 定义双击信号，发送选中的concept_code
    concept_selected = pyqtSignal(str)
    
    # 分页相关属性
    PAGE_SIZE = 100
    current_page = 0
    all_data = None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("[INIT] 开始初始化概念列表组件...")
        
        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 添加搜索框
        self.init_search_box()
        
        # 添加分页控件
        self.init_pagination_controls()
        
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
        
        # 创建复选框布局
        self.checkbox_layout = QHBoxLayout()
        
        # 创建并添加复选框
        self.industry_checkbox = QCheckBox("行业", self)
        self.concept_checkbox = QCheckBox("概念", self)
        self.area_checkbox = QCheckBox("地区", self)
        self.stock_checkbox = QCheckBox("个股", self)
        
        # 默认选中所有复选框
        self.industry_checkbox.setChecked(True)
        self.concept_checkbox.setChecked(True)
        self.area_checkbox.setChecked(True)
        self.stock_checkbox.setChecked(True)
        
        # 连接状态改变信号
        self.industry_checkbox.stateChanged.connect(self.filter_table)
        self.concept_checkbox.stateChanged.connect(self.filter_table)
        self.area_checkbox.stateChanged.connect(self.filter_table)
        self.stock_checkbox.stateChanged.connect(self.filter_table)
        
        # 添加到布局
        self.checkbox_layout.addWidget(self.industry_checkbox)
        self.checkbox_layout.addWidget(self.concept_checkbox)
        self.checkbox_layout.addWidget(self.area_checkbox)
        self.checkbox_layout.addWidget(self.stock_checkbox)
        
        # 将复选框布局添加到主布局
        self.layout.addLayout(self.checkbox_layout)
        
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
        self.model.setHorizontalHeaderLabels(['代码', '名称', '类型'])

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
        logger.debug(f"filter test {self.concept_checkbox.status}")
        self.proxy_model.setFilterFixedString(text)
        
    def init_pagination_controls(self):
        """初始化分页控件"""
        self.pagination_layout = QHBoxLayout()
        
        # 上一页按钮
        self.prev_button = QPushButton("上一页")
        self.prev_button.clicked.connect(self.prev_page)
        self.prev_button.setEnabled(False)
        
        # 下一页按钮
        self.next_button = QPushButton("下一页")
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)
        
        # 页码显示
        self.page_label = QLabel("第 1 页")
        
        self.pagination_layout.addWidget(self.prev_button)
        self.pagination_layout.addWidget(self.page_label)
        self.pagination_layout.addWidget(self.next_button)
        
        self.layout.addLayout(self.pagination_layout)
        
    def prev_page(self):
        """切换到上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()
            
    def next_page(self):
        """切换到下一页"""
        if (self.current_page + 1) * self.PAGE_SIZE < len(self.all_data):
            self.current_page += 1
            self.update_table()
            
    def update_table(self):
        """更新表格显示当前页数据"""
        start = self.current_page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_data = self.all_data.iloc[start:end]
        
        # 清空现有数据
        self.model.removeRows(0, self.model.rowCount())
        
        # 添加新数据
        for index, row in page_data.iterrows():
            code_item = QStandardItem(index)
            name_item = QStandardItem(row['name'])
            type_item = QStandardItem(str(row['contract_type']))
            code_item.setEditable(False)
            name_item.setEditable(False)
            type_item.setEditable(False)
            self.model.appendRow([code_item, name_item, type_item])
            
        # 更新页码显示
        self.page_label.setText(f"第 {self.current_page + 1} 页")
        
        # 更新按钮状态
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled((self.current_page + 1) * self.PAGE_SIZE < len(self.all_data))
        
        # 设置列宽自适应内容
        self.table_view.resizeColumnsToContents()
        
    def load_concept_data(self):
        """加载概念数据"""
        try:
            # 获取所有数据
            self.all_data = ContractUtil.get_contract_data()
            self.all_data.sort_index(ascending=True)
            logger.debug(f"[LOAD] 获取到的概念列表数据：\n{self.all_data.sample()}")
            
            # 初始化分页状态
            self.current_page = 0
            self.update_table()
            
            logger.info(f"[LOAD] 已加载 {len(self.all_data)} 条概念数据")
            
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
            QTimer.singleShot(300, lambda: self.handle_selection_async(concept_code))

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
