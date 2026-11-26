# v0.2 Round 1 审查与实施方案

## 现状与问题

审查范围：src/rag_toolkit/web/、api/service.py、pipeline/retrieval.py、evaluation/、tests/test_web.py、pyproject.toml 与 .github/workflows/ci.yml。

1. Search 仅支持查询和最终 Top K，缺少召回模式、各通道 Top K、融合和重排控制；尚无加载状态。
2. Inspector 使用 trace 顺序连接 BM25 → Dense → Fusion，ranking_rows 也计算相邻 trace 的排名差，造成独立召回通道的语义混淆。
3. Inspector 已保留最终被淘汰候选，但没有显式状态列、分通道候选表和 trace 下载。
4. 没有 Compare、统一 i18n 或 .streamlit/config.toml；文案以中文为主。
5. 当前 service 不保留有效配置及索引指纹，不能安全地在 UI 增加模型切换。
6. 现有异常处理多数使用固定安全文案，可沿用；新增 Settings 不应反射 embedder.__dict__，其中可能包含 api_key/client。
7. datasets 的 clear_results 只清理 Search/Evaluation，新增 Compare 后需要同步失效。
8. 已有离线 AppTest 覆盖数据导入→Search→Inspector→Evaluation，必须保留会话隔离行为。
9. CI 使用 uv sync --locked，并额外检查 ruff format；新增 Plotly 必须同步 uv.lock，保留现有检查。

## 实现方向

沿用现有 RetrievalPipeline 与 RetrievalService，增加 Web 适配服务层。直接在页面临时修改共享 pipeline 容易残留查询参数；每次构造完整新索引则导致重复嵌入和比较耗时失真。选择在 service 锁内创建轻量查询视图，共享不可变索引组件、独立持有查询参数，不改变原 pipeline。

## 模块分层

- web/i18n.py：集中 zh/en 字典及格式化函数；导航页面 ID 稳定，语言切换不改变数据。
- web/services/configuration.py：递归脱敏与允许导出的配置结构；拒绝导出任意模型对象。处理嵌套列表、大小写敏感字段、Authorization、URL 凭据与 token 查询参数。
- web/services/index_state.py：有效 embedding/provider/model/dimension/endpoint、splitter/store 配置生成指纹；查询参数不参与。模型配置变化后禁止调用旧 dense 索引；重建使用新实例，成功后原子替换，失败不激活新配置。
- web/services/query.py：校验 QueryOptions（模式、两路召回 K、最终 K、融合方法、RRF K、权重、重排开关和候选数），通过现有检索链路执行，不改 FastAPI 契约。
- web/services/comparison.py：真实运行五种方案，返回独立 SearchResponse、参数快照、计时与可选评测指标；不支持的 dense/reranker 显示 unavailable，不伪造结果。
- web/services/bad_cases.py：基于标注和实际 trace 判定未召回、融合后丢失、重排后丢失，仅作为可解释启发式，不宣称因果。
- web/inspector.py：保持纯 Python 展示数据转换；独立通道不互算排名变化，Fusion 分别保存相对 BM25/Dense 的差值。
- web/charts.py：Plotly 图形函数，透明背景、使用 Streamlit 原生主题；路径分别为 BM25→Fusion→Reranker 和 Dense→Fusion→Reranker。
- web/search.py、inspection.py、compare.py：输入、加载/空/错误状态、表格、图形与安全 JSON 下载。
- web/app.py：统一侧边栏七个稳定页面入口，Round 1 完成三个核心页；现有 Datasets/Evaluation 保留，Overview/Settings 标明后续范围，Settings 不提供凭据输入或对象反射。

所有业务实现位于独立模块，__init__.py 仅允许导出。

## 页面行为

Search：基础查询和模式在前，高级参数收进 expander；两通道召回数与最终数量独立；当前启用模型展示在侧边栏；模型草稿可在单独区域修改，重建成功后替换服务，草稿不兼容时禁用查询。结果包含正文、metadata、分数及各阶段排名，统一安全导出。

Inspector：每个阶段独立候选表（doc/chunk、rank、score、是否最终保留），排名图按召回通道分支；阶段计时与 overhead、总耗时区分，避免总耗时重复堆叠。提供原始 StageTrace 查看与 JSON 下载。

Compare：五方案使用相同数据和召回预算，顺序执行并显示进度；明确延迟为查询耗时、不含索引构建。单 Query 可看候选、排名、分数及实际耗时；有标注时使用现有 Evaluator 文档去重宏平均指标，标注不足不补零。Avg/P95 基于真实查询延迟，显示样本数，单样本不宣称稳定基准。默认 Hash/TokenOverlap 明示 Offline Pipeline Sanity Check。配置保存为当前会话快照，并支持脱敏下载和报告导出。

## 验收与实施顺序

- [x] 先写配置脱敏、指纹失效及 QueryOptions 逻辑测试；实现服务模块，验证失败不残留状态。
- [x] 写五方案差异及标注/无标注、缺失模型、Bad Case 单测；实现比较服务，复用真实 Evaluator。
- [x] 修正独立召回通道排名语义并测试；实现 Plotly 图和 trace 下载。
- [x] 实现 i18n、导航、原生主题配置；加入 Plotly 并同步锁文件，保留 CI 的 locked/format 检查。
- [x] 完成 Search/Inspector/Compare 的 AppTest：空查询、样例导入、模式/参数/语言切换、对比、模型失效、清空后结果失效、异常不显示秘密及会话隔离。
- [x] 运行 uv run pytest、uv run ruff check .，以及 CI 所需的 uv run ruff format --check .；记录真实输出后暂停，等待下一轮确认。

## 边界和需重点验证的输入

零权重或非法 K 必须在执行前拒绝；缺少 reranker 不自动拿词项替身冒充真实模型；相同维度不同模型仍使向量失效；任何导出都不得携带凭据；重建失败和数据变更不得留下看似有效的旧结果。


## Round 1 验证记录

- 本地 Python 3.12.9：`uv run pytest` → `91 passed in 11.26s`（原有 70 项 + 新增 21 项）。
- `uv run ruff check .` → `All checks passed!`
- `uv run ruff format --check .` → `86 files already formatted`
- `uv lock --check --offline` → `Resolved 107 packages in 2ms`
- 独立审查发现的大写 URL 脱敏与启动配置控件初始化问题均经过失败用例复现并修复。
- Windows 沙箱在 asyncio socketpair 阻塞；测试在允许本地 socket 的环境完成，测试仍离线运行。
- Compare 批量执行当前提供统一 spinner，逐方案完成数量/进度提示作为轻微改进保留后续。
- Overview/Settings 为本轮最小入口，Evaluation/Datasets 沿用现有功能并统一文案；完整页面扩展留下一轮。
