#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Datalink4TJ 启动入口点
"""
import os
import sys
import uvicorn

def dev():
    """以开发模式运行服务器"""
    print("正在以开发模式启动Datalink4TJ后端...")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

def start():
    """以生产模式运行服务器"""
    print("正在启动Datalink4TJ后端...")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

# 这些函数可以直接被Poetry调用
if __name__ == "__main__":
    if len(sys.argv) <= 1:
        dev()
    else:
        command = sys.argv[1]
        if command == "dev":
            dev()
        elif command == "start":
            start()
        else:
            print(f"未知命令: {command}")
            print("可用命令: dev, start")
            sys.exit(1) 