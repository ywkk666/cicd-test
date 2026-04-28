import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from urllib import request, error


ERROR_PATTERNS = [
    r"traceback",
    r"\berror\b",
    r"\bexception\b",
    r"\bfailed\b",
    r"assertionerror",
]

PROVIDER_DEFAULT_MODEL = {
    "zhipu": "glm-4-flash",
    "openai": "gpt-4o-mini",
}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def detect_issues(log_text: str) -> list[str]:
    lines = log_text.splitlines()
    hits = []
    for line in lines:
        lower = line.lower()
        if any(re.search(p, lower) for p in ERROR_PATTERNS):
            hits.append(line.strip())
    # 去重并限制长度，避免报告太长
    dedup = []
    seen = set()
    for h in hits:
        key = h.lower()
        if key not in seen:
            seen.add(key)
            dedup.append(h)
        if len(dedup) >= 8:
            break
    return dedup


def call_openai(prompt: str, model: str) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    payload = {"model": model, "input": prompt}
    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=25) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="ignore"))
            return body.get("output_text", "").strip() or None
    except (error.URLError, TimeoutError, ValueError, KeyError):
        return None


def call_zhipu(prompt: str, model: str) -> Optional[str]:
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        return None

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    req = request.Request(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=25) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="ignore"))
            choices = body.get("choices", [])
            if not choices:
                return None
            content = choices[0].get("message", {}).get("content", "")
            return content.strip() or None
    except (error.URLError, TimeoutError, ValueError, KeyError):
        return None


def build_rule_based_summary(mode: str, log_findings: dict[str, list[str]]) -> str:
    total_issues = sum(len(v) for v in log_findings.values())
    if total_issues == 0:
        return (
            f"本次 {mode} 流水线整体执行正常，没有发现明显报错信息。"
            " 可进入下一步（合并或继续联调）。"
        )

    failed_parts = [name for name, issues in log_findings.items() if issues]
    failed_text = "、".join(failed_parts)
    return (
        f"本次 {mode} 流水线存在异常，主要集中在：{failed_text}。"
        " 建议优先处理首个错误，再重新运行流水线验证。"
    )


def choose_model(provider: str, user_model: Optional[str]) -> str:
    if user_model:
        return user_model
    if provider in PROVIDER_DEFAULT_MODEL:
        return PROVIDER_DEFAULT_MODEL[provider]
    # auto 模式默认优先智普
    return PROVIDER_DEFAULT_MODEL["zhipu"]


def build_report(mode: str, logs_map: dict[str, Path], provider: str, model: str) -> str:
    findings: dict[str, list[str]] = {}
    snippets: dict[str, str] = {}
    missing_logs = []
    for display_name, path in logs_map.items():
        text = read_text(path)
        snippets[display_name] = "\n".join(text.splitlines()[-80:])
        findings[display_name] = detect_issues(text)
        if not path.exists():
            missing_logs.append(f"{display_name}({path})")

    rule_summary = build_rule_based_summary(mode, findings)
    ai_summary = None

    prompt = (
        "你是CI结果分析助手。请用非技术人员能看懂的中文输出：\n"
        "1) 一句话结论（是否通过）\n"
        "2) 影响说明（业务视角）\n"
        "3) 下一步行动（最多3条）\n\n"
        f"流水线类型: {mode}\n"
        f"规则摘要: {rule_summary}\n"
        f"问题清单: {json.dumps(findings, ensure_ascii=False)}\n"
    )
    if provider == "zhipu":
        ai_summary = call_zhipu(prompt, model)
    elif provider == "openai":
        ai_summary = call_openai(prompt, model)
    else:
        # auto: 优先智普，其次 OpenAI
        ai_summary = call_zhipu(prompt, model) or call_openai(prompt, model)

    report_lines = [
        "# CI 执行分析报告（面向非技术同学）",
        "",
        f"- 生成时间: {datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}",
        f"- 流水线类型: `{mode}`",
        "",
        "## 结论",
        ai_summary if ai_summary else rule_summary,
        "",
        "## 脚本执行观察",
    ]

    for name, issues in findings.items():
        status = "通过" if not issues else "异常"
        report_lines.append(f"- `{name}`: {status}")

    report_lines.extend(["", "## 主要异常线索（最多8条/脚本）"])
    for name, issues in findings.items():
        report_lines.append(f"- `{name}`")
        if not issues:
            report_lines.append("  - 未检测到明显异常关键词")
        else:
            for i in issues:
                report_lines.append(f"  - {i}")

    report_lines.extend(
        [
            "",
            "## 原始日志片段（末尾80行）",
        ]
    )
    for name, content in snippets.items():
        report_lines.extend(
            [
                "",
                f"### {name}",
                "```text",
                content if content else "(日志为空或文件不存在)",
                "```",
            ]
        )

    if missing_logs:
        report_lines.extend(
            [
                "",
                "## 日志完整性提醒",
                f"- 以下日志文件缺失，结论可能不完整：{'; '.join(missing_logs)}",
            ]
        )

    if not ai_summary:
        report_lines.extend(
            [
                "",
                "> 说明：未检测到 `ZHIPU_API_KEY/OPENAI_API_KEY` 或 AI 调用失败，当前使用规则兜底分析。",
            ]
        )

    return "\n".join(report_lines) + "\n"


def parse_logs(items: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for item in items:
        # 形如: "构建=build.log"
        if "=" not in item:
            continue
        name, path_str = item.split("=", 1)
        result[name.strip()] = Path(path_str.strip())
    return result


def guess_mode_and_logs(input_mode: Optional[str], input_logs: Dict[str, Path]) -> tuple[str, Dict[str, Path]]:
    if input_mode and input_logs:
        return input_mode, input_logs

    mode = input_mode
    logs = dict(input_logs)

    dev_candidates = {
        "build脚本": Path("build.log"),
        "deploy脚本": Path("deploy.log"),
    }
    test_candidates = {
        "api测试脚本": Path("test_api.log"),
        "性能测试脚本": Path("test_performance.log"),
    }

    dev_exists = any(p.exists() for p in dev_candidates.values())
    test_exists = any(p.exists() for p in test_candidates.values())

    # 自动推断 mode
    if not mode:
        if test_exists and not dev_exists:
            mode = "test"
        else:
            mode = "dev"

    # 自动补全 logs
    if not logs:
        if mode == "test":
            logs = {k: v for k, v in test_candidates.items() if v.exists()}
            if not logs:
                logs = test_candidates
        else:
            logs = {k: v for k, v in dev_candidates.items() if v.exists()}
            if not logs:
                logs = dev_candidates

    return mode, logs


def main():
    parser = argparse.ArgumentParser(description="Generate CI analysis report")
    parser.add_argument("--mode", choices=["dev", "test"], help="dev or test")
    parser.add_argument("--log", action="append", default=[], help="NAME=PATH")
    parser.add_argument("--output", help="Optional output markdown file path")
    parser.add_argument("--provider", default="auto", choices=["auto", "zhipu", "openai"])
    parser.add_argument("--model", help="Optional custom model name")
    args = parser.parse_args()

    logs_map = parse_logs(args.log)
    mode, logs_map = guess_mode_and_logs(args.mode, logs_map)
    model = choose_model(args.provider, args.model)
    report = build_report(mode, logs_map, args.provider, model)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"report generated: {args.output}")
    else:
        # 默认输出到 stdout，适合直接写入 GITHUB_STEP_SUMMARY
        print(report)


if __name__ == "__main__":
    main()
