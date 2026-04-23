# 🚀 TaskFlow-Sync: 基于 Excel 的自动化任务分发系统

**TaskFlow-Sync** 是一套轻量级的任务管理与自动化执行框架。它允许开发者通过熟悉的 **Excel** 界面管理任务，并自动将其转化为 **GitHub Issues 和 Pull Requests**，同时保持全流程的状态同步与视觉化反馈。

---

## 🌀 自动化闭环流程

本项目通过以下三个核心阶段实现任务的闭环管理：

### 1. 任务定义 (Input Phase)
* **操作**：在 `task_manager.xlsx` 中添加或修改任务行。
* **执行**：运行 `excel_to_yaml.py`。
* **结果**：数据被结构化同步至 `tasks.yaml`，作为系统唯一的**“事实来源” (Single Source of Truth)**。

### 2. 任务分发与执行 (Execution Phase)
* **执行**：运行 `sync_tasks.py`。
* **流程细节**：
    1.  **API 调用**：读取 YAML 中的任务，调用 GitHub REST API 批量创建 Issue。
    2.  **PR 创建**：自动为每个 Issue 创建对应的 Pull Request 分支。
    3.  **CI 联动**：PR 创建瞬间触发 `.github/workflows/pr-check.yml` 进行自动化测试。
    4.  **实时反馈**：将生成的 Issue 编号和 PR 链接实时回写到 `tasks.yaml`。

### 3. 状态回写 (Feedback Phase)
* **执行**：运行 `yaml_to_excel.py`。
* **结果**：
    * **数据对齐**：将 GitHub 的最新状态（ID、链接、状态）同步回 Excel。
    * **视觉渲染**：根据任务进度（`Done` / `Processing` / `Error`）自动进行单元格**颜色填充**。

---

## 📂 快速上手
1.  **编辑 Excel**：在 `task_manager.xlsx` 填写任务。
2.  **同步本地**：`python excel_to_yaml.py`
3.  **分发至云端**：`python sync_tasks.py`
4.  **刷新看板**：`python yaml_to_excel.py`

---
*Created by ywkk666 © 2026*