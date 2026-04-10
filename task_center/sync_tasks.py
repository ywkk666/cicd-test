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
        # 1. 创建 Issue
        print(f"  🚀 步骤 1: 创建 GitHub Issue...", end=" ", flush=True)
        try:
            issue = repo.create_issue(
                title=title,
                body=f"该任务专注于 {CODE_DIR_NAME} 目录的开发。\n\n由 LinkMate 指挥中心自动初始化。"
            )
            issue_num = issue.number
            new_branch = f"feat/task-{issue_num}"
            print(f"✅ #{issue_num}")
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

        # 5. 创建 PR
        print(f"  🚀 步骤 5: 开启拉取请求 (Pull Request)...", end=" ", flush=True)
        try:
            pr = repo.create_pull(
                title=f"feat({CODE_DIR_NAME}): {title} (#{issue_num})",
                body=f"Closes #{issue_num}\n\n该 PR 已由脚本自动创建。请在 `{CODE_DIR_NAME}/` 目录下开始开发。",
                head=new_branch,
                base="main"
            )
            print(f"✅")
            
            # 更新内存数据
            task.update({
                "issue_number": issue_num,
                "branch_name": new_branch,
                "pr_url": pr.html_url,
                "status": "in_progress"
            })
            updated = True
        except Exception as e:
            print(f"❌ 失败: {e}")

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