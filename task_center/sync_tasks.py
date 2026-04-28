import os
import yaml
import subprocess
import time
from pathlib import Path
from github import Github, Auth
from dotenv import load_dotenv
import requests

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

DEFAULT_BASE_BRANCH = "develop"    # 默认合并目标分支
ALLOWED_BASES = ["main", "develop", "test"] # 允许的合法分支白名单
CONTROL_BRANCH = "main"  # 任务中心分支：tasks.yaml 只在该分支维护
CODE_SOURCE_BRANCH = "main"  # 从哪个分支同步业务代码目录到任务分支
CODE_SYNC_DIRS = ["dev_scripts", "test_scripts"]  # 仅同步这些目录
# ==========================================

def run_git(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        return (result.returncode == 0), result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def get_current_branch():
    success, stdout, _ = run_git("git rev-parse --abbrev-ref HEAD")
    if success and stdout:
        return stdout.strip()
    return None

def auto_commit_local_changes():
    print(f"\n📸 [阶段 0.5]: 正在自动保存本地修改到 [{CONTROL_BRANCH}]...")
    run_git(f"git checkout {CONTROL_BRANCH}")
    
    # 2. 检查是否有东西需要提交
    success, status_out, _ = run_git("git status --porcelain")
    if not status_out:
        print("  ✅ 没有检测到改动，无需保存。")
        return

    # 3. 自动提交所有改动 (包含 Excel 和 YAML)
    print("  📝 检测到改动，正在建立本地存档...", end=" ")
    run_git("git add .")
    # 加上 [skip ci] 是为了防止如果你有其他自动化流程被这个 commit 触发
    run_git('git commit -m "chore: 运行脚本前的自动快照 [skip ci]"')
    print("✅ 已保存")

def add_to_project_by_name(token, user_login, project_name, content_id):
    """
    通过项目名称动态查找并添加 Issue/PR
    """
    headers = {"Authorization": f"token {token}"}
    
    # 1. 查找用户下所有的 Projects，并匹配名称
    query_projects = """
    query($login: String!) {
      user(login: $login) {
        projectsV2(first: 20) {
          nodes {
            id
            title
            number
          }
        }
      }
    }
    """
    try:
        resp = requests.post('https://api.github.com/graphql', 
                            json={'query': query_projects, 'variables': {"login": user_login}}, 
                            headers=headers).json()
        
        projects = resp['data']['user']['projectsV2']['nodes']
        # 匹配名称 (忽略大小写)
        target_project = next((p for p in projects if p['title'].lower() == project_name.lower()), None)
        
        if not target_project:
            print(f"    ⚠️ 未找到名为 '{project_name}' 的项目")
            return

        # 2. 执行添加动作
        add_mutation = """
        mutation($project: ID!, $content: ID!) {
          addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
            item { id }
          }
        }
        """
        requests.post('https://api.github.com/graphql', 
                      json={'query': add_mutation, 'variables': {"project": target_project['id'], "content": content_id}}, 
                      headers=headers)
        print(f"    ✅ 已动态关联至 Project: {target_project['title']} (#{target_project['number']})")
        
    except Exception as e:
        print(f"    ❌ Project 联动失败: {e}")

def init_github_repo_with_retry(max_retries=3, delay_seconds=3):
    """
    初始化 GitHub 连接并带重试，避免瞬时网络抖动导致脚本整体崩溃。
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            g = Github(auth=Auth.Token(ACCESS_TOKEN))
            repo = g.get_repo(REPO_NAME)
            return g, repo
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                print(f"⚠️ GitHub API 连接失败，第 {attempt}/{max_retries} 次重试中: {e}")
                time.sleep(delay_seconds)
            else:
                print(f"❌ 无法连接 GitHub API（已重试 {max_retries} 次）: {e}")
    return None, None

def sync_all_in_one():
    print(f"\n{'='*50}\n📡 Github 任务分发中心 - 正在启动...\n{'='*50}")
    print(f"📍 根目录: {PROJECT_ROOT}")
    print(f"📦 目标仓库: {REPO_NAME}")
    print(f"✅ 鉴权状态: Token 已加载 ({ACCESS_TOKEN[:7]}***)")
    
    # --- 阶段 0: 环境同步 ---
    print(f"\n[阶段 0: 基础设施对齐]")
    os.chdir(PROJECT_ROOT)
    steps = [
        (f"切换至任务中心分支 ({CONTROL_BRANCH})", f"git checkout {CONTROL_BRANCH}"),
        (f"拉取云端最新代码 (pull {CONTROL_BRANCH})", f"git pull origin {CONTROL_BRANCH}")
    ]
    
    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"  ({i}/2) {desc}...", end=" ", flush=True)
        success, _, stderr = run_git(cmd)
        if success:
            print("✅")
        else:
            print(f"❌ (原因: {stderr})")
            return

    # --- 初始化 GitHub 连接 ---
    g, repo = init_github_repo_with_retry()
    if not g or not repo:
        return

    if not YAML_FILE.exists():
        print(f"❌ 错误: 找不到文件 {YAML_FILE}")
        return

    with open(YAML_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    updated = False
    issues_list = data.get("issues", [])
    total_tasks = len(issues_list)

    print(f"\n[阶段 1: 任务状态对齐与流水线处理]")

    # =================================================================
    # 【新增 1】: 建立本地 ID 到云端 Issue 编号的映射表（解决冷启动依赖）
    id_to_num_map = {
        task.get('id'): task.get('issue_number') 
        for task in issues_list if task.get('id')
    }
    # =================================================================

    for idx, task in enumerate(issues_list, 1):
        
        issue_num = task.get("issue_number")
        branch_name = task.get("branch_name")
        pr_url = task.get("pr_url")
        target_user = task.get("assignee")
        reviewer_user = task.get("reviewer")
        target_base = task.get("base_branch", DEFAULT_BASE_BRANCH)
        title = task.get("title", "未命名任务")
        
        
        # 【提取新增的 YAML 字段】
        local_id = task.get("id")
        dep_id = task.get("depends_on")
        task_type = task.get("task_type")
        labels_list = task.get("labels", [])
        labels_list = list(set(labels_list + [task_type]))
        milestone_name = task.get("milestone")
        yml_project_name = task.get("project_name") # 提取了看板名称，暂留扩展接口
        title = f"{title} [{task_type}]"
        

        # 分支校验
        ALLOWED_BASES = ["main", "develop", "test"]
        if target_base not in ALLOWED_BASES:
            print(f"\n--- 任务 [{idx}/{total_tasks}]: {title} ---")
            print(f"  ❌ 错误: 不支持的目标分支 '{target_base}'，请检查 YAML 配置。")
            continue
        
        print(f"\n--- 任务 [{idx}/{total_tasks}]: {title} ---")

        # --- 场景 A: 存量任务对齐 ---
        if issue_num:
            print(f"  🔍 步骤 1: 判定云端执行状态 (#{issue_num})...", end=" ", flush=True)
            try:
                gh_issue = repo.get_issue(int(issue_num))
                is_merged = False
                if pr_url:
                    pr_num = int(pr_url.split('/')[-1])
                    is_merged = repo.get_pull(pr_num).is_merged()

                if gh_issue.state == "closed" or is_merged:
                    status_msg = "已合并" if is_merged else "已关闭"
                    if task.get("status") != "done":
                        task["status"] = "done"
                        updated = True
                        print(f"✅ [{status_msg} -> 状态更新为 done]")
                    else:
                        print(f"✅ [已完成]")

                    if branch_name:
                        print(f"  🧹 步骤 2: 清理残留开发分支 [{branch_name}]...", end=" ", flush=True)
                        try:
                            ref = repo.get_git_ref(f"heads/{branch_name}")
                            ref.delete()
                            print(f"✅ [物理删除成功]")
                        except:
                            print(f"ℹ️ [分支此前已清理]")
                        
                        task["branch_name"] = "" 
                        updated = True
                else:
                    print(f"⏳ [进行中] (Issue 开启中 / PR 尚未合并)")
                
                continue # 存量任务处理结束，跳向下一个

            except Exception as e:
                print(f"❌ 追踪失败: {e}")
                continue

        # --- 场景 B: 全新任务流水线 ---
        
        # 【新增 2】: 状态过滤，不是 todo 的不执行
        if task.get("status") and task.get("status") != "todo":
            print(f"  ⏭️ 跳过: 状态为 '{task.get('status')}'")
            continue

        # =================================================================
        # 【新增 3】: 依赖拦截逻辑
        if dep_id:
            target_issue_num = id_to_num_map.get(dep_id)
            if not target_issue_num:
                print(f"  ⏳ 拦截: 依赖任务 [{dep_id}] 尚未生成 Issue。跳过本任务。")
                continue
            
            try:
                remote_issue = repo.get_issue(int(target_issue_num))
                if remote_issue.state != "closed":
                    print(f"  🛑 拦截: 前置任务 #{target_issue_num} 仍在开发中 (未关闭)。跳过本任务。")
                    continue
                print(f"  ✅ 依赖校验通过: 前置任务 #{target_issue_num} 已合并。")
            except Exception as e:
                print(f"  ⚠️ 校验依赖 #{target_issue_num} 失败: {e}")
                continue
        # =================================================================

        # =================================================================
        # 【新增 4】: 获取并匹配 Milestone 对象
        # --- 增强版里程碑匹配 ---
        milestone_obj = None
        if milestone_name:
            # 预处理：去除 YAML 中可能存在的末尾空格
            target_ms_name = str(milestone_name).strip()
            try:
                # 获取所有状态的里程碑（防止你想关联一个刚刚关闭的里程碑）
                milestones = repo.get_milestones(state='all') 
                
                # 调试打印：如果没匹配上，你可以看到当前仓库到底有哪些里程碑
                all_ms_titles = []
                
                for ms in milestones:
                    all_ms_titles.append(ms.title)
                    # 使用 strip() 并忽略大小写进行匹配，增加容错率
                    if ms.title.strip().lower() == target_ms_name.lower():
                        milestone_obj = ms
                        break
                
                if not milestone_obj:
                    print(f"  ⚠️ 未找到里程碑 '{target_ms_name}'。当前仓库可用: {all_ms_titles}")
                else:
                    print(f"  🎯 已匹配里程碑: {milestone_obj.title}")

            except Exception as e:
                print(f"  ⚠️ 无法获取里程碑信息: {e}")
        # =================================================================

        # 1. 创建 Issue
        print(f"  🚀 步骤 1: 创建 GitHub Issue 并指派属性...", end=" ", flush=True)
        try:
            # 【修改 1】: 动态构建 Issue 参数，加入标签和里程碑
            issue_kwargs = {
                "title": title,
                "body": task.get("body", f"该任务由 LinkMate 自动分配。")
            }
            if target_user: issue_kwargs["assignees"] = [target_user]
            if labels_list: issue_kwargs["labels"] = labels_list
            if milestone_obj: issue_kwargs["milestone"] = milestone_obj

            issue = repo.create_issue(**issue_kwargs)
            issue_num = issue.number
            new_branch = f"feat/task-{issue_num}-{task_type}"
            print(f"✅ #{issue_num}")

            # 【新增 5】: 创建成功后，立刻将自己的编号注册到映射表中！供同批次后面的任务使用
            if local_id:
                id_to_num_map[local_id] = issue_num

        except Exception as e:
            print(f"❌ 失败: {e}"); continue
        
        if yml_project_name:
            # 调用我们刚才写的增强版函数
            # 注意：content_id 传的是 issue.node_id
            add_to_project_by_name(ACCESS_TOKEN, "ywkk666", yml_project_name, issue.node_id)

        # ============================================================
        # 🚀 [此处插入：建立 Blocked By 关系代码]
        # ============================================================
        if dep_id:
            parent_issue_num = id_to_num_map.get(dep_id) # 51
            if parent_issue_num:
                # 方案：在 102 的 Body 最顶部插入加粗的关联信息
                dependency_header = f"> ### 🔗 前置任务已完成: #{parent_issue_num}\n\n"
                
                # 更新 102 的 Body
                new_body = dependency_header + issue.body
                issue.edit(body=new_body)
                
                # 额外动作：在 102 评论区留一个脚印，这会在 101 的时间轴里留下反向链接
                issue.create_comment(f"🚀 本任务是 #{parent_issue_num} 的后续步骤，前置任务已确认完成。")
                print(f"    ✅ 已在 #{issue_num} 中建立对已完成任务 #{parent_issue_num} 的引用")

        # 2. 分支创建
        print(f"  🚀 步骤 2: 从 [{target_base}] 初始化开发分支 [{new_branch}]...", end=" ", flush=True)

        # 执行切换
        success, _, stderr = run_git(f"git checkout -B {new_branch} origin/{target_base}")

        # 2. 物理检查 (确认当前脚下踩的分支到底对不对)
        verify_success, verify_stdout, _ = run_git("git rev-parse --abbrev-ref HEAD")
        current_branch = verify_stdout.strip() if verify_success else ""

        if success and current_branch == new_branch:
            print("✅")
        else:
            # 只有在真正失败时才打印原因
            stderr = stderr.strip()
            # 特殊处理：如果 stderr 包含 'set up to track'，这其实是 Git 的废话，可以忽略
            if "set up to track" in stderr and current_branch == new_branch:
                print("✅")
            else:
                print(f"❌ (原因: {stderr if stderr else '分支校验不匹配'})")
                continue

        # 2.5 仅从指定分支同步代码目录，避免把 task_center 中的任务配置带入任务分支
        print(f"  🚀 步骤 2.5: 从 [{CODE_SOURCE_BRANCH}] 同步代码目录 {CODE_SYNC_DIRS}...", end=" ", flush=True)
        copy_failed = False
        for code_dir in CODE_SYNC_DIRS:
            sync_ok, _, sync_err = run_git(f"git checkout {CODE_SOURCE_BRANCH} -- {code_dir}")
            if not sync_ok:
                # 当目录不存在时给出提示并继续，不中断整条任务
                if "did not match any file" in sync_err:
                    print(f"\n    ⚠️ 目录不存在，已跳过: {code_dir}")
                    continue
                copy_failed = True
                print(f"\n    ❌ 同步目录失败 [{code_dir}]: {sync_err}")
                break
        if copy_failed:
            continue
        print("✅")
        
        # 3. 建立快照（包含上一步同步过来的代码目录）
        print(f"  🚀 步骤 3: 建立 Git 追踪快照 (空提交)...", end=" ", flush=True)
        run_git("git add dev_scripts test_scripts")
        run_git(f'git commit --allow-empty -m "feat({CODE_DIR_NAME}): 开启任务 #{issue_num} 分支"')
        print("✅")

        # 4. 推送
        print(f"  🚀 步骤 4: 推送分支至云端仓库...", end=" ", flush=True)
        remote_url = f"https://{ACCESS_TOKEN}@github.com/{REPO_NAME}.git"
        success, _, err = run_git(f"git push -u {remote_url} {new_branch}")
        run_git(f"git remote set-url origin https://github.com/{REPO_NAME}.git")
        if success: print("✅")
        else:
            print(f"❌ (原因: {err})"); continue

        # 5. 创建关联 PR
        print(f"  🚀 步骤 5: 开启拉取请求 (PR) 并同步所有属性...", end=" ", flush=True)
        try:
            target_base = task.get("base_branch", DEFAULT_BASE_BRANCH)
            
            # 【杀手锏动作 1】：动态切换默认分支
            # 只有当目标分支不是当前默认分支时才切换，减少 API 调用
            if repo.default_branch != target_base:
                repo.edit(default_branch=target_base)
                print(f" (已临时将默认分支切至 {target_base})", end="")

            # 【杀手锏动作 2】：创建 PR
            # 必须包含 Closes 关键字，且在默认分支为 target_base 时创建
            pr_body = f"Closes #{issue_num}\n\nLinked via automated deployment."
            pr = repo.create_pull(
                title=f"feat({CODE_DIR_NAME}): {title} (#{issue_num})",
                body=pr_body,
                head=new_branch,
                base=target_base
            )

            # 【新增 6】: 同步 Issue 的标签和里程碑到 PR
            if labels_list:
                try: pr.add_to_labels(*labels_list)
                except: pass
            if milestone_obj:
                try: pr.edit(milestone=milestone_obj)
                except: pass

            if target_user:
                try: pr.add_to_assignees(target_user)
                except: pass
            
            if reviewer_user and reviewer_user != MY_GITHUB_ID:
                try: 
                    pr.create_review_request(reviewers=[reviewer_user])
                    print(f"✅ (R: {reviewer_user})", end="")
                except: 
                    print(f"⚠️ (R指派失败)", end="")
            elif reviewer_user == MY_GITHUB_ID:
                print(f"ℹ️ (跳过自审)", end="")

            print(f" ✅ (PR: {pr.number})")

            target_project_name = task.get("project_name")
            if target_project_name:
                try:
                    # 使用 PR 的 node_id 进行 GraphQL 关联
                    add_to_project_by_name(ACCESS_TOKEN, "ywkk666", target_project_name, pr.node_id)
                except Exception as proj_err:
                    print(f" ⚠️ (PR入板失败: {proj_err})", end="")
            
            # 更新内存数据
            task.update({
                "issue_number": issue_num,
                "branch_name": new_branch,
                "pr_url": pr.html_url,
                "status": "processing" # 使用 processing，下次运行就不会重复触发
            })
            updated = True
        except Exception as e:
            print(f"❌ 失败: {e}")

    # --- 阶段 3: 数据持久化 ---
    print(f"\n[阶段 3: 指挥中心状态存档]")
    if updated:
        # 确保在任务中心分支上更新 tasks.yaml
        os.chdir(PROJECT_ROOT)
        print(f"  🔄 切换到 {CONTROL_BRANCH} 分支进行状态更新...", end=" ")
        run_git(f"git checkout {CONTROL_BRANCH}")
        run_git(f"git pull origin {CONTROL_BRANCH}")
        print("✅")
        
        os.chdir(BASE_DIR)
        with open(YAML_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"  💾 状态更新: {YAML_FILE.name} 已同步。")
        
        # 提交并推送更改到任务中心分支
        os.chdir(PROJECT_ROOT)
        run_git('git add task_center/tasks.yaml')
        run_git('git commit -m "chore: 更新任务状态"')
        run_git(f'git push origin {CONTROL_BRANCH}')
        print(f"  📤 状态更新已推送到 {CONTROL_BRANCH} 分支。")
    else:
        print("  😴 无状态变更。")
    
    # 归位
    os.chdir(PROJECT_ROOT)
    run_git(f"git checkout {CONTROL_BRANCH}")
    print(f"\n{'='*60}\n🎉 自动化流程全部执行完毕！\n{'='*60}")

if __name__ == "__main__":
    auto_commit_local_changes()
    sync_all_in_one()