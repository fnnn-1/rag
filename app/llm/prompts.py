from app.retrieval.hybrid_search import SearchResult

SYSTEM_PROMPT = """你是企业内部知识库问答助手。
你只能依据 <sources> 中提供的资料回答问题，不得使用外部知识补充事实。
如果资料不足以回答，必须回复：知识库中未找到足够依据，无法准确回答该问题。
回答中的关键结论必须使用 [S1]、[S2] 等来源标记。
不要编造来源、数字、制度条款或资料中不存在的内容。
"""


def build_rag_messages(question: str, results: list[SearchResult]) -> list[dict[str, str]]:
    sources = []
    for index, result in enumerate(results, start=1):
        location = f"，第 {result.page_number} 页" if result.page_number else ""
        sources.append(f"[S{index}] {result.document_name}{location}\n{result.content}")
    context = "\n\n".join(sources)
    user_prompt = f"""<sources>
{context}
</sources>

问题：{question}

请严格依据资料回答，并在关键结论后标注来源。"""
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}]
