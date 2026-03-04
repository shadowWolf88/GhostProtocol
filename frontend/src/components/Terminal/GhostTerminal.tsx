import { useEffect, useRef, useCallback, useState } from 'react'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'
import { executeCommand, getCompletions, type OutputLine } from '../../services/CommandRouter'
import { useGameStore } from '../../store/gameStore'

const PROMPT = '\r\n\x1b[32m▌\x1b[0m \x1b[36m'
const PROMPT_END = '\x1b[0m \x1b[32m>\x1b[0m '

const BOOT_SEQUENCE = [
  '\x1b[32m',
  '  ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗',
  '  ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝',
  '  ██║  ███╗███████║██║   ██║███████╗   ██║   ',
  '  ██║   ██║██╔══██║██║   ██║╚════██║   ██║   ',
  '  ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   ',
  '   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ',
  '\x1b[0m',
  '\x1b[36m  ██████╗ ██████╗  ██████╗ ████████╗ ██████╗  ██████╗ ██████╗ ██╗     \x1b[0m',
  '\x1b[36m  ██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔═══██╗██╔════╝██╔═══██╗██║     \x1b[0m',
  '\x1b[36m  ██████╔╝██████╔╝██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║     \x1b[0m',
  '\x1b[36m  ██╔═══╝ ██╔══██╗██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║     \x1b[0m',
  '\x1b[36m  ██║     ██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚██████╗╚██████╔╝███████╗\x1b[0m',
  '\x1b[36m  ╚═╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝\x1b[0m',
  '',
  '\x1b[32m  ─────────────────────────────────────────────────────────────────────\x1b[0m',
  '\x1b[33m  ANONYMOUS. UNTRACEABLE. INEVITABLE.\x1b[0m',
  '\x1b[32m  ─────────────────────────────────────────────────────────────────────\x1b[0m',
  '',
  '\x1b[90m  Secure channel established.\x1b[0m',
  '\x1b[90m  Type \x1b[32mhelp\x1b[90m for available commands.\x1b[0m',
  '',
]

function colorize(line: OutputLine): string {
  const classToAnsi: Record<string, string> = {
    'text-terminal-green': '\x1b[32m',
    'text-terminal-red': '\x1b[31m',
    'text-terminal-amber': '\x1b[33m',
    'text-terminal-cyan': '\x1b[36m',
    'text-terminal-white': '\x1b[97m',
    'text-terminal-muted': '\x1b[90m',
    'font-bold': '\x1b[1m',
  }
  let prefix = ''
  if (line.className) {
    for (const [cls, ansi] of Object.entries(classToAnsi)) {
      if (line.className.includes(cls)) prefix += ansi
    }
  }
  return `${prefix}  ${line.text}\x1b[0m`
}

interface GhostTerminalProps {
  onClear?: () => void
}

export function GhostTerminal({ onClear }: GhostTerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const termRef = useRef<Terminal | null>(null)
  const fitAddonRef = useRef<FitAddon | null>(null)
  const inputRef = useRef('')
  const historyRef = useRef<string[]>([])
  const historyIndexRef = useRef(-1)
  const isProcessingRef = useRef(false)
  const [isBooted, setIsBooted] = useState(false)
  const handle = useGameStore((s) => s.handle)

  const writePrompt = useCallback(() => {
    const term = termRef.current
    if (!term) return
    term.write(`${PROMPT}${handle ?? 'ghost'}${PROMPT_END}`)
    inputRef.current = ''
    historyIndexRef.current = -1
  }, [handle])

  const runCommand = useCallback(async (input: string) => {
    const term = termRef.current
    if (!term || isProcessingRef.current) return
    isProcessingRef.current = true

    const trimmed = input.trim()
    term.write('\r\n')

    if (trimmed === 'clear') {
      term.clear()
      onClear?.()
      writePrompt()
      isProcessingRef.current = false
      return
    }

    if (trimmed) {
      historyRef.current.unshift(trimmed)
      if (historyRef.current.length > 100) historyRef.current.pop()
    }

    if (trimmed) {
      const lines = await executeCommand(trimmed)
      for (const line of lines) {
        term.writeln(colorize(line))
      }
    }

    writePrompt()
    isProcessingRef.current = false
  }, [writePrompt, onClear])

  useEffect(() => {
    if (!containerRef.current) return

    const term = new Terminal({
      cursorBlink: true,
      cursorStyle: 'block',
      fontFamily: '"Fira Code", "JetBrains Mono", monospace',
      fontSize: 13,
      lineHeight: 1.5,
      theme: {
        background: '#0a0a0a',
        foreground: '#00ff41',
        cursor: '#00ff41',
        cursorAccent: '#0a0a0a',
        selectionBackground: 'rgba(0,255,65,0.2)',
        black: '#0a0a0a',
        red: '#ff2020',
        green: '#00ff41',
        yellow: '#ffb000',
        blue: '#0088ff',
        magenta: '#9933ff',
        cyan: '#00ffff',
        white: '#e0e0e0',
        brightBlack: '#666666',
        brightGreen: '#39ff14',
        brightYellow: '#ffcc00',
        brightCyan: '#00ffff',
        brightWhite: '#ffffff',
      },
      scrollback: 2000,
      convertEol: true,
      allowProposedApi: true,
    })

    const fitAddon = new FitAddon()
    const webLinksAddon = new WebLinksAddon()
    term.loadAddon(fitAddon)
    term.loadAddon(webLinksAddon)
    term.open(containerRef.current)
    fitAddon.fit()

    termRef.current = term
    fitAddonRef.current = fitAddon

    // Boot sequence
    let lineIndex = 0
    const bootInterval = setInterval(() => {
      if (lineIndex < BOOT_SEQUENCE.length) {
        term.writeln(BOOT_SEQUENCE[lineIndex])
        lineIndex++
      } else {
        clearInterval(bootInterval)
        setIsBooted(true)
        writePrompt()
      }
    }, 40)

    // Key handler
    term.onKey(({ key, domEvent }) => {
      const ev = domEvent
      const printable = !ev.altKey && !ev.ctrlKey && !ev.metaKey

      if (ev.key === 'Enter') {
        const currentInput = inputRef.current
        runCommand(currentInput)
      } else if (ev.key === 'Backspace') {
        if (inputRef.current.length > 0) {
          inputRef.current = inputRef.current.slice(0, -1)
          term.write('\b \b')
        }
      } else if (ev.key === 'ArrowUp') {
        const idx = historyIndexRef.current + 1
        if (idx < historyRef.current.length) {
          historyIndexRef.current = idx
          const prev = historyRef.current[idx]
          // Clear current line
          term.write('\b \b'.repeat(inputRef.current.length))
          inputRef.current = prev
          term.write(prev)
        }
      } else if (ev.key === 'ArrowDown') {
        const idx = historyIndexRef.current - 1
        term.write('\b \b'.repeat(inputRef.current.length))
        if (idx >= 0) {
          historyIndexRef.current = idx
          const next = historyRef.current[idx]
          inputRef.current = next
          term.write(next)
        } else {
          historyIndexRef.current = -1
          inputRef.current = ''
        }
      } else if (ev.key === 'Tab') {
        ev.preventDefault()
        const parts = inputRef.current.split(' ')
        const partial = parts[parts.length - 1]
        const completions = getCompletions(partial)
        if (completions.length === 1) {
          const completed = completions[0]
          const toAdd = completed.slice(partial.length)
          inputRef.current += toAdd
          term.write(toAdd)
        } else if (completions.length > 1) {
          term.writeln('')
          term.writeln('\x1b[90m  ' + completions.join('  ') + '\x1b[0m')
          writePrompt()
          term.write(inputRef.current)
        }
      } else if (ev.ctrlKey && ev.key === 'c') {
        inputRef.current = ''
        term.writeln('^C')
        writePrompt()
      } else if (ev.ctrlKey && ev.key === 'l') {
        term.clear()
        writePrompt()
      } else if (printable) {
        inputRef.current += key
        term.write(key)
      }
    })

    // Resize observer
    const resizeObserver = new ResizeObserver(() => {
      try { fitAddon.fit() } catch { /* ignore */ }
    })
    resizeObserver.observe(containerRef.current)

    return () => {
      clearInterval(bootInterval)
      resizeObserver.disconnect()
      term.dispose()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Re-write prompt when handle changes after boot
  useEffect(() => {
    if (isBooted) {
      // Just update future prompts, no need to redraw current
    }
  }, [handle, isBooted])

  return (
    <div
      ref={containerRef}
      className="w-full h-full bg-terminal-bg"
      style={{ minHeight: 0 }}
    />
  )
}
