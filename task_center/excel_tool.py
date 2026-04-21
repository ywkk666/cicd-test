import pandas as pd
from ruamel.yaml import YAML

yaml_engine = YAML()
yaml_engine.preserve_quotes = True

def excel_to_yaml(excel_file, yaml_file):
    """从 Excel 同步任务到 YAML，支持空值处理"""
    try:
        df = pd.read_excel(excel_file)
        # 核心：将所有空单元格统一转为 Python 的 None
        df = df.where(pd.notnull(df), None)
        tasks_raw = df.to_dict(orient='records')
        
        final_tasks = []
        for task in tasks_raw:
            # 1. 过滤逻辑：如果 id 和 title 都没写，说明是无效空行
            if task.get('id') is None and task.get('title') is None:
                continue

            # 2. 文本字段处理（status, assignee, body, milestone, project_name）
            # 这些字段即使是空（None）也没关系，YAML 会识别为 null
            # 我们可以给 status 设置一个默认值
            if task.get('status') is None:
                task['status'] = 'todo'  # 默认新任务为待办

            # 3. 标签字段处理
            if isinstance(task.get('labels'), str):
                task['labels'] = [l.strip() for l in task['labels'].split(',') if l.strip()]
            else:
                task['labels'] = task.get('labels') or [] # 保证是列表

            # 4. 数字字段（硬性要求）：id 必须有
            try:
                if task.get('id') is not None:
                    task['id'] = int(float(task['id']))
                else:
                    print(f"⚠️ 跳过：任务 '{task.get('title')}' 缺少 ID")
                    continue
            except:
                print(f"⚠️ 跳过：任务 '{task.get('title')}' 的 ID 格式非法")
                continue

            # 5. 数字字段（可选）：depends_on
            if task.get('depends_on') is not None:
                try:
                    task['depends_on'] = int(float(task['depends_on']))
                except:
                    task['depends_on'] = None # 填写错误则清空
            
            final_tasks.append(task)
                    
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml_engine.dump(final_tasks, f)
        print(f"✅ 第一步: 转换完成，共处理 {len(final_tasks)} 个有效任务")
        
    except Exception as e:
        raise Exception(f"Excel 转换 YAML 失败: {e}")

def yaml_to_excel(yaml_file, excel_file):
    """将 GitHub 执行后的 YAML 状态回写到 Excel"""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        tasks = yaml_engine.load(f)
    
    for task in tasks:
        if isinstance(task.get('labels'), list):
            task['labels'] = ", ".join(task['labels'])
            
    df = pd.DataFrame(tasks)
    # 按照管理者习惯排列列顺序
    cols = ['id', 'title', 'status', 'assignee', 'milestone', 'depends_on', 
            'issue_number', 'pr_url', 'project_name', 'labels', 'body']
    df = df[cols]
    df.to_excel(excel_file, index=False)
    print("✅ 第三步：YAML 最新状态已同步回 Excel")