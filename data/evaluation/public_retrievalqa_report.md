# 公开 RetrievalQA 检索评测报告

- 生成时间：2026-08-31T11:21:35+00:00
- 数据集：RetrievalQA / public_retrievalqa_gpt4.jsonl
- 公开数据集来源：hyintell/RetrievalQA
- 本次评测问题数：250

## 检索指标

| 指标 | 结果 |
|---|---:|
| Retrieval Hit@5 | 100.00% |
| Retrieval Recall@5 | 56.30% |
| Retrieval Precision@5 | 94.64% |
| MRR@5 | 0.9900 |
| 平均检索耗时 | 422.12 ms |

## 数据源分类结果

| 数据源 | 问题数 | Hit@5 | Recall@5 | MRR@5 |
|---|---:|---:|---:|---:|
| freshqa | 50 | 100.00% | 85.53% | 0.9700 |
| popqa | 50 | 100.00% | 27.35% | 1.0000 |
| realtimeqa | 50 | 100.00% | 85.53% | 1.0000 |
| toolqa | 50 | 100.00% | 45.60% | 0.9800 |
| triviaqa | 50 | 100.00% | 37.50% | 1.0000 |

## 说明

- 本次评测使用公开 RetrievalQA 仓库提供的 `retrievalqa_gpt4.jsonl` 选定样本文件。
- 数据文件包含来自 RealTimeQA、FreshQA、ToolQA、PopQA 和 TriviaQA 的问题与上下文。
- 本报告评估当前项目的检索器是否找回数据集提供的上下文标题，不评估聊天模型最终答案 EM/F1。
- 评测语料由数据集中的上下文构建，因此指标用于比较检索管线，不等价于真实企业知识库效果。
