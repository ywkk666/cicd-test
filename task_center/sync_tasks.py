import os
import yaml
import subprocess
from pathlib import Path
from github import Github, Auth
from dotenv import load_dotenv

# ================= 配置区 =================
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
ENV_PATH = BASE_DIR / ".env"
YAML_FILE = BASE_DIR / "tasks.yaml"
REPO_NAME = "ywkk666/cicd-test" 

CODE_DIR_NAME = "helloword" 
MY_GITHUB_ID = "ywkk666"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

ACCESS_TOKEN = os.getenv("GITHUB_TOKEN")
if not ACCESS_TOKEN:
    print(f"❌ 错误: 无法在 {ENV_PATH} 中读取到 GITHUB_TOKEN")
    exit(1)
# ==========================================

def run_git(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding="utf-8")
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

def sync_all_in_one():
    print(f"\n{'='*50}\n📡 Github 任务分发中心 - 正在启动...\n{'='*50}")
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

    print(f"\n[阶段 1: 任务状态对齐与流水线处理]")

    for idx, task in enumerate(issues_list, 1):
        title = task.get("title", "未命名任务")
        issue_num = task.get("issue_number")
        branch_name = task.get("branch_name")
        pr_url = task.get("pr_url")
        
        print(f"\n--- 任务 [{idx}/{total_tasks}]: {title} ---")

        # --- 场景 A: 存量任务对齐 (可视化增强版) ---
        if issue_num:
            print(f"  🔍 步骤 1: 判定云端执行状态 (#{issue_num})...", end=" ", flush=True)
            try:
                # 1.1 获取云端实时数据
                gh_issue = repo.get_issue(int(issue_num))
                is_merged = False
                if pr_url:
                    pr_num = int(pr_url.split('/')[-1])
                    is_merged = repo.get_pull(pr_num).is_merged()

                # 1.2 逻辑定性
                if gh_issue.state == "closed" or is_merged:
                    # 确定已完成
                    status_msg = "已合并" if is_merged else "已关闭"
                    if task.get("status") != "done":
                        task["status"] = "done"
                        updated = True
                        print(f"✅ [{status_msg} -> 状态更新为 done]")
                    else:
                        print(f"✅ [已完成]")

                    # 1.3 执行清理动作
                    if branch_name:
                        print(f"  🧹 步骤 2: 清理残留开发分支 [{branch_name}]...", end=" ", flush=True)
                        try:
                            ref = repo.get_git_ref(f"heads/{branch_name}")
                            ref.delete()
                            print(f"✅ [物理删除成功]")
                        except:
                            print(f"ℹ️ [分支此前已清理]")
                        
                        task["branch_name"] = "" # 彻底抹除记录
                        updated = True
                    continue # 存量任务处理结束，跳向下一个
                else:
                    # 仍然在进行中
                    print(f"⏳ [进行中] (Issue 开启中 / PR 尚未合并)")
                    continue 

            except Exception as e:
                print(f"❌ 追踪失败: {e}")
                continue

        # --- 场景 B: 全新任务流水线 ---
        print(f"\n--- 任务 [{idx}/{total_tasks}]: {title} ---")

        # 1. 创建 Issue 并指派负责人
        print(f"  🚀 步骤 1: 创建 GitHub Issue 并指派负责人...", end=" ", flush=True)
        try:
            issue = repo.create_issue(
                title=title,
                body=task.get("body", f"该任务由 LinkMate 自动分配给 {target_user if target_user else '待定'}"),
                assignees=[target_user] if target_user else []
            )
            issue_num = issue.number
            new_branch = f"feat/task-{issue_num}"
            print(f"✅ #{issue_num} (负责人: {target_user if target_user else '未指定'})")
        except Exception as e:
            print(f"❌ 失败: {e}"); continue

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
        run_git(f"git remote set-url origin https://github.com/{REPO_NAME}.git")
        if success: print("✅")
        else:
            print(f"❌ (原因: {err})"); continue

        # 5. 创建关联 PR
        print(f"  🚀 步骤 5: 开启拉取请求 (PR) 并同步负责人...", end=" ", flush=True)
        try:
            pr = repo.create_pull(
                title=f"feat({CODE_DIR_NAME}): {title} (#{issue_num})",
                body=f"Closes #{issue_num}\n\n该 PR 由 LinkMate 自动指派。",
                head=new_branch, base="main"
            )
            if target_user:
                try: pr.add_to_assignees(target_user)
                except: pass
            
            # 指派 Reviewer (跳过自己)
            if reviewer_user and reviewer_user != MY_GITHUB_ID:
                try: pr.create_review_request(reviewers=[reviewer_user])
                except: pass

            print(f" ✅ (PR: {pr.number})")
            
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

    # --- 阶段 3: 数据持久化 ---
    print(f"\n[阶段 3: 指挥中心状态存档]")
    if updated:
        os.chdir(BASE_DIR)
        with open(YAML_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"  💾 状态更新: {YAML_FILE.name} 已同步。")
    else:
        print("  😴 无状态变更。")
    
    # 归位
    os.chdir(PROJECT_ROOT)
    run_git("git checkout main")
    print(f"\n{'='*60}\n🎉 自动化流程全部执行完毕！\n{'='*60}")

if __name__ == "__main__":
    sync_all_in_one()