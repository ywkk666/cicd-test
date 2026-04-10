import yaml
from github import Github
import os
from github import Auth  # 记得在文件顶部加上这行 import

# ================= 配置区 =================
# 1. 在 GitHub 个人设置中生成的 Token
ACCESS_TOKEN = "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" 

# 2. 你的仓库路径，格式为 "用户名/仓库名"
REPO_NAME = "ywkk666/cicd-test" 

# 3. 本地 YAML 文件的名称
YAML_FILE = "tasks.yaml"
# ==========================================

def sync_yaml_to_github():
    # 初始化 GitHub 客户端
    try:
        
        auth = Auth.Token(ACCESS_TOKEN)
        g = Github(auth=auth)
        repo = g.get_repo(REPO_NAME)
    except Exception as e:
        print(f"❌ 连接 GitHub 失败: {e}")
        return

    # 读取本地 YAML 文件
    if not os.path.exists(YAML_FILE):
        print(f"❌ 找不到文件: {YAML_FILE}")
        return

    with open(YAML_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "issues" not in data:
        print("查无任务数据。")
        return

    updated = False
    
    # 遍历任务列表
    for task in data["issues"]:
        # 检查逻辑：如果没有 issue_number，说明是新任务
        if not task.get("issue_number"):
            print(f"🚀 正在同步新任务: {task['title']}")
            
            try:
                # 1. 在 GitHub 上创建 Issue
                # 注意：assignee 必须是有效的 GitHub 用户名，否则会报错
                issue = repo.create_issue(
                    title=task["title"],
                    body=task.get("body", "无描述"),
                    assignee=task.get("assignee") if task.get("assignee") else None,
                    labels=task.get("labels", [])
                )
                
                # 2. 获取 GitHub 返回的信息并回填到内存数据中
                task["issue_number"] = issue.number
                task["branch_name"] = f"feat/task-{issue.number}"
                task["status"] = "todo"
                
                print(f"✅ 已创建 Issue #{issue.number}，并生成分支名: {task['branch_name']}")
                updated = True
                
            except Exception as e:
                print(f"❌ 创建 Issue 失败 [{task['title']}]: {e}")

    # 如果数据有变动，写回 YAML 文件
    if updated:
        with open(YAML_FILE, "w", encoding="utf-8") as f:
            # allow_unicode=True 保证中文不乱码，sort_keys=False 保持原有的字段顺序
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print("\n🎉 所有新任务已同步！请查看并提交 tasks.yaml 文件。")
    else:
        print("\n😴 没有发现需要同步的新任务。")

if __name__ == "__main__":
    sync_yaml_to_github()