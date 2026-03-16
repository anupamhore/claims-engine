"""Initial migration: Create core tables.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-03-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Claims table
    op.create_table(
        'claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('urgency', sa.String(20), nullable=False),
        sa.Column('amount', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('claimant_id', sa.String(100), nullable=False),
        sa.Column('provider_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_claims_claimant_id', 'claims', ['claimant_id'])
    op.create_index('ix_claims_provider_id', 'claims', ['provider_id'])
    op.create_index('ix_claims_created_at', 'claims', ['created_at'])
    op.create_index('ix_claims_claimant_provider', 'claims', ['claimant_id', 'provider_id'])

    # Fraud scores table
    op.create_table(
        'fraud_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('ml_score', sa.Float(), nullable=False),
        sa.Column('pattern_score', sa.Float(), nullable=False),
        sa.Column('ensemble_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('model_version', sa.String(20), nullable=False),
        sa.Column('flagged', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE')
    )
    op.create_index('ix_fraud_scores_claim_id', 'fraud_scores', ['claim_id'])
    op.create_index('ix_fraud_scores_created_at', 'fraud_scores', ['created_at'])

    # Explanations table
    op.create_table(
        'explanations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('llm_explanation', sa.Text(), nullable=False),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('explanation_confidence', sa.Float(), nullable=False),
        sa.Column('model_used', sa.String(20), nullable=False),
        sa.Column('hallucination_score', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(20), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE')
    )
    op.create_index('ix_explanations_claim_id', 'explanations', ['claim_id'])
    op.create_index('ix_explanations_generated_at', 'explanations', ['generated_at'])

    # User feedback table
    op.create_table(
        'user_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('auditor_id', sa.String(100), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('corrected_label', sa.String(20), nullable=True),
        sa.Column('corrected_score', sa.Float(), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='CASCADE')
    )
    op.create_index('ix_user_feedback_claim_id', 'user_feedback', ['claim_id'])
    op.create_index('ix_user_feedback_auditor_id', 'user_feedback', ['auditor_id'])
    op.create_index('ix_user_feedback_created_at', 'user_feedback', ['created_at'])

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=True),
        sa.Column('claim_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ondelete='SET NULL')
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])

    # Fraud patterns table
    op.create_table(
        'fraud_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pattern_description', sa.String(255), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=False),
        sa.Column('historical_examples', sa.JSON(), nullable=True),
        sa.Column('detection_rule', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('fraud_patterns')
    op.drop_table('audit_logs')
    op.drop_table('user_feedback')
    op.drop_table('explanations')
    op.drop_table('fraud_scores')
    op.drop_table('claims')
