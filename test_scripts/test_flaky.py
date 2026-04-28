#!/usr/bin/env python3
# 测试脚本场景：随机波动（Flaky）

import random
import time


def main():
    print("场景: test_flaky")
    print("执行稳定性抽样...")
    time.sleep(1)
    value = random.random()
    print(f"随机值: {value:.4f}")
    if value < 0.5:
        print("结果: FAILED (模拟偶发失败)")
        return 1
    print("结果: SUCCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
