"""
Ghost Protocol — World Seed Data
50 world nodes + 10 NPC market listings
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.models import *  # noqa: F401,F403 — ensures all models are registered with Base.metadata

WORLD_NODES = [
    # CORPORATE (10)
    {"node_key": "corp_nexacorp_hq", "name": "NexaCorp Headquarters", "description": "Global tech conglomerate. Hundreds of engineering systems, financial data, and classified IP.", "category": "corporate", "tier": 3, "vulnerability_score": 45, "patch_rate": 3, "defender_tier": 3, "heat_multiplier": 1.5, "base_crypto_reward": 500, "base_reputation_reward": 25},
    {"node_key": "corp_meridian_bank", "name": "Meridian Financial Group", "description": "Tier-1 investment bank. Cleared for $500B in daily transactions.", "category": "corporate", "tier": 4, "vulnerability_score": 30, "patch_rate": 5, "defender_tier": 4, "heat_multiplier": 2.5, "base_crypto_reward": 1200, "base_reputation_reward": 50},
    {"node_key": "corp_helix_pharma", "name": "Helix Pharmaceuticals", "description": "Biotech leader. Clinical trial data and proprietary compound formulations.", "category": "corporate", "tier": 3, "vulnerability_score": 55, "patch_rate": 2, "defender_tier": 2, "heat_multiplier": 1.2, "base_crypto_reward": 450, "base_reputation_reward": 20},
    {"node_key": "corp_omnicloud", "name": "OmniCloud Infrastructure", "description": "Hosts 30% of internet traffic. Compromising this means compromising everyone using it.", "category": "corporate", "tier": 5, "vulnerability_score": 20, "patch_rate": 8, "defender_tier": 5, "heat_multiplier": 4.0, "base_crypto_reward": 3000, "base_reputation_reward": 100},
    {"node_key": "corp_globalog_logistics", "name": "GlobaLog Supply Chain", "description": "International shipping and logistics. Route manifests, customs data, tracking systems.", "category": "corporate", "tier": 2, "vulnerability_score": 65, "patch_rate": 1, "defender_tier": 2, "heat_multiplier": 1.0, "base_crypto_reward": 200, "base_reputation_reward": 15},
    {"node_key": "corp_tritec_defense", "name": "TriTec Defense Systems", "description": "Defense contractor. Weapons procurement data, government contracts, personnel files.", "category": "corporate", "tier": 4, "vulnerability_score": 35, "patch_rate": 4, "defender_tier": 4, "heat_multiplier": 3.0, "base_crypto_reward": 1500, "base_reputation_reward": 60},
    {"node_key": "corp_cascade_media", "name": "Cascade Media Network", "description": "Global news and entertainment. Influence ops goldmine.", "category": "corporate", "tier": 2, "vulnerability_score": 70, "patch_rate": 1, "defender_tier": 1, "heat_multiplier": 0.8, "base_crypto_reward": 175, "base_reputation_reward": 12},
    {"node_key": "corp_vantis_insurance", "name": "Vantis Insurance Systems", "description": "Healthcare and life insurance. Medical records, payout schedules, fraud detection systems.", "category": "corporate", "tier": 2, "vulnerability_score": 60, "patch_rate": 2, "defender_tier": 2, "heat_multiplier": 1.1, "base_crypto_reward": 220, "base_reputation_reward": 18},
    {"node_key": "corp_axiom_energy", "name": "Axiom Energy Corp", "description": "Petroleum and power grid operator. Industrial control systems adjacent.", "category": "corporate", "tier": 3, "vulnerability_score": 50, "patch_rate": 2, "defender_tier": 3, "heat_multiplier": 2.0, "base_crypto_reward": 600, "base_reputation_reward": 30},
    {"node_key": "corp_startbridge_vc", "name": "Startbridge Ventures", "description": "Silicon Valley VC firm. Pre-IPO financials, founder communications, portfolio secrets.", "category": "corporate", "tier": 1, "vulnerability_score": 75, "patch_rate": 1, "defender_tier": 1, "heat_multiplier": 0.7, "base_crypto_reward": 100, "base_reputation_reward": 8},

    # GOVERNMENT (8)
    {"node_key": "gov_municipal_chicago", "name": "City of Chicago Systems", "description": "Municipal IT infrastructure. Permits, tax records, traffic systems.", "category": "government", "tier": 1, "vulnerability_score": 80, "patch_rate": 1, "defender_tier": 1, "heat_multiplier": 1.5, "base_crypto_reward": 80, "base_reputation_reward": 10},
    {"node_key": "gov_state_dmv_network", "name": "State DMV Network", "description": "Driver's license database. Identity verification goldmine.", "category": "government", "tier": 2, "vulnerability_score": 65, "patch_rate": 1, "defender_tier": 2, "heat_multiplier": 2.0, "base_crypto_reward": 300, "base_reputation_reward": 20},
    {"node_key": "gov_federal_tax_auth", "name": "Federal Tax Authority", "description": "IRS-equivalent. Tax returns, financial records, employer data for millions.", "category": "government", "tier": 3, "vulnerability_score": 40, "patch_rate": 3, "defender_tier": 3, "heat_multiplier": 3.0, "base_crypto_reward": 700, "base_reputation_reward": 40},
    {"node_key": "gov_border_control_db", "name": "Border Control Database", "description": "Entry/exit records, passport data, watchlist integration.", "category": "government", "tier": 4, "vulnerability_score": 30, "patch_rate": 4, "defender_tier": 4, "heat_multiplier": 4.0, "base_crypto_reward": 1200, "base_reputation_reward": 65},
    {"node_key": "gov_law_enforcement_db", "name": "National Law Enforcement DB", "description": "Criminal records, warrants, informant registrations.", "category": "government", "tier": 3, "vulnerability_score": 35, "patch_rate": 3, "defender_tier": 3, "heat_multiplier": 3.5, "base_crypto_reward": 900, "base_reputation_reward": 45},
    {"node_key": "gov_health_agency", "name": "National Health Agency", "description": "Public health records, pandemic data, hospital network access.", "category": "government", "tier": 2, "vulnerability_score": 55, "patch_rate": 2, "defender_tier": 2, "heat_multiplier": 1.8, "base_crypto_reward": 350, "base_reputation_reward": 22},
    {"node_key": "gov_pentagon_adjacent", "name": "Pentagon Administrative Net", "description": "Non-classified military administration. Still extraordinarily sensitive.", "category": "government", "tier": 5, "vulnerability_score": 15, "patch_rate": 10, "defender_tier": 5, "heat_multiplier": 5.0, "base_crypto_reward": 4000, "base_reputation_reward": 120},
    {"node_key": "gov_electoral_commission", "name": "Electoral Commission Systems", "description": "Voter registration, results tabulation, district data.", "category": "government", "tier": 3, "vulnerability_score": 50, "patch_rate": 2, "defender_tier": 3, "heat_multiplier": 4.0, "base_crypto_reward": 800, "base_reputation_reward": 55},

    # DARKNET (12)
    {"node_key": "dark_market_shadow", "name": "ShadowBazaar Exchange", "description": "Established dark market with escrow and reputation system.", "category": "darknet", "tier": 1, "vulnerability_score": 70, "patch_rate": 1, "defender_tier": 1, "heat_multiplier": 0.5, "base_crypto_reward": 120, "base_reputation_reward": 15},
    {"node_key": "dark_forum_zerotrace", "name": "ZeroTrace Forums", "description": "Encrypted discussion board for elite operators. Reputation required to post.", "category": "darknet", "tier": 2, "vulnerability_score": 55, "patch_rate": 1, "defender_tier": 2, "heat_multiplier": 0.4, "base_crypto_reward": 80, "base_reputation_reward": 25},
    {"node_key": "dark_botnet_cmd_alpha", "name": "Botnet C2 Alpha", "description": "Command node for a 50k-device botnet. Tremendous bandwidth available for sale.", "category": "darknet", "tier": 3, "vulnerability_score": 50, "patch_rate": 2, "defender_tier": 2, "heat_multiplier": 1.0, "base_crypto_reward": 600, "base_reputation_reward": 35},
    {"node_key": "dark_zeroday_broker", "name": "Zero-Day Broker Service", "description": "Vuln brokers connecting researchers to buyers. Curated, opaque.", "category": "darknet", "tier": 3, "vulnerability_score": 40, "patch_rate": 2, "defender_tier": 3, "heat_multiplier": 0.8, "base_crypto_reward": 900, "base_reputation_reward": 50},
    {"node_key": "dark_ransomware_node", "name": "Ransomware Infrastructure Hub", "description": "Hosting for active ransomware campaigns. Payment portals, encryption keys.", "category": "darknet", "tier": 2, "vulnerability_score": 60, "patch_rate": 1, "defender_tier": 2, "heat_multiplier": 0.6, "base_crypto_reward": 400, "base_reputation_reward": 30},
    {"node_key": "dark_collective_safe", "name": "The Collective Safehouse", "description": "Encrypted communication node for hacktivist coordination.", "category": "darknet", "tier": 2, "vulnerability_score": 45, "patch_rate": 1, "defender_tier": 2, "heat_multiplier": 0.3, "base_crypto_reward": 200, "base_reputation_reward": 40},
    {"node_key": "dark_black_array_base", "name": "Black Array Operations Base", "description": "Primary C2 for the Black Array ransomware cartel.", "category": "darknet", "tier": 4, "vulnerability_score": 25, "patch_rate": 3, "defender_tier": 4, "heat_multiplier": 0.5, "base_crypto_reward": 1500, "base_reputation_reward": 75},
    {"node_key": "dark_identity_mill", "name": "Identity Mill", "description": "Generates synthetic identities at scale. Documents, legends, social history.", "category": "darknet", "tier": 2, "vulnerability_score": 65, "patch_rate": 1, "defender_tier": 1, "heat_multiplier": 0.4, "base_crypto_reward": 300, "base_reputation_reward": 20},
    {"node_key": "dark_data_fencing", "name": "DataFence Repository", "description": "Receives and sells stolen databases. Active inventory of 200M+ records.", "category": "darknet", "tier": 3, "vulnerability_score": 55, "patch_rate": 2, "defender_tier": 2, "heat_multiplier": 0.7, "base_crypto_reward": 700, "base_reputation_reward": 40},
    {"node_key": "dark_crypto_laundry", "name": "Crypto Laundry Service", "description": "Specialized mixing and tumbling infrastructure for high-volume transactions.", "category": "darknet", "tier": 2, "vulnerability_score": 60, "patch_rate": 1, "defender_tier": 2, "heat_multiplier": 0.5, "base_crypto_reward": 350, "base_reputation_reward": 25},
    {"node_key": "dark_whistleblower_drop", "name": "SecureDrop Equivalent", "description": "Anonymous document submission node used by journalists and insiders.", "category": "darknet", "tier": 1, "vulnerability_score": 75, "patch_rate": 0, "defender_tier": 1, "heat_multiplier": 0.2, "base_crypto_reward": 60, "base_reputation_reward": 30},
    {"node_key": "dark_ai_oracle_node", "name": "DELPHI Infrastructure Node", "description": "Backend for the DELPHI intelligence service. What does it know about you?", "category": "darknet", "tier": 4, "vulnerability_score": 20, "patch_rate": 4, "defender_tier": 4, "heat_multiplier": 0.6, "base_crypto_reward": 2000, "base_reputation_reward": 100},

    # TELECOM (5)
    {"node_key": "tel_isp_tier1_north", "name": "NorthNet ISP Backbone", "description": "Tier-1 ISP. Route traffic. Intercept unencrypted sessions at scale.", "category": "telecom", "tier": 3, "vulnerability_score": 40, "patch_rate": 3, "defender_tier": 3, "heat_multiplier": 2.5, "base_crypto_reward": 700, "base_reputation_reward": 35},
    {"node_key": "tel_mobile_carrier_data", "name": "Pulse Mobile Carrier", "description": "120M subscriber records. Location data, call metadata, billing.", "category": "telecom", "tier": 3, "vulnerability_score": 45, "patch_rate": 3, "defender_tier": 3, "heat_multiplier": 2.0, "base_crypto_reward": 600, "base_reputation_reward": 30},
    {"node_key": "tel_undersea_cable_hub", "name": "Pacific Cable Landing Station", "description": "Physical infrastructure for transatlantic internet traffic.", "category": "telecom", "tier": 4, "vulnerability_score": 30, "patch_rate": 4, "defender_tier": 4, "heat_multiplier": 3.5, "base_crypto_reward": 1800, "base_reputation_reward": 70},
    {"node_key": "tel_satellite_uplink", "name": "SkyNet Satellite Operations", "description": "Commercial satellite operator. GPS, communications, imaging.", "category": "telecom", "tier": 3, "vulnerability_score": 35, "patch_rate": 3, "defender_tier": 3, "heat_multiplier": 2.8, "base_crypto_reward": 800, "base_reputation_reward": 40},
    {"node_key": "tel_voip_exchange", "name": "GlobalVoice Exchange", "description": "VoIP infrastructure. Active call routing for 50M+ daily connections.", "category": "telecom", "tier": 2, "vulnerability_score": 60, "patch_rate": 2, "defender_tier": 2, "heat_multiplier": 1.5, "base_crypto_reward": 300, "base_reputation_reward": 20},

    # SOCIAL MEDIA (8)
    {"node_key": "social_threadnet_core", "name": "ThreadNet Platform Core", "description": "Twitter-equivalent. 500M users. DMs, ad targeting data, shadow bans list.", "category": "social_media", "tier": 3, "vulnerability_score": 50, "patch_rate": 3, "defender_tier": 3, "heat_multiplier": 1.5, "base_crypto_reward": 600, "base_reputation_reward": 30},
    {"node_key": "social_facemesh_auth", "name": "FaceMesh Authentication", "description": "Facebook-equivalent auth systems. OAuth tokens for 2B users.", "category": "social_media", "tier": 4, "vulnerability_score": 30, "patch_rate": 5, "defender_tier": 4, "heat_multiplier": 2.0, "base_crypto_reward": 1500, "base_reputation_reward": 60},
    {"node_key": "social_prism_search", "name": "Prism Search Engine", "description": "Search history, user profiling, predictive behavior data.", "category": "social_media", "tier": 4, "vulnerability_score": 25, "patch_rate": 5, "defender_tier": 4, "heat_multiplier": 2.5, "base_crypto_reward": 2000, "base_reputation_reward": 80},
    {"node_key": "social_cryptogram_app", "name": "CryptoGram Messaging", "description": "End-to-end encrypted messaging. Metadata is everything.", "category": "social_media", "tier": 2, "vulnerability_score": 55, "patch_rate": 2, "defender_tier": 2, "heat_multiplier": 1.0, "base_crypto_reward": 250, "base_reputation_reward": 18},
    {"node_key": "social_stream_platform", "name": "StreamCore Live Platform", "description": "Live streaming and creator economy platform. Financial and identity data.", "category": "social_media", "tier": 2, "vulnerability_score": 65, "patch_rate": 1, "defender_tier": 1, "heat_multiplier": 0.8, "base_crypto_reward": 200, "base_reputation_reward": 12},
    {"node_key": "social_profnet_business", "name": "ProfNet Business Network", "description": "LinkedIn-equivalent. Executive contacts, job history, corporate org charts.", "category": "social_media", "tier": 2, "vulnerability_score": 70, "patch_rate": 1, "defender_tier": 2, "heat_multiplier": 1.0, "base_crypto_reward": 220, "base_reputation_reward": 15},
    {"node_key": "social_shortclip_algo", "name": "ShortClip Algorithm Core", "description": "Short video platform. Content recommendation algorithms, engagement manipulation tools.", "category": "social_media", "tier": 3, "vulnerability_score": 45, "patch_rate": 3, "defender_tier": 3, "heat_multiplier": 1.2, "base_crypto_reward": 550, "base_reputation_reward": 28},
    {"node_key": "social_darkweb_forum", "name": "Crimson Boards", "description": "Surface-layer extremist forum. Recruitment networks, planning threads, funding trails.", "category": "social_media", "tier": 1, "vulnerability_score": 80, "patch_rate": 0, "defender_tier": 1, "heat_multiplier": 0.5, "base_crypto_reward": 90, "base_reputation_reward": 8},

    # INFRASTRUCTURE (7)
    {"node_key": "infra_power_grid_west", "name": "Western Power Grid SCADA", "description": "Industrial control systems for regional power distribution. Catastrophic potential.", "category": "infrastructure", "tier": 5, "vulnerability_score": 20, "patch_rate": 5, "defender_tier": 5, "heat_multiplier": 5.0, "base_crypto_reward": 5000, "base_reputation_reward": 150},
    {"node_key": "infra_hospital_network", "name": "MediCore Hospital Network", "description": "Healthcare systems for 200 hospitals. Patient records, medication dispensers, surgery scheduling.", "category": "infrastructure", "tier": 4, "vulnerability_score": 40, "patch_rate": 3, "defender_tier": 3, "heat_multiplier": 4.0, "base_crypto_reward": 1500, "base_reputation_reward": 70},
    {"node_key": "infra_water_treatment", "name": "Metropolitan Water Authority", "description": "Chemical control systems for urban water treatment. SCADA exposure.", "category": "infrastructure", "tier": 4, "vulnerability_score": 45, "patch_rate": 2, "defender_tier": 3, "heat_multiplier": 4.5, "base_crypto_reward": 1800, "base_reputation_reward": 80},
    {"node_key": "infra_transit_control", "name": "CityTransit Control Center", "description": "Rail and bus fleet management. Signal systems, passenger data.", "category": "infrastructure", "tier": 2, "vulnerability_score": 65, "patch_rate": 1, "defender_tier": 2, "heat_multiplier": 2.5, "base_crypto_reward": 350, "base_reputation_reward": 25},
    {"node_key": "infra_financial_clearing", "name": "Financial Clearing Network", "description": "SWIFT-equivalent interbank clearing. Trillions in daily settlement exposure.", "category": "infrastructure", "tier": 5, "vulnerability_score": 15, "patch_rate": 8, "defender_tier": 5, "heat_multiplier": 5.0, "base_crypto_reward": 6000, "base_reputation_reward": 200},
    {"node_key": "infra_cloud_dns", "name": "Global DNS Infrastructure", "description": "Root DNS servers. DNS hijacking potential is world-class.", "category": "infrastructure", "tier": 4, "vulnerability_score": 25, "patch_rate": 4, "defender_tier": 4, "heat_multiplier": 3.5, "base_crypto_reward": 2500, "base_reputation_reward": 90},
    {"node_key": "infra_emergency_comms", "name": "Emergency Response Network", "description": "Police, fire, ambulance dispatch communications for tri-state area.", "category": "infrastructure", "tier": 3, "vulnerability_score": 50, "patch_rate": 2, "defender_tier": 3, "heat_multiplier": 3.0, "base_crypto_reward": 750, "base_reputation_reward": 45},
]

NPC_MARKET_LISTINGS = [
    {"item_type": "tool", "item_name": "Basic Exploit Kit", "description": "Pre-packaged CVE exploits for Tier 1-2 targets. +10% exploit success for 3 operations.", "price_crypto": 200, "effect_data": {"exploit_bonus": 0.10, "uses": 3}},
    {"item_type": "tool", "item_name": "Burner Phone", "description": "Fresh device with zero forensic trace. Complete operational separation.", "price_crypto": 150, "effect_data": {"device_type": "phone", "trace_level": 0}},
    {"item_type": "identity_package", "item_name": "Identity Package (Basic)", "description": "New alias with supporting documentation. Quality: 60/100.", "price_crypto": 300, "effect_data": {"documents_quality": 60, "alias_quality": "basic"}},
    {"item_type": "tool", "item_name": "VPN Router", "description": "Encrypted routing hardware. Reduces IP leak artifact chance by 30%.", "price_crypto": 400, "effect_data": {"ip_leak_reduction": 0.30}},
    {"item_type": "tool", "item_name": "Log Wiper Pro", "description": "Automated artifact cleanup tool. Wipe 2 artifacts post-operation.", "price_crypto": 250, "effect_data": {"post_op_wipe": 2, "uses": 5}},
    {"item_type": "tool", "item_name": "Privacy Coin Mixer", "description": "Reduces laundering fees by 20% for 24 hours.", "price_crypto": 500, "effect_data": {"laundering_discount": 0.20, "duration_hours": 24}},
    {"item_type": "tool", "item_name": "OSINT Database Access", "description": "6-month subscription to aggregated public data. +15% recon success for 5 ops.", "price_crypto": 350, "effect_data": {"recon_bonus": 0.15, "uses": 5}},
    {"item_type": "tool", "item_name": "Backdoor Kit v2", "description": "Advanced persistence toolkit. +20% persist success for 3 operations.", "price_crypto": 600, "effect_data": {"persist_bonus": 0.20, "uses": 3}},
    {"item_type": "identity_package", "item_name": "Cover Story Package", "description": "Detailed backstory and supporting documents for existing identity. +20 document quality.", "price_crypto": 200, "effect_data": {"document_quality_boost": 20}},
    {"item_type": "pharmaceutical", "item_name": "Paranoia Suppressant", "description": "Clinical-grade anxiolytic. Reduces paranoia by 30, sleep debt by 20. 5 uses.", "price_crypto": 100, "effect_data": {"paranoia_reduction": 30, "sleep_reduction": 20, "uses": 5}},
]


async def run_seed():
    from app.config import settings
    from app.database import Base
    from app.models.player import WorldNode, MarketListing

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionFactory() as session:
        existing = await session.execute(select(WorldNode).limit(1))
        if existing.scalar_one_or_none():
            print("World nodes already seeded. Skipping.")
        else:
            for node_data in WORLD_NODES:
                node = WorldNode(**node_data)
                session.add(node)
            await session.commit()
            print(f"Seeded {len(WORLD_NODES)} world nodes.")

        existing_market = await session.execute(select(MarketListing).limit(1))
        if existing_market.scalar_one_or_none():
            print("Market listings already seeded. Skipping.")
        else:
            for listing_data in NPC_MARKET_LISTINGS:
                listing = MarketListing(**listing_data, quantity=-1)
                session.add(listing)
            await session.commit()
            print(f"Seeded {len(NPC_MARKET_LISTINGS)} NPC market listings.")

    await engine.dispose()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(run_seed())
