import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { economyApi } from '../../services/api'
import { useGameStore } from '../../store/gameStore'

export function MarketPanel() {
  const qc = useQueryClient()
  const addNotification = useGameStore((s) => s.addNotification)
  const { data: listings, isLoading } = useQuery({
    queryKey: ['market'],
    queryFn: economyApi.getMarket,
    refetchInterval: 60_000,
  })
  const { data: wallet } = useQuery({
    queryKey: ['wallet'],
    queryFn: economyApi.getWallet,
    refetchInterval: 30_000,
  })

  const [launderAmount, setLaunderAmount] = useState('')
  const [launderPreview, setLaunderPreview] = useState<Awaited<ReturnType<typeof economyApi.launderPreview>> | null>(null)

  const purchaseMutation = useMutation({
    mutationFn: (id: string) => economyApi.purchase(id),
    onSuccess: (result) => {
      addNotification(`Purchased: ${result.item_name}`, 'success')
      qc.invalidateQueries({ queryKey: ['wallet'] })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      addNotification(err?.response?.data?.detail ?? 'Purchase failed', 'danger')
    },
  })

  const launderMutation = useMutation({
    mutationFn: (amount: number) => economyApi.launder(amount),
    onSuccess: (result) => {
      addNotification(`Laundered +${result.privacy_coin_gained}Ψ`, 'success')
      setLaunderAmount('')
      setLaunderPreview(null)
      qc.invalidateQueries({ queryKey: ['wallet'] })
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      addNotification(err?.response?.data?.detail ?? 'Laundering failed', 'danger')
    },
  })

  async function handleLaunderPreview() {
    const amount = parseInt(launderAmount)
    if (isNaN(amount) || amount <= 0) return
    try {
      const preview = await economyApi.launderPreview(amount)
      setLaunderPreview(preview)
    } catch { /* ignore */ }
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      <div className="px-3 py-2 border-b border-terminal-border text-terminal-cyan text-xs font-bold tracking-widest shrink-0 flex justify-between">
        <span>BLACK MARKET</span>
        {wallet && (
          <span className="text-terminal-green">{wallet.crypto.toLocaleString()}₡ available</span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {isLoading && <div className="text-terminal-muted text-xs">Loading market...</div>}

        {listings?.map((l) => (
          <div key={l.id} className="border border-terminal-border p-3 hover:border-terminal-green transition-colors">
            <div className="flex justify-between items-start mb-1">
              <span className="text-terminal-green text-xs font-bold">{l.item_name}</span>
              <span className="text-terminal-amber text-xs">{l.price_crypto.toLocaleString()}₡</span>
            </div>
            <p className="text-terminal-muted text-xs mb-2">{l.description}</p>
            <button
              onClick={() => purchaseMutation.mutate(l.id)}
              disabled={purchaseMutation.isPending || (wallet?.crypto ?? 0) < l.price_crypto}
              className="text-xs border border-terminal-green text-terminal-green px-3 py-1 hover:bg-terminal-green hover:text-black transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              [BUY]
            </button>
          </div>
        ))}

        {/* Laundering section */}
        <div className="border border-terminal-border mt-4 p-3">
          <div className="text-terminal-cyan text-xs font-bold mb-3 tracking-widest">CRYPTO LAUNDERING</div>
          <div className="flex gap-2 mb-2">
            <input
              type="number"
              value={launderAmount}
              onChange={(e) => { setLaunderAmount(e.target.value); setLaunderPreview(null) }}
              placeholder="Amount (₡)"
              className="flex-1 bg-transparent border border-terminal-border text-terminal-green text-xs px-2 py-1 focus:border-terminal-green focus:outline-none"
            />
            <button
              onClick={handleLaunderPreview}
              className="text-xs border border-terminal-muted text-terminal-muted px-3 py-1 hover:border-terminal-amber hover:text-terminal-amber transition-colors"
            >
              PREVIEW
            </button>
            <button
              onClick={() => launderMutation.mutate(parseInt(launderAmount))}
              disabled={launderMutation.isPending || !launderAmount}
              className="text-xs border border-terminal-amber text-terminal-amber px-3 py-1 hover:bg-terminal-amber hover:text-black transition-colors disabled:opacity-40"
            >
              LAUNDER
            </button>
          </div>
          {launderPreview && (
            <div className="text-xs space-y-1 mt-2">
              {launderPreview.steps.map((s) => (
                <div key={s.step} className="text-terminal-muted">
                  Step {s.step}: {s.amount_in.toLocaleString()}₡ → -{s.fee.toLocaleString()}₡ fee → {s.amount_out.toLocaleString()}₡
                </div>
              ))}
              <div className="text-terminal-amber">Total fees: {launderPreview.total_fees.toLocaleString()}₡</div>
              <div className="text-terminal-green">Output: {launderPreview.final_privacy_coin.toLocaleString()}Ψ</div>
              <div className="text-terminal-red">+{launderPreview.intelligence_heat_added} intelligence heat</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
