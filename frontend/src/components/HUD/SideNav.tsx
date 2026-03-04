import { clsx } from 'clsx'
import { useGameStore } from '../../store/gameStore'

type Panel = 'terminal' | 'trace' | 'skills' | 'market' | 'faction' | 'prison'

const NAV_ITEMS: Array<{ id: Panel; label: string; short: string }> = [
  { id: 'terminal', label: 'TERMINAL', short: 'TRM' },
  { id: 'trace', label: 'TRACE', short: 'TRC' },
  { id: 'skills', label: 'SKILLS', short: 'SKL' },
  { id: 'market', label: 'MARKET', short: 'MKT' },
  { id: 'faction', label: 'FACTIONS', short: 'FCT' },
  { id: 'prison', label: 'PRISON', short: 'PRS' },
]

export function SideNav() {
  const activePanel = useGameStore((s) => s.activePanel)
  const setActivePanel = useGameStore((s) => s.setActivePanel)

  return (
    <div className="w-12 border-r border-terminal-border bg-terminal-surface flex flex-col items-center py-4 gap-1 shrink-0">
      {NAV_ITEMS.map(({ id, label, short }) => (
        <button
          key={id}
          title={label}
          onClick={() => setActivePanel(id)}
          className={clsx(
            'w-9 h-9 text-xs font-mono transition-all border',
            activePanel === id
              ? 'border-terminal-green text-terminal-green bg-terminal-green/10'
              : 'border-transparent text-terminal-muted hover:text-terminal-green hover:border-terminal-border'
          )}
        >
          {short}
        </button>
      ))}
    </div>
  )
}
