import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi } from '../services/api'
import { useGameStore } from '../store/gameStore'

const GLITCH_CHARS = '!@#$%^&*<>?/\\|~`'

function GlitchText({ text }: { text: string }) {
  const [display, setDisplay] = useState(text)
  useEffect(() => {
    let iterations = 0
    const interval = setInterval(() => {
      setDisplay(
        text.split('').map((char, i) =>
          i < iterations ? char : GLITCH_CHARS[Math.floor(Math.random() * GLITCH_CHARS.length)]
        ).join('')
      )
      if (iterations >= text.length) clearInterval(interval)
      iterations += 0.5
    }, 40)
    return () => clearInterval(interval)
  }, [text])
  return <span>{display}</span>
}

export function LoginPage() {
  const [handle, setHandle] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const setAuth = useGameStore((s) => s.setAuth)
  const token = useGameStore((s) => s.token)
  const navigate = useNavigate()

  useEffect(() => {
    if (token) navigate('/game', { replace: true })
  }, [token, navigate])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!handle || !password) return
    setError('')
    setIsLoading(true)
    try {
      const result = await authApi.login(handle, password)
      setAuth(result.access_token, result.player_id, result.handle)
      navigate('/game', { replace: true })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Authentication failed. Signal not recognized.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-terminal-bg flex flex-col items-center justify-center p-4 scanlines">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-terminal-green text-3xl font-bold tracking-[0.5em] text-glow-green mb-1">
            <GlitchText text="GHOST" />
          </h1>
          <h2 className="text-terminal-cyan text-xl tracking-[0.8em] mb-4">
            PROTOCOL
          </h2>
          <p className="text-terminal-muted text-xs tracking-widest">ANONYMOUS. UNTRACEABLE. INEVITABLE.</p>
        </div>

        {/* Login box */}
        <div className="border border-terminal-green p-6 shadow-terminal-green">
          <div className="text-terminal-muted text-xs mb-6 tracking-widest">
            ── AUTHENTICATION REQUIRED ──
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-terminal-muted text-xs block mb-1 tracking-wider">
                HANDLE
              </label>
              <div className="flex items-center border border-terminal-border focus-within:border-terminal-green transition-colors">
                <span className="text-terminal-green text-xs px-2">▶</span>
                <input
                  type="text"
                  value={handle}
                  onChange={(e) => setHandle(e.target.value)}
                  className="flex-1 bg-transparent text-terminal-green text-sm py-2 pr-2 focus:outline-none"
                  placeholder="your_handle"
                  autoComplete="username"
                  autoFocus
                  spellCheck={false}
                />
              </div>
            </div>

            <div>
              <label className="text-terminal-muted text-xs block mb-1 tracking-wider">
                PASSPHRASE
              </label>
              <div className="flex items-center border border-terminal-border focus-within:border-terminal-green transition-colors">
                <span className="text-terminal-green text-xs px-2">▶</span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="flex-1 bg-transparent text-terminal-green text-sm py-2 pr-2 focus:outline-none"
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
              </div>
            </div>

            {error && (
              <div className="border border-terminal-red text-terminal-red text-xs p-2 animate-fade-in">
                [ERROR] {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !handle || !password}
              className="w-full border border-terminal-green text-terminal-green text-sm py-2 hover:bg-terminal-green hover:text-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed tracking-widest"
            >
              {isLoading ? '[ AUTHENTICATING... ]' : '[ AUTHENTICATE ]'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <span className="text-terminal-muted text-xs">Not in the network? </span>
            <Link to="/register" className="text-terminal-cyan text-xs hover:text-terminal-green transition-colors">
              Create identity →
            </Link>
          </div>
        </div>

        <p className="text-center text-terminal-muted text-xs mt-6 tracking-wider">
          ALL CONNECTIONS MONITORED AND LOGGED
        </p>
      </div>
    </div>
  )
}
