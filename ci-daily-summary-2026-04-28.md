# CI 每日汇总报告（本地生成）

- 仓库: `ywkk666/cicd-test`
- 日期: `2026-04-28`
- 流水线: `Task Type Pipeline`

## 一页结论（给非技术同学）
今天共触发 **28** 次流水线，成功 **23** 次，失败 **5** 次，取消 **0** 次，成功率 **82.14%**。
整体建议：流程稳定，可继续按当前节奏推进。

## 统计数据
- 总运行次数: `28`
- 成功次数: `23`
- 失败次数: `5`
- 取消次数: `0`
- 成功率: `82.14%`
- 平均耗时: `29s`
- 最长耗时: `37s`

## 风险提示
- 今日高频失败分支: `main`(2), `feat/task-167-dev`(2), `develop`(1)

## 按触发事件统计
- `push`: 17
- `pull_request`: 11

## 按分支统计
- `main`: 13
- `feat/task-167-dev`: 2
- `feat/task-165-test`: 2
- `develop`: 2
- `feat/task-163-dev`: 1
- `feat/task-161-test`: 1
- `feat/task-159-dev`: 1
- `feat/task-157-test`: 1
- `feat/task-155-dev`: 1
- `feat/task-152-test`: 1
- `feat/task-146-test`: 1
- `feat/task-141-test`: 1
- `feat/task-139-dev`: 1

## 按发起人统计
- `ywkk666`: 28

## 失败/取消任务清单（最近在前）
- run `25041352187` | `main` | `push` | `failure` | [查看详情](https://github.com/ywkk666/cicd-test/actions/runs/25041352187)
- run `25041343425` | `feat/task-167-dev` | `pull_request` | `failure` | [查看详情](https://github.com/ywkk666/cicd-test/actions/runs/25041343425)
- run `25041341395` | `feat/task-167-dev` | `push` | `failure` | [查看详情](https://github.com/ywkk666/cicd-test/actions/runs/25041341395)
- run `25041257043` | `develop` | `push` | `failure` | [查看详情](https://github.com/ywkk666/cicd-test/actions/runs/25041257043)
- run `25040118495` | `main` | `push` | `failure` | [查看详情](https://github.com/ywkk666/cicd-test/actions/runs/25040118495)

## 运行明细（最近在前）
- `chore: 更新任务状态` | run `25041352187` | branch `main` | event `push` | status `completed/failure` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25041352187)
- `feat(helloword): cicd测试02 [dev] (#167)` | run `25041343425` | branch `feat/task-167-dev` | event `pull_request` | status `completed/failure` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25041343425)
- `feat(helloword): 开启任务 #167 分支` | run `25041341395` | branch `feat/task-167-dev` | event `push` | status `completed/failure` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25041341395)
- `feat(helloword): cicd测试01 [test] (#165)` | run `25041330132` | branch `feat/task-165-test` | event `pull_request` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25041330132)
- `feat(helloword): 开启任务 #165 分支` | run `25041327540` | branch `feat/task-165-test` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25041327540)
- `11` | run `25041257043` | branch `develop` | event `push` | status `completed/failure` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25041257043)
- `11` | run `25040118495` | branch `main` | event `push` | status `completed/failure` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25040118495)
- `最终脚本` | run `25039160085` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25039160085)
- `chore: 更新任务状态` | run `25039119440` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25039119440)
- `feat(helloword): cicd测试02 [dev] (#163)` | run `25039112101` | branch `feat/task-163-dev` | event `pull_request` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25039112101)
- `feat(helloword): cicd测试01 [test] (#161)` | run `25039097568` | branch `feat/task-161-test` | event `pull_request` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25039097568)
- `chore: 更新任务状态` | run `25038946512` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25038946512)
- `feat(helloword): cicd测试02 [dev] (#159)` | run `25038939137` | branch `feat/task-159-dev` | event `pull_request` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25038939137)
- `feat(helloword): cicd测试01 [test] (#157)` | run `25038929418` | branch `feat/task-157-test` | event `pull_request` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25038929418)
- `chore: 更新任务状态` | run `25038547659` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25038547659)
- `feat(helloword): cicd测试02 [dev] (#155)` | run `25038538977` | branch `feat/task-155-dev` | event `pull_request` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25038538977)
- `chore: 更新任务状态` | run `25038477151` | branch `develop` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25038477151)
- `chore: 更新任务状态` | run `25038416958` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25038416958)
- `feat(helloword): cicd测试01 [test] (#152)` | run `25038376481` | branch `feat/task-152-test` | event `pull_request` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25038376481)
- `chore: 更新任务状态` | run `25036900585` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25036900585)
- `feat(helloword): cicd测试01 [test] (#146)` | run `25036876421` | branch `feat/task-146-test` | event `pull_request` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25036876421)
- `11` | run `25035316030` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25035316030)
- `Merge branch 'main' of github.com:ywkk666/cicd-test` | run `25035284224` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25035284224)
- `111` | run `25031070483` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25031070483)
- `chore: 更新任务状态` | run `25030191596` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25030191596)
- `feat(helloword): cicd测试01 [test] (#141)` | run `25030184773` | branch `feat/task-141-test` | event `pull_request` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25030184773)
- `chore: 更新任务状态` | run `25029281951` | branch `main` | event `push` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25029281951)
- `feat(helloword): cicd测试02 [dev] (#139)` | run `25029275928` | branch `feat/task-139-dev` | event `pull_request` | status `completed/success` | [详情](https://github.com/ywkk666/cicd-test/actions/runs/25029275928)
