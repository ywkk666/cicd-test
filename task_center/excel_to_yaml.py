import pandas as pd
from ruamel.yaml import YAML
import os

# 1. 初始化 YAML 引擎
yaml_engine = YAML()
yaml_engine.preserve_quotes = True
yaml_engine.indent(mapping=2, sequence=4, offset=2)

# 定义字段顺序
FIELD_ORDER = [
    'id', 'title', 'task_type', 'assignee', 'reviewer', 'base_branch',
    'milestone', 'depends_on', 'project_name', 'labels',
    'body', 'status', 'issue_number', 'branch_name', 'pr_url'
]

def sync_excel_to_yaml_final():
    base_path = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(base_path, "task_manager.xlsx")
    yaml_path = os.path.join(base_path, "tasks.yaml")

    print(f"🔄 正在按照 'issues' 结构进行精准增量同步...")

    header_config = {}
    master_tasks = {}

    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                content = yaml_engine.load(f)
                if isinstance(content, dict):
                    header_config = {k: v for k, v in content.items() if k != 'issues'}
                    old_issues = content.get('issues', [])
                    if isinstance(old_issues, list):
                        for t in old_issues:
                            if isinstance(t, dict) and 'id' in t:
                                # 这里也加上 float 到 int 的转换保护，防止旧 YAML 里的 id 带小数点
                                tid = int(float(t['id']))
                                master_tasks[tid] = t
        except Exception as e:
            print(f"⚠️ 读取旧 YAML 失败: {e}")

    try:
        df = pd.read_excel(excel_path)
        # 即使这里做了处理，循环内仍需二次清洗，因为 Pandas 的 NaN 对象比较顽固
        df = df.where(pd.notnull(df), None)
        excel_rows = df.to_dict(orient='records')
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        return

    for row in excel_rows:
        if row.get('id') is None or str(row.get('id')).strip() == "":
            continue
        
        curr_id = int(float(row['id']))
        old_task = master_tasks.get(curr_id, {})

        new_entry = {}
        for key in FIELD_ORDER:
            excel_val = row.get(key)
            yaml_val = old_task.get(key)

            # --- 修改位置 1：增加全局脏数据清洗 ---
            # 强制将所有形态的 "nan"（无论是 Pandas 产生的还是 YAML 读进来的字符串）转为 None
            if str(excel_val).lower() == "nan" or excel_val is None:
                excel_val = None
            if str(yaml_val).lower() == "nan" or yaml_val is None:
                yaml_val = None
            # -----------------------------------

            # A. 标签处理
            if key == 'labels':
                if isinstance(excel_val, str):
                    new_entry[key] = [l.strip() for l in excel_val.split(',') if l.strip()]
                else:
                    # --- 修改位置 2：确保默认值是空列表 [] 而不是 None ---
                    # 这样可以防止 YAML 在该字段显示 null 或 .nan
                    new_entry[key] = excel_val if excel_val is not None else (yaml_val or [])
            
            # B. 更新与保护逻辑
            elif excel_val is not None and str(excel_val).strip() != "":
                # --- 修改位置 3：扩展数字转换保护名单 ---
                # 将 issue_number 也纳入整数转换，防止 Excel 把 105 读成 105.0
                if key in ['id', 'depends_on', 'issue_number']: 
                    try: 
                        new_entry[key] = int(float(excel_val))
                    except: 
                        new_entry[key] = excel_val
                else:
                    new_entry[key] = excel_val
            
            # C. 如果 Excel 没填，保留 YAML 既有值
            else:
                new_entry[key] = yaml_val

        master_tasks[curr_id] = new_entry

    sorted_issues = [master_tasks[tid] for tid in sorted(master_tasks.keys())]
    final_output = header_config.copy()
    final_output['issues'] = sorted_issues

    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml_engine.dump(final_output, f)
        print(f"✨ 同步成功！")
    except Exception as e:
        print(f"❌ 写入 YAML 失败: {e}")

if __name__ == "__main__":
    sync_excel_to_yaml_final()