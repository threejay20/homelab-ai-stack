import { useState, useEffect, useRef, useCallback } from 'react'

const AGENTS = {
  tribal_chief: {
    name: 'Tribal Chief',
    role: 'Director',
    color: '#4f8ef7',
    sprite: 'Claude-1',
    deskX: 48.9,
    deskY: 52.9,
    deskFacing: 'rear-right',
    voiceId: 'nPczCjzI2devNBz1zQrb',
  },
  nezuko: {
    name: 'Nezuko',
    role: 'Researcher',
    color: '#f472b6',
    sprite: 'employee-2',
    deskX: 25.0,
    deskY: 70.5,
    deskFacing: 'rear-left',
    voiceId: 'EXAVITQu4vr4xnSDxMaL',
  },
  mikasa: {
    name: 'Mikasa',
    role: 'Executor',
    color: '#ef4444',
    sprite: 'security-audit-1',
    deskX: 52.0,
    deskY: 80.5,
    deskFacing: 'rear-left',
    voiceId: 'Xb7hH8MSUJpSbSDYk0k2',
  },
  levi: {
    name: 'Levi',
    role: 'Security',
    color: '#22c55e',
    sprite: 'dev-1',
    deskX: 37.0,
    deskY: 66.5,
    deskFacing: 'rear-right',
    voiceId: 'JBFqnCBsd6RMkjVDRZzb',
  },
  eren: {
    name: 'Eren',
    role: 'DevOps',
    color: '#f59e0b',
    sprite: 'explore-1',
    deskX: 66.5,
    deskY: 74.5,
    deskFacing: 'rear-right',
    voiceId: 'IKne3meq5aSn9XLyUdCD',
  },
  armin: {
    name: 'Armin',
    role: 'Assistant',
    color: '#a78bfa',
    sprite: 'dev-2',
    deskX: 72.0,
    deskY: 63.0,
    deskFacing: 'front-right',
    voiceId: 'cgSgspJ2msm6clMCkdW9',
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
  'tribal_chief-to-nezuko': [
    { x: 41.6, y: 62.7, facing: 'front-left' },
    { x: 37.9, y: 68.2, facing: 'front-left' },
  ],
  'tribal_chief-from-nezuko': [
    { x: 41.6, y: 62.7, facing: 'rear-right' },
    { x: 48.9, y: 52.9, facing: 'rear-right' },
  ],
  'tribal_chief-to-mikasa': [
    { x: 59.5, y: 57.1, facing: 'rear-right' },
    { x: 68.7, y: 66.2, facing: 'rear-right' },
    { x: 65.9, y: 75.8, facing: 'front-right' },
  ],
  'tribal_chief-from-mikasa': [
    { x: 68.7, y: 66.2, facing: 'rear-left' },
    { x: 59.5, y: 57.1, facing: 'rear-left' },
    { x: 48.9, y: 52.9, facing: 'rear-left' },
  ],
  'tribal_chief-to-armin': [
    { x: 63.0, y: 58.0, facing: 'rear-right' },
    { x: 72.0, y: 63.0, facing: 'front-right' },
  ],
  'tribal_chief-from-armin': [
    { x: 63.0, y: 58.0, facing: 'rear-left' },
    { x: 48.9, y: 52.9, facing: 'rear-left' },
  ],
  'tribal_chief-to-levi': [
    { x: 55.0, y: 62.0, facing: 'rear-right' },
    { x: 57.0, y: 70.0, facing: 'rear-right' },
    { x: 55.2, y: 78.7, facing: 'front-right' },
  ],
  'tribal_chief-from-levi': [
    { x: 57.0, y: 70.0, facing: 'rear-left' },
    { x: 53.0, y: 62.0, facing: 'rear-left' },
    { x: 48.9, y: 52.9, facing: 'rear-left' },
  ],
  'tribal_chief-to-eren': [
    { x: 54.0, y: 60.0, facing: 'rear-right' },
    { x: 58.0, y: 67.0, facing: 'rear-right' },
    { x: 59.0, y: 73.7, facing: 'front-right' },
  ],
  'tribal_chief-from-eren': [
    { x: 56.0, y: 65.0, facing: 'rear-left' },
    { x: 52.0, y: 59.0, facing: 'rear-left' },
    { x: 48.9, y: 52.9, facing: 'rear-left' },
  ],
}

function getSpriteSrc(spriteName, facing) {
  return `/sprites/characters/${spriteName}-${facing}.png`
}

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
        <img key={item.id} src={item.src} alt="" draggable={false}
          style={{
            position: 'absolute', left: `${item.x}%`, top: `${item.y}%`,
            width: `${item.w * scale}px`, height: 'auto',
            transform: 'translate(-50%, -100%)', zIndex: item.z,
            pointerEvents: 'none', userSelect: 'none',
          }}
        />
      ))}
    </>
  )
}

function Character({ agentKey, status, position, facing, scale }) {
  const cfg = AGENTS[agentKey]
  const on = status === 'active' || status === 'thinking' || status === 'waiting' || status === 'processing'
  const complete = status === 'complete'
  const zIndex = Math.round(position.y * 10) + 100
  const charHeight = Math.round(90 * scale)
  return (
    <div style={{
      position: 'absolute', left: `${position.x}%`, top: `${position.y}%`,
      transform: 'translate(-50%, -100%)',
      transition: 'left 1.0s cubic-bezier(0.4,0,0.2,1), top 1.0s cubic-bezier(0.4,0,0.2,1)',
      zIndex, pointerEvents: 'none',
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
            {status === 'thinking' ? 'THINKING...' : status === 'waiting' ? 'WAITING...' : status === 'processing' ? 'PROCESSING...' : 'WORKING'}
          </div>
        )}
        <div style={{
          fontSize: Math.max(8, 11 * scale), fontFamily: 'monospace',
          color: cfg.color, fontWeight: 700, display: 'block',
          textShadow: '0 0 8px rgba(0,0,0,1), 0 1px 4px rgba(0,0,0,1)',
        }}>
          {cfg.name} <span style={{fontSize: Math.max(7, 9 * scale), opacity: 0.8}}>({cfg.role})</span>
        </div>
      </div>
      <img src={getSpriteSrc(cfg.sprite, facing)} alt={cfg.name}
        style={{
          height: `${charHeight}px`, width: 'auto', imageRendering: 'auto',
          filter: on ? `drop-shadow(0 0 ${8*scale}px ${cfg.color}) brightness(1.15)`
            : complete ? `drop-shadow(0 0 ${6*scale}px #22c55e)` : 'none',
          transition: 'filter 0.4s ease',
        }}
      />
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
      pointerEvents: 'none', animation: 'orbFloat 0.4s ease infinite alternate',
    }}>
      <div style={{
        width: size, height: size, borderRadius: '50%',
        background: `radial-gradient(circle at 35% 35%, white, ${color})`,
        boxShadow: `0 0 ${size}px ${color}, 0 0 ${size*2}px ${color}88`,
      }} />
    </div>
  )
}

function MicButton({ listening, onClick, disabled }) {
  return (
    <button onClick={onClick} disabled={disabled}
      title={listening ? 'Stop listening' : 'Speak to Tribal Chief'}
      style={{
        width: 36, height: 36, borderRadius: '50%',
        border: `2px solid ${listening ? '#ef4444' : 'rgba(79,142,247,0.5)'}`,
        background: listening ? 'rgba(239,68,68,0.15)' : 'rgba(79,142,247,0.1)',
        color: listening ? '#ef4444' : '#4f8ef7',
        cursor: disabled ? 'not-allowed' : 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 16, flexShrink: 0, transition: 'all 0.2s',
        animation: listening ? 'micPulse 1s ease infinite' : 'none',
      }}
    >
      {listening ? '⏹' : '🎤'}
    </button>
  )
}

export default function App() {
  const [statuses, setStatuses] = useState({ tribal_chief: 'idle', nezuko: 'idle', mikasa: 'idle', levi: 'idle', eren: 'idle', armin: 'idle' })
  const [positions, setPositions] = useState({
    tribal_chief: { x: AGENTS.tribal_chief.deskX, y: AGENTS.tribal_chief.deskY },
    nezuko: { x: AGENTS.nezuko.deskX, y: AGENTS.nezuko.deskY },
    mikasa: { x: AGENTS.mikasa.deskX, y: AGENTS.mikasa.deskY },
    levi: { x: AGENTS.levi.deskX, y: AGENTS.levi.deskY },
    eren: { x: AGENTS.eren.deskX, y: AGENTS.eren.deskY },
    armin: { x: AGENTS.armin.deskX, y: AGENTS.armin.deskY },
  })
  const [facings, setFacings] = useState({
    tribal_chief: AGENTS.tribal_chief.deskFacing,
    nezuko: AGENTS.nezuko.deskFacing,
    mikasa: AGENTS.mikasa.deskFacing,
    levi: AGENTS.levi.deskFacing,
    eren: AGENTS.eren.deskFacing,
    armin: AGENTS.armin.deskFacing,
  })
  const [orb, setOrb] = useState({ visible: false, x: 0, y: 0, color: '#fff' })
  const [log, setLog] = useState([])
  const [finalAnswer, setFinalAnswer] = useState('')
  const [task, setTask] = useState('')
  const [running, setRunning] = useState(false)
  const [connected, setConnected] = useState(false)
  const [listening, setListening] = useState(false)
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  const [stopping, setStopping] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [speaking, setSpeaking] = useState(false)
  const [timeOfDay] = useState(() => {
    const h = new Date().getHours()
    return h >= 7 && h < 19 ? 'day' : 'night'
  })

  const wsRef = useRef(null)
  const tribalChiefWaitingRef = useRef(false)
  const logRef = useRef(null)
  const roomRef = useRef(null)
  const queueRef = useRef([])
  const processingRef = useRef(false)
  const recognitionRef = useRef(null)
  const audioRef = useRef(null)
  const usedVoiceRef = useRef(false)
  const scale = useRoomScale(roomRef)

  const ELEVEN_API_KEY = import.meta.env.VITE_ELEVEN_API_KEY || ''

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [log])

  // ElevenLabs TTS — replaces browser speech synthesis
  const speak = useCallback(async (text, agent = 'tribal_chief') => {
    if (!voiceEnabled) return
    if (!usedVoiceRef.current) return
    const cfg = AGENTS[agent]
    if (!cfg?.voiceId) return
    try {
      setSpeaking(true)
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      const response = await fetch(
        `https://api.elevenlabs.io/v1/text-to-speech/${cfg.voiceId}`,
        {
          method: 'POST',
          headers: {
            'xi-api-key': ELEVEN_API_KEY,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: text.substring(0, 500),
            model_id: 'eleven_turbo_v2',
            voice_settings: { stability: 0.5, similarity_boost: 0.75 },
          }),
        }
      )
      if (!response.ok) { setSpeaking(false); return }
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audioRef.current = audio
      audio.onended = () => { setSpeaking(false); URL.revokeObjectURL(url) }
      audio.onerror = () => { setSpeaking(false) }
      await audio.play()
    } catch (err) {
      console.error('ElevenLabs TTS error:', err)
      setSpeaking(false)
    }
  }, [voiceEnabled])

  const setupRecognition = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return null
    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'
    recognition.onstart = () => setListening(true)
    recognition.onend = () => setListening(false)
    recognition.onresult = (e) => {
      const results = Array.from(e.results)
      const t = results.map(r => r[0].transcript).join('')
      setTranscript(t)
      if (results[results.length - 1].isFinal) {
        setTask(t)
        setTranscript('')
        usedVoiceRef.current = true
      }
    }
    recognition.onerror = (e) => { console.error('Speech error:', e.error); setListening(false) }
    return recognition
  }, [])

  const toggleListening = useCallback(() => {
    if (listening) { recognitionRef.current?.stop(); return }
    if (!recognitionRef.current) recognitionRef.current = setupRecognition()
    if (!recognitionRef.current) {
      alert('Speech recognition not supported. Please use Chrome.')
      return
    }
    recognitionRef.current.start()
  }, [listening, setupRecognition])

  const addLog = useCallback((agent, msg) => {
    const colors = { tribal_chief: '#4f8ef7', nezuko: '#f472b6', mikasa: '#ef4444', levi: '#22c55e', eren: '#f59e0b', armin: '#a78bfa', system: '#6b7280' }
    const names = { tribal_chief: 'Tribal Chief', nezuko: 'Nezuko', mikasa: 'Mikasa', levi: 'Levi', eren: 'Eren', armin: 'Armin', system: 'SYSTEM' }
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
        setFacings(f => ({ ...f, tribal_chief: wp.facing }))
        setPositions(p => ({ ...p, tribal_chief: { x: wp.x, y: wp.y } }))
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
    const wsUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => { setConnected(false); setTimeout(connect, 3000) }
    ws.onerror = () => setConnected(false)
    ws.onmessage = (e) => {
      try {
        const ev = JSON.parse(e.data)
        const { agent, status, message, data, handoff_to } = ev
        if (agent !== 'system') {
          setStatuses(p => {
            // Protect tribal_chief WAITING status while agents are working
            if (agent !== 'tribal_chief' && tribalChiefWaitingRef.current) {
              return { ...p, [agent]: status, tribal_chief: 'waiting' }
            }
            return { ...p, [agent]: status }
          })
          // Track when tribal_chief enters and exits waiting
          if (agent === 'tribal_chief' && status === 'waiting') tribalChiefWaitingRef.current = true
          if (agent === 'tribal_chief' && (status === 'processing' || status === 'complete')) tribalChiefWaitingRef.current = false
          addLog(agent, message)
          if (status === 'thinking' && agent === 'tribal_chief') speak(message, 'tribal_chief')
          if (status === 'active' && agent === 'nezuko') speak(message, 'nezuko')
          if (status === 'active' && agent === 'mikasa') speak(message, 'mikasa')
          if (status === 'active' && agent === 'levi') speak(message, 'levi')
          if (status === 'active' && agent === 'eren') speak(message, 'eren')
          if (status === 'active' && agent === 'armin') speak(message, 'armin')
          if (agent === 'tribal_chief' && status === 'active' && handoff_to && handoff_to !== 'tribal_chief') {
            const target = AGENTS[handoff_to]
            if (target) {
              enqueueWalkPath(`tribal_chief-to-${handoff_to}`)
              enqueueDelay(200)
              enqueueOrb(target.deskX, target.deskY - 8, target.color)
              enqueueDelay(400)
              enqueueWalkPath(`tribal_chief-from-${handoff_to}`)
              enqueueSetStatus('tribal_chief', 'thinking')
            }
          }
          if (status === 'complete' && data?.final_answer) {
            const cleaned = data.final_answer
              .replace(/\*\*(.*?)\*\*/g, '$1')
              .replace(/^\* /gm, '- ')
              .replace(/^\*\*/gm, '')
            setFinalAnswer(cleaned)
            speak(data.final_answer, 'tribal_chief')
          }
        } else {
          addLog('system', message)
          if (status === 'done') {
            setRunning(false)
            enqueue(done => {
              setPositions(p => ({ ...p, tribal_chief: { x: AGENTS.tribal_chief.deskX, y: AGENTS.tribal_chief.deskY } }))
              setFacings(f => ({ ...f, tribal_chief: AGENTS.tribal_chief.deskFacing }))
              setTimeout(done, 1100)
            })
            enqueue(done => { setStatuses({ tribal_chief: 'idle', nezuko: 'idle', mikasa: 'idle', levi: 'idle', eren: 'idle', armin: 'idle' }); usedVoiceRef.current = false; done() })
          }
        }
      } catch (err) { console.error(err) }
    }
  }, [addLog, enqueue, enqueueWalkPath, enqueueOrb, enqueueDelay, enqueueSetStatus, speak])

  const stop = useCallback(() => {
    setStopping(true)
    queueRef.current = []
    processingRef.current = false
    wsRef.current?.send(JSON.stringify({ task: '__STOP__' }))
    setRunning(false)
    setStopping(false)
    setStatuses({ tribal_chief: 'idle', nezuko: 'idle', mikasa: 'idle', levi: 'idle', eren: 'idle', armin: 'idle' })
    setPositions({
      tribal_chief: { x: AGENTS.tribal_chief.deskX, y: AGENTS.tribal_chief.deskY },
      nezuko: { x: AGENTS.nezuko.deskX, y: AGENTS.nezuko.deskY },
      mikasa: { x: AGENTS.mikasa.deskX, y: AGENTS.mikasa.deskY },
      levi: { x: AGENTS.levi.deskX, y: AGENTS.levi.deskY },
      eren: { x: AGENTS.eren.deskX, y: AGENTS.eren.deskY },
      armin: { x: AGENTS.armin.deskX, y: AGENTS.armin.deskY },
    })
    setFacings({
      tribal_chief: AGENTS.tribal_chief.deskFacing,
      nezuko: AGENTS.nezuko.deskFacing,
      mikasa: AGENTS.mikasa.deskFacing,
      levi: AGENTS.levi.deskFacing,
      eren: AGENTS.eren.deskFacing,
      armin: AGENTS.armin.deskFacing,
    })
    addLog('system', 'Task stopped by user.')
  }, [addLog])

  useEffect(() => { connect(); return () => wsRef.current?.close() }, [])

  const send = useCallback(() => {
    if (!task.trim() || !connected || running) return
    setRunning(true)
    setFinalAnswer('')
    setLog([])
    queueRef.current = []
    processingRef.current = false
    setStatuses({ tribal_chief: 'idle', nezuko: 'idle', mikasa: 'idle', levi: 'idle', eren: 'idle', armin: 'idle' })
    setPositions({
      tribal_chief: { x: AGENTS.tribal_chief.deskX, y: AGENTS.tribal_chief.deskY },
      nezuko: { x: AGENTS.nezuko.deskX, y: AGENTS.nezuko.deskY },
      mikasa: { x: AGENTS.mikasa.deskX, y: AGENTS.mikasa.deskY },
      levi: { x: AGENTS.levi.deskX, y: AGENTS.levi.deskY },
      eren: { x: AGENTS.eren.deskX, y: AGENTS.eren.deskY },
      armin: { x: AGENTS.armin.deskX, y: AGENTS.armin.deskY },
    })
    setFacings({
      tribal_chief: AGENTS.tribal_chief.deskFacing,
      nezuko: AGENTS.nezuko.deskFacing,
      mikasa: AGENTS.mikasa.deskFacing,
      levi: AGENTS.levi.deskFacing,
      eren: AGENTS.eren.deskFacing,
      armin: AGENTS.armin.deskFacing,
    })
    wsRef.current?.send(JSON.stringify({ task }))
    setTask('')
  }, [task, connected, running])

  // Auto-send removed - user must press Enter or Send button
  // Voice transcript populates the input box, user confirms by pressing Enter

  const bgImage = timeOfDay === 'day' ? '/rooms/office-day.png' : '/rooms/office-night.png'

  return (
    <div style={{
      height: '100vh', background: '#07071a', color: '#e5e7eb',
      fontFamily: 'monospace', display: 'flex', flexDirection: 'column',
      padding: '12px', gap: '10px', overflow: 'hidden',
    }}>
      <style>{`
        @keyframes fadeIn { from{opacity:0;transform:translateY(3px)} to{opacity:1;transform:none} }
        @keyframes statusPulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
        @keyframes orbFloat { from{transform:translate(-50%,-50%) scale(1)} to{transform:translate(-50%,-50%) scale(1.3)} }
        @keyframes connPulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        @keyframes micPulse { 0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,0.4)} 50%{box-shadow:0 0 0 8px rgba(239,68,68,0)} }
        @keyframes speakPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.7;transform:scale(1.05)} }
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
        }}>AI COMMAND CENTER</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, marginTop: 3 }}>
          <div style={{
            fontSize: 10, letterSpacing: 2,
            color: connected ? '#22c55e' : '#ef4444',
            animation: connected ? 'none' : 'connPulse 1.5s infinite',
          }}>
            {connected ? '● CONNECTED' : '● CONNECTING...'}
          </div>
          <button
            onClick={() => { if(audioRef.current) audioRef.current.pause(); setVoiceEnabled(v => !v) }}
            style={{
              fontSize: 9, letterSpacing: 1, padding: '2px 8px', borderRadius: 10,
              border: `1px solid ${voiceEnabled ? (speaking ? '#22c55e' : '#4f8ef7') : 'rgba(55,65,81,0.4)'}`,
              background: voiceEnabled ? (speaking ? 'rgba(34,197,94,0.15)' : 'rgba(79,142,247,0.15)') : 'transparent',
              color: voiceEnabled ? (speaking ? '#22c55e' : '#4f8ef7') : '#4b5563',
              cursor: 'pointer', fontFamily: 'monospace',
              animation: speaking ? 'speakPulse 0.8s ease infinite' : 'none',
            }}
          >
            {voiceEnabled ? (speaking ? '🔊 SPEAKING...' : '🔊 VOICE ON') : '🔇 VOICE OFF'}
          </button>
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', gap: '10px', overflow: 'hidden', minHeight: 0 }}>
        <div style={{ flex: 1, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', overflow: 'hidden' }}>
          <div ref={roomRef} style={{
            position: 'relative', width: '100%', paddingBottom: '62%',
            borderRadius: 12, overflow: 'hidden', border: '1px solid rgba(55,65,81,0.3)',
          }}>
            <img src={bgImage} alt="Office" draggable={false} style={{
              position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
              objectFit: 'fill', userSelect: 'none', zIndex: 0,
            }} />
            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
              <FurnitureLayer scale={scale} />
              {Object.keys(AGENTS).map(key => (
                <Character key={key} agentKey={key} status={statuses[key]}
                  position={positions[key]} facing={facings[key]} scale={scale} />
              ))}
              <DataOrb visible={orb.visible} x={orb.x} y={orb.y} color={orb.color} scale={scale} />
            </div>
            {listening && (
              <div style={{
                position: 'absolute', bottom: 12, left: '50%', transform: 'translateX(-50%)',
                background: 'rgba(239,68,68,0.9)', borderRadius: 20, padding: '6px 16px',
                zIndex: 400, fontSize: 11, color: 'white', fontFamily: 'monospace',
                fontWeight: 700, letterSpacing: 1, animation: 'micPulse 1s ease infinite',
              }}>
                🎤 LISTENING... {transcript && `"${transcript}"`}
              </div>
            )}
            <div style={{
              position: 'absolute', bottom: 8, left: 12, fontSize: 9,
              letterSpacing: 2, color: 'rgba(255,255,255,0.25)', zIndex: 300,
            }}>
              {timeOfDay === 'day' ? '☀ DAY MODE' : '🌙 NIGHT MODE'}
            </div>
          </div>
        </div>

        <div style={{
          width: 300, display: 'flex', flexDirection: 'column',
          background: 'rgba(5,5,20,0.95)', border: '1px solid rgba(55,65,81,0.4)',
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
              <div style={{ padding: '20px 14px', color: '#374151', fontSize: 11, textAlign: 'center', lineHeight: 1.8 }}>
                <div style={{ fontSize: 28, marginBottom: 8 }}>🎤</div>
                <div style={{ marginBottom: 6 }}>Press the mic or type below</div>
                <div style={{ fontSize: 9, color: '#1f2937' }}>
                  Tribal Chief, Nezuko, Mikasa,<br/>Levi, Eren and Armin are standing by
                </div>
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
                  ✦ TRIBAL CHIEF'S REPORT
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
              border: `1px solid ${listening ? 'rgba(239,68,68,0.5)' : running ? 'rgba(79,142,247,0.4)' : 'rgba(55,65,81,0.4)'}`,
              borderRadius: 8, overflow: 'hidden', transition: 'border-color 0.2s',
            }}>
              <textarea
                value={transcript || task}
                onChange={e => setTask(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
                placeholder={listening ? '🎤 Listening...' : 'Message #command-center...'}
                disabled={running || !connected || listening}
                rows={2}
                style={{
                  width: '100%', background: 'transparent', border: 'none',
                  color: listening ? '#ef4444' : '#e5e7eb',
                  fontFamily: 'monospace', fontSize: 12, lineHeight: 1.5, padding: '8px 10px',
                }}
              />
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '4px 8px 6px', borderTop: '1px solid rgba(55,65,81,0.2)',
              }}>
                <MicButton listening={listening} onClick={toggleListening} disabled={running || !connected} />
                <div style={{ display: 'flex', gap: 4 }}>
                  {running && (
                    <button onClick={stop} style={{
                      padding: '4px 10px',
                      background: 'rgba(239,68,68,0.8)',
                      border: 'none', borderRadius: 5, color: 'white',
                      fontFamily: 'monospace', fontSize: 11, fontWeight: 700,
                      cursor: 'pointer', letterSpacing: 1,
                    }}>
                      ⏹ STOP
                    </button>
                  )}
                  <button onClick={send} disabled={!task.trim() || running || !connected || listening} style={{
                    padding: '4px 14px',
                    background: !task.trim() || running || !connected ? 'rgba(79,142,247,0.2)' : '#4f8ef7',
                    border: 'none', borderRadius: 5, color: 'white',
                    fontFamily: 'monospace', fontSize: 11, fontWeight: 700,
                    cursor: running || !task.trim() ? 'not-allowed' : 'pointer', letterSpacing: 1,
                  }}>
                    {running ? '⚙' : '⏎ SEND'}
                  </button>
                </div>
              </div>
            </div>
            <div style={{ fontSize: 9, color: '#374151', marginTop: 4, textAlign: 'center' }}>
              🎤 mic or Enter to send · Shift+Enter for new line
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
