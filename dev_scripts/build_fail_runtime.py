#!/usr/bin/env python3
# 开发脚本场景：运行时异常失败

import time


def main():
    print("场景: build_fail_runtime")
    print("开始构建...")
    time.sleep(1)
    print("编译阶段触发运行时异常")
    raise RuntimeError("模拟构建运行时错误: package index unavailable")


if __name__ == "__main__":
    main()
