import {
  worldApi, operationApi, heatApi, skillApi,
  economyApi, factionApi, prisonApi, traceApi,
  onboardingApi, aiApi, playerApi,
} from './api'
import { useGameStore } from '../store/gameStore'

// ─── Types ────────────────────────────────────────────────────────────────────

export type OutputLine = {
  text: string
  className?: string
}

type CommandHandler = (args: string[]) => Promise<OutputLine[]>

const OK = (text: string): OutputLine => ({ text, className: 'text-terminal-green' })
const ERR = (text: string): OutputLine => ({ text, className: 'text-terminal-red' })
const INFO = (text: string): OutputLine => ({ text, className: 'text-terminal-white' })
const DIM = (text: string): OutputLine => ({ text, className: 'text-terminal-muted' })
const WARN = (text: string): OutputLine => ({ text, className: 'text-terminal-amber' })
const HEAD = (text: string): OutputLine => ({ text, className: 'text-terminal-cyan font-bold' })

function sep(): OutputLine {
  return DIM('─'.repeat(60))
}

function fmtNum(n: number): string {
  return n.toLocaleString()
}

// ─── Command Registry ─────────────────────────────────────────────────────────

const commands: Record<string, CommandHandler> = {

  // ── Help ──────────────────────────────────────────────────────────────────
  help: async (args) => {
    const topic = args[0]
    if (topic === 'ops' || topic === 'operation') {
      return [
        HEAD('OPERATION COMMANDS'),
        sep(),
        INFO('  scan <node_key>          Run OSINT on a target node'),
        INFO('  op start <node> <device> [approach]   Launch an operation'),
        INFO('  op advance [action]      Execute current operation phase'),
        INFO('  op abort                 Abort active operation (50% XP)'),
        INFO('  op status                Show active operation state'),
        INFO('  op history               Show last 10 operations'),
        DIM('  approaches: technical | social | hybrid'),
      ]
    }
    return [
      HEAD('GHOST PROTOCOL v1.0 — COMMAND REFERENCE'),
      sep(),
      HEAD('SYSTEM'),
      INFO('  help [topic]             This screen. Topics: ops, economy, heat'),
      INFO('  status                   Full player status overview'),
      INFO('  whoami                   Identity summary'),
      INFO('  clear                    Clear terminal'),
      INFO('  panel <name>             Switch panel (trace|skills|market|faction|prison)'),
      sep(),
      HEAD('INTELLIGENCE'),
      INFO('  nodes                    List accessible target nodes'),
      INFO('  scan <node_key>          Intel on specific target'),
      INFO('  map                      World map overview'),
      sep(),
      HEAD('OPERATIONS'),
      INFO('  help ops                 Operation command details'),
      INFO('  op start <node> <device> Start an operation'),
      INFO('  op advance               Execute current phase'),
      INFO('  op abort                 Emergency abort'),
      sep(),
      HEAD('HEAT & OPSEC'),
      INFO('  heat                     Current heat status'),
      INFO('  go-dark <hours>          Reduce heat (disable operations)'),
      INFO('  heat-preview             Decay projection'),
      sep(),
      HEAD('ECONOMY'),
      INFO('  wallet                   Current balances'),
      INFO('  market                   Browse black market'),
      INFO('  buy <item_id>            Purchase from market'),
      INFO('  launder <amount>         Launder crypto to privacy coin'),
      INFO('  txns                     Transaction history'),
      sep(),
      HEAD('SKILLS'),
      INFO('  skills                   All skill trees'),
      INFO('  skills <tree>            Detail on one tree'),
      sep(),
      HEAD('SOCIAL'),
      INFO('  factions                 Faction standings'),
      INFO('  contact <faction>        Initiate faction contact'),
      INFO('  prison                   Prison status (if incarcerated)'),
      INFO('  trace                    Open trace graph (panel)'),
    ]
  },

  // ── Status ────────────────────────────────────────────────────────────────
  status: async () => {
    try {
      const [profile, heat] = await Promise.all([
        playerApi.getProfile(),
        heatApi.getStatus(),
      ])
      const { stats, psych } = profile
      const energyBar = '█'.repeat(Math.floor(stats.energy / 10)) + '░'.repeat(10 - Math.floor(stats.energy / 10))
      const stressBar = '█'.repeat(Math.floor(psych.stress / 10)) + '░'.repeat(10 - Math.floor(psych.stress / 10))
      const heatClass = heat.threat_tier >= 4 ? 'text-terminal-red' : heat.threat_tier >= 3 ? 'text-terminal-amber' : 'text-terminal-green'

      return [
        HEAD(`▌ ${profile.handle.toUpperCase()} — STATUS REPORT`),
        sep(),
        HEAD('RESOURCES'),
        INFO(`  Crypto:        ${fmtNum(stats.crypto)}₡`),
        INFO(`  Privacy Coin:  ${fmtNum(stats.privacy_coin)}Ψ`),
        INFO(`  Fiat:          $${fmtNum(stats.fiat)}`),
        INFO(`  Reputation:    ${stats.reputation}`),
        sep(),
        HEAD('VITALS'),
        INFO(`  Energy:  [${energyBar}] ${stats.energy}/${stats.max_energy}`),
        INFO(`  Focus:   ${psych.focus}%`),
        INFO(`  Stress:  [${stressBar}] ${psych.stress}/100`),
        INFO(`  Paranoia: ${psych.paranoia} | Sleep Debt: ${psych.sleep_debt}`),
        sep(),
        HEAD('THREAT STATUS'),
        { text: `  [${heat.threat_tier_name}] Total Heat: ${Math.round(heat.total_heat)}`, className: heatClass },
        DIM(`  ${heat.threat_description}`),
      ]
    } catch {
      return [ERR('Failed to retrieve status. Signal lost.')]
    }
  },

  whoami: async () => {
    try {
      const profile = await playerApi.getProfile()
      return [
        HEAD('IDENTITY SUMMARY'),
        sep(),
        INFO(`  Handle:      ${profile.handle}`),
        INFO(`  Devices:     ${profile.devices.filter(d => !d.is_destroyed).length} active`),
        INFO(`  Identities:  ${profile.identities.filter(i => !i.is_burned).length} clean`),
        INFO(`  On network:  ${new Date(profile.created_at).toLocaleDateString()}`),
      ]
    } catch {
      return [ERR('Ghost not found.')]
    }
  },

  clear: async () => [],

  panel: async (args) => {
    const panels = ['trace', 'skills', 'market', 'faction', 'prison', 'terminal']
    const p = args[0]
    if (!panels.includes(p)) {
      return [ERR(`Unknown panel. Available: ${panels.join(', ')}`)]
    }
    useGameStore.getState().setActivePanel(p as 'trace' | 'skills' | 'market' | 'faction' | 'prison' | 'terminal')
    return [OK(`Switched to ${p.toUpperCase()} panel.`)]
  },

  // ── World ─────────────────────────────────────────────────────────────────
  nodes: async () => {
    try {
      const nodes = await worldApi.getAccessibleNodes()
      const lines: OutputLine[] = [HEAD(`ACCESSIBLE TARGETS (${nodes.length})`), sep()]
      for (const n of nodes) {
        const tier = '★'.repeat(n.tier) + '☆'.repeat(5 - n.tier)
        lines.push(INFO(`  [${n.node_key.padEnd(24)}] ${tier} ${n.name}`))
        lines.push(DIM(`    ${n.category.toUpperCase()} | Vuln: ${n.vulnerability_score} | Reward: ${n.base_crypto_reward}₡`))
      }
      return lines
    } catch {
      return [ERR('Cannot access node directory. Check connection.')]
    }
  },

  scan: async (args) => {
    if (!args[0]) return [ERR('Usage: scan <node_key>')]
    try {
      const intel = await worldApi.getNodeIntel(args[0])
      const { node } = intel
      const chanceColor = intel.success_chance > 0.7 ? 'text-terminal-green' : intel.success_chance > 0.4 ? 'text-terminal-amber' : 'text-terminal-red'
      return [
        HEAD(`OSINT REPORT — ${node.name}`),
        sep(),
        INFO(`  Category:     ${node.category.toUpperCase()}`),
        INFO(`  Tier:         ${node.tier}/5`),
        INFO(`  Defender:     Tier ${node.defender_tier}`),
        INFO(`  Vuln Score:   ${node.vulnerability_score}/100`),
        INFO(`  Heat Mult:    ×${node.heat_multiplier}`),
        INFO(`  Base Reward:  ${node.base_crypto_reward}₡ + ${node.base_reputation_reward} rep`),
        sep(),
        { text: `  Success Chance:     ${Math.round(intel.success_chance * 100)}%`, className: chanceColor },
        WARN(`  Alert Level:        ${intel.alert_level}/100`),
        WARN(`  Est. Heat Gain:     +${intel.estimated_heat_gain}`),
        INFO(`  Recommended:        ${intel.recommended_approach.toUpperCase()}`),
        DIM(`  ${node.description}`),
      ]
    } catch {
      return [ERR(`Target ${args[0]} not found or inaccessible.`)]
    }
  },

  map: async () => {
    try {
      const map = await worldApi.getWorldMap()
      const byCategory: Record<string, typeof map.nodes> = {}
      for (const n of map.nodes) {
        if (!byCategory[n.category]) byCategory[n.category] = []
        byCategory[n.category].push(n)
      }
      const lines: OutputLine[] = [HEAD('WORLD MAP'), DIM(`  Player Tier Ceiling: ${map.player_max_tier}`), sep()]
      for (const [cat, ns] of Object.entries(byCategory)) {
        lines.push(HEAD(`  ${cat.toUpperCase().replace('_', ' ')} (${ns.length})`))
        for (const n of ns.slice(0, 3)) {
          lines.push(DIM(`    [T${n.tier}] ${n.node_key} — ${n.name}`))
        }
        if (ns.length > 3) lines.push(DIM(`    ... and ${ns.length - 3} more`))
      }
      return lines
    } catch {
      return [ERR('World map unavailable.')]
    }
  },

  // ── Operations ────────────────────────────────────────────────────────────
  op: async (args) => {
    const sub = args[0]
    if (!sub) return [ERR('Usage: op <start|advance|abort|status|history>')]

    if (sub === 'start') {
      const [, nodeKey, deviceId, approach = 'technical'] = args
      if (!nodeKey || !deviceId) return [ERR('Usage: op start <node_key> <device_id> [approach]')]
      try {
        const result = await operationApi.create(nodeKey, deviceId, approach)
        useGameStore.getState().setActiveOperation({ id: result.operation_id } as never)
        return [
          OK(`Operation launched against ${nodeKey}`),
          INFO(`  ID: ${result.operation_id}`),
          INFO(`  Approach: ${approach.toUpperCase()}`),
          WARN(`  Energy cost: -${result.energy_cost}`),
          sep(),
          DIM('BRIEFING:'),
          ...result.briefing.split('\n').map(l => ({ text: `  ${l}`, className: 'text-terminal-muted' } as OutputLine)),
          sep(),
          INFO('  Run: op advance  to execute RECON phase'),
        ]
      } catch (e: unknown) {
        const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        return [ERR(msg ?? 'Operation launch failed.')]
      }
    }

    if (sub === 'advance') {
      const activeOp = useGameStore.getState().activeOperation
      if (!activeOp) return [ERR('No active operation. Run: op start <node> <device>')]
      try {
        const outcome = await operationApi.advance(activeOp.id, args[1] ?? 'execute')
        const lines: OutputLine[] = [
          { text: `[${outcome.phase.toUpperCase()}] ${outcome.success ? '✓ SUCCESS' : '✗ FAILED'}`, className: outcome.success ? 'text-terminal-green' : 'text-terminal-red' },
          sep(),
          ...outcome.narrative.split('\n').map(l => INFO(`  ${l}`)),
          sep(),
          WARN(`  Heat generated:  +${outcome.heat_generated}`),
        ]
        if (outcome.artifacts_generated.length > 0) {
          lines.push(ERR(`  Artifacts left:  ${outcome.artifacts_generated.join(', ')}`))
        }
        if (outcome.next_phase) {
          lines.push(OK(`  Next phase:      ${outcome.next_phase.toUpperCase()}`))
          lines.push(DIM('  Run: op advance  to continue'))
        } else {
          useGameStore.getState().setActiveOperation(null)
          lines.push(OK('  Operation concluded.'))
        }
        return lines
      } catch (e: unknown) {
        const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        return [ERR(msg ?? 'Phase execution failed.')]
      }
    }

    if (sub === 'abort') {
      const activeOp = useGameStore.getState().activeOperation
      if (!activeOp) return [WARN('No active operation.')]
      try {
        const result = await operationApi.abort(activeOp.id)
        useGameStore.getState().setActiveOperation(null)
        const xpLines = Object.entries(result.xp_awarded).map(([k, v]) =>
          DIM(`  ${k}: +${v} XP`)
        )
        return [WARN('Operation aborted.'), INFO(result.message), ...xpLines]
      } catch {
        return [ERR('Abort failed.')]
      }
    }

    if (sub === 'status') {
      const activeOp = useGameStore.getState().activeOperation
      if (!activeOp) return [INFO('No active operation.')]
      return [
        HEAD('ACTIVE OPERATION'),
        INFO(`  ID: ${activeOp.id}`),
        INFO(`  Status: ${activeOp.status}`),
      ]
    }

    if (sub === 'history') {
      try {
        const history = await operationApi.getHistory(10)
        if (!history.length) return [INFO('No operations on record.')]
        const lines: OutputLine[] = [HEAD('OPERATION HISTORY'), sep()]
        for (const op of history) {
          const status = op.status === 'completed' ? OK : op.status === 'failed' ? ERR : WARN
          lines.push(status(`  [${op.started_at.slice(0, 10)}] ${op.status.toUpperCase()} — +${op.crypto_earned}₡`))
        }
        return lines
      } catch {
        return [ERR('Failed to retrieve history.')]
      }
    }

    return [ERR(`Unknown op subcommand: ${sub}`)]
  },

  // ── Heat ──────────────────────────────────────────────────────────────────
  heat: async () => {
    try {
      const heat = await heatApi.getStatus()
      const tierColor = heat.threat_tier >= 4 ? 'text-terminal-red' : heat.threat_tier >= 3 ? 'text-terminal-amber' : 'text-terminal-green'
      const lines: OutputLine[] = [
        HEAD('HEAT STATUS'),
        { text: `  [${heat.threat_tier_name}] Total: ${Math.round(heat.total_heat)}`, className: tierColor },
        DIM(`  ${heat.threat_description}`),
        sep(),
      ]
      for (const [domain, d] of Object.entries(heat.domains)) {
        const bar = '█'.repeat(Math.floor(d.level / 10)) + '░'.repeat(10 - Math.floor(d.level / 10))
        const color = d.level > 60 ? 'text-terminal-red' : d.level > 30 ? 'text-terminal-amber' : 'text-terminal-green'
        lines.push({ text: `  ${domain.padEnd(16)} [${bar}] ${Math.round(d.level)}`, className: color })
      }
      if (heat.go_dark_until) {
        lines.push(sep())
        lines.push(WARN(`  GO DARK active until: ${heat.go_dark_until}`))
      }
      return lines
    } catch {
      return [ERR('Heat status unavailable.')]
    }
  },

  'go-dark': async (args) => {
    const hours = parseInt(args[0] ?? '24')
    if (isNaN(hours) || hours < 1 || hours > 168) {
      return [ERR('Usage: go-dark <hours> (1–168)')]
    }
    try {
      const result = await heatApi.goDark(hours)
      return [
        OK(`Going dark for ${hours} hours.`),
        WARN(result.message),
        DIM(`  Dark until: ${result.go_dark_until}`),
        DIM('  Heat decay accelerated. No operations possible during this time.'),
      ]
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      return [ERR(msg ?? 'Go dark failed.')]
    }
  },

  'heat-preview': async () => {
    try {
      const preview = await heatApi.getDecayPreview()
      return [
        HEAD('HEAT DECAY PROJECTION'),
        sep(),
        INFO(`  Current:    ${Math.round(preview.current_total)}`),
        OK(`  In 24h:     ${Math.round(preview.projected_24h)}`),
        OK(`  In 72h:     ${Math.round(preview.projected_72h)}`),
        DIM('  (Projections assume no new incidents)'),
      ]
    } catch {
      return [ERR('Projection unavailable.')]
    }
  },

  // ── Economy ───────────────────────────────────────────────────────────────
  wallet: async () => {
    try {
      const w = await economyApi.getWallet()
      return [
        HEAD('WALLET'),
        sep(),
        INFO(`  Crypto:        ${fmtNum(w.crypto)}₡`),
        INFO(`  Privacy Coin:  ${fmtNum(w.privacy_coin)}Ψ`),
        INFO(`  Fiat:          $${fmtNum(w.fiat)}`),
      ]
    } catch {
      return [ERR('Wallet inaccessible.')]
    }
  },

  market: async () => {
    try {
      const listings = await economyApi.getMarket()
      const lines: OutputLine[] = [HEAD(`BLACK MARKET (${listings.length} listings)`), sep()]
      for (const l of listings) {
        lines.push(INFO(`  [${l.id.slice(0, 8)}] ${l.item_name.padEnd(30)} ${fmtNum(l.price_crypto)}₡`))
        lines.push(DIM(`    ${l.description}`))
      }
      lines.push(sep())
      lines.push(DIM('  Run: buy <item_id> to purchase'))
      return lines
    } catch {
      return [ERR('Market offline.')]
    }
  },

  buy: async (args) => {
    if (!args[0]) return [ERR('Usage: buy <item_id>')]
    try {
      const result = await economyApi.purchase(args[0])
      return [
        OK(`Purchased: ${result.item_name}`),
        INFO(result.message),
        DIM(`  Remaining balance: ${fmtNum(result.new_balance)}₡`),
      ]
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      return [ERR(msg ?? 'Purchase failed.')]
    }
  },

  launder: async (args) => {
    const amount = parseInt(args[0])
    if (isNaN(amount) || amount <= 0) return [ERR('Usage: launder <amount>')]
    if (args[1] === '--preview') {
      try {
        const chain = await economyApi.launderPreview(amount)
        const lines: OutputLine[] = [HEAD('LAUNDERING PREVIEW'), sep()]
        for (const step of chain.steps) {
          lines.push(INFO(`  Step ${step.step}: ${fmtNum(step.amount_in)}₡ → fee ${fmtNum(step.fee)}₡ → ${fmtNum(step.amount_out)}₡`))
        }
        lines.push(sep())
        lines.push(WARN(`  Total fees:      ${fmtNum(chain.total_fees)}₡`))
        lines.push(OK(`  Final output:    ${fmtNum(chain.final_privacy_coin)}Ψ`))
        lines.push(WARN(`  Heat added:      +${chain.intelligence_heat_added} (intelligence)`))
        lines.push(DIM('  Run: launder <amount>  to execute'))
        return lines
      } catch {
        return [ERR('Launder preview failed.')]
      }
    }
    try {
      const result = await economyApi.launder(amount)
      return [
        OK(`Laundering complete.`),
        INFO(`  Privacy coin gained: +${fmtNum(result.privacy_coin_gained)}Ψ`),
        INFO(`  Crypto remaining:    ${fmtNum(result.new_crypto)}₡`),
        WARN(`  Intelligence heat increased.`),
      ]
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      return [ERR(msg ?? 'Laundering failed.')]
    }
  },

  txns: async () => {
    try {
      const txns = await economyApi.getTransactions(15)
      if (!txns.length) return [INFO('No transactions on record.')]
      const lines: OutputLine[] = [HEAD('TRANSACTION HISTORY'), sep()]
      for (const t of txns) {
        const sign = t.amount > 0 ? '+' : ''
        const color = t.amount > 0 ? 'text-terminal-green' : 'text-terminal-red'
        lines.push({ text: `  ${t.created_at.slice(0, 10)} ${sign}${fmtNum(t.amount)} ${t.currency.padEnd(12)} ${t.description}`, className: color })
      }
      return lines
    } catch {
      return [ERR('Transaction history unavailable.')]
    }
  },

  // ── Skills ────────────────────────────────────────────────────────────────
  skills: async (args) => {
    try {
      if (args[0]) {
        const tree = await skillApi.getTree(args[0])
        const lines: OutputLine[] = [
          HEAD(`${tree.tree_name.toUpperCase()} — ${tree.code}`),
          DIM(tree.description),
          sep(),
          INFO(`  Level: ${tree.current_level} | XP: ${fmtNum(tree.current_xp)} / ${fmtNum(tree.xp_to_next)}`),
          sep(),
        ]
        for (const ab of tree.abilities) {
          const unlocked = ab.unlocked ? OK : DIM
          lines.push(unlocked(`  [T${ab.tier}] ${ab.name} ${ab.unlocked ? '✓' : `(req: L${ab.level_required})`}`))
          lines.push(DIM(`    ${ab.description} | +${ab.operation_bonus}%`))
        }
        return lines
      }
      const { trees, total_level } = await skillApi.getTrees()
      const lines: OutputLine[] = [HEAD(`SKILL TREES — Total Level: ${total_level}`), sep()]
      for (const [key, tree] of Object.entries(trees)) {
        const bar = '█'.repeat(Math.min(10, Math.floor(tree.current_level / 5))) + '░'.repeat(10 - Math.min(10, Math.floor(tree.current_level / 5)))
        lines.push(INFO(`  ${key.padEnd(14)} [${bar}] L${tree.current_level} — ${tree.tree_name}`))
      }
      lines.push(sep())
      lines.push(DIM('  Run: skills <tree>  for details'))
      return lines
    } catch {
      return [ERR('Skill data unavailable.')]
    }
  },

  // ── Factions ──────────────────────────────────────────────────────────────
  factions: async () => {
    try {
      const relations = await factionApi.getRelations()
      const lines: OutputLine[] = [HEAD('FACTION STANDINGS'), sep()]
      for (const r of relations) {
        const color = r.is_member ? 'text-terminal-cyan' : r.standing > 50 ? 'text-terminal-green' : 'text-terminal-muted'
        const tag = r.is_member ? '[MEMBER]' : r.contact_eligible ? '[ELIGIBLE]' : ''
        lines.push({ text: `  ${r.faction_key.toUpperCase().padEnd(20)} ${r.standing.toString().padStart(4)} rep  ${tag}`, className: color })
      }
      lines.push(sep())
      lines.push(DIM('  Run: contact <faction_key>  to initiate'))
      return lines
    } catch {
      return [ERR('Faction directory offline.')]
    }
  },

  contact: async (args) => {
    if (!args[0]) return [ERR('Usage: contact <faction_key>')]
    try {
      const intro = await factionApi.getIntroMessage(args[0])
      return [
        HEAD(`[${intro.npc_name.toUpperCase()}] — ${args[0].toUpperCase()}`),
        sep(),
        ...intro.message.split('\n').map(l => ({ text: `  ${l}`, className: 'text-terminal-white' } as OutputLine)),
        sep(),
        DIM(`  Requirements: ${JSON.stringify(intro.requirements)}`),
      ]
    } catch {
      return [ERR('Contact not found or not yet eligible.')]
    }
  },

  // ── Prison ────────────────────────────────────────────────────────────────
  prison: async () => {
    try {
      const status = await prisonApi.getStatus()
      if (!status.is_imprisoned) return [OK('You are not currently incarcerated.')]
      return [
        { text: '▌ INCARCERATED', className: 'text-terminal-red font-bold' },
        sep(),
        INFO(`  Charge:          ${status.charge_description}`),
        WARN(`  Sentence:        ${status.sentence_hours}h`),
        WARN(`  Time remaining:  ${Math.round(status.time_remaining_hours)}h`),
        INFO(`  Release:         ${status.release_at}`),
        sep(),
        HEAD('AVAILABLE ACTIVITIES'),
        INFO('  broker-info      Sell intelligence (rep gain)'),
        INFO('  recruit-contact  Find an ally (costs 100₡)'),
        INFO('  escape-plan      Attempt escape (20% success, needs 3 broker_info)'),
        INFO('  legal-fight      Legal challenge (costs 500₡, -20% sentence)'),
        sep(),
        DIM('  Run: prison-do <activity>  to perform'),
      ]
    } catch {
      return [ERR('Prison status unavailable.')]
    }
  },

  'prison-do': async (args) => {
    if (!args[0]) return [ERR('Usage: prison-do <broker-info|recruit-contact|escape-plan|legal-fight>')]
    const activityMap: Record<string, string> = {
      'broker-info': 'broker_info',
      'recruit-contact': 'recruit_contact',
      'escape-plan': 'escape_plan',
      'legal-fight': 'legal_fight',
    }
    const actType = activityMap[args[0]] ?? args[0]
    try {
      const result = await prisonApi.performActivity(actType)
      return [
        OK(result.message),
        INFO(result.outcome),
        result.cost_crypto > 0 ? WARN(`  Cost: -${result.cost_crypto}₡`) : DIM(''),
      ]
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      return [ERR(msg ?? 'Activity failed.')]
    }
  },

  // ── Trace ─────────────────────────────────────────────────────────────────
  trace: async () => {
    useGameStore.getState().setActivePanel('trace')
    return [OK('Trace graph opened in right panel.'), DIM('  Nodes represent identities, devices, and artifacts.')]
  },

  // ── NPC Chat ─────────────────────────────────────────────────────────────
  chat: async (args) => {
    const [npcKey, ...messageParts] = args
    if (!npcKey || !messageParts.length) return [ERR('Usage: chat <npc_key> <message>')]
    try {
      const response = await aiApi.chat(npcKey, messageParts.join(' '))
      return [
        HEAD(`[${npcKey.toUpperCase()}]`),
        sep(),
        ...response.response.split('\n').map(l => ({ text: `  ${l}`, className: 'text-terminal-white' } as OutputLine)),
        sep(),
        DIM(`  Suspicion delta: ${response.suspicion_delta > 0 ? '+' : ''}${response.suspicion_delta}`),
        DIM(`  Success probability: ${Math.round(response.success_probability * 100)}%`),
      ]
    } catch {
      return [ERR('NPC unreachable.')]
    }
  },

  // ── Onboarding ────────────────────────────────────────────────────────────
  handler: async () => {
    try {
      const state = await onboardingApi.getState()
      if (!state.handler_message) return [DIM('No messages from PHANTOM.')]
      return [
        HEAD('[PHANTOM]'),
        sep(),
        ...state.handler_message.split('\n').map(l => ({ text: `  ${l}`, className: 'text-terminal-white' } as OutputLine)),
        DIM(`  Step: ${state.current_step} | Progress: ${state.completed_steps.length}/${state.completed_steps.length + 1}`),
      ]
    } catch {
      return [ERR('Handler offline.')]
    }
  },
}

// ─── Public API ───────────────────────────────────────────────────────────────

export async function executeCommand(input: string): Promise<OutputLine[]> {
  const trimmed = input.trim()
  if (!trimmed) return []

  const parts = trimmed.split(/\s+/)
  const cmd = parts[0].toLowerCase()
  const args = parts.slice(1)

  const handler = commands[cmd]
  if (!handler) {
    return [
      ERR(`Command not found: ${cmd}`),
      DIM('  Run: help  for available commands'),
    ]
  }

  try {
    return await handler(args)
  } catch {
    return [ERR(`Command error. Try: help`)]
  }
}

export function getCompletions(partial: string): string[] {
  if (!partial) return Object.keys(commands)
  return Object.keys(commands).filter(k => k.startsWith(partial))
}
