import os
from ruamel.yaml import YAML

def run_task_logic():
    # 1. 自动定位 tasks.yaml 的路径（假设它在 test1.py 的上一级目录的上一级）
    base_path = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(os.path.dirname(base_path), "tasks.yaml")
    
    print(f"🚀 正在启动任务执行器...")
    print(f"📂 正在读取配置文件: {yaml_path}")

    # 2. 检查文件是否存在
    if not os.path.exists(yaml_path):
        print("❌ 错误: 找不到 tasks.yaml 文件！")
        exit(1)

    # 3. 加载并解析 YAML
    yaml = YAML()
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f)
            
        project_name = data.get('project', 'Unknown')
        issues = data.get('issues', [])
        
        print(f"✅ 成功加载项目: {project_name}")
        print(f"📊 发现 {len(issues)} 个待处理任务\n")

        # 4. 模拟任务执行逻辑
        for task in issues:
            task_id = task.get('id')
            title = task.get('title')
            assignee = task.get('assignee')
            
            # 简单的业务规则：必须有 ID 和标题，否则视为无效任务
            if not task_id or not title:
                print(f"⚠️ 发现无效任务数据: {task}")
                continue
                
            print(f"🔎 [ID: {task_id}] 正在处理: {title} (负责人: {assignee})")
            
            # 这里可以放你真正的业务逻辑，比如：
            # if task.get('status') == 'todo':
            #     do_something()

        print("\n✨ 所有任务逻辑模拟运行完毕！")

    except Exception as e:
        print(f"❌ 运行过程中出错: {e}")
        exit(1) # 只有退出码非 0，CI 流水线才会报红

if __name__ == "__main__":
    run_task_logic()