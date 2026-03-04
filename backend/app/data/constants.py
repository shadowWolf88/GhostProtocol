"""
Ghost Protocol — Game Balance Constants
All tunable game values live here. No magic numbers elsewhere.
"""

GAME_CONSTANTS = {
    # Economy
    "STARTING_CRYPTO": 500,
    "OPERATION_ENERGY_COST": 20,
    "ENERGY_REGEN_RATE": 10,  # per hour
    "MAX_ENERGY": 100,

    # Node Rewards
    "TIER1_CRYPTO_MIN": 50,
    "TIER1_CRYPTO_MAX": 150,
    "TIER2_CRYPTO_MIN": 150,
    "TIER2_CRYPTO_MAX": 400,
    "TIER3_CRYPTO_MIN": 400,
    "TIER3_CRYPTO_MAX": 900,
    "TIER4_CRYPTO_MIN": 900,
    "TIER4_CRYPTO_MAX": 2000,
    "TIER5_CRYPTO_MIN": 2000,
    "TIER5_CRYPTO_MAX": 5000,

    # XP Awards
    "XP_RECON": 50,
    "XP_EXPLOIT": 150,
    "XP_PERSIST": 100,
    "XP_MONETIZE": 100,

    # Heat
    "HEAT_TIER1_MAX": 20,
    "HEAT_TIER2_MAX": 40,
    "HEAT_TIER3_MAX": 60,
    "HEAT_TIER4_MAX": 80,
    "HEAT_TIER5_MAX": 100,

    # Heat weights for total calculation
    "HEAT_WEIGHT_LOCAL_LEO": 0.10,
    "HEAT_WEIGHT_FEDERAL": 0.25,
    "HEAT_WEIGHT_INTELLIGENCE": 0.35,
    "HEAT_WEIGHT_CORPORATE": 0.20,
    "HEAT_WEIGHT_RIVALS": 0.10,

    # Heat decay rates (points per hour)
    "DECAY_LOCAL_LEO": 10.0,
    "DECAY_FEDERAL": 2.0,
    "DECAY_INTELLIGENCE": 0.5,
    "DECAY_CORPORATE": 5.0,
    "DECAY_RIVALS": 3.0,

    # Heat generation per phase
    "HEAT_RECON_SUCCESS": 5,
    "HEAT_EXPLOIT_SUCCESS": 20,
    "HEAT_PERSIST_SUCCESS": 15,
    "HEAT_MONETIZE_SUCCESS": 25,
    "HEAT_FAILURE_MULTIPLIER": 10,

    # Skill progression
    "XP_PER_LEVEL": 1000,
    "MAX_SKILL_LEVEL": 50,
    "TIER1_MIN_LEVEL": 1,
    "TIER2_MIN_LEVEL": 10,
    "TIER3_MIN_LEVEL": 20,
    "TIER4_MIN_LEVEL": 35,
    "TIER5_MIN_LEVEL": 45,

    # Faction
    "FACTION_CONTACT_REP": 100,
    "FACTION_JOIN_REP": 300,

    # Psych
    "PSYCH_STRESS_PER_PHASE": 5,
    "PSYCH_SLEEP_DEBT_PER_PHASE": 2,
    "PSYCH_BURNOUT_PER_OP": 3,
    "GO_DARK_DECAY_MULTIPLIER": 3.0,

    # Prison
    "PRISON_BASE_HOURS": 12,
    "PRISON_MAX_HOURS": 168,
    "PRISON_TIME_SERVED_XP_PER_HOUR": 50,
    "PRISON_ESCAPE_SUCCESS_CHANCE": 0.20,
    "PRISON_ESCAPE_PENALTY_HOURS": 24,
    "PRISON_LEGAL_FIGHT_REDUCTION": 0.20,
    "PRISON_LEGAL_FIGHT_COST": 500,
    "PRISON_LEGAL_FIGHT_MAX": 3,

    # Node accessibility thresholds
    "NODE_TIER2_SKILL_REQUIRED": 5,
    "NODE_TIER3_SKILL_REQUIRED": 15,
    "NODE_TIER4_SKILL_REQUIRED": 25,
    "NODE_TIER5_SKILL_REQUIRED": 35,

    # Rate limiting
    "RATE_LIMIT_DEFAULT": "60/minute",
    "RATE_LIMIT_AUTH": "10/minute",

    # WebSocket
    "WS_PING_INTERVAL": 30,
    "WORLD_EVENT_INTERVAL_HOURS": 2,
}
