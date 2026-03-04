import { useGameStore } from '../store/gameStore'
import type { WSEvent } from '../types'

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 2000
  private pingInterval: ReturnType<typeof setInterval> | null = null
  private playerId: string | null = null
  private token: string | null = null

  connect(playerId: string, token: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) return

    this.playerId = playerId
    this.token = token

    let wsBase: string
    if (import.meta.env.VITE_API_URL) {
      // Production: derive ws(s):// from the API URL
      wsBase = import.meta.env.VITE_API_URL.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:')
    } else {
      // Dev: use same host (proxied by vite)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsBase = `${protocol}//${window.location.host}`
    }
    const url = `${wsBase}/ws/${playerId}?token=${token}`

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      useGameStore.getState().setWSConnected(true)
      useGameStore.getState().addActivity({
        type: 'system',
        message: '[SYSTEM] Secure channel established.',
        level: 'success',
      })
      this.startPing()
    }

    this.ws.onmessage = (evt) => {
      try {
        const event = JSON.parse(evt.data) as WSEvent
        useGameStore.getState().handleWSEvent(event)
      } catch {
        // malformed message — ignore
      }
    }

    this.ws.onerror = () => {
      useGameStore.getState().setWSConnected(false)
    }

    this.ws.onclose = () => {
      this.stopPing()
      useGameStore.getState().setWSConnected(false)
      useGameStore.getState().addActivity({
        type: 'system',
        message: '[SYSTEM] Channel dropped. Reconnecting...',
        level: 'warning',
      })
      this.scheduleReconnect()
    }
  }

  disconnect(): void {
    this.stopPing()
    this.reconnectAttempts = this.maxReconnectAttempts // prevent auto-reconnect
    this.ws?.close()
    this.ws = null
    useGameStore.getState().setWSConnected(false)
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts || !this.playerId || !this.token) return
    this.reconnectAttempts++
    const delay = this.reconnectDelay * this.reconnectAttempts
    setTimeout(() => {
      if (this.playerId && this.token) {
        this.connect(this.playerId, this.token)
      }
    }, delay)
  }

  private startPing(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  private stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export const wsService = new WebSocketService()
