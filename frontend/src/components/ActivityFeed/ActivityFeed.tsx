import { useGameStore } from '../../store/gameStore'
import { clsx } from 'clsx'
import type { ActivityEntry } from '../../types'

const LEVEL_STYLES: Record<ActivityEntry['level'], string> = {
  info: 'text-terminal-muted',
  success: 'text-terminal-green',
  warning: 'text-terminal-amber',
  danger: 'text-terminal-red',
}

const TYPE_PREFIX: Record<ActivityEntry['type'], string> = {
  operation: 'OP',
  heat: 'HT',
  economy: 'EC',
  faction: 'FC',
  system: 'SY',
  world_event: 'WE',
  prison: 'PR',
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function ActivityFeed() {
  const feed = useGameStore((s) => s.feed)
  const clearFeed = useGameStore((s) => s.clearFeed)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-terminal-border shrink-0">
        <span className="text-terminal-cyan text-xs font-bold tracking-widest">ACTIVITY FEED</span>
        <button
          onClick={clearFeed}
          className="text-terminal-muted text-xs hover:text-terminal-red transition-colors"
        >
          [CLEAR]
        </button>
      </div>

      {/* Feed entries */}
      <div className="flex-1 overflow-y-auto p-2 space-y-px">
        {feed.length === 0 && (
          <div className="text-terminal-muted text-xs text-center mt-8">
            — No activity —
          </div>
        )}
        {feed.map((entry) => (
          <div
            key={entry.id}
            className="flex gap-2 text-xs font-mono animate-fade-in py-0.5"
          >
            <span className="text-terminal-muted shrink-0 w-20">
              {formatTime(entry.timestamp)}
            </span>
            <span className="text-terminal-muted shrink-0 w-6">
              [{TYPE_PREFIX[entry.type]}]
            </span>
            <span className={clsx('flex-1 leading-snug', LEVEL_STYLES[entry.level])}>
              {entry.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
