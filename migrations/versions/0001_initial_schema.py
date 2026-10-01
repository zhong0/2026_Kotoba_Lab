"""initial schema: comments, daily_sessions, stats_counters, stats_applied

Revision ID: 0001
Revises:
Create Date: 2026-10-01
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# 一個 op.execute 只放一個語句：psycopg 3 以 prepared statement 送出時不接受多語句


def upgrade() -> None:
    # 「第幾則」的號碼；送出當下發號，種子留言不佔號（seq_no 為 NULL）
    # 作廢、rollback 都會造成跳號
    op.execute("CREATE SEQUENCE comment_seq_no")

    op.execute("""
    CREATE TABLE comments (
        id                    uuid PRIMARY KEY,
        seq_no                bigint UNIQUE DEFAULT nextval('comment_seq_no'),
        client_key            text,             -- hash(IP + UA + 當日 salt)；種子留言為 NULL
        visitor_id            text,             -- cookie 匿名 ID（回訪判斷）
        day                   date,             -- 台北時間
        slot                  smallint CHECK (slot IN (1, 2)),
        content               text NOT NULL,
        ui_language           text,
        status                text NOT NULL DEFAULT 'pending'
                              CHECK (status IN ('pending', 'done', 'failed', 'void')),
        -- 以下為分析結果，status = 'done' 之前皆為 NULL
        polarity              text CHECK (polarity IN ('positive', 'neutral', 'negative')),
        language              text,             -- ISO 639-1
        type_ratios           jsonb,
        primary_type          text CHECK (primary_type IN (
                                  'encouragement', 'attack', 'self_disclosure',
                                  'factual', 'stance', 'question', 'other')),
        harm                  text CHECK (harm IN ('none', 'borderline', 'severe')),
        contains_private_pii  boolean,
        crisis                text CHECK (crisis IN ('none', 'mental_crisis', 'emergency', 'violence')),
        display_status        text CHECK (display_status IN (
                                  'shown', 'blurred', 'hidden_inappropriate', 'hidden_privacy')),
        is_seed               boolean NOT NULL DEFAULT false,
        flags                 jsonb NOT NULL DEFAULT '{}',   -- 異常標記
        created_at            timestamptz NOT NULL DEFAULT now(),
        analyzed_at           timestamptz
    )
    """)

    op.execute("ALTER SEQUENCE comment_seq_no OWNED BY comments.seq_no")

    # 每人每天每個 slot 只能有一則；作廢（void）的不算，才能重新留言
    op.execute("""
    CREATE UNIQUE INDEX comments_client_day_slot_uq
        ON comments (client_key, day, slot)
        WHERE status <> 'void'
    """)

    # 每個識別碼每天一筆；沒有資料 = START
    op.execute("""
    CREATE TABLE daily_sessions (
        client_key            text NOT NULL,
        day                   date NOT NULL,
        state                 text NOT NULL CHECK (state IN (
                                  'POSTED_1', 'DECLINED', 'VIEWED', 'SKIPPED', 'POSTED_2', 'CRISIS')),
        first_comment_id      uuid REFERENCES comments (id),
        shown_comment_id      uuid REFERENCES comments (id),   -- 看到的留言
        shown_at              timestamptz,
        blurred_revealed      boolean,          -- NULL = 看到的不是模糊留言
        second_comment_id     uuid REFERENCES comments (id),
        is_returning          boolean NOT NULL DEFAULT false,
        created_at            timestamptz NOT NULL DEFAULT now(),
        updated_at            timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (client_key, day)
    )
    """)

    # 預先聚合的統計計數（第一份報表的整體分布）
    op.execute("""
    CREATE TABLE stats_counters (
        dimension             text NOT NULL,    -- polarity / language / primary_type / display_group / polarity_x_type
        value                 text NOT NULL,
        count                 bigint NOT NULL DEFAULT 0,
        PRIMARY KEY (dimension, value)
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
    op.execute("DROP TABLE daily_sessions")
    op.execute("DROP TABLE comments")  # comment_seq_no 由 OWNED BY 一併刪除
