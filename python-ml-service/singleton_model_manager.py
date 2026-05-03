"""
全局单例模型管理器
确保模型在应用启动时就常驻内存，完全避免请求时重复加载
"""
import logging
import threading
from typing import Optional
from contextlib import contextmanager

from traffic_model_optimized import OptimizedTrafficPredictionModel

logger = logging.getLogger(__name__)


class SingletonModelManager:
    """
    全局单例模型管理器
    
    设计要点：
    1. 模块级单例：在模块导入时就初始化（如果启用预加载）
    2. 双重检查锁：确保多线程环境下的安全性
    3. 显式初始化/销毁：支持应用生命周期管理
    4. 全局访问函数：提供简单的访问接口
    """
    
    _instance: Optional[OptimizedTrafficPredictionModel] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False
    _preloaded: bool = False
    
    @classmethod
    def preload(cls) -> OptimizedTrafficPredictionModel:
        """
        预加载模型到内存
        
        在应用启动时调用此方法，确保模型在处理任何请求之前就已加载
        """
        with cls._lock:
            if cls._instance is None:
                logger.info("=" * 60)
                logger.info("  PRELOADING TRAFFIC PREDICTION MODEL (GLOBAL SINGLETON)")
                logger.info("=" * 60)
                
                import time
                start_time = time.time()
                
                cls._instance = OptimizedTrafficPredictionModel()
                
                load_time = time.time() - start_time
                cls._preloaded = True
                cls._initialized = True
                
                logger.info(f"Model preloaded successfully in {load_time:.3f} seconds")
                logger.info(f"Model instance ID: {id(cls._instance)}")
                logger.info("=" * 60)
        
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> OptimizedTrafficPredictionModel:
        """
        获取全局单例模型实例
        
        此方法确保：
        1. 如果模型已预加载，直接返回
        2. 如果未预加载，初始化（带双重检查锁）
        3. 永远不会在请求时重复加载
        """
        if cls._instance is not None:
            return cls._instance
        
        with cls._lock:
            if cls._instance is None:
                if not cls._preloaded:
                    logger.warning("Model not preloaded at startup. Initializing now...")
                    logger.warning("For best performance, call preload() at application startup.")
                
                cls._instance = OptimizedTrafficPredictionModel()
                cls._initialized = True
        
        return cls._instance
    
    @classmethod
    def is_initialized(cls) -> bool:
        """检查模型是否已初始化"""
        return cls._instance is not None
    
    @classmethod
    def is_preloaded(cls) -> bool:
        """检查模型是否在启动时预加载"""
        return cls._preloaded
    
    @classmethod
    def get_instance_id(cls) -> Optional[int]:
        """获取模型实例的内存地址（用于调试）"""
        if cls._instance is not None:
            return id(cls._instance)
        return None
    
    @classmethod
    def reset(cls) -> None:
        """
        重置单例（仅用于测试）
        
        注意：在生产环境中不应调用此方法
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False
            cls._preloaded = False
            logger.warning("Singleton model reset (for testing only)")


def get_global_model() -> OptimizedTrafficPredictionModel:
    """
    全局访问函数：获取预加载的模型实例
    
    这是推荐的访问方式，简单直接
    """
    return SingletonModelManager.get_instance()


def is_model_ready() -> bool:
    """检查模型是否准备就绪"""
    return SingletonModelManager.is_initialized()


def preload_global_model() -> OptimizedTrafficPredictionModel:
    """
    预加载全局模型
    
    在应用启动时调用此函数
    """
    return SingletonModelManager.preload()


@contextmanager
def model_context():
    """
    模型上下文管理器（用于确保模型已加载）
    
    使用示例：
        with model_context() as model:
            prediction = model.predict_congestion("INT-001")
    """
    model = get_global_model()
    try:
        yield model
    finally:
        pass
