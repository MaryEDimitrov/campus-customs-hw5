import { StrictMode, useEffect, useMemo, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, ArrowRight, CheckCircle2, CircleDollarSign, Clock3, Layers3, LoaderCircle, Play, RotateCcw, Shirt, ShieldCheck, UserRound } from 'lucide-react'
import './styles.css'
import './spunk.css'

const API = 'http://localhost:8001'
type Ticket = { id:number; subject:string; type:string; status:string; requester:string; notes:string|null; payment_status:string|null }
type Event = { run_id:string; timestamp:string; step:number; role:string; event_type:string; details:Record<string, unknown> }
type TeamResult = { run_id:string; findings:{role:string;ticket_id:number;recommendation:string;evidence:string[];blockers:string[];needs_human_approval:boolean;proposed_next_step:string}[]; final_plan:string; human_approval_required:boolean }

async function api<T>(path:string, options?:RequestInit):Promise<T> { const response=await fetch(`${API}${path}`, { headers:{'Content-Type':'application/json'}, ...options }); if(!response.ok) throw new Error(await response.text()); return response.json() }

function formatEventDetails(details:Record<string, unknown>={}) {
  return Object.entries(details).map(([key,value]) => {
    if(key==='tool_names') return ''
    if(Array.isArray(value)) {
      const items=[...new Set(value.map(String))]
      return `${key.replace(/_/g,' ')}: ${items.join(', ')}`
    }
    if(value && typeof value==='object') return `${key.replace(/_/g,' ')}: ${Object.values(value).join(', ')}`
    return `${key.replace(/_/g,' ')}: ${String(value)}`
  }).filter(Boolean).join(' · ')
}

function App() {
  const [tickets,setTickets]=useState<Ticket[]>([]), [selected,setSelected]=useState(101), [events,setEvents]=useState<Event[]>([]), [result,setResult]=useState<TeamResult|null>(null), [balance,setBalance]=useState<{balance:number;date:string}|null>(null), [running,setRunning]=useState(false), [loading,setLoading]=useState(true), [error,setError]=useState(''), [payment,setPayment]=useState(false)
  const autoStarted=useRef(false)
  const active=tickets.find(t=>t.id===selected)
  const activeEvents=useMemo(()=>events.filter(e=>!e.run_id || (result?.run_id ? e.run_id===result.run_id : true)),[events,result])
  async function refresh(){ setLoading(true); try { const [ts,bal,ev]=await Promise.all([api<Ticket[]>('/api/tickets'),api<typeof balance>('/api/cash/checking'),api<Event[]>('/api/agent-events?limit=80')]); setTickets(ts); setBalance(bal); setEvents(ev); setError('') } catch(e){ setError(e instanceof Error?e.message:'Could not reach backend') } finally { setLoading(false) } }
  useEffect(()=>{
    if(autoStarted.current) return
    autoStarted.current=true
    const startOpenTickets=async()=>{
      await refresh()
      try {
        const open=await api<Ticket[]>('/api/tickets')
        for(const ticket of open.filter(t=>t.status==='open')){
          setSelected(ticket.id); setRunning(true)
          const team=await api<TeamResult>(`/api/tickets/${ticket.id}/run`,{method:'POST'})
          if(ticket.id===selected) setResult(team)
          const status=team.human_approval_required?'in_progress':'resolved'
          const note=team.human_approval_required?`Automatic agent run ${team.run_id} completed; human approval is required before resolution.`:`Automatic agent run ${team.run_id} completed; no human approval was required.`
          await api(`/api/tickets/${ticket.id}/status`,{method:'POST',body:JSON.stringify({status,note})})
        }
        await refresh()
      } catch(e){ setError(e instanceof Error?e.message:'Automatic agent run failed') }
      finally { setRunning(false) }
    }
    startOpenTickets()
  },[])
  async function run(){ setRunning(true); setResult(null); setError(''); const timer=window.setInterval(()=>api<Event[]>('/api/agent-events?limit=80').then(setEvents).catch(()=>{}),1200); try { const team=await api<TeamResult>(`/api/tickets/${selected}/run`,{method:'POST'}); setResult(team); const status=team.human_approval_required?'in_progress':'resolved'; const note=team.human_approval_required?`Agent team completed run ${team.run_id}; findings flagged for human approval. Ticket remains unresolved.`:`Agent team completed run ${team.run_id}; no human approval was required and the agent resolved the ticket.`; await api(`/api/tickets/${selected}/status`,{method:'POST',body:JSON.stringify({status,note})}); await refresh() } catch(e){ setError(e instanceof Error?e.message:'Agent run failed') } finally { window.clearInterval(timer); setRunning(false) } }
  async function approve(){ if(!window.confirm('Approve invoice 501 for $840? This will deduct the money, mark the invoice paid, and finish ticket #101.')) return; setPayment(true); setError(''); try { await api('/api/payments/approve',{method:'POST',body:JSON.stringify({kind:'invoice',ref_id:501,amount:840,account:'checking',approved_by:'Human supervisor'})}); await api('/api/tickets/101/status',{method:'POST',body:JSON.stringify({status:'resolved',note:'Human supervisor approved invoice 501 for $840; payment recorded and invoice marked paid.'})}); await refresh() } catch(e){ setError(e instanceof Error?e.message:'Payment refused') } finally { setPayment(false) } }
  async function resolveTicket(){ if(!active || !window.confirm(`Mark ticket #${active.id} resolved? Do this only after reviewing the agent findings and completing any approved action.`)) return; setError(''); try { await api(`/api/tickets/${active.id}/status`,{method:'POST',body:JSON.stringify({status:'resolved',note:`Human supervisor approved resolution after reviewing agent findings for run ${result?.run_id || 'manual review'}.`})}); await refresh() } catch(e){ setError(e instanceof Error?e.message:'Could not resolve ticket') } }
  return <div className="app"><header className="topbar"><div className="brand"><div className="brand-mark"><Shirt size={20}/></div><div><div className="kicker">CAMPUS CUSTOMS</div><h1>Agent desk</h1></div></div><div className="top-meta"><span className="live-dot"/> Local operations board <button className="icon-button" onClick={refresh} title="Refresh"><RotateCcw size={16}/></button></div></header>
    <main className="shell"><section className="hero"><div><p className="eyebrow">Supervisor dashboard · Problem 8</p><h2>Resolve the work queue<br/><em>with evidence, not guesswork.</em></h2><p className="hero-copy">Select a ticket, run the focused agent team, and watch every decision leave an auditable trail through MCP.</p></div><div className="hero-badge"><ShieldCheck size={19}/><span>MCP-grounded<br/><strong>Human in the loop</strong></span></div></section>
      {error && <div className="error">{error}</div>}
      <section className="stat-grid"><div className="stat"><span>Open queue</span><strong>{tickets.filter(t=>t.status==='open').length}<small> / 3 tickets</small></strong><Layers3 size={20}/></div><div className="stat"><span>Checking balance</span><strong>{balance ? `$${balance.balance.toLocaleString(undefined,{minimumFractionDigits:2})}` : '—'}</strong><CircleDollarSign size={20}/></div><div className="stat"><span>Agent activity</span><strong>{events.length}<small> audit events</small></strong><Activity size={20}/></div></section>
      <div className="workspace"><aside className="ticket-list"><div className="section-heading"><div><p className="eyebrow">Work queue</p><h3>Three tickets</h3></div><span className="count-pill">{tickets.length}</span></div>{loading && !tickets.length ? <div className="loading">Loading tickets…</div> : tickets.map(t=><button className={`ticket-card ${selected===t.id?'selected':''}`} key={t.id} onClick={()=>{setSelected(t.id);setResult(null)}}><div className="ticket-number">#{t.id}</div><div className="ticket-info"><strong>{t.subject}</strong><span>{t.requester}</span><small>{t.type.replace('_',' ')}</small></div><span className={`status ${t.status}`}>{t.status}</span><ArrowRight size={16}/></button>)}</aside>
        <section className="detail"><div className="detail-head"><div><p className="eyebrow">Selected ticket · #{active?.id}</p><h3>{active?.subject || 'Select a ticket'}</h3><p className="muted">{active?.notes}</p></div><button className="run-button" disabled={running||!active} onClick={run}>{running?<><LoaderCircle className="spin" size={17}/> Team running</>:<><Play size={16}/> Run team</>}</button></div><div className="run-strip"><div><Clock3 size={17}/><span>{running?'Live run in progress':'Ready for a focused run'}</span></div><span>Agents use MCP tools only</span></div><div className="section-heading agents-heading"><div><p className="eyebrow">Live collaboration</p><h3>Agent activity</h3></div>{running&&<span className="pulse-label"><i/> Streaming</span>}</div><div className="event-feed">{activeEvents.length ? activeEvents.slice(-8).map((e,i)=><div className="event" key={`${e.run_id}-${e.step}-${i}`}><div className="event-icon"><UserRound size={15}/></div><div><strong>{e.role.replace('_',' ')}</strong><span>{e.event_type.replace('_',' ')}</span><p>{formatEventDetails(e.details)}</p></div><time>{new Date(e.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</time></div>) : <div className="empty-feed"><Activity size={25}/><strong>No run activity yet</strong><span>Choose a ticket and run the focused team to see the work appear here.</span></div>}</div>{result&&<><div className="section-heading"><div><p className="eyebrow">Run complete · {result.run_id.slice(0,8)}</p><h3>What the team did</h3></div><CheckCircle2 className="success-icon" size={22}/></div><div className="findings">{result.findings.map((f,i)=><article className="finding" key={`${f.role}-${i}`}><div className="finding-top"><strong>{f.role.replace('_',' ')}</strong></div><p>{f.recommendation}</p><small>Next: {f.proposed_next_step}</small></article>)}</div><div className="plan"><strong>Boss summary</strong><p>{result.final_plan}</p></div></>}
          {active?.id===101 && active.payment_status==='paid' && <div className="payment-card paid-card"><div><p className="eyebrow">Payment complete</p><h4>Invoice 501 is paid</h4><p className="muted">The $840 payment for ticket #101 was approved and recorded. Duplicate payments are blocked.</p></div><CheckCircle2 className="success-icon" size={22}/></div>}
          {active?.id===101 && active.payment_status!=='paid' && <div className="payment-card"><div><p className="eyebrow">Payment authorized</p><h4>Pay invoice 501</h4><p className="muted">Funds are available for this $840 invoice, so the agent is authorized to pay it. Duplicate payments are refused.</p></div><button className="secondary-button" onClick={approve} disabled={payment}>{payment?<LoaderCircle className="spin" size={16}/>:<CircleDollarSign size={16}/>} {payment?'Paying…':'Pay $840 invoice'}</button></div>}
          {active?.status === 'in_progress' && <div className="resolve-card"><div><p className="eyebrow">Final human decision</p><h4>{active.id===103?'Ticket 103 needs your review':'Ready to close this ticket?'}</h4><p className="muted">{active.id===103?'Only 8 of 20 medium hoodies are in stock. No bulk discount is authorized, and approving different sale terms requires a human decision.':'Review the findings and complete any required action before closing this ticket.'}</p></div><button className="resolve-button" onClick={resolveTicket}><CheckCircle2 size={16}/> Mark resolved</button></div>}
        </section></div></main><footer>Campus Customs · Evidence-led operations · Human approval required for money</footer></div>
}
createRoot(document.getElementById('root')!).render(<StrictMode><App/></StrictMode>)
