"""add payment models

Revision ID: payment_models_001
Revises: e249469f1b65
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'payment_models_001'
down_revision: Union[str, Sequence[str], None] = 'e249469f1b65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create PaymentType enum
    payment_type_enum = postgresql.ENUM('lateral', 'monthly', name='paymenttype')
    payment_type_enum.create(op.get_bind())
    
    # Create PaymentStatus enum
    payment_status_enum = postgresql.ENUM('pending', 'success', 'failed', 'cancelled', 'refunded', name='paymentstatus')
    payment_status_enum.create(op.get_bind())
    
    # Create PaymentPlan enum
    payment_plan_enum = postgresql.ENUM('1st', '2nd', '3rd', name='paymentplan')
    payment_plan_enum.create(op.get_bind())
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('partnership_level', postgresql.ENUM('DROP_SHIPPING', 'CONSIGNMENT', 'IMPORT_EXPORT', 'WHOLESALE', 'EXHIBITION', 'AUCTION', 'WHITE_LABEL', 'BRICK_MORTRAR', 'DESIGN_COLLABORATION', 'STORYTELLING', 'WAREHOUSE', 'PACKAGING', 'LOGISTICS', 'MUSEUM_INSTITUTIONAL', 'NGO_GOVERNMENT', 'TECHNOLOGY_PARTNERSHIP', name='partnershipl evel'), nullable=False),
        sa.Column('plan', payment_plan_enum, nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_type', payment_type_enum, nullable=False),
        sa.Column('payment_status', payment_status_enum, nullable=True),
        sa.Column('stripe_payment_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('next_payment_due', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    
    # Create payment_notifications table
    op.create_table('payment_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('days_overdue', sa.Integer(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_notifications_id'), 'payment_notifications', ['id'], unique=False)
    
    # Create partnership_deactivations table
    op.create_table('partnership_deactivations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('partnership_level', postgresql.ENUM('DROP_SHIPPING', 'CONSIGNMENT', 'IMPORT_EXPORT', 'WHOLESALE', 'EXHIBITION', 'AUCTION', 'WHITE_LABEL', 'BRICK_MORTRAR', 'DESIGN_COLLABORATION', 'STORYTELLING', 'WAREHOUSE', 'PACKAGING', 'LOGISTICS', 'MUSEUM_INSTITUTIONAL', 'NGO_GOVERNMENT', 'TECHNOLOGY_PARTNERSHIP', name='partnershipl evel'), nullable=False),
        sa.Column('deactivation_reason', sa.String(length=255), nullable=False),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('reactivation_available', sa.Boolean(), nullable=True),
        sa.Column('reactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_partnership_deactivations_id'), 'partnership_deactivations', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_partnership_deactivations_id'), table_name='partnership_deactivations')
    op.drop_table('partnership_deactivations')
    op.drop_index(op.f('ix_payment_notifications_id'), table_name='payment_notifications')
    op.drop_table('payment_notifications')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS paymentplan')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS paymenttype')
