"""Add referral and discount logic

Revision ID: 357a5db4e709
Revises: aba0c090356b
Create Date: 2025-08-24 10:47:35.822285

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '357a5db4e709'
down_revision: Union[str, None] = 'aba0c090356b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

referralpayoutstatus_enum = postgresql.ENUM('PENDING', 'APPROVED', 'REJECTED', name='referralpayoutstatus', create_type=False)
userdiscountlevel_enum = postgresql.ENUM('BRONZE', 'SILVER', 'GOLD', 'NONE', name='userdiscountlevel', create_type=False)


def upgrade() -> None:
    op.execute("CREATE TYPE userdiscountlevel AS ENUM ('BRONZE', 'SILVER', 'GOLD', 'NONE');", execution_options={'autocommit': True})
    op.execute("CREATE TYPE referralpayoutstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED');", execution_options={'autocommit': True})

    op.add_column('users', sa.Column('invited_by_id', sa.UUID(), nullable=True))
    op.add_column('users', sa.Column('bonus_balance', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'))
    op.add_column('users', sa.Column('monthly_spent', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0.00'))
    op.add_column('users', sa.Column('payment_details', sa.String(), nullable=True))
    op.add_column('users', sa.Column('accepted_terms', sa.Boolean(), nullable=False, server_default='false'))
    
    op.create_foreign_key('fk_users_invited_by_id', 'users', 'users', ['invited_by_id'], ['id'])
    
    op.add_column('user_discounts', 
        sa.Column('current_level', 
            userdiscountlevel_enum, 
            nullable=False, 
            server_default='NONE'
        )
    )

    op.create_table('payout_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', referralpayoutstatus_enum, nullable=False, server_default='PENDING'),
        sa.Column('payment_details', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_payout_requests_user_id'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_constraint('fk_payout_requests_user_id', 'payout_requests', type_='foreignkey')
    op.drop_table('payout_requests')

    op.drop_column('user_discounts', 'current_level')
    
    op.drop_constraint('fk_users_invited_by_id', 'users', type_='foreignkey')
    op.drop_column('users', 'accepted_terms')
    op.drop_column('users', 'payment_details')
    op.drop_column('users', 'monthly_spent')
    op.drop_column('users', 'bonus_balance')
    op.drop_column('users', 'invited_by_id')

    op.execute("DROP TYPE userdiscountlevel;")
    op.execute("DROP TYPE referralpayoutstatus;")