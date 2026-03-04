import { useState, useEffect, useRef } from 'react'
import { useGameStore } from '../../store/gameStore'
import { onboardingApi } from '../../services/api'

interface Props {
  onDismiss: () => void
}

export function HandlerMessage({ onDismiss }: Props) {
  const onboarding = useGameStore((s) => s.onboarding)
  const setOnboarding = useGameStore((s) => s.setOnboarding)
  const [displayedText, setDisplayedText] = useState('')
  const [isTyping, setIsTyping] = useState(true)
  const [hint, setHint] = useState('')
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fullText = onboarding?.handler_message ?? ''

  useEffect(() => {
    if (!fullText) return
    setDisplayedText('')
    setIsTyping(true)
    let i = 0
    intervalRef.current = setInterval(() => {
      if (i < fullText.length) {
        setDisplayedText(fullText.slice(0, i + 1))
        i++
      } else {
        setIsTyping(false)
        if (intervalRef.current) clearInterval(intervalRef.current)
      }
    }, 18)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [fullText])

  useEffect(() => {
    if (!onboarding?.current_step) return
    onboardingApi.getHandlerMessage(onboarding.current_step)
      .then((r) => setHint(r.hint))
      .catch(() => { /* no hint */ })
  }, [onboarding?.current_step])

  // Refresh onboarding state
  useEffect(() => {
    onboardingApi.getState().then(setOnboarding).catch(() => { /* ignore */ })
  }, [setOnboarding])

  if (!onboarding || onboarding.is_complete) return null

  const progress = `${onboarding.completed_steps.length} / 5`

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/70">
      <div className="max-w-lg w-full mx-4 border border-terminal-green bg-terminal-bg p-6 shadow-terminal-green">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-terminal-green font-bold text-sm tracking-widest">[ PHANTOM ]</span>
            <span className="text-terminal-muted text-xs ml-3">Secure Handler</span>
          </div>
          <span className="text-terminal-muted text-xs">STEP {progress}</span>
        </div>

        {/* Message body */}
        <div className="text-terminal-white text-sm leading-relaxed min-h-24 mb-4 font-mono">
          {displayedText}
          {isTyping && <span className="terminal-cursor ml-0.5" />}
        </div>

        {/* Hint */}
        {hint && !isTyping && (
          <div className="border border-terminal-border p-2 mb-4 text-terminal-muted text-xs">
            <span className="text-terminal-amber mr-2">HINT:</span>{hint}
          </div>
        )}

        {/* Footer */}
        {!isTyping && (
          <div className="flex items-center justify-between">
            <button
              onClick={() => {
                setDisplayedText(fullText)
                setIsTyping(false)
                if (intervalRef.current) clearInterval(intervalRef.current)
              }}
              className="text-terminal-muted text-xs hover:text-terminal-green transition-colors"
            >
              [SKIP]
            </button>
            <button
              onClick={onDismiss}
              className="border border-terminal-green text-terminal-green text-xs px-4 py-1 hover:bg-terminal-green hover:text-black transition-colors"
            >
              [ACKNOWLEDGE]
            </button>
          </div>
        )}
        {isTyping && (
          <button
            onClick={() => {
              setDisplayedText(fullText)
              setIsTyping(false)
              if (intervalRef.current) clearInterval(intervalRef.current)
            }}
            className="text-terminal-muted text-xs hover:text-terminal-green transition-colors"
          >
            [SKIP TRANSMISSION]
          </button>
        )}
      </div>
    </div>
  )
}
