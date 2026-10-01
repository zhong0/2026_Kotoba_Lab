"""假的 LLM：不呼叫 Bedrock，回傳固定的分析結果（地端開發、跑通訊息流程用）。

輸出格式與需求 4.7 的 JSON 相同；真正的 Bedrock 呼叫、prompt、輸出驗證在第 2 階段實作。
"""


def analyze(content: str) -> dict:
    return {
        "polarity": "neutral",
        "language": "zh",
        "type_ratios": {
            "encouragement": 0, "attack": 0, "self_disclosure": 0,
            "factual": 0, "stance": 0, "question": 0, "other": 100,
        },
        "harm": "none",
        "contains_private_pii": False,
        "crisis": "none",
    }
