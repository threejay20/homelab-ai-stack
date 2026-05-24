import { useEffect, useRef, useCallback, useState } from 'react'

const ISO = {
  tileW: 64,
  tileH: 32,
  toScreen: (gx, gy, gz=0) => ({
    x: (gx - gy) * 32,
    y: (gx + gy) * 16 - gz * 28
  }),
  FLOOR_W: 20,
  FLOOR_H: 14,
}

const SKIN = {
  chichi:  { base:'#8B5E3C', shadow:'#6B3F20', highlight:'#A8724A' },
  nezuko:  { base:'#FDBCB4', shadow:'#E8967A', highlight:'#FFD4CC' },
  mikasa:  { base:'#C68642', shadow:'#A0522D', highlight:'#D4956A' },
}

const HAIR = {
  chichi: { base:'#1a1a3a', highlight:'#2a2a5a' },
  nezuko: { base:'#d4508a', highlight:'#f472b6' },
  mikasa: { base:'#0a0a0a', highlight:'#1a0a0a' },
}

const OUTFIT = {
  chichi: { main:'#1a3a7a', accent:'#4f8ef7', shirt:'#e8f0ff' },
  nezuko: { main:'#f472b6', accent:'#ff80b0', shirt:'#ffffff' },
  mikasa: { main:'#1a0505', accent:'#ef4444', shirt:'#ef4444' },
}

function drawCharacter(ctx, agent, x, y, status, facing='right') {
  const skin = SKIN[agent]
  const hair = HAIR[agent]
  const outfit = OUTFIT[agent]
  const on = status === 'active' || status === 'thinking'
  const scale = 1
  ctx.save()
  ctx.translate(x, y)
  if (facing === 'left') ctx.scale(-1, 1)

  // shadow
  ctx.fillStyle = 'rgba(0,0,0,0.2)'
  ctx.beginPath()
  ctx.ellipse(0, 2, 12, 5, 0, 0, Math.PI*2)
  ctx.fill()

  // legs
  ctx.fillStyle = agent === 'mikasa' ? '#0a0505' : agent === 'nezuko' ? '#e060a0' : '#0f2a5a'
  ctx.fillRect(-8, 14, 6, 16)
  ctx.fillRect(2, 14, 6, 16)

  // shoes
  ctx.fillStyle = agent === 'chichi' ? '#1a1a3a' : agent === 'nezuko' ? '#4a2060' : '#0a0505'
  ctx.beginPath(); ctx.ellipse(-5, 30, 6, 3, 0, 0, Math.PI*2); ctx.fill()
  ctx.beginPath(); ctx.ellipse(5, 30, 6, 3, 0, 0, Math.PI*2); ctx.fill()

  // body
  ctx.fillStyle = outfit.main
  ctx.beginPath()
  ctx.roundRect(-10, -2, 20, 18, 3)
  ctx.fill()

  // outfit details
  if (agent === 'chichi') {
    ctx.fillStyle = outfit.shirt
    ctx.beginPath(); ctx.moveTo(-2,-2); ctx.lineTo(2,-2); ctx.lineTo(4,8); ctx.lineTo(-4,8); ctx.closePath(); ctx.fill()
    ctx.fillStyle = outfit.accent
    ctx.fillRect(-10,-2,20,4)
  } else if (agent === 'nezuko') {
    ctx.fillStyle = outfit.shirt
    ctx.beginPath(); ctx.moveTo(-3,-2); ctx.lineTo(3,-2); ctx.lineTo(4,10); ctx.lineTo(-4,10); ctx.closePath(); ctx.fill()
    ctx.fillStyle = '#ff80b0'
    ctx.beginPath(); ctx.arc(0, 2, 4, 0, Math.PI*2); ctx.fill()
  } else {
    ctx.fillStyle = outfit.accent
    ctx.fillRect(-10,-2,20,6)
    ctx.strokeStyle = '#5a3010'; ctx.lineWidth = 1.5
    ctx.beginPath(); ctx.moveTo(-6,4); ctx.lineTo(-8,16); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(6,4); ctx.lineTo(8,16); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(-6,10); ctx.lineTo(6,10); ctx.stroke()
  }

  // arms
  ctx.fillStyle = outfit.main
  ctx.beginPath(); ctx.roundRect(-16, -2, 6, 14, 3); ctx.fill()
  ctx.beginPath(); ctx.roundRect(10, -2, 6, 14, 3); ctx.fill()

  // hands
  ctx.fillStyle = skin.base
  ctx.beginPath(); ctx.ellipse(-13, 13, 4, 3, 0, 0, Math.PI*2); ctx.fill()
  ctx.beginPath(); ctx.ellipse(13, 13, 4, 3, 0, 0, Math.PI*2); ctx.fill()

  // neck
  ctx.fillStyle = skin.base
  ctx.fillRect(-3, -8, 6, 8)

  // head
  ctx.fillStyle = skin.base
  ctx.beginPath(); ctx.ellipse(0, -20, 13, 15, 0, 0, Math.PI*2); ctx.fill()

  // ear
  ctx.beginPath(); ctx.ellipse(-13, -20, 3, 4, 0, 0, Math.PI*2); ctx.fill()
  ctx.beginPath(); ctx.ellipse(13, -20, 3, 4, 0, 0, Math.PI*2); ctx.fill()

  // hair
  ctx.fillStyle = hair.base
  if (agent === 'chichi') {
    ctx.beginPath()
    ctx.moveTo(-13,-20); ctx.quadraticCurveTo(-14,-38,0,-40)
    ctx.quadraticCurveTo(14,-38,13,-20)
    ctx.quadraticCurveTo(14,-10,12,-8)
    ctx.quadraticCurveTo(10,-16,8,-12)
    ctx.quadraticCurveTo(6,-18,4,-14)
    ctx.quadraticCurveTo(2,-20,0,-16)
    ctx.quadraticCurveTo(-2,-20,-4,-14)
    ctx.quadraticCurveTo(-6,-18,-8,-12)
    ctx.quadraticCurveTo(-10,-16,-12,-8)
    ctx.quadraticCurveTo(-14,-10,-13,-20)
    ctx.fill()
    ctx.strokeStyle = hair.highlight; ctx.lineWidth = 0.8
    ctx.beginPath(); ctx.moveTo(-4,-38); ctx.quadraticCurveTo(2,-42,8,-38); ctx.stroke()
  } else if (agent === 'nezuko') {
    ctx.beginPath()
    ctx.moveTo(-13,-18); ctx.quadraticCurveTo(-14,-40,0,-42)
    ctx.quadraticCurveTo(14,-40,13,-18)
    ctx.fill()
    ctx.beginPath()
    ctx.moveTo(-13,-18); ctx.quadraticCurveTo(-16,-10,-14,10)
    ctx.lineTo(-10,10); ctx.quadraticCurveTo(-10,-8,-10,-18); ctx.fill()
    ctx.beginPath()
    ctx.moveTo(13,-18); ctx.quadraticCurveTo(16,-10,14,10)
    ctx.lineTo(10,10); ctx.quadraticCurveTo(10,-8,10,-18); ctx.fill()
    ctx.fillStyle = hair.highlight
    ctx.beginPath(); ctx.ellipse(8,-38,5,4,0.3,0,Math.PI*2); ctx.fill()
    ctx.beginPath(); ctx.ellipse(14,-38,4,3,-0.3,0,Math.PI*2); ctx.fill()
    ctx.fillStyle = '#ffb0d0'
    ctx.beginPath(); ctx.moveTo(6,-36); ctx.quadraticCurveTo(10,-42,14,-36); ctx.quadraticCurveTo(10,-32,6,-36); ctx.fill()
    ctx.beginPath(); ctx.moveTo(6,-36); ctx.quadraticCurveTo(2,-42,-2,-36); ctx.quadraticCurveTo(2,-32,6,-36); ctx.fill()
    ctx.fillStyle = '#ff80b0'; ctx.beginPath(); ctx.arc(6,-36,2.5,0,Math.PI*2); ctx.fill()
    ctx.fillStyle = hair.base
    ctx.beginPath()
    ctx.moveTo(-13,-24); ctx.quadraticCurveTo(-10,-30,-6,-26)
    ctx.quadraticCurveTo(-2,-22,0,-26)
    ctx.quadraticCurveTo(4,-30,8,-26)
    ctx.quadraticCurveTo(10,-22,13,-24)
    ctx.lineTo(13,-18); ctx.lineTo(-13,-18); ctx.fill()
  } else {
    ctx.beginPath()
    ctx.moveTo(-13,-18); ctx.quadraticCurveTo(-13,-38,0,-40)
    ctx.quadraticCurveTo(13,-38,13,-18)
    ctx.quadraticCurveTo(14,-8,12,-4)
    ctx.quadraticCurveTo(8,-12,4,-8)
    ctx.quadraticCurveTo(0,-14,-4,-8)
    ctx.quadraticCurveTo(-8,-12,-12,-4)
    ctx.quadraticCurveTo(-14,-8,-13,-18)
    ctx.fill()
    ctx.strokeStyle = '#1a0a0a'; ctx.lineWidth = 1
    ctx.beginPath(); ctx.moveTo(-8,-4); ctx.lineTo(-4,-2); ctx.stroke()
  }

  // face details - cheeks
  if (agent === 'nezuko') {
    ctx.fillStyle = 'rgba(255,150,180,0.4)'
    ctx.beginPath(); ctx.ellipse(-8,-18,4,3,0,0,Math.PI*2); ctx.fill()
    ctx.beginPath(); ctx.ellipse(8,-18,4,3,0,0,Math.PI*2); ctx.fill()
  }
  if (agent === 'mikasa') {
    ctx.strokeStyle = '#e8a898'; ctx.lineWidth = 0.8
    ctx.beginPath(); ctx.moveTo(-8,-23); ctx.lineTo(-5,-19); ctx.stroke()
  }

  // eyes
  ctx.fillStyle = '#1a1a2a'
  if (agent === 'chichi') {
    ctx.strokeStyle = '#4f8ef7'; ctx.lineWidth = 1.2
    ctx.strokeRect(-9,-23,7,6)
    ctx.strokeRect(2,-23,7,6)
    ctx.fillStyle = '#3a3a7a'
    ctx.fillRect(-8,-22,5,4)
    ctx.fillRect(3,-22,5,4)
  } else if (agent === 'nezuko') {
    ctx.fillStyle = '#7030a0'
    ctx.beginPath(); ctx.ellipse(-6,-22,5,6,0,0,Math.PI*2); ctx.fill()
    ctx.beginPath(); ctx.ellipse(6,-22,5,6,0,0,Math.PI*2); ctx.fill()
    ctx.fillStyle = '#9050c0'
    ctx.beginPath(); ctx.ellipse(-6,-22,3,4,0,0,Math.PI*2); ctx.fill()
    ctx.beginPath(); ctx.ellipse(6,-22,3,4,0,0,Math.PI*2); ctx.fill()
    ctx.strokeStyle = '#2a0a2a'; ctx.lineWidth = 1
    ctx.beginPath(); ctx.moveTo(-11,-26); ctx.quadraticCurveTo(-6,-29,-2,-26); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(2,-26); ctx.quadraticCurveTo(7,-29,11,-26); ctx.stroke()
  } else {
    ctx.fillStyle = '#1a0a0a'
    ctx.beginPath(); ctx.ellipse(-6,-22,5,5.5,0,0,Math.PI*2); ctx.fill()
    ctx.beginPath(); ctx.ellipse(6,-22,5,5.5,0,0,Math.PI*2); ctx.fill()
    ctx.fillStyle = '#6a1010'
    ctx.beginPath(); ctx.ellipse(-6,-22,3,3.5,0,0,Math.PI*2); ctx.fill()
    ctx.beginPath(); ctx.ellipse(6,-22,3,3.5,0,0,Math.PI*2); ctx.fill()
    ctx.strokeStyle = '#0a0a0a'; ctx.lineWidth = 1.8
    ctx.beginPath(); ctx.moveTo(-11,-28); ctx.lineTo(-3,-26); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(3,-26); ctx.lineTo(11,-28); ctx.stroke()
  }
  ctx.fillStyle = 'white'
  ctx.beginPath(); ctx.arc(-5,-23,1.5,0,Math.PI*2); ctx.fill()
  ctx.beginPath(); ctx.arc(7,-23,1.5,0,Math.PI*2); ctx.fill()

  // mouth
  ctx.strokeStyle = agent==='mikasa' ? '#c06050' : '#c87a6a'
  ctx.lineWidth = 1.5
  if (agent === 'nezuko') {
    ctx.beginPath(); ctx.moveTo(-4,-14); ctx.quadraticCurveTo(0,-11,4,-14); ctx.stroke()
  } else if (agent === 'mikasa') {
    ctx.beginPath(); ctx.moveTo(-4,-14); ctx.lineTo(4,-14); ctx.stroke()
  } else {
    ctx.beginPath(); ctx.moveTo(-3,-14); ctx.quadraticCurveTo(0,-12,3,-14); ctx.stroke()
  }

  // accessories
  if (agent === 'chichi') {
    ctx.fillStyle = '#4f8ef7'
    ctx.fillRect(10,2,14,18)
    ctx.fillStyle = '#e8f4ff'
    ctx.fillRect(11,3,12,15)
    ctx.strokeStyle = '#4f8ef7'; ctx.lineWidth = 0.7
    ctx.beginPath(); ctx.moveTo(13,7); ctx.lineTo(21,7); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(13,10); ctx.lineTo(21,10); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(13,13); ctx.lineTo(18,13); ctx.stroke()
  }
  if (agent === 'nezuko') {
    ctx.fillStyle = '#1a0a2a'
    ctx.roundRect && ctx.roundRect(-24,2,14,18,2)
    ctx.fill()
    ctx.fillStyle = 'rgba(244,114,182,0.15)'
    ctx.fillRect(-23,3,12,15)
  }

  // status glow above head
  if (on) {
    ctx.fillStyle = agent==='chichi'?'#4f8ef7':agent==='nezuko'?'#f472b6':'#ef4444'
    ctx.globalAlpha = 0.7 + 0.3*Math.sin(Date.now()/300)
    ctx.beginPath(); ctx.arc(0,-50,5,0,Math.PI*2); ctx.fill()
    ctx.globalAlpha = 1
  }

  ctx.restore()
}

function drawIsoTile(ctx, sx, sy, w, h, fillTop, fillFront, fillSide) {
  ctx.fillStyle = fillTop
  ctx.beginPath()
  ctx.moveTo(sx, sy)
  ctx.lineTo(sx + w/2, sy + h/2)
  ctx.lineTo(sx + w, sy)
  ctx.lineTo(sx + w/2, sy - h/2)
  ctx.closePath()
  ctx.fill()
  if (fillFront) {
    ctx.fillStyle = fillFront
    ctx.beginPath()
    ctx.moveTo(sx, sy)
    ctx.lineTo(sx + w/2, sy + h/2)
    ctx.lineTo(sx + w/2, sy + h/2 + 20)
    ctx.lineTo(sx, sy + 20)
    ctx.closePath()
    ctx.fill()
  }
  if (fillSide) {
    ctx.fillStyle = fillSide
    ctx.beginPath()
    ctx.moveTo(sx + w, sy)
    ctx.lineTo(sx + w/2, sy + h/2)
    ctx.lineTo(sx + w/2, sy + h/2 + 20)
    ctx.lineTo(sx + w, sy + 20)
    ctx.closePath()
    ctx.fill()
  }
}

function drawFloor(ctx, ox, oy) {
  for (let gx = 0; gx < ISO.FLOOR_W; gx++) {
    for (let gy = 0; gy < ISO.FLOOR_H; gy++) {
      const s = ISO.toScreen(gx, gy)
      const sx = ox + s.x
      const sy = oy + s.y
      const isOffice = gx <= 6 && gy <= 7
      const light = isOffice
        ? ((gx+gy)%2===0 ? '#1a2a4a' : '#162240')
        : ((gx+gy)%2===0 ? '#13131f' : '#0f0f1a')
      ctx.fillStyle = light
      ctx.beginPath()
      ctx.moveTo(sx + 32, sy)
      ctx.lineTo(sx + 64, sy + 16)
      ctx.lineTo(sx + 32, sy + 32)
      ctx.lineTo(sx, sy + 16)
      ctx.closePath()
      ctx.fill()
      ctx.strokeStyle = isOffice ? 'rgba(79,142,247,0.08)' : 'rgba(55,65,81,0.06)'
      ctx.lineWidth = 0.5
      ctx.stroke()
    }
  }
}

function drawWalls(ctx, ox, oy) {
  const wallH = 100
  // Back walls
  for (let gx = 0; gx <= ISO.FLOOR_W; gx++) {
    const s = ISO.toScreen(gx, 0)
    const sx = ox + s.x
    const sy = oy + s.y
    ctx.fillStyle = '#0d1520'
    ctx.fillRect(sx, sy - wallH, 64, wallH)
    ctx.strokeStyle = 'rgba(79,142,247,0.06)'
    ctx.lineWidth = 0.3
    ctx.strokeRect(sx, sy - wallH, 64, wallH)
  }
  for (let gy = 0; gy <= ISO.FLOOR_H; gy++) {
    const s = ISO.toScreen(0, gy)
    const sx = ox + s.x
    const sy = oy + s.y
    ctx.fillStyle = '#0a1020'
    ctx.beginPath()
    ctx.moveTo(sx, sy - wallH)
    ctx.lineTo(sx, sy)
    ctx.lineTo(sx - 32, sy - 16)
    ctx.lineTo(sx - 32, sy - 16 - wallH)
    ctx.closePath()
    ctx.fill()
  }
}

function drawOfficeWalls(ctx, ox, oy) {
  const wallH = 90
  const glassAlpha = 0.12
  // Office divider - right wall (gx=7)
  for (let gy = 0; gy <= 7; gy++) {
    const s = ISO.toScreen(7, gy)
    const sx = ox + s.x
    const sy = oy + s.y
    ctx.fillStyle = `rgba(79,142,247,${glassAlpha})`
    ctx.fillRect(sx, sy - wallH, 4, wallH + 16)
    ctx.strokeStyle = 'rgba(79,142,247,0.5)'
    ctx.lineWidth = 1
    ctx.strokeRect(sx, sy - wallH, 4, wallH + 16)
    // Glass panels
    if (gy !== 5) {
      ctx.fillStyle = `rgba(79,142,247,${glassAlpha})`
      ctx.beginPath()
      ctx.moveTo(sx, sy - wallH)
      ctx.lineTo(sx + 32, sy - wallH + 16)
      ctx.lineTo(sx + 32, sy + 16)
      ctx.lineTo(sx, sy)
      ctx.closePath()
      ctx.fill()
      ctx.strokeStyle = 'rgba(79,142,247,0.3)'
      ctx.lineWidth = 0.5
      ctx.stroke()
    }
  }
  // Door frame at gy=5
  const ds = ISO.toScreen(7, 5)
  ctx.strokeStyle = 'rgba(79,142,247,0.8)'
  ctx.lineWidth = 2
  ctx.strokeRect(ox + ds.x, oy + ds.y - wallH, 4, wallH + 16)
}

function drawDesk(ctx, sx, sy, color, hasPlant) {
  const w = 64, h = 32
  drawIsoTile(ctx, sx, sy, w, h, color.top, color.front, color.side)
  // Monitor
  ctx.fillStyle = '#0a0a1a'
  ctx.beginPath()
  ctx.moveTo(sx+20, sy-8)
  ctx.lineTo(sx+44, sy+4)
  ctx.lineTo(sx+44, sy-20)
  ctx.lineTo(sx+20, sy-32)
  ctx.closePath()
  ctx.fill()
  ctx.strokeStyle = color.top
  ctx.lineWidth = 1
  ctx.stroke()
  ctx.fillStyle = '#050520'
  ctx.beginPath()
  ctx.moveTo(sx+22, sy-9)
  ctx.lineTo(sx+42, sy+2)
  ctx.lineTo(sx+42, sy-18)
  ctx.lineTo(sx+22, sy-30)
  ctx.closePath()
  ctx.fill()
  // Screen glow lines
  ctx.strokeStyle = color.top
  ctx.globalAlpha = 0.5
  ctx.lineWidth = 0.8
  for (let i = 0; i < 3; i++) {
    ctx.beginPath()
    ctx.moveTo(sx+24, sy-26+i*7)
    ctx.lineTo(sx+40, sy-18+i*7)
    ctx.stroke()
  }
  ctx.globalAlpha = 1
  // Plant
  if (hasPlant) {
    const px = sx + 50, py = sy - 4
    ctx.fillStyle = '#2a4a1a'
    ctx.fillRect(px-3, py-8, 6, 10)
    ctx.fillStyle = '#1a3a1a'
    ctx.fillRect(px-4, py-8, 8, 3)
    ctx.fillStyle = '#3a6a2a'
    ctx.beginPath(); ctx.arc(px, py-16, 10, 0, Math.PI*2); ctx.fill()
    ctx.fillStyle = '#4a8a3a'
    ctx.beginPath(); ctx.arc(px-4, py-18, 7, 0, Math.PI*2); ctx.fill()
    ctx.beginPath(); ctx.arc(px+4, py-18, 7, 0, Math.PI*2); ctx.fill()
  }
}

function drawChair(ctx, sx, sy, color) {
  ctx.fillStyle = color
  ctx.beginPath()
  ctx.moveTo(sx+16, sy+8)
  ctx.lineTo(sx+32, sy+16)
  ctx.lineTo(sx+32, sy+8)
  ctx.lineTo(sx+16, sy)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = color
  ctx.beginPath()
  ctx.moveTo(sx+16, sy)
  ctx.lineTo(sx+32, sy+8)
  ctx.lineTo(sx+32, sy-8)
  ctx.lineTo(sx+16, sy-16)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = '#1a1a2a'
  ctx.beginPath()
  ctx.moveTo(sx+22, sy+8)
  ctx.lineTo(sx+26, sy+10)
  ctx.lineTo(sx+26, sy+20)
  ctx.lineTo(sx+22, sy+18)
  ctx.closePath()
  ctx.fill()
}

function drawBookshelf(ctx, sx, sy) {
  drawIsoTile(ctx, sx, sy, 32, 16, '#1a0f08', '#120a05', '#0f0803')
  const colors = ['#f472b6','#9050c0','#4f8ef7','#ef4444','#22c55e','#f59e0b']
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 2; j++) {
      ctx.fillStyle = colors[(i*2+j)%colors.length]
      ctx.globalAlpha = 0.8
      ctx.fillRect(sx+4+j*14, sy-28+i*18, 10, 16)
      ctx.globalAlpha = 1
    }
  }
  ctx.strokeStyle = '#1a0f08'
  ctx.lineWidth = 0.5
  for (let i = 0; i < 4; i++) {
    ctx.beginPath()
    ctx.moveTo(sx+2, sy-10+i*18)
    ctx.lineTo(sx+30, sy-10+i*18)
    ctx.stroke()
  }
}

function drawPlant(ctx, sx, sy) {
  ctx.fillStyle = '#3a2a1a'
  ctx.beginPath()
  ctx.moveTo(sx+12, sy)
  ctx.lineTo(sx+20, sy+4)
  ctx.lineTo(sx+20, sy-6)
  ctx.lineTo(sx+12, sy-10)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = '#3a6a2a'
  ctx.beginPath(); ctx.arc(sx+12, sy-18, 12, 0, Math.PI*2); ctx.fill()
  ctx.fillStyle = '#4a8a3a'
  ctx.beginPath(); ctx.arc(sx+6, sy-22, 8, 0, Math.PI*2); ctx.fill()
  ctx.beginPath(); ctx.arc(sx+18, sy-22, 8, 0, Math.PI*2); ctx.fill()
  ctx.fillStyle = '#5a9a4a'
  ctx.beginPath(); ctx.arc(sx+12, sy-26, 6, 0, Math.PI*2); ctx.fill()
}

function drawWhiteboard(ctx, sx, sy) {
  ctx.fillStyle = '#0d1520'
  ctx.fillRect(sx-2, sy-80, 70, 5)
  ctx.fillStyle = '#f0f4ff'
  ctx.fillRect(sx, sy-76, 66, 50)
  ctx.fillStyle = '#e0e8ff'
  ctx.fillRect(sx+2, sy-74, 62, 46)
  ctx.strokeStyle = '#4f8ef7'; ctx.lineWidth = 0.8
  ctx.beginPath(); ctx.moveTo(sx+6, sy-65); ctx.lineTo(sx+30, sy-65); ctx.stroke()
  ctx.beginPath(); ctx.moveTo(sx+6, sy-58); ctx.lineTo(sx+45, sy-58); ctx.stroke()
  ctx.beginPath(); ctx.moveTo(sx+6, sy-51); ctx.lineTo(sx+35, sy-51); ctx.stroke()
  ctx.strokeStyle = '#f472b6'; ctx.lineWidth = 1
  ctx.beginPath(); ctx.moveTo(sx+38, sy-68); ctx.quadraticCurveTo(sx+50, sy-60, sx+58, sy-70); ctx.stroke()
}

function drawWaterCooler(ctx, sx, sy) {
  ctx.fillStyle = '#1a2a3a'
  ctx.fillRect(sx, sy-30, 16, 30)
  ctx.fillStyle = '#4f8ef733'
  ctx.beginPath(); ctx.ellipse(sx+8, sy-30, 8, 10, 0, 0, Math.PI*2); ctx.fill()
  ctx.fillStyle = '#4f8ef7'
  ctx.beginPath(); ctx.ellipse(sx+8, sy-30, 6, 8, 0, 0, Math.PI*2); ctx.fill()
  ctx.fillStyle = '#4f8ef788'
  ctx.beginPath(); ctx.ellipse(sx+8, sy-30, 4, 6, 0, 0, Math.PI*2); ctx.fill()
}

export default function App() {
  const canvasRef = useRef(null)
  const stateRef = useRef({
    statuses: { chichi:'idle', nezuko:'idle', mikasa:'idle' },
    chichiPos: { gx: 3.5, gy: 3.5 },
    chichiTarget: null,
    chichiWalking: false,
    chichiDir: 'right',
    doorOpen: false,
    orbVisible: false,
    orbPos: { x: 0, y: 0 },
    orbColor: '#4f8ef7',
    frame: 0,
  })
  const [connected, setConnected] = useState(false)
  const [running, setRunning] = useState(false)
  const [task, setTask] = useState('')
  const [log, setLog] = useState([])
  const [finalAnswer, setFinalAnswer] = useState('')
  const logRef = useRef(null)
  const wsRef = useRef(null)
  const animRef = useRef(null)

  const addLog = useCallback((agent, msg) => {
    const colors = { chichi:'#4f8ef7', nezuko:'#f472b6', mikasa:'#ef4444', system:'#6b7280' }
    const names = { chichi:'ChiChi', nezuko:'Nezuko', mikasa:'Mikasa', system:'SYSTEM' }
    setLog(prev => [...prev.slice(-60), {
      id: Date.now()+Math.random(), agent, msg,
      color: colors[agent]||'#6b7280',
      name: names[agent]||'SYSTEM',
      time: new Date().toLocaleTimeString()
    }])
  }, [])

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [log])

  const sleep = ms => new Promise(r => setTimeout(r, ms))

  const walkTo = useCallback(async (targetGx, targetGy, dir='right') => {
    const s = stateRef.current
    s.chichiWalking = true
    s.chichiDir = dir
    if (targetGx > 6) s.doorOpen = true
    s.chichiTarget = { gx: targetGx, gy: targetGy }
    await sleep(1000)
    s.chichiPos = { gx: targetGx, gy: targetGy }
    s.chichiWalking = false
    s.chichiTarget = null
    if (targetGx <= 4) s.doorOpen = false
  }, [])

  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const W = canvas.width
    const H = canvas.height
    const s = stateRef.current
    s.frame++

    ctx.clearRect(0, 0, W, H)
    ctx.fillStyle = '#07071a'
    ctx.fillRect(0, 0, W, H)

    const ox = W/2 - 20
    const oy = 80

    drawFloor(ctx, ox, oy)
    drawWalls(ctx, ox, oy)
    drawOfficeWalls(ctx, ox, oy)

    // Whiteboard in office
    const wbs = ISO.toScreen(1, 0)
    drawWhiteboard(ctx, ox + wbs.x + 10, oy + wbs.y)

    // Office desk
    const ods = ISO.toScreen(3, 3)
    drawDesk(ctx, ox+ods.x, oy+ods.y, {
      top:'#1a3a6a', front:'#0f2a5a', side:'#0a2050'
    }, false)
    drawChair(ctx, ox+ods.x-20, oy+ods.y+10, '#2a4a8a')

    // Office plant
    const ops = ISO.toScreen(1, 5)
    drawPlant(ctx, ox+ops.x+10, oy+ops.y)

    // Nezuko bookshelf
    const nbs = ISO.toScreen(9, 1)
    drawBookshelf(ctx, ox+nbs.x, oy+nbs.y)

    // Nezuko desk
    const nds = ISO.toScreen(10, 4)
    drawDesk(ctx, ox+nds.x, oy+nds.y, {
      top:'#3a1a3a', front:'#2a1028', side:'#201020'
    }, true)
    drawChair(ctx, ox+nds.x-20, oy+nds.y+10, '#6a2a6a')

    // Mikasa desk
    const mds = ISO.toScreen(15, 4)
    drawDesk(ctx, ox+mds.x, oy+mds.y, {
      top:'#3a1010', front:'#2a0808', side:'#200606'
    }, false)
    drawChair(ctx, ox+mds.x-20, oy+mds.y+10, '#6a1a1a')

    // Water cooler
    const wcs = ISO.toScreen(17, 1)
    drawWaterCooler(ctx, ox+wcs.x+20, oy+wcs.y-10)

    // Open floor plant
    const fp = ISO.toScreen(13, 8)
    drawPlant(ctx, ox+fp.x+10, oy+fp.y)

    // Draw characters
    // Nezuko at her desk
    const nezukoS = ISO.toScreen(10, 5)
    const nezukoOn = s.statuses.nezuko==='active'||s.statuses.nezuko==='thinking'
    if (nezukoOn) {
      ctx.fillStyle = 'rgba(244,114,182,0.15)'
      ctx.beginPath(); ctx.ellipse(ox+nezukoS.x+32, oy+nezukoS.y+16, 30, 15, 0, 0, Math.PI*2); ctx.fill()
    }
    drawCharacter(ctx, 'nezuko', ox+nezukoS.x+32, oy+nezukoS.y-10, s.statuses.nezuko, 'right')

    // Mikasa at her desk
    const mikasaS = ISO.toScreen(15, 5)
    const mikasaOn = s.statuses.mikasa==='active'||s.statuses.mikasa==='thinking'
    if (mikasaOn) {
      ctx.fillStyle = 'rgba(239,68,68,0.15)'
      ctx.beginPath(); ctx.ellipse(ox+mikasaS.x+32, oy+mikasaS.y+16, 30, 15, 0, 0, Math.PI*2); ctx.fill()
    }
    drawCharacter(ctx, 'mikasa', ox+mikasaS.x+32, oy+mikasaS.y-10, s.statuses.mikasa, 'right')

    // ChiChi - interpolate position
    let chichiGx = s.chichiPos.gx
    let chichiGy = s.chichiPos.gy
    if (s.chichiTarget && s.chichiWalking) {
      chichiGx = s.chichiPos.gx + (s.chichiTarget.gx - s.chichiPos.gx) * Math.min(1, (s.frame%60)/60)
      chichiGy = s.chichiPos.gy + (s.chichiTarget.gy - s.chichiPos.gy) * Math.min(1, (s.frame%60)/60)
    }
    const chichiScreen = ISO.toScreen(chichiGx, chichiGy)
    const chichiOn = s.statuses.chichi==='active'||s.statuses.chichi==='thinking'
    if (chichiOn) {
      ctx.fillStyle = 'rgba(79,142,247,0.15)'
      ctx.beginPath(); ctx.ellipse(ox+chichiScreen.x+32, oy+chichiScreen.y+16, 30, 15, 0, 0, Math.PI*2); ctx.fill()
    }
    const chichiStatus = s.chichiWalking ? 'walking' : s.statuses.chichi
    const bounce = s.chichiWalking ? Math.sin(s.frame * 0.3) * 3 : 0
    drawCharacter(ctx, 'chichi', ox+chichiScreen.x+32, oy+chichiScreen.y-10+bounce, chichiStatus, s.chichiDir)

    // Data orb
    if (s.orbVisible) {
      const orbBounce = Math.sin(s.frame * 0.1) * 4
      ctx.save()
      ctx.translate(s.orbPos.x, s.orbPos.y + orbBounce)
      ctx.fillStyle = s.orbColor
      ctx.globalAlpha = 0.3
      ctx.beginPath(); ctx.arc(0, 0, 14, 0, Math.PI*2); ctx.fill()
      ctx.globalAlpha = 0.6
      ctx.beginPath(); ctx.arc(0, 0, 9, 0, Math.PI*2); ctx.fill()
      ctx.globalAlpha = 1
      ctx.fillStyle = 'white'
      ctx.beginPath(); ctx.arc(0, 0, 5, 0, Math.PI*2); ctx.fill()
      ctx.beginPath(); ctx.arc(-2, -2, 2, 0, Math.PI*2); ctx.fill()
      ctx.restore()
    }

    // Agent status labels
    const labels = [
      { key:'chichi', sx: ox+chichiScreen.x+32, sy: oy+chichiScreen.y-60 },
      { key:'nezuko', sx: ox+nezukoS.x+32, sy: oy+nezukoS.y-60 },
      { key:'mikasa', sx: ox+mikasaS.x+32, sy: oy+mikasaS.y-60 },
    ]
    const nameColors = { chichi:'#4f8ef7', nezuko:'#f472b6', mikasa:'#ef4444' }
    const names = { chichi:'ChiChi', nezuko:'Nezuko', mikasa:'Mikasa' }
    labels.forEach(({ key, sx, sy }) => {
      const st = key==='chichi' ? s.statuses.chichi : s.statuses[key]
      ctx.fillStyle = nameColors[key]
      ctx.font = 'bold 11px monospace'
      ctx.textAlign = 'center'
      ctx.fillText(names[key], sx, sy)
      if (st !== 'idle') {
        ctx.font = '9px monospace'
        ctx.fillStyle = 'rgba(255,255,255,0.5)'
        ctx.fillText(st.toUpperCase(), sx, sy + 12)
      }
    })

    // Room labels
    ctx.font = '9px monospace'
    ctx.textAlign = 'left'
    ctx.fillStyle = 'rgba(79,142,247,0.4)'
    const rl = ISO.toScreen(2, 6)
    ctx.fillText("DIRECTOR'S OFFICE", ox+rl.x, oy+rl.y)
    ctx.fillStyle = 'rgba(100,80,120,0.3)'
    const fl = ISO.toScreen(12, 9)
    ctx.fillText('OPERATIONS FLOOR', ox+fl.x, oy+fl.y)

    animRef.current = requestAnimationFrame(draw)
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight
    const resize = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
    }
    window.addEventListener('resize', resize)
    animRef.current = requestAnimationFrame(draw)
    return () => {
      window.removeEventListener('resize', resize)
      if (animRef.current) cancelAnimationFrame(animRef.current)
    }
  }, [draw])

  const connect = useCallback(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws`)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => { setConnected(false); setTimeout(connect, 3000) }
    ws.onerror = () => setConnected(false)
    ws.onmessage = async (e) => {
      try {
        const ev = JSON.parse(e.data)
        const { agent, status, message, data, handoff_to } = ev
        const s = stateRef.current
        if (agent !== 'system') {
          s.statuses[agent] = status
          addLog(agent, message)
          if (agent==='chichi' && status==='active' && handoff_to && handoff_to!=='chichi') {
            const targets = {
              nezuko: { gx: 8.5, gy: 4.5, dir:'right' },
              mikasa: { gx: 13.5, gy: 4.5, dir:'right' }
            }
            const t = targets[handoff_to]
            if (t) {
              await walkTo(t.gx, t.gy, t.dir)
              const ts = ISO.toScreen(t.gx, t.gy)
              const canvas = canvasRef.current
              const ox = canvas.width/2 - 20
              s.orbPos = { x: ox+ts.x+60, y: 80+ts.y-40 }
              s.orbColor = handoff_to==='nezuko' ? '#f472b6' : '#ef4444'
              s.orbVisible = true
              await sleep(700)
              s.orbVisible = false
              await walkTo(3.5, 3.5, 'left')
              s.chichiDir = 'right'
              s.statuses.chichi = 'thinking'
            }
          }
          if (status==='complete' && data?.final_answer) {
            setFinalAnswer(data.final_answer)
          }
        } else {
          addLog('system', message)
          if (status==='done') {
            setRunning(false)
            s.statuses = { chichi:'idle', nezuko:'idle', mikasa:'idle' }
            await walkTo(3.5, 3.5, 'right')
          }
        }
      } catch(err) { console.error(err) }
    }
  }, [addLog, walkTo])

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [])

  const send = () => {
    if (!task.trim()||!connected||running) return
    setRunning(true)
    setFinalAnswer('')
    setLog([])
    stateRef.current.statuses = { chichi:'idle', nezuko:'idle', mikasa:'idle' }
    wsRef.current?.send(JSON.stringify({ task }))
    setTask('')
  }

  return (
    <div style={{
      height:'100vh', background:'#07071a',
      color:'#e5e7eb', fontFamily:'monospace',
      display:'flex', flexDirection:'column',
      padding:'12px', gap:'10px', overflow:'hidden'
    }}>
      <style>{`
        @keyframes fadeIn{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
        *{box-sizing:border-box}
        ::-webkit-scrollbar{width:4px}
        ::-webkit-scrollbar-track{background:#050510}
        ::-webkit-scrollbar-thumb{background:#1f2937;border-radius:2px}
        textarea{outline:none}
      `}</style>

      <div style={{textAlign:'center', flexShrink:0}}>
        <div style={{
          fontSize:20, fontWeight:900, letterSpacing:4,
          background:'linear-gradient(90deg,#4f8ef7,#f472b6,#ef4444)',
          WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent'
        }}>HOMELAB AI COMMAND CENTER</div>
        <div style={{
          fontSize:10, marginTop:3, letterSpacing:2,
          color:connected?'#22c55e':'#ef4444',
          animation:connected?'none':'pulse 1.5s infinite'
        }}>
          {connected?'● CONNECTED — AGENTS STANDING BY':'● CONNECTING...'}
        </div>
      </div>

      <canvas ref={canvasRef} style={{
        flex:1, width:'100%', borderRadius:'12px',
        border:'1px solid rgba(55,65,81,0.3)'
      }}/>

      <div style={{
        flexShrink:0, background:'rgba(8,8,20,0.9)',
        border:'1px solid rgba(79,142,247,0.2)',
        borderRadius:'10px', padding:'10px 14px',
        display:'flex', gap:'10px', alignItems:'flex-end'
      }}>
        <textarea
          value={task}
          onChange={e=>setTask(e.target.value)}
          onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}}
          placeholder="Ask ChiChi, Nezuko and Mikasa anything..."
          disabled={running||!connected}
          rows={2}
          style={{
            flex:1, background:'transparent', border:'none',
            color:'#e5e7eb', fontFamily:'monospace',
            fontSize:13, resize:'none', lineHeight:1.5
          }}
        />
        <button onClick={send} disabled={!task.trim()||running||!connected} style={{
          padding:'8px 18px',
          background:running?'rgba(79,142,247,0.15)':'rgba(79,142,247,0.85)',
          border:'1px solid #4f8ef7', borderRadius:'8px',
          color:'white', fontFamily:'monospace',
          fontSize:11, fontWeight:700, cursor:running?'wait':'pointer',
          letterSpacing:1, whiteSpace:'nowrap'
        }}>
          {running?'PROCESSING...':'DEPLOY \u2192'}
        </button>
      </div>

      <div style={{flexShrink:0, display:'flex', gap:'10px', height:'160px'}}>
        <div style={{
          flex:1, background:'rgba(5,5,16,0.9)',
          border:'1px solid rgba(55,65,81,0.3)',
          borderRadius:'10px', overflow:'hidden',
          display:'flex', flexDirection:'column'
        }}>
          <div style={{
            padding:'6px 12px', flexShrink:0,
            borderBottom:'1px solid rgba(55,65,81,0.3)',
            fontSize:9, letterSpacing:2, color:'#4b5563'
          }}>ACTIVITY FEED</div>
          <div ref={logRef} style={{flex:1, overflowY:'auto', padding:'4px 0'}}>
            {log.length===0
              ? <div style={{padding:12,color:'#1f2937',fontSize:11,textAlign:'center'}}>Awaiting deployment...</div>
              : log.map(e=>(
                <div key={e.id} style={{
                  padding:'4px 12px', animation:'fadeIn 0.2s ease',
                  borderBottom:'1px solid rgba(55,65,81,0.1)'
                }}>
                  <span style={{color:'#374151',fontSize:9}}>{e.time} </span>
                  <span style={{color:e.color,fontWeight:700,fontSize:10}}>[{e.name}] </span>
                  <span style={{color:'#9ca3af',fontSize:11}}>{e.msg}</span>
                </div>
              ))
            }
          </div>
        </div>

        <div style={{
          flex:1.4, background:'rgba(5,5,16,0.9)',
          border:`1px solid ${finalAnswer?'rgba(167,139,250,0.4)':'rgba(55,65,81,0.3)'}`,
          borderRadius:'10px', overflow:'hidden',
          display:'flex', flexDirection:'column',
          transition:'border-color 0.5s'
        }}>
          <div style={{
            padding:'6px 12px', flexShrink:0,
            borderBottom:'1px solid rgba(55,65,81,0.3)',
            fontSize:9, letterSpacing:2,
            color:finalAnswer?'#a78bfa':'#4b5563'
          }}>
            {finalAnswer?"\u2728 CHICHI'S REPORT":'FINAL ANSWER'}
          </div>
          <div style={{flex:1, overflowY:'auto', padding:'10px 12px'}}>
            {finalAnswer
              ? <div style={{
                  fontSize:12,color:'#d1d5db',lineHeight:1.7,
                  animation:'fadeIn 0.5s ease',whiteSpace:'pre-wrap'
                }}>{finalAnswer}</div>
              : <div style={{color:'#1f2937',fontSize:11,textAlign:'center',marginTop:50}}>
                  Report will appear here...
                </div>
            }
          </div>
        </div>
      </div>
    </div>
  )
}
