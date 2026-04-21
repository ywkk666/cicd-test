import pandas as pd
from ruamel.yaml import YAML
import os

# 1. 初始化 YAML 引擎
yaml_engine = YAML()
yaml_engine.preserve_quotes = True
yaml_engine.indent(mapping=2, sequence=4, offset=2)

# 定义你希望在 YAML 中展示的字段顺序
FIELD_ORDER = [
      'id',
  'title',
  'assignee',
  'reviewer',
  'base_branch',
  'milestone',
  'depends_on',
  'project_name',
  'labels',
  'body',
  'status',
  'issue_number',
  'branch_name',
  'pr_url'
]

def sync_excel_to_yaml_final():
    base_path = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(base_path, "task_manager.xlsx")
    yaml_path = os.path.join(os.path.dirname(base_path), "tasks.yaml")

    print(f"🔄 正在按照 'issues' 结构进行精准增量同步...")

    # --- 1. 读取 YAML 并保护非任务字段 ---
    header_config = {}
    master_tasks = {} # 用 ID 作为 Key 强制去重

    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                content = yaml_engine.load(f)
                
                if isinstance(content, dict):
                    # 保护所有非 'issues' 的全局配置 (project, repo 等)
                    header_config = {k: v for k, v in content.items() if k != 'issues'}
                    
                    # 读取旧任务并压入字典去重
                    old_issues = content.get('issues', [])
                    if isinstance(old_issues, list):
                        for t in old_issues:
                            if isinstance(t, dict) and 'id' in t:
                                tid = int(float(t['id']))
                                master_tasks[tid] = t # 旧数据暂存
                else:
                    print("⚠️ YAML 格式异常，将初始化新结构。")
        except Exception as e:
            print(f"⚠️ 读取旧 YAML 失败: {e}")

    # --- 2. 读取 Excel 数据 ---
    try:
        df = pd.read_excel(excel_path)
        # 彻底清洗 .nan 脏数据
        df = df.where(pd.notnull(df), None)
        excel_rows = df.to_dict(orient='records')
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        return

    # --- 3. 核心同步逻辑 (对比 ID, 更新或增量添加) ---
    for row in excel_rows:
        if row.get('id') is None or str(row.get('id')).strip() == "":
            continue
        
        curr_id = int(float(row['id']))
        old_task = master_tasks.get(curr_id, {}) # 查找是否存在重复 ID

        new_entry = {}
        for key in FIELD_ORDER:
            # 特别处理：如果 Excel 里的字段名和 FIELD_ORDER 不完全一致，做兼容
            excel_val = row.get(key)
            yaml_val = old_task.get(key)

            # A. 标签处理
            if key == 'labels':
                if isinstance(excel_val, str):
                    new_entry[key] = [l.strip() for l in excel_val.split(',') if l.strip()]
                else:
                    new_entry[key] = excel_val if excel_val is not None else (yaml_val or [])
            
            # B. 更新与保护逻辑
            # 如果 Excel 填了内容，同步更新到 YAML (要求 2)
            elif excel_val is not None and str(excel_val).strip() != "":
                if key in ['id', 'depends_on']:
                    try: new_entry[key] = int(float(excel_val))
                    except: new_entry[key] = excel_val
                else:
                    new_entry[key] = excel_val
            
            # C. 如果 Excel 没填，保留 YAML 既有值 (保护 issue_number, branch_name 等)
            else:
                new_entry[key] = yaml_val

        # 强制覆盖字典中的 ID，实现去重 (要求 3)
        master_tasks[curr_id] = new_entry

    # --- 4. 排序并写回 ---
    # 按照 ID 升序排列
    sorted_issues = [master_tasks[tid] for tid in sorted(master_tasks.keys())]
    
    # 重新组装 (要求 4: 保护 header)
    final_output = header_config.copy()
    final_output['issues'] = sorted_issues

    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml_engine.dump(final_output, f)
        print(f"✨ 同步成功！")
        print(f"📊 已处理 ID 列表: {list(master_tasks.keys())}")
    except Exception as e:
        print(f"❌ 写入 YAML 失败: {e}")

if __name__ == "__main__":
    sync_excel_to_yaml_final()