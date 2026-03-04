import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { useGameStore } from '../../store/gameStore'
import { heatApi, playerApi } from '../../services/api'

function EnergyBar({ energy, max }: { energy: number; max: number }) {
  const pct = Math.round((energy / max) * 100)
  const color = pct > 50 ? 'bg-terminal-green' : pct > 20 ? 'bg-terminal-amber' : 'bg-terminal-red'
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-terminal-muted text-xs w-12">ENERGY</span>
      <div className="w-20 h-2 bg-terminal-border relative">
        <div className={clsx('h-full transition-all', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-terminal-muted text-xs">{energy}/{max}</span>
    </div>
  )
}

function HeatIndicator({ total, tier }: { total: number; tier: number }) {
  const color = tier >= 4 ? 'text-terminal-red animate-pulse' : tier >= 3 ? 'text-terminal-amber' : 'text-terminal-green'
  const label = ['', 'OFF RADAR', 'PERSONS OF INTEREST', 'ACTIVE INQUIRY', 'MANHUNT', 'ARREST PROBABLE'][tier] ?? '?'
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-terminal-muted text-xs">HEAT</span>
      <span className={clsx('text-xs font-bold', color)}>{Math.round(total)}</span>
      <span className={clsx('text-xs', color)}>[{label}]</span>
    </div>
  )
}

export function StatusBar() {
  const handle = useGameStore((s) => s.handle)
  const wsConnected = useGameStore((s) => s.wsConnected)
  const setProfile = useGameStore((s) => s.setProfile)
  const setHeatStatus = useGameStore((s) => s.setHeatStatus)
  const profile = useGameStore((s) => s.profile)
  const heatStatus = useGameStore((s) => s.heatStatus)

  const { data: freshProfile } = useQuery({
    queryKey: ['playerProfile'],
    queryFn: playerApi.getProfile,
    refetchInterval: 60_000,
  })

  const { data: freshHeat } = useQuery({
    queryKey: ['heatStatus'],
    queryFn: heatApi.getStatus,
    refetchInterval: 30_000,
  })

  useEffect(() => { if (freshProfile) setProfile(freshProfile) }, [freshProfile, setProfile])
  useEffect(() => { if (freshHeat) setHeatStatus(freshHeat) }, [freshHeat, setHeatStatus])

  const stats = profile?.stats
  const psych = profile?.psych

  return (
    <div className="h-10 border-b border-terminal-border bg-terminal-surface flex items-center px-4 gap-6 shrink-0 overflow-x-auto">
      {/* Handle */}
      <span className="text-terminal-green text-xs font-bold tracking-widest shrink-0">
        {handle?.toUpperCase() ?? 'GHOST'}
      </span>

      <span className="text-terminal-border">|</span>

      {/* Energy */}
      {stats && (
        <EnergyBar energy={stats.energy} max={stats.max_energy} />
      )}

      <span className="text-terminal-border">|</span>

      {/* Heat */}
      {heatStatus && (
        <HeatIndicator total={heatStatus.total_heat} tier={heatStatus.threat_tier} />
      )}

      <span className="text-terminal-border">|</span>

      {/* Crypto */}
      {stats && (
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-terminal-muted text-xs">₡</span>
          <span className="text-terminal-green text-xs">{stats.crypto.toLocaleString()}</span>
        </div>
      )}

      {/* Focus */}
      {psych && (
        <>
          <span className="text-terminal-border">|</span>
          <div className="flex items-center gap-1.5 shrink-0">
            <span className="text-terminal-muted text-xs">FOCUS</span>
            <span className={clsx('text-xs', psych.focus > 60 ? 'text-terminal-green' : psych.focus > 30 ? 'text-terminal-amber' : 'text-terminal-red')}>
              {Math.round(psych.focus)}%
            </span>
          </div>
        </>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* WS status */}
      <div className="flex items-center gap-1.5 shrink-0">
        <div className={clsx('w-1.5 h-1.5 rounded-full', wsConnected ? 'bg-terminal-green animate-pulse' : 'bg-terminal-red')} />
        <span className="text-terminal-muted text-xs">{wsConnected ? 'LIVE' : 'OFFLINE'}</span>
      </div>
    </div>
  )
}
