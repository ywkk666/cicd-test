#!/usr/bin/env python3
# 测试脚本 test2.py

import time

def test_function():
    """测试函数"""
    print("开始执行测试...")
    time.sleep(1)  # 模拟执行时间
    print("测试执行中...")
    time.sleep(1)
    print("测试完成！")
    return True

if __name__ == "__main__":
    result = test_function()
    print(f"测试结果: {'成功' if result else '失败'}")