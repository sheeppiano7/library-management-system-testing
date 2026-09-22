# 多数据库图书管理系统：测试与缺陷闭环

面向管理员、操作员和查看员的 Flask 图书管理系统。项目支持图书、读者、借阅、归还、库存和权限管理，并使用 MySQL、SQL Server、PostgreSQL 三套数据库验证业务数据一致性。

> 本仓库来自独立测试与修复副本。公开版本已移除真实数据库口令、邮箱授权码、日志、数据库文件及本机绝对路径，不会连接原 `book_manage` 数据库。

## 测试结果

| 阶段 | 用例 | 通过 | 失败 | 结论 |
|---|---:|---:|---:|---|
| 首轮唯一用例 | 70 | 61 | 9 | 高优先级缺陷未关闭，暂不验收 |
| 修复后原用例回归 | 70 | 70 | 0 | 通过 |
| 新增专项回归 | 31 | 31 | 0 | 通过 |
| Postman 接口验证 | 31 个请求 / 64 项断言 | 全部通过 | 0 | 通过 |
| Selenium + pytest UI 自动化 | 19 | 19 | 0 | 通过 |

原有 70 项与新增 31 项合计 **101 项全部通过**。结论仅覆盖登录、图书、读者、借还、库存、权限和逾期查询；同步、邮件、报表未纳入本轮测试。

## 代表性问题与闭环

- 连续 3 轮复现“库存为 1，却生成 2 条借阅记录”的并发超借，使用数据库条件更新实现原子扣减并回归通过。
- 修复库存非数字、借阅参数缺失导致的 HTTP 500，将非法输入转为明确的 400 响应与页面提示。
- 在请求结束时释放数据库会话，验证连续请求下连接池不再耗尽。
- 按借阅日期和未归还状态查询实际逾期记录，修复只依赖旧标志造成的漏查。
- 使用禅道维护用例、缺陷、严重程度、优先级、复现步骤和关闭记录。

## 仓库结构

```text
app/             Flask 应用修复副本（配置已脱敏）
database/        三种数据库的建表、合成初始化脚本与关键快照
tests/api/       Postman Collection 与公开环境模板
tests/ui/        Selenium + pytest + Page Object 用例
docs/            缺陷修复记录、执行记录与可浏览的回归报告
```

## 本地运行

1. 新建三套专用测试库，例如 `book_manage_test_demo`，不要使用生产或原始业务库。
2. 复制 `.env.example` 中的变量到本机环境，并填写自己的测试数据库连接。
3. 安装依赖：`pip install -r app/requirements.txt`
4. 在 `app` 目录运行：`python app.py`

接口用例可直接导入 `tests/api/library.postman_collection.json` 和公开环境模板；UI 用例安装 `tests/requirements.txt` 后执行 `pytest tests/ui -v --html=ui-report.html --self-contained-html`。

配置默认关闭跨库同步、邮件和定时任务；应用还会拒绝数据库名恰好为 `book_manage` 的连接串。

## 证据索引

- [第二轮回归测试报告](docs/regression-report.md)
- [缺陷修复记录](docs/defect-fix-record.md)
- [逐条执行记录](docs/execution-record.md)
- [Selenium HTML 报告](docs/selenium-report.html)
- [脱敏数据库复现材料](database/README.md)

## 范围说明

本仓库用于作品展示与测试方法复现。并发规模为双会话，连续请求验证不等同于长时间压力测试；三库采用页面、服务层响应和数据库快照组合核对。
