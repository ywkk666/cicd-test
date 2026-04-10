import os
import yaml
import subprocess
from pathlib import Path
from github import Github, Auth
from dotenv import load_dotenv

# ================= 配置区 =================
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent                # cicd-test 仓库根目录
ENV_PATH = BASE_DIR / ".env"
YAML_FILE = BASE_DIR / "tasks.yaml"
REPO_NAME = "ywkk666/cicd-test" 

# 核心配置：你的代码区目录
CODE_DIR_NAME = "helloword" 

# 加载 Token
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")
if not ACCESS_TOKEN:
    print(f"❌ 错误: 无法在 {ENV_PATH} 中读取到 GITHUB_TOKEN")
    exit(1)
# ==========================================

def run_git(command):
    """执行 Git 命令并返回是否成功"""
    try:
        result = subprocess.run(
            command, shell=True, check=True, 
            capture_output=True, text=True, encoding="utf-8"
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

def sync_all_in_one():
    print(f"\n{'='*50}")
    print(f"📡 LinkMate 自动化指挥中心 - 正在启动...")
    print(f"{'='*50}")
    print(f"📍 根目录: {PROJECT_ROOT}")
    print(f"📦 目标仓库: {REPO_NAME}")
    print(f"✅ 鉴权状态: Token 已加载 ({ACCESS_TOKEN[:7]}***)")
    
    # --- 阶段 0: 环境同步 ---
    print(f"\n[阶段 0: 基础设施对齐]")
    os.chdir(PROJECT_ROOT)
    
    steps = [
        ("切换至主分支 (main)", "git checkout main"),
        ("拉取云端最新代码 (pull)", "git pull origin main")
    ]
    
    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"  ({i}/2) {desc}...", end=" ", flush=True)
        success, _ = run_git(cmd)
        if success:
            print("✅")
        else:
            print("❌")
            return

    # --- 初始化 GitHub 连接 ---
    g = Github(auth=Auth.Token(ACCESS_TOKEN))
    repo = g.get_repo(REPO_NAME)

    if not YAML_FILE.exists():
        print(f"❌ 错误: 找不到文件 {YAML_FILE}")
        return

    with open(YAML_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    updated = False
    issues_list = data.get("issues", [])
    total_tasks = len(issues_list)

    print(f"\n[阶段 1: 任务流水线处理 (共 {total_tasks} 项)]")

    for idx, task in enumerate(issues_list, 1):
        title = task.get("title", "未命名任务")
        issue_num = task.get("issue_number")
        
        print(f"\n--- 任务 [{idx}/{total_tasks}]: {title} ---")

        # --- 场景 A: 存量任务状态对齐 ---
        if issue_num:
            try:
                print(f"  🔍 步骤: 检查云端 Issue #{issue_num} 状态...", end=" ", flush=True)
                gh_issue = repo.get_issue(int(issue_num))
                
                if gh_issue.state == "closed":
                    if task.get("status") != "done":
                        task["status"] = "done"
                        updated = True
                        print("✅ [已关闭 -> 同步本地]")
                    else:
                        print("✅ [已完成]")
                else:
                    print(f"⏳ [进行中] (PR: {task.get('pr_url', '无')})")
                continue 
            except Exception as e:
                print(f"⚠️  追踪失败: {e}")
                continue

        # --- 场景 B: 全新任务流水线 ---
        # --- 场景 B: 全新任务流水线 ---
        # 1. 创建 Issue 并指派负责人
        print(f"  🚀 步骤 1: 创建 GitHub Issue 并指派负责人...", end=" ", flush=True)
        try:
            # 从任务数据中获取负责人
            target_user = task.get("assignee") 
            
            issue = repo.create_issue(
                title=title,
                body=task.get("body", f"该任务由 LinkMate 自动分配给 {target_user if target_user else '待定'}"),
                # 如果有负责人，则传入列表格式；否则传空列表
                assignees=[target_user] if target_user else []
            )
            
            issue_num = issue.number
            new_branch = f"feat/task-{issue_num}"
            print(f"✅ #{issue_num} (负责人: {target_user if target_user else '未指定'})")
        except Exception as e:
            print(f"❌ 失败: {e}")
            continue

        # 2. 分支创建
        print(f"  🚀 步骤 2: 初始化本地开发分支 [{new_branch}]...", end=" ", flush=True)
        run_git(f"git checkout -b {new_branch}")
        print("✅")

        # 3. 建立快照
        print(f"  🚀 步骤 3: 建立 Git 追踪快照 (空提交)...", end=" ", flush=True)
        run_git(f'git commit --allow-empty -m "feat({CODE_DIR_NAME}): 开启任务 #{issue_num} 分支"')
        print("✅")

        # 4. 推送
        print(f"  🚀 步骤 4: 推送分支至云端仓库...", end=" ", flush=True)
        remote_url = f"https://{ACCESS_TOKEN}@github.com/{REPO_NAME}.git"
        success, err = run_git(f"git push -u {remote_url} {new_branch}")
        run_git(f"git remote set-url origin https://github.com/{REPO_NAME}.git") # 安全重置
        
        if success:
            print("✅")
        else:
            print(f"❌ (原因: {err})")
            continue

        # --- 步骤 5: 开启拉取请求 (PR) ---
        print(f"  🚀 步骤 5: 开启拉取请求 (PR)...", end=" ", flush=True)
        try:
            # 1. 先创建 PR 实体
            pr = repo.create_pull(
                title=f"feat({CODE_DIR_NAME}): {title} (#{issue_num})",
                body=f"Closes #{issue_num}\n\n该任务已自动指派给负责人，请在完成后请求 Review。",
                head=new_branch,
                base="main"
            )

            # 2. 【在此处插入代码】指派负责人 (Assignee)
            target_user = task.get("assignee")
            if target_user:
                pr.add_to_assignees(target_user)

            # 3. 【在此处插入代码】指派审查者 (Reviewer)
            reviewer = task.get("reviewer")
            if reviewer:
                try:
                    # 注意：reviewers 参数必须是一个列表 []
                    pr.create_review_request(reviewers=[reviewer])
                    print(f" ✅ (Reviewer: {reviewer})", end="")
                except Exception as e:
                    print(f" ⚠️ Reviewer指派失败: {e}", end="")

            # 4. 最后更新本地数据状态
            task.update({
                "issue_number": issue_num,
                "branch_name": new_branch,
                "pr_url": pr.html_url,
                "status": "in_progress"
            })
            updated = True
            print(f" ✅")

        except Exception as e:
            print(f" ❌ 失败: {e}")
    # --- 阶段 2: 数据持久化 ---
    print(f"\n[阶段 2: 指挥中心状态存档]")
    if updated:
        os.chdir(BASE_DIR)
        with open(YAML_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"  💾 状态更新: {YAML_FILE.name} 已同步。")
    else:
        print("  😴 无状态变更，无需存档。")
    
    # 归位
    os.chdir(PROJECT_ROOT)
    run_git("git checkout main")
    
    print(f"\n{'='*50}")
    print(f"🎉 自动化流程全部执行完毕！")
    print(f"{'='*50}")

if __name__ == "__main__":
    sync_all_in_one()