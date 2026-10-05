"""initial schema: comments, exposures, stats_counters, stats_applied

Revision ID: 0001
Revises:
Create Date: 2026-10-05
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# 一個 op.execute 只放一個語句：psycopg 3 以 prepared statement 送出時不接受多語句


def upgrade() -> None:
    # 「第幾則」的號碼；送出當下發號。AI 句子不佔號（INSERT 時明確給 NULL）
    # 作廢、rollback 都會造成跳號
    op.execute("CREATE SEQUENCE comment_seq_no")

    # 人類留言與 AI 句子放同一張表，用 source 區分
    op.execute("""
    CREATE TABLE comments (
        id                    uuid PRIMARY KEY,
        seq_no                bigint UNIQUE DEFAULT nextval('comment_seq_no'),
        source                text NOT NULL CHECK (source IN ('human', 'ai')),
        anon_id               text,             -- cookie 匿名 ID（跨次造訪）
        ipua_hash             text,             -- hash(IP + User-Agent)，不存原始值
        session_id            text,             -- 同一次造訪
        round_no              integer CHECK (round_no >= 1),   -- 該 session 的第幾輪
        day                   date NOT NULL,    -- APP_TIMEZONE 的日期；決定進哪一天的 queue
        content               text NOT NULL CHECK (char_length(content) BETWEEN 1 AND 100),
        ui_language           text CHECK (ui_language IN ('zh-TW', 'en', 'ja')),
        status                text NOT NULL DEFAULT 'pending'
                              CHECK (status IN ('pending', 'done', 'failed', 'void')),
        -- 以下為分析結果，status = 'done' 之前皆為 NULL
        sentiment             text CHECK (sentiment IN ('positive', 'neutral', 'negative')),
        category_ratios       jsonb,            -- 八類 + other 的比例，程式驗證並正規化
        main_category         text CHECK (main_category IN (
                                  'encouragement', 'attack', 'complaint', 'self_disclosure',
                                  'factual', 'stance', 'question', 'humor', 'other')),
        language              text,             -- ISO 639-1
        display_level         text CHECK (display_level IN ('show', 'hide')),
        self_harm_risk        boolean,
        ai_likeness           smallint CHECK (ai_likeness BETWEEN 0 AND 100 AND ai_likeness % 10 = 0),
        ai_explanation        text,             -- 報表一 01 的 AI 解說，依 ui_language 產生
        flags                 jsonb NOT NULL DEFAULT '{}',   -- 異常標記
        created_at            timestamptz NOT NULL DEFAULT now(),
        analyzed_at           timestamptz,
        -- 人類留言必須有來源識別；AI 句子不可有
        CONSTRAINT comments_source_identity_ck CHECK (
            (source = 'human' AND anon_id IS NOT NULL AND ipua_hash IS NOT NULL
                              AND session_id IS NOT NULL AND round_no IS NOT NULL)
         OR (source = 'ai' AND anon_id IS NULL AND ipua_hash IS NULL
                           AND session_id IS NULL AND round_no IS NULL AND seq_no IS NULL)
        ),
        -- 分析完成時，分析欄位必須齊全
        CONSTRAINT comments_done_analyzed_ck CHECK (
            status <> 'done' OR (
                sentiment IS NOT NULL AND category_ratios IS NOT NULL AND main_category IS NOT NULL
                AND language IS NOT NULL AND display_level IS NOT NULL AND self_harm_risk IS NOT NULL
                AND ai_likeness IS NOT NULL AND analyzed_at IS NOT NULL
            )
        )
    )
    """)

    op.execute("ALTER SEQUENCE comment_seq_no OWNED BY comments.seq_no")

    # 同一個 session 的同一輪只能有一則（擋連按兩次送出）；作廢的不算，才能重新留言
    # AI 句子的 session_id 為 NULL，PostgreSQL 中 NULL 彼此不衝突
    op.execute("""
    CREATE UNIQUE INDEX comments_session_round_uq
        ON comments (session_id, round_no)
        WHERE status <> 'void'
    """)

    # 被檢舉作者之後的留言一律不展示：analyzer 依 anon_id 或 ipua_hash 查詢
    op.execute("CREATE INDEX comments_anon_id_idx ON comments (anon_id)")
    op.execute("CREATE INDEX comments_ipua_hash_idx ON comments (ipua_hash)")

    # 一留一拿：每一輪的「拿」或「不拿」一筆
    op.execute("""
    CREATE TABLE exposures (
        id                    uuid PRIMARY KEY,
        from_comment_id       uuid NOT NULL UNIQUE REFERENCES comments (id),   -- 用哪則兌換（一留一拿）
        shown_comment_id      uuid UNIQUE REFERENCES comments (id),            -- 拿到哪則（每則只被看一次）
        skipped               boolean NOT NULL DEFAULT false,   -- 選擇不拿
        shown_at              timestamptz NOT NULL DEFAULT now(),   -- 拿到（或選擇不拿）的時間
        rating                text CHECK (rating IN ('positive', 'neutral', 'negative')),
        guess                 text CHECK (guess IN ('human', 'ai')),
        is_correct            boolean,          -- guess 是否等於 shown 留言的 source
        would_open_again      boolean,
        would_post_again      boolean,
        rated_at              timestamptz,
        reported              boolean NOT NULL DEFAULT false,
        reported_at           timestamptz,
        -- 不拿 ⇔ 沒有拿到的留言
        CONSTRAINT exposures_skipped_ck CHECK (skipped = (shown_comment_id IS NULL)),
        -- 不會拿到自己剛留的那則
        CONSTRAINT exposures_not_self_ck CHECK (shown_comment_id <> from_comment_id),
        -- 評價四題必填：要嘛全部未填，要嘛全部填好（不拿的不能評價）
        CONSTRAINT exposures_rating_ck CHECK (
            (rated_at IS NULL AND rating IS NULL AND guess IS NULL AND is_correct IS NULL
                AND would_open_again IS NULL AND would_post_again IS NULL)
         OR (NOT skipped AND rated_at IS NOT NULL AND rating IS NOT NULL AND guess IS NOT NULL
                AND is_correct IS NOT NULL AND would_open_again IS NOT NULL AND would_post_again IS NOT NULL)
        ),
        -- 只能檢舉拿到的留言
        CONSTRAINT exposures_reported_ck CHECK (
            (NOT reported AND reported_at IS NULL) OR (reported AND NOT skipped AND reported_at IS NOT NULL)
        )
    )
    """)

    # 預先聚合的統計計數；人類留言與 AI 句子分開計
    op.execute("""
    CREATE TABLE stats_counters (
        source                text NOT NULL CHECK (source IN ('human', 'ai')),
        dimension             text NOT NULL,    -- sentiment / language / main_category / display_level / sentiment_x_category
        value                 text NOT NULL,
        count                 bigint NOT NULL DEFAULT 0,
        PRIMARY KEY (source, dimension, value)
    )
    """)

    # 「此留言已計入統計」的標記；與計數更新放在同一個 transaction，
    # 訊息重送時 INSERT 撞主鍵 → 整個 transaction rollback → 不會重複計數
    op.execute("""
    CREATE TABLE stats_applied (
        comment_id            uuid PRIMARY KEY REFERENCES comments (id),
        applied_at            timestamptz NOT NULL DEFAULT now()
    )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE stats_applied")
    op.execute("DROP TABLE stats_counters")
    op.execute("DROP TABLE exposures")
    op.execute("DROP TABLE comments")  # comment_seq_no 由 OWNED BY 一併刪除
