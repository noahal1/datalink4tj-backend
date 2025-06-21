#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Datalink4TJ 后端服务启动脚本
"""
import uvicorn
import argparse
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def setup_logging(log_level):
    """设置日志配置"""
    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    
    level = log_levels.get(log_level.lower(), logging.INFO)
    
    # 创建logs目录（如果不存在）
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "app.log"
    
    # 配置日志格式
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("run")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="启动Datalink4TJ后端服务")
    parser.add_argument("--host", default=os.getenv("API_HOST", "0.0.0.0"), help="服务主机地址")
    parser.add_argument("--port", type=int, default=int(os.getenv("API_PORT", "8000")), help="服务端口")
    parser.add_argument("--reload", action="store_true", default=bool(os.getenv("API_RELOAD", True)), help="启用自动重载")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "info"), 
                        choices=["debug", "info", "warning", "error", "critical"], help="日志级别")
    parser.add_argument("--workers", type=int, default=int(os.getenv("WORKERS", "1")), help="工作进程数")
    
    return parser.parse_args()

def main():
    """主函数"""
    # 确保logs目录存在
    Path("logs").mkdir(exist_ok=True)
    
    # 解析参数并设置日志
    args = parse_args()
    logger = setup_logging(args.log_level)
    
    logger.info(f"启动Datalink4TJ后端服务，主机: {args.host}, 端口: {args.port}")
    logger.info(f"日志级别: {args.log_level}, 工作进程数: {args.workers}")
    
    # 如果是开发环境，设置单个工作进程
    if args.reload and args.workers > 1:
        logger.warning("开发模式(reload=True)下只能使用1个工作进程，已自动调整workers=1")
        workers = 1
    else:
        workers = args.workers
    
    # 启动Uvicorn服务器
    try:
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            workers=workers
        )
    except Exception as e:
        logger.error(f"启动服务时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n服务已停止")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1) 