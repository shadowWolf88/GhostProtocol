import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { factionApi } from '../../services/api'
import { useGameStore } from '../../store/gameStore'

const FACTION_COLORS: Record<string, string> = {
  collective: '#00ffff',
  black_array: '#ff2020',
  sovereign_shield: '#9933ff',
  signal_zero: '#ffb000',
  freenode: '#00ff41',
}

export function FactionPanel() {
  const addNotification = useGameStore((s) => s.addNotification)
  const { data: relations, isLoading } = useQuery({
    queryKey: ['factions'],
    queryFn: factionApi.getRelations,
    refetchInterval: 60_000,
  })
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const { data: intro } = useQuery({
    queryKey: ['factionIntro', selectedKey],
    queryFn: () => factionApi.getIntroMessage(selectedKey!),
    enabled: !!selectedKey,
  })

  const joinMutation = useMutation({
    mutationFn: (key: string) => factionApi.joinFaction(key),
    onSuccess: (result) => {
      addNotification(result.message, 'success')
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      addNotification(err?.response?.data?.detail ?? 'Join failed', 'danger')
    },
  })

  return (
    <div className="flex h-full min-h-0">
      {/* Faction list */}
      <div className="w-44 border-r border-terminal-border flex flex-col shrink-0">
        <div className="px-3 py-2 border-b border-terminal-border text-terminal-cyan text-xs font-bold tracking-widest">
          FACTIONS
        </div>
        <div className="flex-1 overflow-y-auto">
          {isLoading && <div className="text-terminal-muted text-xs p-3">Loading...</div>}
          {relations?.map((r) => {
            const color = FACTION_COLORS[r.faction_key] ?? '#666'
            return (
              <button
                key={r.faction_key}
                onClick={() => setSelectedKey(r.faction_key)}
                className={clsx(
                  'w-full text-left px-3 py-3 border-b border-terminal-border transition-colors',
                  selectedKey === r.faction_key ? 'bg-white/5' : 'hover:bg-white/5'
                )}
              >
                <div className="text-xs font-bold" style={{ color }}>
                  {r.faction_key.replace('_', ' ').toUpperCase()}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="text-terminal-muted text-xs">{r.standing} rep</div>
                  {r.is_member && <span className="text-xs" style={{ color }}>[MEMBER]</span>}
                  {!r.is_member && r.contact_eligible && (
                    <span className="text-terminal-amber text-xs">[ELIGIBLE]</span>
                  )}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Detail pane */}
      <div className="flex-1 overflow-y-auto p-4">
        {!selectedKey ? (
          <div className="text-terminal-muted text-sm text-center mt-16">Select a faction</div>
        ) : intro ? (
          <div className="space-y-4">
            <div>
              <h2 className="font-bold text-sm tracking-widest" style={{ color: FACTION_COLORS[selectedKey] ?? '#666' }}>
                [{intro.npc_name}]
              </h2>
              <p className="text-terminal-muted text-xs mt-1">{selectedKey.replace('_', ' ').toUpperCase()}</p>
            </div>

            <div className="border border-terminal-border p-3">
              <p className="text-terminal-white text-xs leading-relaxed whitespace-pre-wrap">{intro.message}</p>
            </div>

            <div className="text-terminal-muted text-xs">
              <div className="mb-2 text-terminal-amber">REQUIREMENTS:</div>
              {Object.entries(intro.requirements).map(([k, v]) => (
                <div key={k}>{k}: {String(v)}</div>
              ))}
            </div>

            {relations?.find((r) => r.faction_key === selectedKey)?.contact_eligible &&
              !relations?.find((r) => r.faction_key === selectedKey)?.is_member && (
              <button
                onClick={() => joinMutation.mutate(selectedKey)}
                disabled={joinMutation.isPending}
                className="border text-xs px-4 py-2 transition-colors hover:text-black disabled:opacity-40"
                style={{
                  borderColor: FACTION_COLORS[selectedKey] ?? '#666',
                  color: FACTION_COLORS[selectedKey] ?? '#666',
                }}
              >
                [INITIATE JOIN]
              </button>
            )}
          </div>
        ) : (
          <div className="text-terminal-muted text-xs">Contact not yet available or below threshold.</div>
        )}
      </div>
    </div>
  )
}
