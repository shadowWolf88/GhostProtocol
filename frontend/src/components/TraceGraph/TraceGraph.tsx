import { useEffect, useRef, useCallback } from 'react'
import * as d3 from 'd3'
import type { TraceNode, TraceEdge, TraceGraph as TraceGraphData } from '../../types'

interface Props {
  data: TraceGraphData
  width: number
  height: number
  onNodeClick?: (node: TraceNode) => void
}

const NODE_COLORS: Record<string, string> = {
  Player: '#00ff41',
  Identity: '#00ffff',
  Device: '#ffb000',
  WorldNode: '#9933ff',
  Artifact: '#ff2020',
}

const NODE_RADIUS: Record<string, number> = {
  Player: 12,
  Identity: 9,
  Device: 8,
  WorldNode: 10,
  Artifact: 6,
}

const LINK_COLORS: Record<string, string> = {
  USES: '#ffb000',
  OPERATES: '#00ffff',
  ACCESSED: '#9933ff',
  IMPLICATES: '#ff2020',
  LEFT_AT: '#ff6600',
  CONNECTS_TO: '#666666',
}

export function TraceGraph({ data, width, height, onNodeClick }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const simulationRef = useRef<d3.Simulation<TraceNode, TraceEdge> | null>(null)

  const draw = useCallback(() => {
    if (!svgRef.current || !data.nodes.length) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    // Deep clone data to avoid mutating props
    const nodes: TraceNode[] = data.nodes.map((n) => ({ ...n }))
    const edges: TraceEdge[] = data.edges.map((e) => ({ ...e }))

    // Build id → node map for edge resolution
    const nodeById = new Map(nodes.map((n) => [n.id, n]))

    // Resolve string source/target references
    const resolvedEdges = edges.map((e) => ({
      ...e,
      source: typeof e.source === 'string' ? (nodeById.get(e.source) ?? e.source) : e.source,
      target: typeof e.target === 'string' ? (nodeById.get(e.target) ?? e.target) : e.target,
    }))

    const g = svg.append('g')

    // ── Zoom ──────────────────────────────────────────────────────────────────
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })
    svg.call(zoom)

    // ── Arrowhead marker ──────────────────────────────────────────────────────
    const defs = svg.append('defs')
    const markerTypes = Object.keys(LINK_COLORS)
    markerTypes.forEach((type) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 18)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', LINK_COLORS[type] ?? '#666')
        .attr('opacity', 0.7)
    })

    // ── Links ─────────────────────────────────────────────────────────────────
    const link = g.append('g')
      .selectAll<SVGLineElement, typeof resolvedEdges[0]>('line')
      .data(resolvedEdges)
      .join('line')
      .attr('stroke', (d) => LINK_COLORS[d.type] ?? '#444')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', (d) => `url(#arrow-${d.type})`)

    // ── Link labels ───────────────────────────────────────────────────────────
    const linkLabel = g.append('g')
      .selectAll<SVGTextElement, typeof resolvedEdges[0]>('text')
      .data(resolvedEdges)
      .join('text')
      .attr('font-size', 8)
      .attr('fill', '#444')
      .attr('text-anchor', 'middle')
      .text((d) => d.type)

    // ── Nodes ─────────────────────────────────────────────────────────────────
    const node = g.append('g')
      .selectAll<SVGGElement, TraceNode>('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .style('cursor', 'pointer')
      .call(
        d3.drag<SVGGElement, TraceNode>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on('drag', (event, d) => {
            d.fx = event.x
            d.fy = event.y
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0)
            d.fx = null
            d.fy = null
          })
      )
      .on('click', (_event, d) => onNodeClick?.(d))

    node.append('circle')
      .attr('r', (d) => NODE_RADIUS[d.type] ?? 7)
      .attr('fill', (d) => NODE_COLORS[d.type] ?? '#666')
      .attr('fill-opacity', 0.85)
      .attr('stroke', (d) => NODE_COLORS[d.type] ?? '#666')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.4)

    // Pulse ring for Player node
    node.filter((d) => d.type === 'Player')
      .append('circle')
      .attr('r', 18)
      .attr('fill', 'none')
      .attr('stroke', '#00ff41')
      .attr('stroke-width', 1)
      .attr('stroke-opacity', 0.3)
      .attr('stroke-dasharray', '4 2')

    node.append('text')
      .attr('dy', (d) => (NODE_RADIUS[d.type] ?? 7) + 12)
      .attr('text-anchor', 'middle')
      .attr('font-size', 9)
      .attr('fill', (d) => NODE_COLORS[d.type] ?? '#666')
      .attr('fill-opacity', 0.8)
      .text((d) => d.label.slice(0, 16))

    // ── Simulation ────────────────────────────────────────────────────────────
    const simulation = d3.forceSimulation<TraceNode>(nodes)
      .force('link', d3.forceLink<TraceNode, typeof resolvedEdges[0]>(resolvedEdges)
        .id((d) => d.id)
        .distance(80)
        .strength(0.5)
      )
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(24))

    simulationRef.current = simulation as unknown as d3.Simulation<TraceNode, TraceEdge>

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as TraceNode).x ?? 0)
        .attr('y1', (d) => (d.source as TraceNode).y ?? 0)
        .attr('x2', (d) => (d.target as TraceNode).x ?? 0)
        .attr('y2', (d) => (d.target as TraceNode).y ?? 0)

      linkLabel
        .attr('x', (d) => (((d.source as TraceNode).x ?? 0) + ((d.target as TraceNode).x ?? 0)) / 2)
        .attr('y', (d) => (((d.source as TraceNode).y ?? 0) + ((d.target as TraceNode).y ?? 0)) / 2)

      node.attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })

    // Stop after settling
    setTimeout(() => simulation.alphaTarget(0), 3000)
  }, [data, width, height, onNodeClick])

  useEffect(() => {
    draw()
    return () => {
      simulationRef.current?.stop()
    }
  }, [draw])

  if (!data.nodes.length) {
    return (
      <div className="flex items-center justify-center h-full text-terminal-muted text-sm">
        <div className="text-center">
          <div className="mb-2">[ NO TRACE DATA ]</div>
          <div className="text-xs">Complete an operation to generate trace artifacts.</div>
        </div>
      </div>
    )
  }

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      style={{ background: '#0a0a0a', display: 'block' }}
    />
  )
}
