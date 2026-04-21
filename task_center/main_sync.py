import sys
import os
from excel_tool import excel_to_yaml, yaml_to_excel

# 这样无论你在哪个目录下运行脚本，路径都不会错
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 拼接完整的绝对路径
EXCEL_PATH = os.path.join(CURRENT_DIR, "task_manager.xlsx")
YAML_PATH = os.path.join(CURRENT_DIR, "tasks.yaml")

def run_pipeline():
    print("=== 🚀 开始执行任务同步流 ===")

    # --- 步骤 1: Excel ➔ YAML ---
    print("\n[Step 1/3] 正在从 Excel 同步新任务到 YAML...")
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ 终止：找不到 Excel 文件 {EXCEL_PATH}")
        sys.exit(1) # 异常退出
    
    try:
        excel_to_yaml(EXCEL_PATH, YAML_PATH)
        print("✅ 步骤 1 成功")
    except Exception as e:
        print(f"❌ 步骤 1 失败：Excel 格式可能错误或文件被占用。\n详情: {e}")
        sys.exit(1) # 发生错误，立即停止，不运行 GitHub 脚本

    # --- 步骤 2: 运行 GitHub 自动化 (sync_tasks.py) ---
    print("\n[Step 2/3] 正在连接 GitHub 并处理 Issue/PR...")
    try:
        # 导入你的 GitHub 同步脚本
        from sync_tasks import sync_all_in_one 
        
        # 运行主逻辑
        sync_all_in_one() 
        print("✅ 步骤 2 成功")
    except ImportError:
        print("❌ 终止：找不到 sync_tasks.py 脚本文件")
        sys.exit(1)
    except Exception as e:
        # 如果 GitHub API 报错（如网络断开、Token 失效等）
        print(f"❌ 步骤 2 失败：GitHub 自动化运行中断。\n详情: {e}")
        print("⚠️  为了保护数据一致性，流程已停止，不会回写 Excel。")
        sys.exit(1) # 发生错误，立即停止，不回写 Excel

    # --- 步骤 3: YAML ➔ Excel ---
    print("\n[Step 3/3] 正在将最新状态回写至 Excel...")
    try:
        yaml_to_excel(YAML_PATH, EXCEL_PATH)
        print("✅ 步骤 3 成功")
    except Exception as e:
        print(f"❌ 步骤 3 失败：无法更新 Excel 文件（请检查文件是否被 PM 打开）。\n详情: {e}")
        sys.exit(1)

    print("\n=== ✨ 所有流程处理完毕，数据已同步 ===\n")

if __name__ == "__main__":
    run_pipeline()