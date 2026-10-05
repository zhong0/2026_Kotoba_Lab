"""分析維度的允許值。與 migrations/versions/0001_initial_schema.py 的 CHECK 一致，改一邊要一起改。"""

SENTIMENTS = ("positive", "neutral", "negative")

# 順序即類別表順序（同分時依此取第一個）；other 不畫在雷達圖上
CATEGORIES = (
    "encouragement",    # 鼓勵／善意
    "attack",           # 攻擊性（針對人）
    "complaint",        # 抱怨／不滿（針對事）
    "self_disclosure",  # 自我抒發
    "factual",          # 講述事實
    "stance",           # 表達立場
    "question",         # 提問／求助
    "humor",            # 幽默／閒聊
    "other",            # 其他
)

DISPLAY_LEVELS = ("show", "hide")

UI_LANGUAGES = ("zh-TW", "en", "ja")

AI_LIKENESS_STEP = 10  # 0～100，以 10% 為單位
