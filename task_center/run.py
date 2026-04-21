# run.py 示例逻辑
import subprocess

def run_pipeline():
    steps = [
        ("Excel -> YAML", "python task_center/excel_to_yaml.py"),
        ("GitHub 执行 (API)", "python task_center/sync_tasks.py"),
        ("YAML -> Excel (回写上色)", "python task_center/yaml_to_excel.py")
    ]
    
    for desc, cmd in steps:
        print(f"执行中: {desc}...")
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"❌ {desc} 失败，流程终止。")
            break
    print("🎉 全流程执行完毕！")

if __name__ == "__main__":
    run_pipeline()