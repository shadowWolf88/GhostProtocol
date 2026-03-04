import { useGameStore } from '../../store/gameStore'
import { clsx } from 'clsx'

const LEVEL_STYLES = {
  info: 'border-terminal-green text-terminal-green bg-black/80',
  success: 'border-terminal-green text-terminal-green bg-black/80',
  warning: 'border-terminal-amber text-terminal-amber bg-black/80',
  danger: 'border-terminal-red text-terminal-red bg-black/80',
}

export function NotificationBanner() {
  const notifications = useGameStore((s) => s.notifications)
  const dismiss = useGameStore((s) => s.dismissNotification)

  if (!notifications.length) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
      {notifications.slice(0, 4).map((n) => (
        <div
          key={n.id}
          className={clsx(
            'border px-4 py-2 text-xs font-mono animate-slide-up pointer-events-auto',
            LEVEL_STYLES[n.level as keyof typeof LEVEL_STYLES] ?? LEVEL_STYLES.info
          )}
          onClick={() => dismiss(n.id)}
          style={{ cursor: 'pointer' }}
        >
          <span className="opacity-50 mr-2">▶</span>
          {n.message}
        </div>
      ))}
    </div>
  )
}
