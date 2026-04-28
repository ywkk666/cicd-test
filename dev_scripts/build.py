#!/usr/bin/env python3
# 开发脚本：构建任务（故意报错）

import time

def build_project():
    """构建项目"""
    print("开始构建项目...")
    time.sleep(1)
    print("编译源代码...")
    time.sleep(1)
    print("构建失败！故意报错...")
    # 故意返回失败
    return False

if __name__ == "__main__":
    result = build_project()
    qqwweea
    print(f"构建结果: {'成功' if result else '失败'}")
    # 故意退出码为1，表示失败
    exit(1)

