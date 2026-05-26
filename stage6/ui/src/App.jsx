import { useState, useEffect, useRef, useCallback } from 'react'

const AGENTS = {
  chichi: {
    name: 'ChiChi',
    role: 'Director',
    color: '#4f8ef7',
    sprite: 'Claude-1',
    deskX: 48.9,
    deskY: 52.9,
    deskFacing: 'rear-right',
  },
  nezuko: {
    name: 'Nezuko',
    role: 'Researcher',
    color: '#f472b6',
    sprite: 'employee-2',
    deskX: 37.9,
    deskY: 68.2,
    deskFacing: 'rear-right',
  },
  mikasa: {
    name: 'Mikasa',
    role: 'Executor',
    color: '#ef4444',
    sprite: 'security-audit-1',
    deskX: 65.9,
    deskY: 75.8,
    deskFacing: 'rear-right',
  },
}

const FURNITURE = [
  { id: 'desk-1a', src: '/sprites/furniture/standing-desk-left-rear.png',   x: 42.4, y: 50.4, z: 50, w: 80 },
  { id: 'desk-1b', src: '/sprites/furniture/standing-desk-left-front.png',  x: 46.7, y: 53.0, z: 53, w: 80 },
  { id: 'desk-1c', src: '/sprites/furniture/standing-desk-right-front.png', x: 39.9, y: 55.2, z: 55, w: 80 },
  { id: 'desk-2a', src: '/sprites/furniture/standing-desk-left-rear.png',   x: 31.4, y: 64.8, z: 65, w: 80 },
  { id: 'desk-2b', src: '/sprites/furniture/standing-desk-left-front.png',  x: 35.4, y: 67.5, z: 68, w: 80 },
  { id: 'desk-2c', src: '/sprites/furniture/standing-desk-right-front.png', x: 27.9, y: 70.0, z: 70, w: 80 },
  { id: 'desk-3a', src: '/sprites/furniture/standing-desk-left-rear.png',   x: 59.0, y: 73.7, z: 74, w: 80 },
  { id: 'desk-3b', src: '/sprites/furniture/standing-desk-left-front.png',  x: 62.6, y: 76.0, z: 76, w: 80 },
  { id: 'desk-3c', src: '/sprites/furniture/standing-desk-right-front.png', x: 55.4, y: 78.7, z: 79, w: 80 },
  { id: 'desk-3d', src: '/sprites/furniture/standing-desk-right-rear.png',  x: 66.6, y: 71.1, z: 71, w: 80 },
  { id: 'filing',  src: '/sprites/furniture/filling-closed.png',            x: 45.0, y: 56.5, z: 57, w: 40 },
  { id: 'plant-2', src: '/sprites/decoration/snake-plant.png',              x: 43.2, y: 37.9, z: 38, w: 28 },
  { id: 'plant-3', src: '/sprites/decoration/money-tree.png',               x: 32.0, y: 71.2, z: 71, w: 28 },
  { id: 'plant-1', src: '/sprites/decoration/monstera-plant.png',           x: 91.9, y: 64.7, z: 65, w: 36 },
  { id: 'printer', src: '/sprites/decoration/printer-working.png',          x: 85.4, y: 56.8, z: 57, w: 36 },
]

const WALK_PATHS = {
  'chichi-to-nezuko': [
    { x: 41.6, y: 62.7, facing: 'front-left' },
    { x: 37.9, y: 68.2, facing: 'front-left' },
  ],
  'chichi-from-nezuko': [
    { x: 41.6, y: 62.7, facing: 'rear-right' },
    { x: 48.9, y: 52.9, facing: 'rear-right' },
  ],
  'chichi-to-mikasa': [
    { x: 59.5, y: 57.1, facing: 'rear-right' },
    { x: 68.7, y: 66.2, facing: 'rear-right' },
    { x: 65.9, y: 75.8, facing: 'front-right' },
  ],
  'chichi-from-mikasa': [
    { x: 68.7, y: 66.2, facing: 'rear-left' },
    { x: 59.5, y: 57.1, facing: 'rear-left' },
    { x: 48.9, y: 52.9, facing: 'rear-left' },
  ],
}

function getSpriteSrc(spriteName, facing) {
  return `/sprites/characters/${spriteName}-${facing}.png`
}

// Room renders at 800x600 internally
// We scale everything relative to that
function useRoomScale(containerRef) {
  const [scale, setScale] = useState(1)
  useEffect(() => {
    const update = () => {
      if (!containerRef.current) return
      const { width } = containerRef.current.getBoundingClientRect()
      setScale(width / 800)
    }
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [containerRef])
  return scale
}

function FurnitureLayer({ scale }) {
  return (
    <>
      {FURNITURE.map(item => (
        <img
          key={item.id} src={item.src} alt=""
          draggable={false}
          style={{
            position: 'absolute',
            left: `${item.x}%`,
            top: `${item.y}%`,
            width: `${item.w * scale}px`,
            height: 'auto',
            transform: 'translate(-50%, -100%)',
            zIndex: item.z,
            pointerEvents: 'none',
            userSelect: 'none',
          }}
        />
      ))}
    </>
  )
}

function Character({ agentKey, status, position, facing, scale }) {
  const cfg = AGENTS[agentKey]
  const on = status === 'active' || status === 'thinking'
  const complete = status === 'complete'
  const zIndex = Math.round(position.y * 10) + 100
  const charHeight = Math.round(90 * scale)

  return (
    <div style={{
      position: 'absolute',
      left: `${position.x}%`,
      top: `${position.y}%`,
      transform: 'translate(-50%, -100%)',
      transition: 'left 1.0s cubic-bezier(0.4,0,0.2,1), top 1.0s cubic-bezier(0.4,0,0.2,1)',
      zIndex,
      pointerEvents: 'none',
    }}>
      <div style={{
        position: 'absolute', bottom: '100%', left: '50%',
        transform: 'translateX(-50%)', textAlign: 'center',
        whiteSpace: 'nowrap', marginBottom: 4,
      }}>
        {on && (
          <div style={{
            background: cfg.color, borderRadius: 10, padding: '2px 8px',
            fontSize: Math.max(8, 9 * scale), fontFamily: 'monospace',
            color: 'white', fontWeight: 700, letterSpacing: 1, marginBottom: 2,
            animation: 'statusPulse 1s ease infinite', display: 'inline-block',
          }}>
            {status === 'thinking' ? 'THINKING...' : 'WORKING'}
          </div>
        )}
        <div style={{
          fontSize: Math.max(8, 11 * scale), fontFamily: 'monospace',
          color: cfg.color, fontWeight: 700, display: 'block',
          textShadow: '0 0 8px rgba(0,0,0,1), 0 1px 4px rgba(0,0,0,1)',
        }}>
          {cfg.name}
        </div>
      </div>
      <img
        src={getSpriteSrc(cfg.sprite, facing)}
        alt={cfg.name}
        style={{
          height: `${charHeight}px`,
          width: 'auto',
          imageRendering: 'auto',
          filter: on
            ? `drop-shadow(0 0 ${8*scale}px ${cfg.color}) brightness(1.15)`
            : complete ? `drop-shadow(0 0 ${6*scale}px #22c55e)` : 'none',
          transition: 'filter 0.4s ease',
        }}
      />
      {complete && (
        <div style={{
          position: 'absolute', top: `-${3*charHeight/90}em`, right: '-0.5em',
          fontSize: 16 * scale, animation: 'fadeIn 0.3s ease',
        }}>✓</div>
      )}
    </div>
  )
}

function DataOrb({ visible, x, y, color, scale }) {
  if (!visible) return null
  const size = Math.round(24 * scale)
  return (
    <div style={{
      position: 'absolute', left: `${x}%`, top: `${y}%`,
      transform: 'translate(-50%, -50%)', zIndex: 500,
      pointerEvents: 'none',
      animation: 'orbFloat 0.4s ease infinite alternate',
    }}>
      <div style={{
        width: size, height: size, borderRadius: '50%',
        background: `radial-gradient(circle at 35% 35%, white, ${color})`,
        boxShadow: `0 0 ${size}px ${color}, 0 0 ${size*2}px ${color}88`,
      }} />
    </div>
  )
}

export default function App() {
  const [statuses, setStatuses] = useState({ chichi: 'idle', nezuko: 'idle', mikasa: 'idle' })
  const [positions, setPositions] = useState({
    chichi: { x: AGENTS.chichi.deskX, y: AGENTS.chichi.deskY },
    nezuko: { x: AGENTS.nezuko.deskX, y: AGENTS.nezuko.deskY },
    mikasa: { x: AGENTS.mikasa.deskX, y: AGENTS.mikasa.deskY },
  })
  const [facings, setFacings] = useState({
    chichi: AGENTS.chichi.deskFacing,
    nezuko: AGENTS.nezuko.deskFacing,
    mikasa: AGENTS.mikasa.deskFacing,
  })
  const [orb, setOrb] = useState({ visible: false, x: 0, y: 0, color: '#fff' })
  const [log, setLog] = useState([])
  const [finalAnswer, setFinalAnswer] = useState('')
  const [task, setTask] = useState('')
  const [running, setRunning] = useState(false)
  const [connected, setConnected] = useState(false)
  const [timeOfDay] = useState(() => {
    const h = new Date().getHours()
    return h >= 7 && h < 19 ? 'day' : 'night'
  })

  const wsRef = useRef(null)
  const logRef = useRef(null)
  const roomRef = useRef(null)
  const queueRef = useRef([])
  const processingRef = useRef(false)
  const scale = useRoomScale(roomRef)

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [log])

  const addLog = useCallback((agent, msg) => {
    const colors = { chichi: '#4f8ef7', nezuko: '#f472b6', mikasa: '#ef4444', system: '#6b7280' }
    const names = { chichi: 'ChiChi', nezuko: 'Nezuko', mikasa: 'Mikasa', system: 'SYSTEM' }
    setLog(prev => [...prev.slice(-60), {
      id: Date.now() + Math.random(), agent, msg,
      color: colors[agent] || '#6b7280',
      name: names[agent] || 'SYSTEM',
      time: new Date().toLocaleTimeString()
    }])
  }, [])

  const processQueue = useCallback(() => {
    if (processingRef.current || queueRef.current.length === 0) return
    processingRef.current = true
    const step = queueRef.current.shift()
    step(() => { processingRef.current = false; processQueue() })
  }, [])

  const enqueue = useCallback((fn) => {
    queueRef.current.push(fn)
    processQueue()
  }, [processQueue])

  const enqueueWalkPath = useCallback((pathKey) => {
    const path = WALK_PATHS[pathKey]
    if (!path) return
    path.forEach(wp => {
      enqueue(done => {
        setFacings(f => ({ ...f, chichi: wp.facing }))
        setPositions(p => ({ ...p, chichi: { x: wp.x, y: wp.y } }))
        setTimeout(done, 1050)
      })
    })
  }, [enqueue])

  const enqueueOrb = useCallback((x, y, color) => {
    enqueue(done => {
      setOrb({ visible: true, x, y, color })
      setTimeout(() => { setOrb(o => ({ ...o, visible: false })); done() }, 900)
    })
  }, [enqueue])

  const enqueueDelay = useCallback((ms) => {
    enqueue(done => setTimeout(done, ms))
  }, [enqueue])

  const enqueueSetStatus = useCallback((agent, status) => {
    enqueue(done => { setStatuses(p => ({ ...p, [agent]: status })); done() })
  }, [enqueue])

  const connect = useCallback(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws`)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => { setConnected(false); setTimeout(connect, 3000) }
    ws.onerror = () => setConnected(false)
    ws.onmessage = (e) => {
      try {
        const ev = JSON.parse(e.data)
        const { agent, status, message, data, handoff_to } = ev
        if (agent !== 'system') {
          setStatuses(p => ({ ...p, [agent]: status }))
          addLog(agent, message)
          if (agent === 'chichi' && status === 'active' && handoff_to && handoff_to !== 'chichi') {
            const target = AGENTS[handoff_to]
            if (target) {
              enqueueWalkPath(`chichi-to-${handoff_to}`)
              enqueueDelay(200)
              enqueueOrb(target.deskX, target.deskY - 8, target.color)
              enqueueDelay(400)
              enqueueWalkPath(`chichi-from-${handoff_to}`)
              enqueueSetStatus('chichi', 'thinking')
            }
          }
          if (status === 'complete' && data?.final_answer) setFinalAnswer(data.final_answer)
        } else {
          addLog('system', message)
          if (status === 'done') {
            setRunning(false)
            enqueue(done => {
              setPositions(p => ({ ...p, chichi: { x: AGENTS.chichi.deskX, y: AGENTS.chichi.deskY } }))
              setFacings(f => ({ ...f, chichi: AGENTS.chichi.deskFacing }))
              setTimeout(done, 1100)
            })
            enqueue(done => { setStatuses({ chichi: 'idle', nezuko: 'idle', mikasa: 'idle' }); done() })
          }
        }
      } catch (err) { console.error(err) }
    }
  }, [addLog, enqueue, enqueueWalkPath, enqueueOrb, enqueueDelay, enqueueSetStatus])

  useEffect(() => { connect(); return () => wsRef.current?.close() }, [])

  const send = () => {
    if (!task.trim() || !connected || running) return
    setRunning(true)
    setFinalAnswer('')
    setLog([])
    queueRef.current = []
    processingRef.current = false
    setStatuses({ chichi: 'idle', nezuko: 'idle', mikasa: 'idle' })
    setPositions({
      chichi: { x: AGENTS.chichi.deskX, y: AGENTS.chichi.deskY },
      nezuko: { x: AGENTS.nezuko.deskX, y: AGENTS.nezuko.deskY },
      mikasa: { x: AGENTS.mikasa.deskX, y: AGENTS.mikasa.deskY },
    })
    setFacings({
      chichi: AGENTS.chichi.deskFacing,
      nezuko: AGENTS.nezuko.deskFacing,
      mikasa: AGENTS.mikasa.deskFacing,
    })
    wsRef.current?.send(JSON.stringify({ task }))
    setTask('')
  }

  const bgImage = timeOfDay === 'day' ? '/rooms/office-day.png' : '/rooms/office-night.png'

  return (
    <div style={{
      height: '100vh', background: '#07071a',
      color: '#e5e7eb', fontFamily: 'monospace',
      display: 'flex', flexDirection: 'column',
      padding: '12px', gap: '10px', overflow: 'hidden',
    }}>
      <style>{`
        @keyframes fadeIn { from{opacity:0;transform:translateY(3px)} to{opacity:1;transform:none} }
        @keyframes statusPulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
        @keyframes orbFloat { from{transform:translate(-50%,-50%) scale(1)} to{transform:translate(-50%,-50%) scale(1.3)} }
        @keyframes connPulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        * { box-sizing: border-box }
        ::-webkit-scrollbar { width: 4px }
        ::-webkit-scrollbar-track { background: #050510 }
        ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 2px }
        textarea { outline: none; resize: none; }
      `}</style>

      <div style={{ textAlign: 'center', flexShrink: 0 }}>
        <div style={{
          fontSize: 20, fontWeight: 900, letterSpacing: 4,
          background: 'linear-gradient(90deg,#4f8ef7,#f472b6,#ef4444)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>HOMELAB AI COMMAND CENTER</div>
        <div style={{
          fontSize: 10, marginTop: 3, letterSpacing: 2,
          color: connected ? '#22c55e' : '#ef4444',
          animation: connected ? 'none' : 'connPulse 1.5s infinite',
        }}>
          {connected ? '● CONNECTED — AGENTS STANDING BY' : '● CONNECTING...'}
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', gap: '10px', overflow: 'hidden', minHeight: 0 }}>

        {/* Office - 800:600 aspect ratio, scale everything inside */}
        <div style={{
          flex: 1, display: 'flex', alignItems: 'flex-start',
          justifyContent: 'center', overflow: 'hidden',
        }}>
          <div
            ref={roomRef}
            style={{
              position: 'relative',
              width: '100%',
              paddingBottom: '75%', // 600/800 = 75%
              borderRadius: 12,
              overflow: 'hidden',
              border: '1px solid rgba(55,65,81,0.3)',
            }}
          >
            <img
              src={bgImage} alt="Office" draggable={false}
              style={{
                position: 'absolute', top: 0, left: 0,
                width: '100%', height: '100%',
                objectFit: 'fill',
                userSelect: 'none', zIndex: 0,
              }}
            />
            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
              <FurnitureLayer scale={scale} />
              {Object.keys(AGENTS).map(key => (
                <Character
                  key={key} agentKey={key}
                  status={statuses[key]} position={positions[key]}
                  facing={facings[key]} scale={scale}
                />
              ))}
              <DataOrb visible={orb.visible} x={orb.x} y={orb.y} color={orb.color} scale={scale} />
            </div>
            <div style={{
              position: 'absolute', bottom: 8, left: 12,
              fontSize: 9, letterSpacing: 2,
              color: 'rgba(255,255,255,0.25)', zIndex: 300,
            }}>
              {timeOfDay === 'day' ? '☀ DAY MODE' : '🌙 NIGHT MODE'}
            </div>
          </div>
        </div>

        {/* Chat panel */}
        <div style={{
          width: 300, display: 'flex', flexDirection: 'column',
          background: 'rgba(5,5,20,0.95)',
          border: '1px solid rgba(55,65,81,0.4)',
          borderRadius: 12, overflow: 'hidden', flexShrink: 0,
        }}>
          <div style={{
            padding: '10px 14px', flexShrink: 0,
            borderBottom: '1px solid rgba(55,65,81,0.4)',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span style={{ fontSize: 14, color: '#4b5563' }}>#</span>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#e5e7eb', letterSpacing: 1 }}>command-center</span>
            <div style={{ marginLeft: 'auto', fontSize: 9, color: finalAnswer ? '#a78bfa' : '#4b5563' }}>
              {finalAnswer ? '✦ READY' : 'AWAITING'}
            </div>
          </div>

          <div style={{
            padding: '8px 14px', flexShrink: 0,
            borderBottom: '1px solid rgba(55,65,81,0.2)',
            display: 'flex', gap: 6, flexWrap: 'wrap',
          }}>
            {Object.keys(AGENTS).map(key => {
              const cfg = AGENTS[key]
              const on = statuses[key] === 'active' || statuses[key] === 'thinking'
              const done = statuses[key] === 'complete'
              return (
                <div key={key} style={{
                  display: 'flex', alignItems: 'center', gap: 4,
                  padding: '2px 8px', borderRadius: 20,
                  background: on ? `${cfg.color}22` : done ? '#22c55e22' : 'rgba(55,65,81,0.2)',
                  border: `1px solid ${on ? cfg.color : done ? '#22c55e' : 'rgba(55,65,81,0.3)'}`,
                  fontSize: 9, transition: 'all 0.3s',
                }}>
                  <div style={{
                    width: 6, height: 6, borderRadius: '50%',
                    background: on ? cfg.color : done ? '#22c55e' : '#374151',
                    animation: on ? 'connPulse 1s infinite' : 'none',
                  }}/>
                  <span style={{ color: on ? cfg.color : done ? '#22c55e' : '#6b7280', fontWeight: 700 }}>
                    {cfg.name}
                  </span>
                </div>
              )
            })}
          </div>

          <div ref={logRef} style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
            {log.length === 0 ? (
              <div style={{ padding: '20px 14px', color: '#374151', fontSize: 11, textAlign: 'center', lineHeight: 1.6 }}>
                <div style={{ fontSize: 24, marginBottom: 8 }}>💬</div>
                Type a task below to deploy<br/>ChiChi, Nezuko and Mikasa
              </div>
            ) : (
              log.map(e => (
                <div key={e.id} style={{
                  padding: '6px 14px', animation: 'fadeIn 0.2s ease',
                  display: 'flex', gap: 8, alignItems: 'flex-start',
                }}>
                  <div style={{
                    width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                    background: e.agent === 'system' ? 'rgba(55,65,81,0.4)' : `${e.color}33`,
                    border: `1px solid ${e.agent === 'system' ? 'rgba(55,65,81,0.3)' : e.color}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 10, color: e.color, fontWeight: 700,
                  }}>
                    {e.name[0]}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 2 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: e.color }}>{e.name}</span>
                      <span style={{ fontSize: 9, color: '#374151' }}>{e.time}</span>
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af', lineHeight: 1.4, wordBreak: 'break-word' }}>
                      {e.msg}
                    </div>
                  </div>
                </div>
              ))
            )}
            {finalAnswer && (
              <div style={{
                margin: '8px 14px', padding: '10px 12px',
                background: 'rgba(167,139,250,0.08)',
                border: '1px solid rgba(167,139,250,0.3)',
                borderRadius: 8, animation: 'fadeIn 0.5s ease',
              }}>
                <div style={{ fontSize: 9, color: '#a78bfa', fontWeight: 700, letterSpacing: 1, marginBottom: 6 }}>
                  ✦ CHICHI'S REPORT
                </div>
                <div style={{ fontSize: 11, color: '#d1d5db', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                  {finalAnswer}
                </div>
              </div>
            )}
          </div>

          <div style={{ padding: '10px 12px', flexShrink: 0, borderTop: '1px solid rgba(55,65,81,0.3)' }}>
            <div style={{
              background: 'rgba(15,15,30,0.8)',
              border: `1px solid ${running ? 'rgba(79,142,247,0.4)' : 'rgba(55,65,81,0.4)'}`,
              borderRadius: 8, overflow: 'hidden',
            }}>
              <textarea
                value={task}
                onChange={e => setTask(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
                placeholder="Message #command-center..."
                disabled={running || !connected}
                rows={2}
                style={{
                  width: '100%', background: 'transparent', border: 'none',
                  color: '#e5e7eb', fontFamily: 'monospace',
                  fontSize: 12, lineHeight: 1.5, padding: '8px 10px',
                }}
              />
              <div style={{
                display: 'flex', justifyContent: 'flex-end',
                padding: '4px 8px 6px',
                borderTop: '1px solid rgba(55,65,81,0.2)',
              }}>
                <button onClick={send} disabled={!task.trim() || running || !connected} style={{
                  padding: '4px 14px',
                  background: !task.trim() || running || !connected ? 'rgba(79,142,247,0.2)' : '#4f8ef7',
                  border: 'none', borderRadius: 5, color: 'white',
                  fontFamily: 'monospace', fontSize: 11, fontWeight: 700,
                  cursor: running || !task.trim() ? 'not-allowed' : 'pointer',
                  letterSpacing: 1,
                }}>
                  {running ? '⚙' : '⏎ SEND'}
                </button>
              </div>
            </div>
            <div style={{ fontSize: 9, color: '#374151', marginTop: 4, textAlign: 'center' }}>
              Enter to send · Shift+Enter for new line
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
