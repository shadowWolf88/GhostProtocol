"""
Ghost Protocol — Faction Definitions
Five factions. Each a different answer to the same question: how do you survive?
"""

FACTION_DATA = {
    "collective": {
        "name": "The Collective",
        "philosophy": "Information wants to be free. We are the proof.",
        "specialty": "Coordination and reach. Numbers are our weapon.",
        "contact_threshold": 100,
        "join_threshold": 300,
        "initiation_mission_type": "data_exfil",
        "faction_bonuses": {
            "recon_success": 0.05,
            "market_discount": 0.10,
        },
        "faction_penalties": {
            "solo_op_heat": 1.15,
        },
        "npc_contact": {
            "handle": "STATIC",
            "intro_message": (
                "STATIC: Signal established. You've been noticed. Your work has a... philosophy to it.\n"
                "We appreciate philosophy. Numbers move mountains. One operator moves files.\n"
                "When you're ready to stop working alone, find us.\n"
                "— STATIC, The Collective"
            ),
            "flavor": "Sounds like static on an encrypted channel. Then a voice.",
        },
        "color": "#00ff41",
    },
    "black_array": {
        "name": "Black Array",
        "philosophy": "Everything has a price. We set it.",
        "specialty": "Ransomware operations, extortion, pure financial extraction.",
        "contact_threshold": 150,
        "join_threshold": 400,
        "initiation_mission_type": "ransomware",
        "faction_bonuses": {
            "monetize_success": 0.10,
            "crypto_reward": 1.25,
        },
        "faction_penalties": {
            "heat_multiplier": 1.20,
        },
        "npc_contact": {
            "handle": "PAYDAY",
            "intro_message": (
                "PAYDAY: We've been watching your numbers. Solid.\n"
                "Sentiment is irrelevant. Ransom is religion.\n"
                "You want to make real money or play activist?\n"
                "Join us. We'll show you what your work is worth.\n"
                "— PAYDAY, Black Array"
            ),
            "flavor": "A notification. No sender. Just a number. A very large number.",
        },
        "color": "#ff4444",
    },
    "sovereign_shield": {
        "name": "Sovereign Shield",
        "philosophy": "Security is a product. We manufacture it.",
        "specialty": "Corporate resources, legal cover, institutional knowledge.",
        "contact_threshold": 200,
        "join_threshold": 500,
        "initiation_mission_type": "counter_intel",
        "faction_bonuses": {
            "heat_decay": 1.30,
            "legal_protection": True,
        },
        "faction_penalties": {
            "exploit_heat": 1.10,
        },
        "npc_contact": {
            "handle": "DIRECTOR",
            "intro_message": (
                "DIRECTOR: Your operational profile is... unconventional. Effective.\n"
                "We offer structure. Resources. Legitimate cover when needed.\n"
                "In exchange, we ask for professionalism. And occasionally, a favor.\n"
                "Consider our offer carefully.\n"
                "— DIRECTOR, Sovereign Shield"
            ),
            "flavor": "An encrypted attachment. Corporate letterhead. An offer.",
        },
        "color": "#00ffff",
    },
    "signal_zero": {
        "name": "Signal Zero",
        "philosophy": "Intelligence is the only currency that matters.",
        "specialty": "Information control, government connections, plausible deniability.",
        "contact_threshold": 250,
        "join_threshold": 600,
        "initiation_mission_type": "osint_hunt",
        "faction_bonuses": {
            "intel_quality": 0.20,
            "heat_immunity_intel_domain": True,
        },
        "faction_penalties": {
            "anonymity_cost": 1.20,
        },
        "npc_contact": {
            "handle": "ORACLE",
            "intro_message": (
                "ORACLE: We know what you did. We know what you're planning.\n"
                "We're not here to arrest you. We're here to employ you.\n"
                "The distinction matters. For now.\n"
                "— ORACLE, Signal Zero"
            ),
            "flavor": "Nothing. Then everything. They were watching the whole time.",
        },
        "color": "#ffaa00",
    },
    "freenode": {
        "name": "Freenode",
        "philosophy": "No flags. No masters. The work is the work.",
        "specialty": "Flexible, neutral, mercenary. Take any contract, serve no ideology.",
        "contact_threshold": 80,
        "join_threshold": 200,
        "initiation_mission_type": "any",
        "faction_bonuses": {
            "contract_variety": True,
            "reputation_conversion": 1.15,
        },
        "faction_penalties": {
            "faction_loyalty_cap": 60,
        },
        "npc_contact": {
            "handle": "BROKER",
            "intro_message": (
                "BROKER: Work's available. No questions. No commitments.\n"
                "You in?\n"
                "— BROKER, Freenode"
            ),
            "flavor": "Three words on a forum post. Encrypted. Then deleted.",
        },
        "color": "#888888",
    },
}
