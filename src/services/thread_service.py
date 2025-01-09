from abc import ABC, abstractmethod
from PyQt5.QtCore import QThread, pyqtSignal
from typing import Callable, Dict
import pandas as pd
from loguru import logger

class EventThreadService(QThread, ABC):
    """数据服务线程的抽象基类"""
    
    # 定义通用信号
    data_ready = pyqtSignal(pd.DataFrame)  # 数据就绪信号
    error_occurred = pyqtSignal(str)       # 错误信号
    
    def __init__(self):
        super().__init__()
        self._is_running = True
        self._signal_slots: Dict[pyqtSignal, Callable] = {}
        logger.debug(f"[INIT] {self.__class__.__name__} initialized")
        
    def connect(self, signal_name: str, slot: Callable) -> bool:
        """连接信号到槽函数
        
        Args:
            signal_name: 信号名称
            slot: 槽函数
            
        Returns:
            bool: 连接是否成功
        """
        try:
            if hasattr(self, signal_name):
                signal = getattr(self, signal_name)
                signal.connect(slot)
                self._signal_slots[signal] = slot
                logger.debug(f"[SIGNAL] Connected {signal_name} -> {slot.__name__}")
                return True
            else:
                logger.error(f"[ERROR] Signal {signal_name} not found")
                return False
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect signal {signal_name}: {str(e)}")
            return False
            
    def disconnect_all(self):
        """断开所有信号连接"""
        for signal, slot in self._signal_slots.items():
            try:
                signal.disconnect(slot)
                logger.debug(f"[SIGNAL] Disconnected {signal} -> {slot.__name__}")
            except Exception as e:
                logger.error(f"[ERROR] Failed to disconnect signal: {str(e)}")
                
    def stop(self):
        """停止线程"""
        self._is_running = False
        self.disconnect_all()
        self.wait()
        
    @abstractmethod
    def run(self):
        """线程运行方法"""
        pass