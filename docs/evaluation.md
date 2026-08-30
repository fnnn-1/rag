# RAG 评测方案

## 目标

本项目使用可重复执行的标准数据集评估知识库检索、引用选择与知识库外问题拒答能力。评测默认不调用聊天大模型，因此不会产生额外对话模型费用；Embedding 查询会调用当前配置的向量模型。

## 数据集

- 演示文档：6 份虚构、脱敏企业制度
- 评测问题：30 条
- 可回答问题：24 条
- 知识库外问题：6 条
- 领域：员工手册、考勤、休假、报销、差旅、采购

数据文件：

```text
data/seed/company_policies/
data/evaluation/eval_dataset.json
```

## 指标定义

- **Retrieval Hit@5**：Top 5 是否至少包含一份标准相关文档。
- **Retrieval Recall@5**：Top 5 找回的标准相关文档占全部标准相关文档的比例。
- **MRR@5**：第一份标准相关文档排名倒数的平均值。
- **引用准确率**：证据门控选中的引用中，来自标准相关文档的比例。
- **引用覆盖率**：可回答问题中，至少引用一份标准相关文档的比例。
- **答案词覆盖率**：引用内容覆盖标准答案关键词的比例。
- **拒答通过率**：知识库外问题被正确判断为证据不足的比例。
- **平均耗时**：单条问题执行 Embedding、混合检索和重排序的平均耗时。

## 执行命令

首次运行会重建专用演示知识库并生成向量：

```powershell
docker exec kb-api python scripts/evaluate_rag.py
```

仅复用现有演示知识库重新评测：

```powershell
docker exec kb-api python scripts/evaluate_rag.py --skip-prepare
```

输出文件：

```text
data/evaluation/latest_report.json
data/evaluation/latest_report.md
```

## 2026-08-30 基准结果

| 指标 | 结果 |
|---|---:|
| Retrieval Hit@5 | 100.00% |
| Retrieval Recall@5 | 100.00% |
| MRR@5 | 1.0000 |
| 引用准确率 | 100.00% |
| 引用覆盖率 | 100.00% |
| 答案词覆盖率 | 100.00% |
| 知识库外问题拒答通过率 | 100.00% |
| 平均检索与重排序耗时 | 430.58 ms |

这些结果只代表当前自拟演示数据集，不应被解释为所有真实企业文档上的通用准确率。
