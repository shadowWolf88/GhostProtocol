"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-03-03

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── players ───────────────────────────────────────────────────────────────
    op.create_table(
        'players',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('handle', sa.String(32), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_banned', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_active', sa.DateTime(timezone=True), nullable=True),
    )

    # ── player_stats ──────────────────────────────────────────────────────────
    op.create_table(
        'player_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('xp_social', sa.Integer, server_default='0'),
        sa.Column('xp_exploitation', sa.Integer, server_default='0'),
        sa.Column('xp_cryptography', sa.Integer, server_default='0'),
        sa.Column('xp_hardware', sa.Integer, server_default='0'),
        sa.Column('xp_counterintel', sa.Integer, server_default='0'),
        sa.Column('xp_economics', sa.Integer, server_default='0'),
        sa.Column('fiat', sa.Integer, server_default='0'),
        sa.Column('crypto', sa.Integer, server_default='500'),
        sa.Column('privacy_coin', sa.Integer, server_default='0'),
        sa.Column('reputation', sa.Integer, server_default='0'),
        sa.Column('energy', sa.Integer, server_default='100'),
        sa.Column('max_energy', sa.Integer, server_default='100'),
        sa.Column('energy_regen_rate', sa.Integer, server_default='10'),
        sa.Column('last_energy_update', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── psych_states ──────────────────────────────────────────────────────────
    op.create_table(
        'psych_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('stress', sa.Integer, server_default='0'),
        sa.Column('paranoia', sa.Integer, server_default='20'),
        sa.Column('sleep_debt', sa.Integer, server_default='0'),
        sa.Column('ego', sa.Integer, server_default='50'),
        sa.Column('burnout', sa.Integer, server_default='0'),
        sa.Column('trust_index', sa.Integer, server_default='60'),
        sa.Column('focus', sa.Integer, server_default='80'),
        sa.Column('stimulant_dependency', sa.Integer, server_default='0'),
        sa.Column('sedative_dependency', sa.Integer, server_default='0'),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── devices ───────────────────────────────────────────────────────────────
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('device_type', sa.String(20), nullable=False),
        sa.Column('mac_fingerprint', sa.String(64), nullable=False, unique=True),
        sa.Column('ip_fingerprint', sa.String(64), nullable=True),
        sa.Column('firmware_version', sa.String(20), server_default='1.0.0'),
        sa.Column('forensic_trace_level', sa.Integer, server_default='0'),
        sa.Column('is_compromised', sa.Boolean, server_default='false'),
        sa.Column('is_destroyed', sa.Boolean, server_default='false'),
        sa.Column('under_surveillance', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('destroyed_at', sa.DateTime(timezone=True), nullable=True),
    )

    # ── identities ────────────────────────────────────────────────────────────
    op.create_table(
        'identities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alias', sa.String(64), nullable=False),
        sa.Column('cover_story', sa.Text, server_default=''),
        sa.Column('documents_quality', sa.Integer, server_default='50'),
        sa.Column('is_burned', sa.Boolean, server_default='false'),
        sa.Column('heat_accumulated', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('burned_at', sa.DateTime(timezone=True), nullable=True),
    )

    # ── world_nodes ───────────────────────────────────────────────────────────
    op.create_table(
        'world_nodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('node_key', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(32), nullable=False),
        sa.Column('tier', sa.Integer, nullable=False, server_default='1'),
        sa.Column('vulnerability_score', sa.Integer, server_default='50'),
        sa.Column('patch_rate', sa.Integer, server_default='2'),
        sa.Column('defender_tier', sa.Integer, server_default='1'),
        sa.Column('heat_multiplier', sa.Float, server_default='1.0'),
        sa.Column('base_crypto_reward', sa.Integer, server_default='100'),
        sa.Column('base_reputation_reward', sa.Integer, server_default='10'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('last_breached_at', sa.DateTime(timezone=True), nullable=True),
    )

    # ── operations ────────────────────────────────────────────────────────────
    op.create_table(
        'operations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('world_nodes.id'), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('identity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identities.id'), nullable=True),
        sa.Column('status', sa.String(20), server_default='planning'),
        sa.Column('approach', sa.String(20), server_default='technical'),
        sa.Column('phase_data', postgresql.JSONB, server_default='{}'),
        sa.Column('artifacts_left', postgresql.JSONB, server_default='[]'),
        sa.Column('heat_generated', sa.Integer, server_default='0'),
        sa.Column('xp_awarded', postgresql.JSONB, server_default='{}'),
        sa.Column('crypto_earned', sa.Integer, server_default='0'),
        sa.Column('reputation_earned', sa.Integer, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fail_reason', sa.String(255), nullable=True),
    )
    op.create_index('ix_operations_player_status', 'operations', ['player_id', 'status'])

    # ── heat_records ──────────────────────────────────────────────────────────
    op.create_table(
        'heat_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('domain', sa.String(32), nullable=False),
        sa.Column('level', sa.Integer, server_default='0'),
        sa.Column('decay_rate', sa.Float, nullable=False, server_default='5.0'),
        sa.Column('last_incident_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('player_id', 'domain', name='uq_heat_player_domain'),
    )

    # ── trace_artifacts ───────────────────────────────────────────────────────
    op.create_table(
        'trace_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('operation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('operations.id'), nullable=True),
        sa.Column('artifact_type', sa.String(32), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('world_nodes.id'), nullable=True),
        sa.Column('identity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identities.id'), nullable=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('severity', sa.Integer, server_default='3'),
        sa.Column('is_wiped', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── faction_npcs ──────────────────────────────────────────────────────────
    op.create_table(
        'faction_npcs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('faction_key', sa.String(32), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('contact_requirement', sa.Integer, server_default='0'),
    )

    # ── player_faction_relations ──────────────────────────────────────────────
    op.create_table(
        'player_faction_relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('faction_key', sa.String(32), nullable=False),
        sa.Column('standing', sa.Integer, server_default='0'),
        sa.Column('is_member', sa.Boolean, server_default='false'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('player_id', 'faction_key', name='uq_faction_relation'),
    )

    # ── market_listings ───────────────────────────────────────────────────────
    op.create_table(
        'market_listings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('seller_player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='SET NULL'), nullable=True),
        sa.Column('item_type', sa.String(32), nullable=False),
        sa.Column('item_name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('price_crypto', sa.Integer, nullable=False),
        sa.Column('quantity', sa.Integer, server_default='1'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('effect_data', postgresql.JSONB, server_default='{}'),
    )

    # ── transactions ──────────────────────────────────────────────────────────
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(20), nullable=False),
        sa.Column('description', sa.String(255), nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_transactions_player', 'transactions', ['player_id', 'created_at'])

    # ── player_inventory ──────────────────────────────────────────────────────
    op.create_table(
        'player_inventory',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_type', sa.String(32), nullable=False),
        sa.Column('item_name', sa.String(128), nullable=False),
        sa.Column('quantity', sa.Integer, server_default='1'),
        sa.Column('effect_data', postgresql.JSONB, server_default='{}'),
        sa.Column('uses_remaining', sa.Integer, server_default='-1'),
        sa.Column('acquired_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── prison_records ────────────────────────────────────────────────────────
    op.create_table(
        'prison_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sentence_hours', sa.Integer, nullable=False),
        sa.Column('arrested_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('release_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('charge_description', sa.Text, nullable=False),
        sa.Column('time_served_bonus', sa.Integer, server_default='0'),
        sa.Column('informant_deal', sa.Boolean, server_default='false'),
        sa.Column('escaped', sa.Boolean, server_default='false'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('broker_info_count', sa.Integer, server_default='0'),
        sa.Column('legal_fight_count', sa.Integer, server_default='0'),
    )

    # ── prison_activities ─────────────────────────────────────────────────────
    op.create_table(
        'prison_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('player_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('players.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activity_type', sa.String(32), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('cost_crypto', sa.Integer, server_default='0'),
        sa.Column('outcome', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('prison_activities')
    op.drop_table('prison_records')
    op.drop_table('player_inventory')
    op.drop_index('ix_transactions_player', table_name='transactions')
    op.drop_table('transactions')
    op.drop_table('market_listings')
    op.drop_table('player_faction_relations')
    op.drop_table('faction_npcs')
    op.drop_table('trace_artifacts')
    op.drop_table('heat_records')
    op.drop_index('ix_operations_player_status', table_name='operations')
    op.drop_table('operations')
    op.drop_table('world_nodes')
    op.drop_table('identities')
    op.drop_table('devices')
    op.drop_table('psych_states')
    op.drop_table('player_stats')
    op.drop_table('players')
