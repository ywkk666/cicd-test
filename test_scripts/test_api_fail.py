#!/usr/bin/env python3
# 测试脚本场景：API 用例失败

import time


def main():
    print("场景: test_api_fail")
    print("开始 API 测试...")
    time.sleep(1)
    print("登录接口: PASS")
    time.sleep(1)
    print("订单接口: FAIL (HTTP 500)")
    print("结果: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
