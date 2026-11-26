"""Shared bilingual copy. Stable navigation IDs survive language changes."""

import streamlit as st

COPY = {
    "权重仅用于 Weighted Fusion；RRF 使用排名与 RRF K。": (
        "Weights apply to Weighted Fusion; RRF uses ranks and RRF K."
    ),
    "未配置 Reranker，请通过启动配置加载模型。": (
        "Reranker unavailable. Load a model through the startup configuration."
    ),
    "加载样例数据": "Load sample data",
    "仅修改当前会话的内存索引；同 ID 文档会被替换，服务重启后数据不保留。": (
        "Session-local index. Matching document IDs are replaced; data is not persistent."
    ),
    "上传文档（TXT / Markdown / JSONL）": "Upload documents (TXT / Markdown / JSONL)",
    "导入文档": "Import documents",
    "上传标注查询 JSONL": "Upload labeled queries (JSONL)",
    "导入标注查询": "Import labeled queries",
    "当前文档": "Current documents",
    "导出文档 JSONL": "Export documents (JSONL)",
    "当前标注查询": "Current judgments",
    "导出标注查询": "Export judgments",
    "清空当前会话数据": "Clear session data",
    "无法重置检索服务，请检查配置。": "Could not reset service. Check configuration.",
    "样例导入失败，请检查模型与服务配置。": "Sample import failed. Check models and configuration.",
    "导入失败，请检查配置与数据。": "Import failed. Check configuration and data.",
    "二元相关性、文档去重、宏平均；Hash 与词项重排只用于离线链路验证。": (
        "Binary relevance, document deduplication, macro averages. Hash/token "
        "reranking is offline sanity only."
    ),
    "请在 Datasets 中加载相关性标注查询。": "Load relevance judgments in Datasets.",
    "检索数量": "Retrieval count",
    "评测 K（逗号分隔）": "Evaluation K (comma-separated)",
    "运行评测": "Run evaluation",
    "下载评测报告": "Download evaluation report",
    "评测失败，请检查模型与服务配置。": "Evaluation failed. Check models and configuration.",
    "已加载 {count} 条标注查询": "Loaded {count} labeled queries",
    "已加载 {docs} 篇文档、{queries} 条查询。": "Loaded {docs} documents and {queries} queries.",
    "已导入 {count} 篇文档。": "Imported {count} documents.",
    "已导入 {count} 条查询。": "Imported {count} queries.",
    "文档格式无效。": "Invalid document format.",
    "查询格式无效。": "Invalid query format.",
    "无法加载样例数据。": "Could not load sample data.",
    "评测参数无效。": "Invalid evaluation parameters.",
    "查询": "Query",
    "搜索": "Search",
    "返回数量": "Final Top K",
    "视图": "Navigation",
    "运行对比": "Run comparison",
    "高级查询参数": "Query options",
    "召回模式": "Retrieval mode",
    "融合方式": "Fusion method",
    "启用重排": "Enable reranker",
    "重排候选数": "Reranker candidate count",
    "加载中…": "Working…",
    "请输入查询。": "Enter a query.",
    "暂无文档，请在 Datasets 加载数据。": "No documents yet. Load data in Datasets.",
    "检索失败，请检查模型与服务配置。": "Search failed. Check model and service configuration.",
    "没有检索结果，请检查数据集和查询。": "No results. Check your dataset and query.",
    "总耗时（ms）": "Total latency (ms)",
    "下载搜索结果": "Download results",
    "请先在 Search 中执行检索。": "Run a search first.",
    "阶段排名变化": "Ranking paths",
    "阶段耗时": "Stage latency",
    "原始 StageTrace": "Raw StageTrace",
    "下载 StageTrace": "Download StageTrace",
    "保留与淘汰候选": "Retained and dropped candidates",
    "独立召回通道分别进入融合；空值表示未进入该阶段。": (
        "Independent recall channels feed fusion; missing ranks mean absent from that stage."
    ),
    "保存配置": "Save configuration",
    "下载配置": "Download configuration",
    "下载报告": "Download report",
    "已保存到当前会话。": "Saved to this session.",
    "使用已加载标注批量对比": "Compare loaded labeled queries",
    "没有标注，指标不适用。": "No judgments; relevance metrics are not available.",
    "对比失败，请检查模型与配置。": "Comparison failed. Check models and configuration.",
    "查询耗时不含建索引；单样本 P95 不代表稳定基准。": (
        "Query latency excludes indexing; a single-sample P95 is not a stable benchmark."
    ),
    "模型配置变更后必须重建索引。": "Model configuration changes require index rebuilding.",
    "模型配置（需重建）": "Model configuration (requires rebuild)",
    "Embedding 模型": "Embedding model",
    "重建索引": "Rebuild index",
    "模型配置已改变，请重建索引后查询。": (
        "Model configuration changed. Rebuild the index before searching."
    ),
    "重建失败，原服务保持不变。": "Rebuild failed; the original service is unchanged.",
    "本页将在后续轮次完善。": "This page will be expanded in a later round.",
    "配置已脱敏，凭据通过环境变量管理。": (
        "Configuration is redacted; manage credentials through environment variables."
    ),
    "无法初始化检索服务，请检查 RAG_TOOLKIT_CONFIG。": (
        "Could not initialize retrieval. Check RAG_TOOLKIT_CONFIG."
    ),
}


COPY.update(
    {
        "文档数": "Documents",
        "当前模型与索引状态": "Current models and index status",
        "远程连接未主动探测；ready 表示当前会话索引已构建，不代表远程服务健康。": (
            "Remote connectivity is not probed. Ready means "
            "locally indexed, not remote service health."
        ),
        "检索流水线": "Retrieval pipeline",
        "最近检索与评测记录": "Recent searches and evaluations",
        "暂无记录，请先运行 Search 或 Evaluation。": "No activity yet. Run Search or Evaluation.",
        "评测策略": "Evaluation strategies",
        "仅显示失败案例": "Failures only",
        "筛选 Query": "Filter query",
        "诊断线索筛选": "Filter diagnostic clues",
        "逐 Query StageTrace 与诊断证据": "Per-query StageTrace and diagnostic evidence",
        "选择 Query 记录": "Select query record",
        "导入标注 Query": "Import labeled queries",
        "或粘贴标注 JSONL": "Or paste labeled JSONL",
        "导入/替换标注": "Import / replace judgments",
        "请导入标注 Query，或在 Datasets 加载样例。": (
            "Import labeled queries or load samples in Datasets."
        ),
        "以下诊断仅为 StageTrace 规则推断线索，不是已确认根因。": (
            "Diagnostics are rule-based clues from StageTrace, not confirmed root causes."
        ),
        "示例为仓库公开样例（MIT），离线加载，不代表真实模型基准。": (
            "Bundled public repository samples (MIT), loaded offline; not a real-model benchmark."
        ),
        "Chunk 预览": "Chunk preview",
        "按文档筛选": "Filter by document",
        "管理 Query 标注": "Manage query judgments",
        "标注 JSONL（编辑后替换）": "Judgments JSONL (edit to replace)",
        "保存标注": "Save judgments",
        "清空标注": "Clear judgments",
        "当前数据集与索引状态": "Dataset and index status",
        "粘贴导入文档": "Paste documents to import",
        "文档格式": "Document format",
        "文档内容": "Document content",
        "导入粘贴文档": "Import pasted documents",
        "向量库与分块": "Vector store and chunking",
        "默认检索参数": "Default retrieval settings",
        "Tokenizer 仅用于 BM25；Embedding 使用模型自身的分词器。": (
            "Tokenizer applies to BM25 only; embeddings use their model tokenizer."
        ),
        "索引相关变更将重建；仅查询参数变更直接生效。": (
            "Index changes rebuild; query-only defaults apply without re-embedding."
        ),
        "应用配置": "Apply configuration",
        "配置已应用。": "Configuration applied.",
        "配置无效或重建失败，原服务保持不变。": (
            "Invalid configuration or rebuild failed; original service retained."
        ),
        "导入配置 YAML / JSON（仅脱敏配置）": "Import configuration YAML / JSON (redacted only)",
        "应用导入配置": "Apply imported configuration",
        "需要重建索引": "Index rebuild required",
        "仅查询参数变更": "Query defaults only",
        "配置无效或包含凭据；请使用环境变量。": (
            "Invalid configuration or embedded credentials. Use environment variables."
        ),
    }
)


def t(text, **values):
    translated = COPY.get(text, text) if st.session_state.get("language") == "English" else text
    return translated.format(**values) if values else translated
