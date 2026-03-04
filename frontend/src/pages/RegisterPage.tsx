import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi } from '../services/api'
import { useGameStore } from '../store/gameStore'

const REQUIREMENTS = [
  { label: 'Handle: 3–32 chars, letters/numbers/underscores/dashes', key: 'handle' },
  { label: 'Valid email address', key: 'email' },
  { label: 'Passphrase: 8+ characters', key: 'password' },
]

function validate(handle: string, email: string, password: string) {
  const errors: Record<string, string> = {}
  if (!/^[a-zA-Z0-9_-]{3,32}$/.test(handle)) {
    errors.handle = 'Handle must be 3–32 chars: letters, numbers, _ or -'
  }
  if (!email.includes('@') || !email.includes('.')) {
    errors.email = 'Invalid email address'
  }
  if (password.length < 8) {
    errors.password = 'Passphrase must be at least 8 characters'
  }
  return errors
}

export function RegisterPage() {
  const [handle, setHandle] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [submitError, setSubmitError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [step, setStep] = useState(0) // 0=form, 1=confirming, 2=success
  const setAuth = useGameStore((s) => s.setAuth)
  const token = useGameStore((s) => s.token)
  const navigate = useNavigate()

  useEffect(() => {
    if (token) navigate('/game', { replace: true })
  }, [token, navigate])

  function handleChange(field: 'handle' | 'email' | 'password', value: string) {
    if (field === 'handle') setHandle(value)
    if (field === 'email') setEmail(value)
    if (field === 'password') setPassword(value)
    // Clear field error on change
    setFieldErrors((prev) => ({ ...prev, [field]: '' }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const errors = validate(handle, email, password)
    if (Object.keys(errors).length) {
      setFieldErrors(errors)
      return
    }
    setSubmitError('')
    setIsLoading(true)
    setStep(1)
    try {
      const result = await authApi.register(handle, email, password)
      setStep(2)
      setTimeout(() => {
        setAuth(result.access_token, result.player_id, result.handle)
        navigate('/game', { replace: true })
      }, 1500)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setSubmitError(msg ?? 'Registration failed. Handle may already be claimed.')
      setStep(0)
    } finally {
      setIsLoading(false)
    }
  }

  if (step === 2) {
    return (
      <div className="min-h-screen bg-terminal-bg flex flex-col items-center justify-center">
        <div className="text-center animate-fade-in">
          <div className="text-terminal-green text-lg font-bold tracking-widest mb-2">IDENTITY CREATED</div>
          <div className="text-terminal-muted text-sm">Welcome to the network, {handle}.</div>
          <div className="text-terminal-muted text-xs mt-2">Establishing secure channel...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-terminal-bg flex flex-col items-center justify-center p-4 scanlines">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-terminal-green text-2xl font-bold tracking-[0.5em] text-glow-green mb-1">GHOST</h1>
          <h2 className="text-terminal-cyan text-lg tracking-[0.8em] mb-4">PROTOCOL</h2>
          <p className="text-terminal-muted text-xs tracking-widest">CREATE NEW IDENTITY</p>
        </div>

        <div className="border border-terminal-cyan p-6 shadow-[0_0_10px_rgba(0,255,255,0.2)]">
          <div className="text-terminal-muted text-xs mb-6 tracking-widest">
            ── IDENTITY REGISTRATION ──
          </div>

          {/* Requirement hints */}
          <div className="mb-5 space-y-1">
            {REQUIREMENTS.map(({ label, key }) => (
              <div key={key} className="flex items-center gap-2 text-xs">
                <span className={fieldErrors[key] ? 'text-terminal-red' : 'text-terminal-muted'}>
                  {fieldErrors[key] ? '✗' : '○'}
                </span>
                <span className={fieldErrors[key] ? 'text-terminal-red' : 'text-terminal-muted'}>
                  {fieldErrors[key] ?? label}
                </span>
              </div>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-terminal-muted text-xs block mb-1 tracking-wider">HANDLE</label>
              <div className={`flex items-center border focus-within:border-terminal-cyan transition-colors ${fieldErrors.handle ? 'border-terminal-red' : 'border-terminal-border'}`}>
                <span className="text-terminal-cyan text-xs px-2">▶</span>
                <input
                  type="text"
                  value={handle}
                  onChange={(e) => handleChange('handle', e.target.value)}
                  className="flex-1 bg-transparent text-terminal-green text-sm py-2 pr-2 focus:outline-none"
                  placeholder="ghost_handle"
                  autoFocus
                  spellCheck={false}
                />
              </div>
            </div>

            <div>
              <label className="text-terminal-muted text-xs block mb-1 tracking-wider">EMAIL</label>
              <div className={`flex items-center border focus-within:border-terminal-cyan transition-colors ${fieldErrors.email ? 'border-terminal-red' : 'border-terminal-border'}`}>
                <span className="text-terminal-cyan text-xs px-2">▶</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => handleChange('email', e.target.value)}
                  className="flex-1 bg-transparent text-terminal-green text-sm py-2 pr-2 focus:outline-none"
                  placeholder="anon@darkweb.onion"
                  autoComplete="email"
                />
              </div>
            </div>

            <div>
              <label className="text-terminal-muted text-xs block mb-1 tracking-wider">PASSPHRASE</label>
              <div className={`flex items-center border focus-within:border-terminal-cyan transition-colors ${fieldErrors.password ? 'border-terminal-red' : 'border-terminal-border'}`}>
                <span className="text-terminal-cyan text-xs px-2">▶</span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => handleChange('password', e.target.value)}
                  className="flex-1 bg-transparent text-terminal-green text-sm py-2 pr-2 focus:outline-none"
                  placeholder="••••••••"
                  autoComplete="new-password"
                />
              </div>
            </div>

            {submitError && (
              <div className="border border-terminal-red text-terminal-red text-xs p-2 animate-fade-in">
                [ERROR] {submitError}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full border border-terminal-cyan text-terminal-cyan text-sm py-2 hover:bg-terminal-cyan hover:text-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed tracking-widest"
            >
              {step === 1 ? '[ ESTABLISHING IDENTITY... ]' : '[ CREATE IDENTITY ]'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <span className="text-terminal-muted text-xs">Already in the network? </span>
            <Link to="/" className="text-terminal-green text-xs hover:text-terminal-cyan transition-colors">
              Authenticate →
            </Link>
          </div>
        </div>

        <p className="text-center text-terminal-muted text-xs mt-6 tracking-wider">
          BY REGISTERING YOU ACCEPT ALL RISKS
        </p>
      </div>
    </div>
  )
}
