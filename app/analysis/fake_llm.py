"""假的 LLM：不呼叫 Bedrock，回傳固定的分析結果（地端開發、跑通訊息流程用）。

輸出欄位即 LLM 要回傳的原始判斷；main_category（由 category_ratios 取最高者）與
display_level（displayable 加上第二道內容審核）由程式推導，不是 LLM 給的。
真正的 Bedrock 呼叫、prompt、輸出驗證之後再實作。
"""
from app.analysis.dimensions import CATEGORIES

_FAKE_EXPLANATIONS = {
    "zh-TW": "（假的解說：尚未接上 LLM）",
    "en": "(Fake explanation: LLM not connected yet)",
    "ja": "（ダミーの解説：LLM 未接続）",
}


def analyze(content: str, ui_language: str) -> dict:
    return {
        "sentiment": "neutral",
        "category_ratios": {c: (100 if c == "other" else 0) for c in CATEGORIES},
        "language": "zh",
        "displayable": True,       # 第一道：analyzer 判斷可展示（不含個資等）
        "self_harm_risk": False,
        "ai_likeness": 50,
        "ai_explanation": _FAKE_EXPLANATIONS.get(ui_language, _FAKE_EXPLANATIONS["zh-TW"]),
    }
