import { useState, useRef, useEffect } from 'react'
import { TraceGraph } from './TraceGraph'
import { useTraceGraph } from '../../hooks/useTraceGraph'
import type { TraceNode } from '../../types'

export function TracePanel() {
  const { data, isLoading, isError, refetch } = useTraceGraph()
  const [selectedNode, setSelectedNode] = useState<TraceNode | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dims, setDims] = useState({ width: 400, height: 400 })

  useEffect(() => {
    if (!containerRef.current) return
    const obs = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDims({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        })
      }
    })
    obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-terminal-border shrink-0">
        <span className="text-terminal-cyan text-xs font-bold tracking-widest">TRACE GRAPH</span>
        <div className="flex items-center gap-3">
          {data?.fallback && (
            <span className="text-terminal-amber text-xs">[NEO4J OFFLINE — FALLBACK]</span>
          )}
          <button
            onClick={() => refetch()}
            className="text-terminal-muted text-xs hover:text-terminal-green transition-colors"
          >
            [REFRESH]
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex gap-4 px-3 py-1 border-b border-terminal-border shrink-0">
        {[
          { type: 'Player', color: '#00ff41' },
          { type: 'Identity', color: '#00ffff' },
          { type: 'Device', color: '#ffb000' },
          { type: 'WorldNode', color: '#9933ff' },
          { type: 'Artifact', color: '#ff2020' },
        ].map(({ type, color }) => (
          <div key={type} className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full" style={{ background: color }} />
            <span className="text-terminal-muted text-xs">{type}</span>
          </div>
        ))}
      </div>

      {/* Graph area */}
      <div ref={containerRef} className="flex-1 relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-terminal-muted text-sm">
            Mapping trace network...
          </div>
        )}
        {isError && (
          <div className="absolute inset-0 flex items-center justify-center text-terminal-red text-sm">
            [ERROR] Trace graph unavailable.
          </div>
        )}
        {data && !isLoading && (
          <TraceGraph
            data={data}
            width={dims.width}
            height={dims.height}
            onNodeClick={setSelectedNode}
          />
        )}
      </div>

      {/* Node detail drawer */}
      {selectedNode && (
        <div className="shrink-0 border-t border-terminal-border bg-terminal-surface p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-terminal-cyan text-xs font-bold">{selectedNode.type.toUpperCase()}</span>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-terminal-muted text-xs hover:text-terminal-red"
            >
              [×]
            </button>
          </div>
          <div className="text-terminal-green text-xs mb-1">{selectedNode.label}</div>
          <div className="text-terminal-muted text-xs font-mono">
            {Object.entries(selectedNode.properties)
              .slice(0, 6)
              .map(([k, v]) => (
                <div key={k}>{k}: {String(v)}</div>
              ))
            }
          </div>
        </div>
      )}
    </div>
  )
}
