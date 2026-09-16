import { useState, useRef } from 'react'

const EXAMPLES = [
  { tag: 'HAPPY PATH',      query: '2 blue shirts, size M, delivered to 560001' },
  { tag: 'OUT OF STOCK',    query: '5 red jackets in size XL to 400001' },
  { tag: 'BULK DISCOUNT',   query: '10 white t-shirts, size L, to 110001' },
  { tag: 'BAD PINCODE',     query: '1 trouser size 32 to pincode 999999' },
  { tag: 'UNKNOWN PRODUCT', query: '3 purple hats size M to 600001' },
]

const TOOLS = [
  { name: 'check_stock',  src: 'inventory.json' },
  { name: 'price_order',  src: 'discounts.json' },
  { name: 'delivery_eta', src: 'shipping.json' },
]

function stepClass(type, result) {
  if (type === 'thought') return 's-thought'
  if (type === 'action')  return 's-action'
  if (type === 'observation') return result?.error ? 's-obs-err' : 's-obs-ok'
  return 's-thought'
}

function stepLabel(type, hasErr) {
  if (type === 'thought')     return 'THOUGHT'
  if (type === 'action')      return 'ACTION'
  if (type === 'observation') return hasErr ? 'ERROR' : 'OBSERVATION'
  return type.toUpperCase()
}

function StepCard({ step, index }) {
  const hasErr = step.result?.error
  const cls = stepClass(step.type, step.result)

  return (
    <div className={`step-card ${cls}`}>
      <div className="step-header">
        <span className="step-num">{String(index + 1).padStart(2, '0')}</span>
        <span className="step-type-badge">{stepLabel(step.type, hasErr)}</span>
        {step.tool && <span className="step-tool-tag">{step.tool}</span>}
      </div>

      {step.type === 'thought' && (
        <div className="step-body">{step.content}</div>
      )}

      {step.type === 'action' && step.args && (
        <>
          <div className="code-lbl">ARGUMENTS</div>
          <div className="code-blk">{JSON.stringify(step.args, null, 2)}</div>
        </>
      )}

      {step.type === 'observation' && step.result && (
        <>
          <div className="code-lbl">{hasErr ? 'ERROR RESPONSE' : 'TOOL RESPONSE'}</div>
          <div className="code-blk">{JSON.stringify(step.result, null, 2)}</div>
        </>
      )}
    </div>
  )
}

function renderMarkdown(text) {
  return text.split('\n').map((line, li) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/)
    return (
      <span key={li}>
        {parts.map((p, i) =>
          p.startsWith('**') && p.endsWith('**')
            ? <strong key={i}>{p.slice(2, -2)}</strong>
            : p
        )}
        {li < text.split('\n').length - 1 && <br />}
      </span>
    )
  })
}

function FinalCard({ answer, toolsChain, apiCalls }) {
  return (
    <div className="final-card">
      <div className="final-lbl">FINAL ANSWER</div>
      <div className="final-answer-text">{renderMarkdown(answer)}</div>
      <div className="final-footer">
        <div className="tool-chain">
          {toolsChain.length === 0
            ? <span className="tc-item" style={{ color: '#FF50A0', borderColor: '#FF50A0' }}>no tools reached</span>
            : toolsChain.map((t, i) => (
                <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span className="tc-item">{t}</span>
                  {i < toolsChain.length - 1 && <span className="tc-arrow">›</span>}
                </span>
              ))
          }
        </div>
        <div className="final-stats">
          <span className="f-stat"><span className="f-stat-dot" />{toolsChain.length} tool{toolsChain.length !== 1 ? 's' : ''}</span>
          <span className="f-stat"><span className="f-stat-dot" />{apiCalls} LLM call{apiCalls !== 1 ? 's' : ''}</span>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [query, setQuery]       = useState('')
  const [steps, setSteps]       = useState([])
  const [finalData, setFinalData] = useState(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError]       = useState(null)
  const abortRef = useRef(null)

  async function runAgent(overrideQuery) {
    const q = (overrideQuery ?? query).trim()
    if (!q) return

    if (abortRef.current) abortRef.current.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    setIsRunning(true)
    setSteps([])
    setFinalData(null)
    setError(null)

    let buf = ''
    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
        signal: ctrl.signal,
      })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)

      const reader  = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const parts = buf.split('\n\n')
        buf = parts.pop()
        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6)
          if (raw === '[DONE]') continue
          try {
            const evt = JSON.parse(raw)
            if (evt.type === 'start')  continue
            if (evt.type === 'final')  { setFinalData(evt); continue }
            setSteps(prev => [...prev, evt])
          } catch { /* ignore */ }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message)
    } finally {
      setIsRunning(false)
    }
  }

  const [traceOpen, setTraceOpen] = useState(false)

  const busy = isRunning
  const hasTrace = steps.length > 0 || isRunning || finalData

  return (
    <>
      {/* ── Navigation ── */}
      <nav className="nav">
        <span className="nav-product">AI Engineering · Project 4</span>
        <div className="nav-right">
          <span className="nav-tag">LEVEL 2 MEDIUM</span>
          {isRunning && <span className="nav-dot" />}
        </div>
      </nav>

      <div className="page">

        {/* ── Hero ── */}
        <header className="hero">
          <div className="hero-left">
            <div className="hero-eyebrow">BUILDING AGENTS</div>
            <h1>Store Assistant<br /><em>Agent</em></h1>           
          </div>
          <div className="hero-right"></div>
        </header>

        {/* ── Query ── */}
        <section className="query-section">
          <div className="section-label">CUSTOMER REQUEST</div>
          <div className="query-box">
            <label htmlFor="q">Describe what the customer wants to order</label>
            <div className="query-row">
              <input
                id="q"
                className="query-input"
                type="text"
                placeholder='e.g. "2 blue shirts, size M, delivered to 560001"'
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && runAgent()}
                disabled={busy}
              />
              <button
                className="run-btn"
                onClick={() => runAgent()}
                disabled={busy || !query.trim()}
              >
                {busy ? 'RUNNING' : 'RUN AGENT'}
                <span className="btn-arrow">{busy ? '…' : '›'}</span>
              </button>
            </div>

            <div className="ex-label">EXAMPLE SCENARIOS</div>
            <div className="examples">
              {EXAMPLES.map(ex => (
                <button
                  key={ex.tag}
                  className="ex-chip"
                  disabled={busy}
                  onClick={() => { setQuery(ex.query); runAgent(ex.query) }}
                >
                  {ex.tag}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* ── Error ── */}
        {error && (
          <div className="error-bar">
            <strong>ERROR</strong> {error}
          </div>
        )}

        {/* ── Final Answer — always visible ── */}
        {finalData && (
          <FinalCard
            answer={finalData.answer}
            toolsChain={finalData.tools_called ?? []}
            apiCalls={finalData.api_calls ?? 0}
          />
        )}

        {/* ── Trace — collapsible ── */}
        {hasTrace && (
          <section className="trace-section">
            <button
              className="trace-toggle"
              onClick={() => setTraceOpen(o => !o)}
            >
              <div className="trace-topbar">
                <div className="section-label" style={{ flex: 1, marginBottom: 0 }}>AGENT TRACE</div>
                <div className="trace-stats-row">
                  <span className="t-stat">Steps <strong>{steps.length}</strong></span>
                  {finalData && (
                    <>
                      <span className="t-stat">API calls <strong>{finalData.api_calls}</strong></span>
                      <span className="t-stat">Tools <strong>{finalData.tools_called?.length ?? 0}</strong></span>
                    </>
                  )}
                  <span className="trace-chevron">{traceOpen ? '▲' : '▼'}</span>
                </div>
              </div>
            </button>

            {traceOpen && (
              <div className="trace-list">
                {steps.map((s, i) => <StepCard key={i} step={s} index={i} />)}
                {isRunning && (
                  <div className="thinking-card">
                    <div className="spinner" />
                    <span>Agent is reasoning</span>
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {/* ── Footer ── */}
        <footer className="page-footer">
          <div className="footer-brand">
            <span>Store Assistant Agent</span>
          </div>
        </footer>
      </div>
    </>
  )
}
