#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志配置模块 - 适用于生产环境
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from core.config import settings

# 创建日志目录
os.makedirs("logs", exist_ok=True)

# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# 获取环境变量中的日志级别，默认为INFO
log_level = LOG_LEVELS.get(settings.LOG_LEVEL.upper(), logging.INFO)

# 创建格式化器
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def get_logger(name):
    """
    获取配置好的logger实例
    
    参数:
    - name: logger名称
    
    返回:
    - 配置好的logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 防止重复添加handler
    if not logger.handlers:
        # 文件处理器 - 使用循环日志文件
        file_handler = RotatingFileHandler(
            filename=f"logs/{name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# 创建主应用日志器
app_logger = get_logger("app")
