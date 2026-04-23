🚀 TaskFlow-Sync: 基于 Excel 的自动化任务分发系统
TaskFlow-Sync 是一套轻量级的任务管理与自动化执行框架。它允许开发者通过熟悉的 Excel 界面管理任务，并自动将其转化为 GitHub Issues 和 Pull Requests，同时保持全流程的状态同步与视觉化反馈。

🌀 自动化闭环流程
本项目通过以下三个核心阶段实现任务的闭环管理：

1. 任务定义 (Input Phase)
操作：在 task_manager.xlsx 中添加或修改任务行。

执行：运行 excel_to_yaml.py。

结果：数据被结构化同步至 tasks.yaml，作为系统唯一的“事实来源”。

2. 任务分发与执行 (Execution Phase)
执行：运行 sync_tasks.py。

流程：

读取 YAML 中的任务，调用 GitHub API 批量创建 Issue。

自动为每个 Issue 创建对应的 Pull Request。

CI 联动：PR 创建瞬间触发 .github/workflows/pr-check.yml 进行自动化测试。

反馈：将生成的 Issue 编号和 PR 链接实时回写到 tasks.yaml。

3. 状态回写 (Feedback Phase)
执行：运行 yaml_to_excel.py。

结果：将 GitHub 的最新状态（ID、链接、状态）同步回 Excel，并根据任务进度（Done/Processing/Error）自动进行单元格上色渲染。
