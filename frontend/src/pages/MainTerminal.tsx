import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGameStore } from '../store/gameStore'
import { wsService } from '../services/WebSocketService'
import { onboardingApi } from '../services/api'

import { GhostTerminal } from '../components/Terminal/GhostTerminal'
import { TracePanel } from '../components/TraceGraph/TracePanel'
import { ActivityFeed } from '../components/ActivityFeed/ActivityFeed'
import { NotificationBanner } from '../components/Notifications/NotificationBanner'
import { HandlerMessage } from '../components/Onboarding/HandlerMessage'
import { StatusBar } from '../components/HUD/StatusBar'
import { SideNav } from '../components/HUD/SideNav'
import { SkillsPanel } from './panels/SkillsPanel'
import { MarketPanel } from './panels/MarketPanel'
import { FactionPanel } from './panels/FactionPanel'
import { PrisonPanel } from './panels/PrisonPanel'

export function MainTerminal() {
  const navigate = useNavigate()
  const token = useGameStore((s) => s.token)
  const playerId = useGameStore((s) => s.playerId)
  const activePanel = useGameStore((s) => s.activePanel)
  const isScanlines = useGameStore((s) => s.isScanlines)
  const setOnboarding = useGameStore((s) => s.setOnboarding)
  const onboarding = useGameStore((s) => s.onboarding)
  const [showHandler, setShowHandler] = useState(false)

  // Auth guard
  useEffect(() => {
    if (!token || !playerId) {
      navigate('/', { replace: true })
    }
  }, [token, playerId, navigate])

  // Connect WebSocket
  useEffect(() => {
    if (!token || !playerId) return
    wsService.connect(playerId, token)
    return () => {
      // Don't disconnect on unmount — keep alive during navigation
    }
  }, [token, playerId])

  // Load onboarding
  useEffect(() => {
    onboardingApi.getState()
      .then((state) => {
        setOnboarding(state)
        if (!state.is_complete && state.handler_message) {
          setShowHandler(true)
        }
      })
      .catch(() => { /* ignore */ })
  }, [setOnboarding])

  if (!token || !playerId) return null

  return (
    <div className={`flex flex-col h-screen w-screen bg-terminal-bg overflow-hidden ${isScanlines ? 'scanlines' : ''}`}>
      {/* Status bar */}
      <StatusBar />

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* Side nav */}
        <SideNav />

        {/* Main content area */}
        <div className="flex flex-1 min-w-0 min-h-0">
          {/* Left: Terminal (always mounted, shown/hidden) */}
          <div
            className="flex-1 min-w-0 min-h-0 border-r border-terminal-border"
            style={{ display: activePanel === 'terminal' ? 'flex' : 'none', flexDirection: 'column' }}
          >
            <GhostTerminal />
          </div>

          {/* Panels shown in main area when not terminal */}
          {activePanel !== 'terminal' && (
            <div className="flex-1 min-w-0 min-h-0 border-r border-terminal-border flex flex-col">
              {activePanel === 'trace' && <TracePanel />}
              {activePanel === 'skills' && <SkillsPanel />}
              {activePanel === 'market' && <MarketPanel />}
              {activePanel === 'faction' && <FactionPanel />}
              {activePanel === 'prison' && <PrisonPanel />}
            </div>
          )}

          {/* Right: Activity feed — always visible */}
          <div className="w-72 shrink-0 min-h-0 flex flex-col">
            <ActivityFeed />
          </div>
        </div>
      </div>

      {/* Notifications */}
      <NotificationBanner />

      {/* Onboarding handler modal */}
      {showHandler && onboarding && !onboarding.is_complete && (
        <HandlerMessage onDismiss={() => setShowHandler(false)} />
      )}
    </div>
  )
}
