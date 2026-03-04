// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string
  token_type: string
  player_id: string
  handle: string
}

// ─── Player ───────────────────────────────────────────────────────────────────

export interface PlayerStats {
  xp_social: number
  xp_exploitation: number
  xp_cryptography: number
  xp_hardware: number
  xp_counterintel: number
  xp_economics: number
  fiat: number
  crypto: number
  privacy_coin: number
  reputation: number
  energy: number
  max_energy: number
  energy_regen_rate: number
  last_energy_update: string
}

export interface PsychState {
  stress: number
  paranoia: number
  sleep_debt: number
  ego: number
  burnout: number
  trust_index: number
  focus: number
  stimulant_dependency: number
  sedative_dependency: number
  last_updated: string
}

export interface Device {
  id: string
  name: string
  device_type: string
  mac_fingerprint: string
  firmware_version: string
  forensic_trace_level: number
  is_compromised: boolean
  is_destroyed: boolean
  under_surveillance: boolean
  created_at: string
}

export interface Identity {
  id: string
  alias: string
  cover_story: string
  documents_quality: number
  is_burned: boolean
  heat_accumulated: number
  created_at: string
}

export interface PlayerProfile {
  id: string
  handle: string
  created_at: string
  last_active: string | null
  stats: PlayerStats
  psych: PsychState
  devices: Device[]
  identities: Identity[]
}

// ─── World ────────────────────────────────────────────────────────────────────

export interface WorldNode {
  id: string
  node_key: string
  name: string
  description: string
  category: string
  tier: number
  vulnerability_score: number
  patch_rate: number
  defender_tier: number
  heat_multiplier: number
  base_crypto_reward: number
  base_reputation_reward: number
  is_active: boolean
  last_breached_at: string | null
}

export interface NodeIntel {
  node: WorldNode
  success_chance: number
  alert_level: number
  estimated_heat_gain: number
  recommended_approach: string
  skill_assessment: {
    relevant_tree: string
    current_level: number
    bonus_applied: number
  }
}

// ─── Operations ───────────────────────────────────────────────────────────────

export type OperationPhase = 'recon' | 'exploit' | 'persist' | 'monetize'
export type OperationApproach = 'technical' | 'social' | 'hybrid'
export type OperationStatus = 'planning' | 'active' | 'completed' | 'failed' | 'aborted'

export interface PhaseOutcome {
  phase: OperationPhase
  success: boolean
  narrative: string
  artifacts_generated: string[]
  xp_partial: Record<string, number>
  heat_generated: number
  next_phase_unlocked: boolean
  can_abort: boolean
  next_phase: OperationPhase | null
}

export interface Operation {
  id: string
  player_id: string
  node_id: string
  status: OperationStatus
  approach: OperationApproach
  phase_data: Record<string, unknown>
  artifacts_left: string[]
  heat_generated: number
  xp_awarded: Record<string, number>
  crypto_earned: number
  reputation_earned: number
  started_at: string
  completed_at: string | null
  fail_reason: string | null
}

export interface OperationResult {
  operation_id: string
  status: OperationStatus
  narrative: string
  total_xp: Record<string, number>
  crypto_earned: number
  reputation_earned: number
  heat_generated: number
  artifacts_left: number
  phases_completed: number
  ai_debrief: string | null
}

// ─── Heat ─────────────────────────────────────────────────────────────────────

export type HeatDomain = 'local_leo' | 'federal' | 'intelligence' | 'corporate' | 'rivals'

export interface HeatDomainStatus {
  domain: HeatDomain
  level: number
  decay_rate: number
  last_incident_at: string
}

export type ThreatTier = 1 | 2 | 3 | 4 | 5
export const THREAT_TIER_NAMES: Record<ThreatTier, string> = {
  1: 'OFF THE RADAR',
  2: 'PERSONS OF INTEREST',
  3: 'ACTIVE INQUIRY',
  4: 'MANHUNT',
  5: 'ARREST PROBABLE',
}

export interface HeatStatus {
  player_id: string
  domains: Record<HeatDomain, HeatDomainStatus>
  total_heat: number
  threat_tier: ThreatTier
  threat_tier_name: string
  threat_description: string
  is_dark_web_burned: boolean
  estimated_time_to_decay_safe: number
  go_dark_until: string | null
}

// ─── Economy ──────────────────────────────────────────────────────────────────

export interface WalletStatus {
  player_id: string
  fiat: number
  crypto: number
  privacy_coin: number
}

export interface MarketListing {
  id: string
  seller_player_id: string | null
  item_type: string
  item_name: string
  description: string
  price_crypto: number
  quantity: number
  is_active: boolean
  expires_at: string | null
  effect_data: Record<string, unknown>
}

export interface LaunderingStep {
  step: number
  amount_in: number
  fee: number
  amount_out: number
}

export interface LaunderingChain {
  steps: LaunderingStep[]
  total_fees: number
  final_privacy_coin: number
  intelligence_heat_added: number
}

// ─── Skills ───────────────────────────────────────────────────────────────────

export interface SkillAbility {
  id: string
  name: string
  tier: number
  level_required: number
  description: string
  operation_bonus: number
  passive: boolean
  unlocked: boolean
}

export interface SkillTree {
  tree_name: string
  code: string
  stat_field: string
  description: string
  current_level: number
  current_xp: number
  xp_to_next: number
  abilities: SkillAbility[]
}

// ─── Trace Graph ──────────────────────────────────────────────────────────────

export interface TraceNode {
  id: string
  label: string
  type: 'Player' | 'Identity' | 'Device' | 'WorldNode' | 'Artifact'
  properties: Record<string, unknown>
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

export interface TraceEdge {
  source: string | TraceNode
  target: string | TraceNode
  type: string
  properties: Record<string, unknown>
}

export interface TraceGraph {
  nodes: TraceNode[]
  edges: TraceEdge[]
  fallback?: boolean
}

// ─── Factions ─────────────────────────────────────────────────────────────────

export interface FactionRelation {
  faction_key: string
  standing: number
  is_member: boolean
  joined_at: string | null
  contact_eligible: boolean
}

// ─── Prison ───────────────────────────────────────────────────────────────────

export interface PrisonStatus {
  is_imprisoned: boolean
  sentence_hours: number
  arrested_at: string
  release_at: string
  charge_description: string
  time_remaining_hours: number
  broker_info_count: number
  legal_fight_count: number
  escaped: boolean
  activities: PrisonActivity[]
}

export interface PrisonActivity {
  id: string
  activity_type: string
  description: string
  cost_crypto: number
  outcome: string | null
  created_at: string
  resolved_at: string | null
}

// ─── WebSocket Events ─────────────────────────────────────────────────────────

export type WSEventType =
  | 'heat_update'
  | 'operation_update'
  | 'operation_complete'
  | 'world_event'
  | 'faction_contact'
  | 'prison_update'
  | 'onboarding_update'
  | 'pong'

export interface WSEvent {
  type: WSEventType
  data: Record<string, unknown>
  timestamp: string
}

// ─── Onboarding ───────────────────────────────────────────────────────────────

export interface OnboardingState {
  current_step: string
  completed_steps: string[]
  is_complete: boolean
  handler_message: string | null
}

// ─── Activity Feed ────────────────────────────────────────────────────────────

export interface ActivityEntry {
  id: string
  timestamp: string
  type: 'operation' | 'heat' | 'economy' | 'faction' | 'system' | 'world_event' | 'prison'
  message: string
  level: 'info' | 'success' | 'warning' | 'danger'
}
