import argparse
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


API_BASE = "https://api.github.com"
WORKFLOW_NAME_DEFAULT = "Task Type Pipeline"


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def load_env_token_from_file() -> Optional[str]:
    """
    从 task_center/.env 读取 GITHUB_TOKEN，作为本地手动运行时的兜底。
    """
    env_path = Path("task_center/.env")
    if not env_path.exists():
        return None

    try:
        content = env_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == "GITHUB_TOKEN":
            token = value.strip().strip('"').strip("'")
            return token or None
    return None


def github_get(url: str, token: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def list_workflows(repo: str, token: str) -> List[Dict[str, Any]]:
    url = f"{API_BASE}/repos/{repo}/actions/workflows"
    data = github_get(url, token)
    return data.get("workflows", [])


def find_workflow_id(repo: str, token: str, workflow_name: str) -> Optional[int]:
    for wf in list_workflows(repo, token):
        if wf.get("name") == workflow_name:
            return wf.get("id")
    return None


def list_runs(repo: str, token: str, workflow_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
    url = f"{API_BASE}/repos/{repo}/actions/workflows/{workflow_id}/runs"
    page = 1
    all_runs: List[Dict[str, Any]] = []
    while True:
        data = github_get(url, token, params={"per_page": per_page, "page": page})
        runs = data.get("workflow_runs", [])
        if not runs:
            break
        all_runs.extend(runs)
        if len(runs) < per_page:
            break
        page += 1
    return all_runs


def filter_runs_by_date(runs: List[Dict[str, Any]], day_str: str, tz_offset_hours: int) -> List[Dict[str, Any]]:
    tz = timezone(timedelta(hours=tz_offset_hours))
    start_local = parse_date(day_str).replace(tzinfo=tz)
    start = start_local.astimezone(timezone.utc)
    end = start + timedelta(days=1)
    filtered = []
    for run in runs:
        created_at = run.get("created_at")
        if not created_at:
            continue
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        if start <= dt < end:
            filtered.append(run)
    return filtered


def duration_seconds(run: Dict[str, Any]) -> Optional[int]:
    start = run.get("run_started_at")
    end = run.get("updated_at")
    if not start or not end:
        return None
    s = datetime.fromisoformat(start.replace("Z", "+00:00"))
    e = datetime.fromisoformat(end.replace("Z", "+00:00"))
    return max(0, int((e - s).total_seconds()))


def safe_pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def build_report(repo: str, day_str: str, workflow_name: str, runs: List[Dict[str, Any]]) -> str:
    total = len(runs)
    by_conclusion = Counter((r.get("conclusion") or "unknown") for r in runs)
    by_event = Counter((r.get("event") or "unknown") for r in runs)
    by_branch = Counter((r.get("head_branch") or "unknown") for r in runs)
    by_actor = Counter((r.get("actor", {}) or {}).get("login", "unknown") for r in runs)

    success = by_conclusion.get("success", 0)
    failure = by_conclusion.get("failure", 0)
    cancelled = by_conclusion.get("cancelled", 0)
    success_rate = safe_pct(success, total)

    durations = [d for d in (duration_seconds(r) for r in runs) if d is not None]
    avg_duration = int(sum(durations) / len(durations)) if durations else 0
    max_duration = max(durations) if durations else 0

    failed_runs = [r for r in runs if (r.get("conclusion") or "") in ("failure", "timed_out", "cancelled")]
    failed_runs = sorted(failed_runs, key=lambda x: x.get("created_at", ""), reverse=True)
    top_failed_branches = Counter((r.get("head_branch") or "unknown") for r in failed_runs).most_common(5)

    lines = [
        "# CI 每日汇总报告（本地生成）",
        "",
        f"- 仓库: `{repo}`",
        f"- 日期: `{day_str}`",
        f"- 流水线: `{workflow_name}`",
        "",
        "## 一页结论（给非技术同学）",
        (
            f"今天共触发 **{total}** 次流水线，成功 **{success}** 次，失败 **{failure}** 次，"
            f"取消 **{cancelled}** 次，成功率 **{success_rate}%**。"
        ),
        (
            "整体建议："
            + ("流程稳定，可继续按当前节奏推进。" if success_rate >= 80 else "存在较多失败，建议优先修复失败任务后再扩展任务量。")
        ),
        "",
        "## 统计数据",
        f"- 总运行次数: `{total}`",
        f"- 成功次数: `{success}`",
        f"- 失败次数: `{failure}`",
        f"- 取消次数: `{cancelled}`",
        f"- 成功率: `{success_rate}%`",
        f"- 平均耗时: `{avg_duration}s`",
        f"- 最长耗时: `{max_duration}s`",
        "",
        "## 风险提示",
        (
            "- 今日高频失败分支: "
            + (", ".join(f"`{b}`({c})" for b, c in top_failed_branches) if top_failed_branches else "无")
        ),
        "",
        "## 按触发事件统计",
    ]

    for k, v in by_event.most_common():
        lines.append(f"- `{k}`: {v}")

    lines.extend(["", "## 按分支统计"])
    for k, v in by_branch.most_common():
        lines.append(f"- `{k}`: {v}")

    lines.extend(["", "## 按发起人统计"])
    for k, v in by_actor.most_common():
        lines.append(f"- `{k}`: {v}")

    lines.extend(["", "## 失败/取消任务清单（最近在前）"])
    if not failed_runs:
        lines.append("- 无")
    else:
        for r in failed_runs[:20]:
            run_id = r.get("id")
            branch = r.get("head_branch")
            conclusion = r.get("conclusion")
            event = r.get("event")
            html_url = r.get("html_url")
            lines.append(f"- run `{run_id}` | `{branch}` | `{event}` | `{conclusion}` | [查看详情]({html_url})")

    lines.extend(["", "## 运行明细（最近在前）"])
    sorted_runs = sorted(runs, key=lambda x: x.get("created_at", ""), reverse=True)
    for r in sorted_runs[:50]:
        run_id = r.get("id")
        name = r.get("display_title") or r.get("name")
        branch = r.get("head_branch")
        event = r.get("event")
        status = r.get("status")
        conclusion = r.get("conclusion")
        html_url = r.get("html_url")
        lines.append(
            f"- `{name}` | run `{run_id}` | branch `{branch}` | event `{event}` | status `{status}/{conclusion}` | [详情]({html_url})"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize daily GitHub Actions runs into markdown")
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY"), help="owner/repo")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--workflow-name", default=WORKFLOW_NAME_DEFAULT, help="Workflow name")
    parser.add_argument("--tz-offset", type=int, default=8, help="Timezone offset hour for date window, e.g. 8")
    parser.add_argument("--output", default=None, help="Output markdown path")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token")
    args = parser.parse_args()

    if not args.repo:
        raise SystemExit("Missing --repo and GITHUB_REPOSITORY")
    if not args.token:
        args.token = load_env_token_from_file()
    if not args.token:
        raise SystemExit("Missing --token and GITHUB_TOKEN")

    wf_id = find_workflow_id(args.repo, args.token, args.workflow_name)
    if not wf_id:
        raise SystemExit(f"Workflow not found by name: {args.workflow_name}")

    runs = list_runs(args.repo, args.token, wf_id)
    day_runs = filter_runs_by_date(runs, args.date, args.tz_offset)
    output = args.output or f"ci-daily-summary-{args.date}.md"
    report = build_report(args.repo, args.date, args.workflow_name, day_runs)
    Path(output).write_text(report, encoding="utf-8")
    print(f"generated: {output} (runs={len(day_runs)})")


if __name__ == "__main__":
    main()
