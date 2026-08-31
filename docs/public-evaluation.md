# 公开评测集复评说明

## 数据集来源

本次使用 GitHub 公开仓库 `hyintell/RetrievalQA` 中的 `data/retrievalqa_gpt4.jsonl`，文件包含 250 条问题及其上下文，来源类型包括 RealTimeQA、FreshQA、ToolQA、PopQA 和 TriviaQA。

本地副本：

```text
data/evaluation/public_retrievalqa_gpt4.jsonl
```

## 评测方法

1. 将公开数据集提供的上下文去重后写入临时的“公开 RetrievalQA 评测知识库”。
2. 使用当前配置的 Embedding 模型对上下文和查询向量化。
3. 使用现有 pgvector + PostgreSQL 全文检索 + RRF 混合检索。
4. 使用当前重排序逻辑计算 Top 5 结果。
5. 将数据集给出的上下文标题作为该问题的相关文档集合。
6. 计算 Hit@5、Recall@5、Precision@5 和 MRR@5。

本次公开评测只评估检索能力，不调用聊天模型生成答案，因此不会泄露或打印任何 API Key，也不统计 EM/F1 等答案生成指标。

## 执行命令

```powershell
docker exec kb-api python scripts/evaluate_public_retrievalqa.py
```

本次完整评测使用文件中的 250 条问题。为降低测试成本，也可以按数据源轮转抽取子集：

```powershell
docker exec kb-api python scripts/evaluate_public_retrievalqa.py --limit 50
```

报告：

```text
data/evaluation/public_retrievalqa_report.json
data/evaluation/public_retrievalqa_report.md
```

## 结果解释

公开 RetrievalQA 的上下文列表是数据集提供的检索上下文，不等同于真实企业知识库中的唯一标准答案文档。因此本次 Recall@5 反映的是找回提供上下文标题的比例，不能与企业制度演示集的引用准确率直接比较。
