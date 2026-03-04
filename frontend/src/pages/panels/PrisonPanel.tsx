import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { prisonApi } from '../../services/api'
import { useGameStore } from '../../store/gameStore'

type Activity = 'broker_info' | 'recruit_contact' | 'escape_plan' | 'legal_fight'

const ACTIVITIES: Array<{ key: Activity; label: string; cost: string; description: string }> = [
  { key: 'broker_info', label: 'SELL INTEL', cost: 'Free', description: 'Trade information for reputation. Needed for escape.' },
  { key: 'recruit_contact', label: 'RECRUIT', cost: '100₡', description: 'Find an ally on the inside.' },
  { key: 'escape_plan', label: 'ESCAPE', cost: 'Free', description: '20% chance. Requires 3 broker_info first.' },
  { key: 'legal_fight', label: 'LEGAL CHALLENGE', cost: '500₡', description: 'Reduce sentence by 20%. Max 3 times.' },
]

function formatHours(h: number): string {
  if (h < 1) return `${Math.round(h * 60)}m`
  return `${Math.round(h)}h`
}

export function PrisonPanel() {
  const qc = useQueryClient()
  const addNotification = useGameStore((s) => s.addNotification)

  const { data: status, isLoading } = useQuery({
    queryKey: ['prison'],
    queryFn: prisonApi.getStatus,
    refetchInterval: 30_000,
  })

  const activityMutation = useMutation({
    mutationFn: (activity: Activity) => prisonApi.performActivity(activity),
    onSuccess: (result) => {
      addNotification(result.message, 'success')
      qc.invalidateQueries({ queryKey: ['prison'] })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      addNotification(err?.response?.data?.detail ?? 'Activity failed', 'danger')
    },
  })

  if (isLoading) {
    return <div className="flex items-center justify-center h-full text-terminal-muted text-sm">Checking status...</div>
  }

  if (!status?.is_imprisoned) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-terminal-green text-sm font-bold mb-2">NOT INCARCERATED</div>
          <div className="text-terminal-muted text-xs">You are currently free.</div>
        </div>
      </div>
    )
  }

  const pct = Math.max(0, 100 - (status.time_remaining_hours / status.sentence_hours) * 100)

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="px-3 py-2 border-b border-terminal-border shrink-0">
        <span className="text-terminal-red text-xs font-bold tracking-widest">INCARCERATED</span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Sentence info */}
        <div className="border border-terminal-red p-3 space-y-2">
          <div className="text-terminal-red text-xs font-bold">{status.charge_description}</div>
          <div className="text-terminal-muted text-xs">
            Sentence: {status.sentence_hours}h |
            Remaining: {formatHours(status.time_remaining_hours)} |
            Release: {new Date(status.release_at).toLocaleString()}
          </div>
          {/* Progress bar */}
          <div className="w-full h-2 bg-terminal-border mt-2">
            <div className="h-full bg-terminal-amber transition-all" style={{ width: `${pct}%` }} />
          </div>
          <div className="text-terminal-muted text-xs">{Math.round(pct)}% served</div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="border border-terminal-border p-2">
            <div className="text-terminal-muted">Broker Info</div>
            <div className="text-terminal-green font-bold">{status.broker_info_count} / 3</div>
          </div>
          <div className="border border-terminal-border p-2">
            <div className="text-terminal-muted">Legal Fights</div>
            <div className="text-terminal-green font-bold">{status.legal_fight_count} / 3</div>
          </div>
        </div>

        {/* Activities */}
        <div>
          <div className="text-terminal-cyan text-xs font-bold mb-2 tracking-widest">ACTIVITIES</div>
          <div className="space-y-2">
            {ACTIVITIES.map(({ key, label, cost, description }) => (
              <div key={key} className="border border-terminal-border p-3">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-terminal-green text-xs font-bold">{label}</span>
                  <span className="text-terminal-amber text-xs">{cost}</span>
                </div>
                <p className="text-terminal-muted text-xs mb-2">{description}</p>
                <button
                  onClick={() => activityMutation.mutate(key)}
                  disabled={activityMutation.isPending}
                  className="text-xs border border-terminal-green text-terminal-green px-3 py-1 hover:bg-terminal-green hover:text-black transition-colors disabled:opacity-40"
                >
                  [EXECUTE]
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Activity log */}
        {status.activities.length > 0 && (
          <div>
            <div className="text-terminal-cyan text-xs font-bold mb-2 tracking-widest">ACTIVITY LOG</div>
            <div className="space-y-1">
              {status.activities.map((a) => (
                <div key={a.id} className="text-xs text-terminal-muted border-b border-terminal-border pb-1">
                  <span className="text-terminal-white">{a.activity_type}</span>
                  {a.outcome && <span className="ml-2 text-terminal-green">→ {a.outcome}</span>}
                  <span className="ml-2 text-terminal-muted">{new Date(a.created_at).toLocaleTimeString()}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
