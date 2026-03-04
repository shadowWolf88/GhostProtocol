import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type {
  PlayerProfile,
  HeatStatus,
  Operation,
  ActivityEntry,
  OnboardingState,
  WSEvent,
} from '../types'

interface AuthSlice {
  token: string | null
  playerId: string | null
  handle: string | null
  setAuth: (token: string, playerId: string, handle: string) => void
  clearAuth: () => void
}

interface PlayerSlice {
  profile: PlayerProfile | null
  heatStatus: HeatStatus | null
  activeOperation: Operation | null
  setProfile: (profile: PlayerProfile) => void
  setHeatStatus: (heat: HeatStatus) => void
  setActiveOperation: (op: Operation | null) => void
  updateEnergy: (energy: number) => void
}

interface UISlice {
  activePanel: 'terminal' | 'trace' | 'skills' | 'market' | 'faction' | 'prison'
  isScanlines: boolean
  notifications: Array<{ id: string; message: string; level: string; expires: number }>
  setActivePanel: (panel: UISlice['activePanel']) => void
  toggleScanlines: () => void
  addNotification: (message: string, level?: string, durationMs?: number) => void
  dismissNotification: (id: string) => void
}

interface ActivitySlice {
  feed: ActivityEntry[]
  addActivity: (entry: Omit<ActivityEntry, 'id' | 'timestamp'>) => void
  clearFeed: () => void
}

interface OnboardingSlice {
  onboarding: OnboardingState | null
  setOnboarding: (state: OnboardingState) => void
  dismissOnboarding: () => void
}

interface WSSlice {
  wsConnected: boolean
  lastEvent: WSEvent | null
  setWSConnected: (connected: boolean) => void
  handleWSEvent: (event: WSEvent) => void
}

type GameStore = AuthSlice & PlayerSlice & UISlice & ActivitySlice & OnboardingSlice & WSSlice

let notifCounter = 0

export const useGameStore = create<GameStore>()(
  persist(
    (set, get) => ({
      // ── Auth ────────────────────────────────────────────────────────────────
      token: null,
      playerId: null,
      handle: null,
      setAuth: (token, playerId, handle) => set({ token, playerId, handle }),
      clearAuth: () => set({
        token: null, playerId: null, handle: null,
        profile: null, heatStatus: null, activeOperation: null,
      }),

      // ── Player ──────────────────────────────────────────────────────────────
      profile: null,
      heatStatus: null,
      activeOperation: null,
      setProfile: (profile) => set({ profile }),
      setHeatStatus: (heatStatus) => set({ heatStatus }),
      setActiveOperation: (op) => set({ activeOperation: op }),
      updateEnergy: (energy) => set((s) => {
        if (!s.profile) return {}
        return { profile: { ...s.profile, stats: { ...s.profile.stats, energy } } }
      }),

      // ── UI ───────────────────────────────────────────────────────────────────
      activePanel: 'terminal',
      isScanlines: true,
      notifications: [],
      setActivePanel: (panel) => set({ activePanel: panel }),
      toggleScanlines: () => set((s) => ({ isScanlines: !s.isScanlines })),
      addNotification: (message, level = 'info', durationMs = 5000) => {
        const id = `notif-${++notifCounter}`
        const expires = Date.now() + durationMs
        set((s) => ({ notifications: [...s.notifications, { id, message, level, expires }] }))
        setTimeout(() => get().dismissNotification(id), durationMs)
      },
      dismissNotification: (id) =>
        set((s) => ({ notifications: s.notifications.filter((n) => n.id !== id) })),

      // ── Activity Feed ─────────────────────────────────────────────────────────
      feed: [],
      addActivity: (entry) => {
        const full: ActivityEntry = {
          ...entry,
          id: `act-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
          timestamp: new Date().toISOString(),
        }
        set((s) => ({ feed: [full, ...s.feed].slice(0, 100) }))
      },
      clearFeed: () => set({ feed: [] }),

      // ── Onboarding ────────────────────────────────────────────────────────────
      onboarding: null,
      setOnboarding: (onboarding) => set({ onboarding }),
      dismissOnboarding: () => set({ onboarding: null }),

      // ── WebSocket ─────────────────────────────────────────────────────────────
      wsConnected: false,
      lastEvent: null,
      setWSConnected: (wsConnected) => set({ wsConnected }),
      handleWSEvent: (event) => {
        set({ lastEvent: event })
        const { addActivity, addNotification, setHeatStatus, setActiveOperation } = get()

        switch (event.type) {
          case 'heat_update': {
            const heat = event.data as unknown as HeatStatus
            setHeatStatus(heat)
            if (heat.threat_tier >= 4) {
              addNotification(
                `[!] HEAT CRITICAL — ${heat.threat_tier_name} — ${Math.round(heat.total_heat)}`,
                'danger',
                8000
              )
            }
            addActivity({ type: 'heat', message: `Heat updated: ${Math.round(heat.total_heat)} (${heat.threat_tier_name})`, level: heat.threat_tier >= 4 ? 'danger' : 'info' })
            break
          }
          case 'operation_update': {
            const data = event.data as { operation_id: string; phase: string; success: boolean; narrative: string }
            addActivity({
              type: 'operation',
              message: `[${data.phase.toUpperCase()}] ${data.success ? '✓' : '✗'} ${data.narrative.slice(0, 80)}...`,
              level: data.success ? 'success' : 'warning',
            })
            break
          }
          case 'operation_complete': {
            setActiveOperation(null)
            const data = event.data as { status: string; crypto_earned: number }
            addActivity({
              type: 'operation',
              message: `Operation ${data.status}. +${data.crypto_earned} crypto`,
              level: data.status === 'completed' ? 'success' : 'danger',
            })
            addNotification(
              `Operation ${data.status.toUpperCase()} — +${data.crypto_earned}₡`,
              data.status === 'completed' ? 'success' : 'danger',
            )
            break
          }
          case 'world_event': {
            const data = event.data as { title: string; description: string }
            addActivity({ type: 'world_event', message: `[WORLD EVENT] ${data.title}`, level: 'warning' })
            addNotification(`[WORLD EVENT] ${data.title}`, 'warning', 10000)
            break
          }
          case 'faction_contact': {
            const data = event.data as { faction_key: string; message: string }
            addActivity({ type: 'faction', message: `[CONTACT] ${data.faction_key}: ${data.message.slice(0, 60)}...`, level: 'info' })
            addNotification(`Incoming contact from ${data.faction_key.toUpperCase()}`, 'info', 8000)
            break
          }
          default:
            break
        }
      },
    }),
    {
      name: 'ghost-protocol-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({ token: s.token, playerId: s.playerId, handle: s.handle, isScanlines: s.isScanlines }),
    }
  )
)
