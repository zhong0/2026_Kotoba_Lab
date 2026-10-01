"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from alembic import op

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

# 一個 op.execute 只放一個語句：psycopg 3 以 prepared statement 送出時不接受多語句


def upgrade() -> None:
    op.execute("""
    """)


def downgrade() -> None:
    op.execute("""
    """)
