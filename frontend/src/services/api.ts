import axios, { type AxiosError } from 'axios'
import { useGameStore } from '../store/gameStore'
import type {
  TokenResponse,
  PlayerProfile,
  HeatStatus,
  WorldNode,
  NodeIntel,
  Operation,
  PhaseOutcome,
  OperationResult,
  SkillTree,
  WalletStatus,
  MarketListing,
  LaunderingChain,
  FactionRelation,
  PrisonStatus,
  OnboardingState,
  TraceGraph,
} from '../types'

// ─── Axios instance ───────────────────────────────────────────────────────────
// VITE_API_URL is set in production (e.g. https://ghost-protocol-backend.railway.app)
// In dev, falls back to /api/v1 which is proxied by vite to localhost:8000

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach auth token from store
api.interceptors.request.use((config) => {
  const token = useGameStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 globally — clear auth and redirect to login
api.interceptors.response.use(
  (res) => res,
  (err: AxiosError) => {
    if (err.response?.status === 401) {
      useGameStore.getState().clearAuth()
      window.location.href = '/'
    }
    return Promise.reject(err)
  }
)

// ─── Helper ───────────────────────────────────────────────────────────────────

function data<T>(promise: Promise<{ data: T }>): Promise<T> {
  return promise.then((r) => r.data)
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (handle: string, email: string, password: string) =>
    data<TokenResponse>(api.post('/auth/register', { handle, email, password })),

  login: (handle: string, password: string) =>
    data<TokenResponse>(api.post('/auth/login', { handle, password })),

  me: () =>
    data<PlayerProfile>(api.get('/auth/me')),
}

// ─── Player ───────────────────────────────────────────────────────────────────

export const playerApi = {
  getProfile: () =>
    data<PlayerProfile>(api.get('/players/me')),

  getPublicProfile: (handle: string) =>
    data<{ id: string; handle: string; reputation: number; created_at: string }>(
      api.get(`/players/${handle}`)
    ),
}

// ─── World ────────────────────────────────────────────────────────────────────

export const worldApi = {
  getNodes: () =>
    data<WorldNode[]>(api.get('/world/nodes')),

  getAccessibleNodes: () =>
    data<WorldNode[]>(api.get('/world/nodes/accessible')),

  getNodeIntel: (nodeKey: string) =>
    data<NodeIntel>(api.get(`/world/nodes/${nodeKey}/intel`)),

  getWorldMap: () =>
    data<{ nodes: WorldNode[]; categories: string[]; player_max_tier: number }>(
      api.get('/world/map')
    ),
}

// ─── Operations ───────────────────────────────────────────────────────────────

export const operationApi = {
  create: (nodeKey: string, deviceId: string, approach: string, identityId?: string) =>
    data<{ operation_id: string; briefing: string; node: WorldNode; energy_cost: number }>(
      api.post('/operations/', { node_key: nodeKey, device_id: deviceId, approach, identity_id: identityId })
    ),

  advance: (operationId: string, phaseAction: string, parameters: Record<string, unknown> = {}) =>
    data<PhaseOutcome>(
      api.post(`/operations/${operationId}/advance`, { phase_action: phaseAction, parameters })
    ),

  abort: (operationId: string) =>
    data<{ message: string; xp_awarded: Record<string, number> }>(
      api.post(`/operations/${operationId}/abort`)
    ),

  getResult: (operationId: string) =>
    data<OperationResult>(api.get(`/operations/${operationId}/result`)),

  getHistory: (limit = 20) =>
    data<Operation[]>(api.get(`/operations/history?limit=${limit}`)),

  getActive: () =>
    data<Operation | null>(api.get('/operations/active')),
}

// ─── Heat ─────────────────────────────────────────────────────────────────────

export const heatApi = {
  getStatus: () =>
    data<HeatStatus>(api.get('/heat/status')),

  goDark: (hours: number) =>
    data<{ message: string; go_dark_until: string; projected_heat: Record<string, number> }>(
      api.post('/heat/go-dark', { hours })
    ),

  getDecayPreview: () =>
    data<{ current_total: number; projected_24h: number; projected_72h: number; domains: Record<string, unknown> }>(
      api.get('/heat/decay-preview')
    ),
}

// ─── Trace Graph ──────────────────────────────────────────────────────────────

export const traceApi = {
  getGraph: () =>
    data<TraceGraph>(api.get('/trace/graph')),

  getExposure: (identityId: string) =>
    data<{ identity_id: string; exposure_score: number; connected_artifacts: number; risk_level: string }>(
      api.get(`/trace/identity/${identityId}/exposure`)
    ),

  wipeArtifact: (artifactId: string) =>
    data<{ message: string }>(api.post(`/trace/artifact/${artifactId}/wipe`)),
}

// ─── Skills ───────────────────────────────────────────────────────────────────

export const skillApi = {
  getTrees: () =>
    data<{ trees: Record<string, SkillTree>; total_level: number }>(api.get('/skills/')),

  getTree: (treeKey: string) =>
    data<SkillTree>(api.get(`/skills/${treeKey}`)),
}

// ─── Economy ──────────────────────────────────────────────────────────────────

export const economyApi = {
  getWallet: () =>
    data<WalletStatus>(api.get('/economy/wallet')),

  getMarket: () =>
    data<MarketListing[]>(api.get('/economy/market')),

  purchase: (listingId: string) =>
    data<{ message: string; item_name: string; new_balance: number }>(
      api.post('/economy/market/purchase', { listing_id: listingId })
    ),

  launderPreview: (amount: number) =>
    data<LaunderingChain>(api.post('/economy/launder/preview', { amount })),

  launder: (amount: number) =>
    data<{ message: string; chain: LaunderingChain; new_crypto: number; privacy_coin_gained: number }>(
      api.post('/economy/launder', { amount })
    ),

  getTransactions: (limit = 20) =>
    data<Array<{ id: string; amount: number; currency: string; description: string; created_at: string }>>(
      api.get(`/economy/transactions?limit=${limit}`)
    ),
}

// ─── Factions ─────────────────────────────────────────────────────────────────

export const factionApi = {
  getRelations: () =>
    data<FactionRelation[]>(api.get('/factions/')),

  getIntroMessage: (factionKey: string) =>
    data<{ faction_key: string; npc_name: string; message: string; requirements: Record<string, unknown> }>(
      api.get(`/factions/${factionKey}/intro`)
    ),

  joinFaction: (factionKey: string) =>
    data<{ message: string; faction_key: string }>(
      api.post(`/factions/${factionKey}/join`)
    ),
}

// ─── Prison ───────────────────────────────────────────────────────────────────

export const prisonApi = {
  getStatus: () =>
    data<PrisonStatus>(api.get('/prison/status')),

  performActivity: (activityType: string) =>
    data<{ message: string; outcome: string; cost_crypto: number }>(
      api.post('/prison/activity', { activity_type: activityType })
    ),
}

// ─── Onboarding ───────────────────────────────────────────────────────────────

export const onboardingApi = {
  getState: () =>
    data<OnboardingState>(api.get('/onboarding/state')),

  getHandlerMessage: (step: string) =>
    data<{ step: string; message: string; hint: string }>(
      api.get(`/onboarding/handler-message/${step}`)
    ),
}

// ─── AI ───────────────────────────────────────────────────────────────────────

export const aiApi = {
  chat: (npcKey: string, message: string, context: Record<string, unknown> = {}) =>
    data<{ response: string; suspicion_delta: number; success_probability: number }>(
      api.post('/ai/npc-chat', { npc_key: npcKey, message, context })
    ),
}

export default api
