#!/usr/bin/env python3
# 测试脚本场景：超时模拟

import time


def main():
    print("场景: test_timeout_sim")
    print("开始长耗时测试...")
    for i in range(1, 7):
        print(f"运行中... {i}/6")
        time.sleep(3)
    print("测试结束（可用于验证 workflow timeout 行为）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
