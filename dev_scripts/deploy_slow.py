#!/usr/bin/env python3
# 开发脚本场景：慢部署（用于观察超时与日志）

import time


def main():
    print("场景: deploy_slow")
    print("开始部署...")
    for step in range(1, 6):
        print(f"执行步骤 {step}/5")
        time.sleep(2)
    print("部署完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
