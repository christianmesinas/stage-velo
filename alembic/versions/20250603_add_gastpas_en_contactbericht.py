"""Add GastPas and ContactBericht tables

Revision ID: gast_contact_001
Revises: a1b3dc41e070
Create Date: 2025-06-03 19:00:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'gast_contact_001'
down_revision = 'a1b3dc41e070'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'gastpassen',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('type', sa.String, nullable=False),
        sa.Column('voornaam', sa.String, nullable=False),
        sa.Column('achternaam', sa.String, nullable=False),
        sa.Column('email', sa.String, nullable=False),
        sa.Column('telefoon', sa.String),
        sa.Column('geboortedatum', sa.DateTime, nullable=False),
        sa.Column('pincode', sa.String, nullable=False),
        sa.Column('start_datum', sa.DateTime, default=datetime.utcnow),
        sa.Column('eind_datum', sa.DateTime)
    )

    op.create_table(
        'contact_berichten',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('naam', sa.String, nullable=False),
        sa.Column('email', sa.String, nullable=False),
        sa.Column('telefoon', sa.String),
        sa.Column('reden', sa.String, nullable=False),
        sa.Column('onderwerp', sa.String, nullable=False),
        sa.Column('bericht', sa.String, nullable=False),
        sa.Column('datum', sa.DateTime, default=datetime.utcnow)
    )


def downgrade() -> None:
    op.drop_table('contact_berichten')
    op.drop_table('gastpassen')