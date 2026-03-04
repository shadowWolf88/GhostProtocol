import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { skillApi } from '../../services/api'

export function SkillsPanel() {
  const { data, isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: skillApi.getTrees,
    refetchInterval: 60_000,
  })
  const [selected, setSelected] = useState<string | null>(null)

  if (isLoading) return <div className="flex items-center justify-center h-full text-terminal-muted text-sm">Loading skill trees...</div>
  if (!data) return null

  const trees = Object.entries(data.trees)
  const activeFull = selected ? data.trees[selected] : null

  return (
    <div className="flex h-full min-h-0">
      {/* Tree list */}
      <div className="w-40 border-r border-terminal-border flex flex-col shrink-0">
        <div className="px-3 py-2 border-b border-terminal-border text-terminal-cyan text-xs font-bold tracking-widest">
          SKILL TREES
        </div>
        <div className="flex-1 overflow-y-auto">
          {trees.map(([key, tree]) => (
            <button
              key={key}
              onClick={() => setSelected(key)}
              className={clsx(
                'w-full text-left px-3 py-2 text-xs border-b border-terminal-border transition-colors',
                selected === key ? 'bg-terminal-green/10 text-terminal-green' : 'text-terminal-muted hover:text-terminal-green'
              )}
            >
              <div className="font-bold">{tree.tree_name}</div>
              <div className="text-terminal-muted text-xs">L{tree.current_level}</div>
            </button>
          ))}
        </div>
        <div className="px-3 py-2 border-t border-terminal-border text-terminal-muted text-xs">
          Total: {data.total_level}
        </div>
      </div>

      {/* Tree detail */}
      <div className="flex-1 overflow-y-auto p-4">
        {!activeFull ? (
          <div className="text-terminal-muted text-sm text-center mt-16">Select a skill tree</div>
        ) : (
          <div className="space-y-4">
            <div>
              <h2 className="text-terminal-green font-bold text-sm tracking-widest">{activeFull.tree_name}</h2>
              <p className="text-terminal-muted text-xs mt-1">{activeFull.description}</p>
            </div>

            {/* XP bar */}
            <div>
              <div className="flex justify-between text-xs text-terminal-muted mb-1">
                <span>Level {activeFull.current_level}</span>
                <span>{activeFull.current_xp.toLocaleString()} / {activeFull.xp_to_next.toLocaleString()} XP</span>
              </div>
              <div className="w-full h-2 bg-terminal-border">
                <div
                  className="h-full bg-terminal-green transition-all"
                  style={{ width: `${Math.min(100, (activeFull.current_xp / activeFull.xp_to_next) * 100)}%` }}
                />
              </div>
            </div>

            {/* Abilities by tier */}
            {[1, 2, 3, 4, 5].map((tier) => {
              const tierAbilities = activeFull.abilities.filter((a) => a.tier === tier)
              if (!tierAbilities.length) return null
              return (
                <div key={tier}>
                  <div className="text-terminal-muted text-xs mb-2">— TIER {tier} —</div>
                  <div className="space-y-2">
                    {tierAbilities.map((ab) => (
                      <div
                        key={ab.id}
                        className={clsx(
                          'border p-3',
                          ab.unlocked ? 'border-terminal-green bg-terminal-green/5' : 'border-terminal-border opacity-50'
                        )}
                      >
                        <div className="flex justify-between items-start">
                          <span className={clsx('text-xs font-bold', ab.unlocked ? 'text-terminal-green' : 'text-terminal-muted')}>
                            {ab.name}
                          </span>
                          <span className="text-terminal-amber text-xs">+{ab.operation_bonus}%</span>
                        </div>
                        <p className="text-terminal-muted text-xs mt-1">{ab.description}</p>
                        {!ab.unlocked && (
                          <p className="text-terminal-muted text-xs mt-1 opacity-60">Requires Level {ab.level_required}</p>
                        )}
                        {ab.passive && (
                          <span className="text-terminal-cyan text-xs">[PASSIVE]</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
