// ══════════════════════════════════════════════════════════
// GLOBALS
// ══════════════════════════════════════════════════════════
const $ = id => document.getElementById(id)
let currentPlayerTag='', currentClanTag=''
let allBattleLog=[], allWarLog=[], allMembers=[], currentClanData={}
let playerPeriodDays=7, clanPeriodCount=5
const chartInstances={}

Chart.defaults.color='#7a8aaa'
Chart.defaults.borderColor='#2a3a5c'
Chart.defaults.font.family="'Nunito', sans-serif"
Chart.defaults.plugins.legend.labels.padding=14
Chart.defaults.plugins.legend.labels.usePointStyle=true
const PALETTE=['#f5c842','#3b82f6','#22c55e','#ef4444','#a855f7','#fb923c','#06b6d4','#ec4899']
const WEEKDAYS=['Dom','Seg','Ter','Qua','Qui','Sex','Sáb']
const ROLES={leader:'Líder',coLeader:'Co-Líder',elder:'Ancião',member:'Membro'}

// ── ÍCONES ─────────────────────────────────────────────
// Conjunto de ícones em SVG (estilo linha), no mesmo espírito do brasão do
// cabeçalho. Cada ícone herda a cor do texto ao redor via currentColor —
// por isso badges/estatísticas que já trocam de cor (ex: trophyColor())
// continuam funcionando sem nenhuma mudança na lógica que as envolve.
function ic(name){
  return `<svg class="ic" viewBox="0 0 24 24"><use href="#ic-${name}" width="24" height="24"></use></svg>`
}

// ── UTILS ──────────────────────────────────────────────
function apiKey(){ return $('apiKey').value.trim() }
function trophyColor(t){ return t>=7000?'#ff4da6':t>=5000?'#ffd700':t>=3000?'#c0c0c0':'#cd7f32' }
function fmtDate(ts){
  const s=String(ts); if(s.length<8) return s
  const h=s.length>9?s.slice(9,11):'00', m=s.length>11?s.slice(11,13):'00'
  return `${s.slice(6,8)}/${s.slice(4,6)}/${s.slice(0,4)} ${h}:${m}`
}
function parseTs(ts){
  const s=String(ts); if(s.length<8) return null
  return new Date(`${s.slice(0,4)}-${s.slice(4,6)}-${s.slice(6,8)}T${s.length>9?s.slice(9,11):'00'}:${s.length>11?s.slice(11,13):'00'}:00`)
}
function showError(msg){const el=$('errorBox');el.innerHTML=ic('warning')+' ';el.append(msg);el.classList.remove('hidden')}
function clearError(){$('errorBox').classList.add('hidden')}
async function apiFetch(url){
  const res=await fetch(url,{headers:{'X-Api-Key':apiKey()}})
  const data=await res.json()
  if(!res.ok) throw new Error(data.message||`Erro ${res.status}`)
  return data
}
function destroyChart(id){if(chartInstances[id]){chartInstances[id].destroy();delete chartInstances[id]}}
function emptyState(icon,msg){return `<div class="empty"><div class="icon">${icon}</div><p>${msg}</p></div>`}

// ── DOWNLOADS ──────────────────────────────────────────
function downloadPlayer(fmt){
  if(!currentPlayerTag){showError('Pesquise um jogador primeiro.');return}
  if(!apiKey()){showError('Insira sua chave de API.');return}
  window.location.href=`/download/player/${currentPlayerTag.replace(/^#/,'')}/${fmt}?key=${encodeURIComponent(apiKey())}`
}
function downloadClan(fmt){
  if(!currentClanTag){showError('Pesquise um clã primeiro.');return}
  if(!apiKey()){showError('Insira sua chave de API.');return}
  window.location.href=`/download/clan/${currentClanTag.replace(/^#/,'')}/${fmt}?key=${encodeURIComponent(apiKey())}`
}

// ── TABS ──────────────────────────────────────────────
function switchTab(tab){
  $('tabPlayer').classList.toggle('hidden',tab!=='player')
  $('tabClan').classList.toggle('hidden',  tab!=='clan')
  clearError()
  document.querySelectorAll('.tabs .tab').forEach((el,i)=>{
    el.classList.toggle('active',(tab==='player'&&i===0)||(tab==='clan'&&i===1))
  })
}
function switchPlayerTab(tab){
  const tabs=['profile','battles','wars','tournaments','charts']
  tabs.forEach(t=>$('pt'+t[0].toUpperCase()+t.slice(1)).classList.toggle('hidden',t!==tab))
  document.querySelectorAll('#tabPlayer .sub-tab').forEach((el,i)=>el.classList.toggle('active',i===tabs.indexOf(tab)))
  if(tab==='charts') renderPlayerCharts()
}
function switchClanTab(tab){
  const tabs=['info','members','wars','charts']
  tabs.forEach(t=>$('ct'+t[0].toUpperCase()+t.slice(1)).classList.toggle('hidden',t!==tab))
  document.querySelectorAll('#tabClan .sub-tab').forEach((el,i)=>el.classList.toggle('active',i===tabs.indexOf(tab)))
  if(tab==='charts') renderClanCharts()
}

// ── FILTROS PERÍODO JOGADOR ────────────────────────────
function setPlayerPeriod(days,btn){
  playerPeriodDays=days;$('pDateFrom').value='';$('pDateTo').value=''
  document.querySelectorAll('#ptCharts .period-btn').forEach(b=>b.classList.remove('active'))
  btn.classList.add('active');renderPlayerCharts()
}
function applyPlayerCustomRange(){
  playerPeriodDays=-1
  document.querySelectorAll('#ptCharts .period-btn').forEach(b=>b.classList.remove('active'))
  renderPlayerCharts()
}
function filterBattlesByPeriod(battles){
  const now=new Date()
  const from=$('pDateFrom').value?new Date($('pDateFrom').value):null
  const to  =$('pDateTo').value  ?new Date($('pDateTo').value+'T23:59:59'):null
  return battles.filter(b=>{
    const d=parseTs(b.battleTime); if(!d) return false
    if(from&&to) return d>=from&&d<=to
    if(playerPeriodDays<=0) return true
    return d>=new Date(now-playerPeriodDays*86400000)
  })
}

// ── FILTROS CLÃ ────────────────────────────────────────
function setClanPeriod(n,btn){
  clanPeriodCount=n
  document.querySelectorAll('#ctCharts .period-btn').forEach(b=>b.classList.remove('active'))
  btn.classList.add('active');renderClanCharts()
}
function filterWarlog(w){ return clanPeriodCount<=0?w:w.slice(0,clanPeriodCount) }

// ══════════════════════════════════════════════════════════
// BUSCA JOGADOR
// ══════════════════════════════════════════════════════════
async function searchPlayer(){
  if(!apiKey()){showError('Insira sua chave de API.');return}
  const tag=$('playerTag').value.trim().replace(/^#/,'')
  if(!tag){showError('Insira a tag do jogador.');return}
  clearError();$('playerResult').classList.add('hidden')
  $('spinnerPlayer').classList.remove('hidden');$('btnPlayer').disabled=true
  try{
    const [p,blog]=await Promise.all([
      apiFetch(`/api/player/${tag}`),
      apiFetch(`/api/player/${tag}/battlelog`)
    ])
    allBattleLog=Array.isArray(blog)?blog:(blog.items||[])
    currentPlayerTag=p.tag||('#'+tag)
    renderPlayer(p,allBattleLog)
    $('playerResult').classList.remove('hidden')
    switchPlayerTab('profile')
  }catch(e){showError('Erro ao buscar jogador: '+e.message)}
  finally{$('spinnerPlayer').classList.add('hidden');$('btnPlayer').disabled=false}
}

function renderPlayer(p,blog){
  $('pName').textContent   =p.name
  $('pTag').textContent    =p.tag
  $('pTrophies').innerHTML =`<span style="font-size:13px;font-weight:700;color:${trophyColor(p.trophies)}">${ic('trophy')} ${(p.trophies||0).toLocaleString()} Troféus</span>`
  $('pBest').innerHTML     =`<span style="font-size:13px;font-weight:700;color:#fbbf24">${ic('star')} ${(p.bestTrophies||0).toLocaleString()} Máx.</span>`
  $('pLevel').innerHTML  =`${ic('crown')} Nível ${p.expLevel}`
  $('pClanBadge').innerHTML=p.clan?`<span class="badge badge-purple">${ic('castle')} ${p.clan.name}</span>`:`<span class="badge badge-gray">Sem Clã</span>`

  $('pStats').innerHTML=[
    {v:p.trophies,l:`${ic('trophy')} Troféus`,c:trophyColor(p.trophies)},
    {v:p.bestTrophies,l:`${ic('star')} Melhor`,c:'#fbbf24'},
    {v:p.wins,l:`${ic('check')} Vitórias`,c:'#4ade80'},
    {v:p.losses,l:`${ic('cross')} Derrotas`,c:'#f87171'},
    {v:p.battleCount,l:`${ic('sword')} Batalhas`,c:'#60a5fa'},
    {v:p.threeCrownWins,l:`${ic('crown')} 3 Coroas`,c:'#c084fc'},
  ].map(s=>`<div class="stat-card"><div class="stat-value" style="color:${s.c}">${(s.v||0).toLocaleString()}</div>
    <div class="stat-label">${s.l}</div></div>`).join('')

  $('pClanCard').innerHTML=p.clan?`<div class="card">
    <div class="card-header"><span>${ic('castle')}</span><span class="card-title">Clã Atual</span></div>
    <div class="card-body" style="display:flex;gap:14px;align-items:center">
      <div style="width:48px;height:48px;border-radius:10px;background:linear-gradient(135deg,#7c3aed,#4f46e5);
        display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">${ic('shield')}</div>
      <div>
        <div style="font-family:'Cinzel',serif;font-size:15px;font-weight:700;margin-bottom:3px">${p.clan.name}</div>
        <div style="font-size:11px;color:var(--muted);font-family:monospace;margin-bottom:6px">${p.clan.tag}</div>
        <span class="badge badge-purple">${ROLES[p.role]||p.role}</span>
      </div>
    </div></div>`:''

  const WAR_TYPES=['riverRacePvP','riverRace','boatBattle']
  const TOUR_TYPES=['tournament','challengeFinal','challenge']
  const wars   =blog.filter(b=>WAR_TYPES.includes(b.type))
  const tours  =blog.filter(b=>TOUR_TYPES.includes(b.type))
  const regular=blog.filter(b=>!WAR_TYPES.includes(b.type)&&!TOUR_TYPES.includes(b.type))

  $('btnBattles').innerHTML   =`${ic('sword')} Batalhas (${regular.length})`
  $('btnWars').innerHTML      =`${ic('flag')} Guerras (${wars.length})`
  $('btnTournaments').innerHTML=`${ic('trophy')} Torneios (${tours.length})`

  $('listBattles').innerHTML =regular.length?regular.map(simpleBattleCard).join(''):emptyState(ic('sword'),'Nenhuma batalha recente.')
  $('listTournaments').innerHTML=tours.length?tours.map(simpleBattleCard).join(''):emptyState(ic('trophy'),'Nenhum torneio recente.')

  renderWarSection(wars)
}

// ── SIMPLE BATTLE CARD (não-guerra) ───────────────────
function simpleBattleCard(b){
  const myC=b.team?.[0]?.crowns??0,opC=b.opponent?.[0]?.crowns??0
  const r=myC>opC?'win':myC<opC?'loss':'draw', l=r==='win'?'V':r==='loss'?'D':'E'
  const opName=b.opponent?.[0]?.name||'Desconhecido', opTag=b.opponent?.[0]?.tag||''
  return `<div class="battle-item">
    <div class="result-box ${r}">${l}</div>
    <div>
      <div style="font-size:13px;font-weight:700;margin-bottom:2px">vs ${opName}
        <span style="font-size:10px;color:var(--muted);font-family:monospace">${opTag}</span></div>
      <div style="font-size:11px;color:var(--muted)">${b.arena?.name||''} · ${fmtDate(b.battleTime)}
        · <span class="badge badge-gray" style="font-size:10px">${b.type}</span></div>
    </div>
    <div class="crowns"><span style="color:#4ade80">${myC}</span><span style="color:var(--gold)">${ic('crown')}</span><span style="color:#f87171">${opC}</span></div>
  </div>`
}

// ══════════════════════════════════════════════════════════
// SEÇÃO DE GUERRAS — DETALHADA
// ══════════════════════════════════════════════════════════
function renderWarSection(wars){
  if(!wars.length){
    $('warContent').innerHTML=emptyState(ic('flag'),'Nenhuma batalha de guerra no histórico recente.')
    return
  }

  const pvp   =wars.filter(b=>b.type==='riverRacePvP')
  const boat  =wars.filter(b=>b.type==='boatBattle')
  const other =wars.filter(b=>b.type==='riverRace')

  // ── KPIs de guerra ──
  const wins  =wars.filter(b=>(b.team?.[0]?.crowns??0)>(b.opponent?.[0]?.crowns??0)).length
  const losses=wars.filter(b=>(b.team?.[0]?.crowns??0)<(b.opponent?.[0]?.crowns??0)).length
  const draws =wars.length-wins-losses
  const winRate=wars.length?((wins/wars.length)*100).toFixed(1):0
  const totalCrowns=wars.filter(b=>b.type!=='boatBattle').reduce((s,b)=>s+(b.team?.[0]?.crowns??0),0)
  const avgCrowns=pvp.length?(totalCrowns/pvp.length).toFixed(1):0

  // ── Calcular elixir médio dos decks usados ──
  function avgElixir(battles){
    const decks=battles.filter(b=>b.team?.[0]?.cards?.length).map(b=>b.team[0].cards)
    if(!decks.length) return null
    const total=decks.reduce((s,cards)=>{
      const sum=cards.reduce((cs,c)=>cs+(c.elixirCost||0),0)
      return s+sum/cards.length
    },0)
    return (total/decks.length).toFixed(1)
  }
  const avgElixirVal=avgElixir(pvp)

  const kpiData=[
    {v:wars.length,     l:'Batalhas de Guerra', c:'#60a5fa'},
    {v:`${winRate}%`,   l:'Taxa de Vitória',    c:'#4ade80'},
    {v:wins,            l:'Vitórias PvP',        c:'#4ade80'},
    {v:totalCrowns,     l:'Coroas Marcadas',     c:trophyColor(4000)},
    {v:pvp.length,      l:'Batalhas PvP',        c:'#f5c842'},
    {v:boat.length,     l:'Ataques ao Barco',    c:'#fb923c'},
    {v:avgCrowns,       l:'Média de Coroas/Bat.', c:'#c084fc'},
    {v:avgElixirVal||'—',l:'Elixir Médio/Deck',  c:'#a855f7'},
  ]

  let html=`<div class="grid4" style="grid-template-columns:repeat(4,1fr)">
    ${kpiData.map(k=>`<div class="kpi"><div class="kpi-val" style="color:${k.c}">${k.v}</div>
      <div class="kpi-lbl">${k.l}</div></div>`).join('')}
  </div>`

  // ── Gráficos de guerra ──
  html+=`<div class="chart-grid" style="margin-bottom:16px">
    <div class="chart-card">
      <div class="chart-header"><span class="chart-title">${ic('check')} Resultados nas Guerras</span></div>
      <div class="chart-body"><div class="chart-wrap"><canvas id="chartWarResults"></canvas></div></div>
    </div>
    <div class="chart-card">
      <div class="chart-header"><span class="chart-title">${ic('sword')} PvP vs ${ic('boat')} Barco vs Outros</span></div>
      <div class="chart-body"><div class="chart-wrap"><canvas id="chartWarTypes"></canvas></div></div>
    </div>
    <div class="chart-card full">
      <div class="chart-header"><span class="chart-title">${ic('crown')} Coroas por Batalha de Guerra (Cronológico)</span></div>
      <div class="chart-body"><div class="chart-wrap"><canvas id="chartWarCrowns"></canvas></div></div>
    </div>
  </div>`

  // ── Batalhas PvP ──
  if(pvp.length){
    html+=`<div class="war-section">
      <div class="war-section-title">${ic('sword')} Batalhas PvP (River Race) — ${pvp.length} batalhas
        <span class="badge badge-purple" style="margin-left:auto">${((wins/pvp.length)*100).toFixed(0)}% vitórias</span>
      </div>
      ${pvp.map((b,i)=>warBattleCard(b,i,'pvp')).join('')}
    </div>`
  }

  // ── Ataques ao Barco ──
  if(boat.length){
    const boatWins=boat.filter(b=>(b.team?.[0]?.crowns??0)>(b.opponent?.[0]?.crowns??0)).length
    html+=`<div class="war-section">
      <div class="war-section-title">${ic('boat')} Ataques ao Barco — ${boat.length} batalha${boat.length>1?'s':''}
        <span class="badge badge-orange" style="margin-left:auto">${boatWins} vitória${boatWins!==1?'s':''}</span>
      </div>
      ${boat.map((b,i)=>warBattleCard(b,i,'boat')).join('')}
    </div>`
  }

  // ── Outros tipos de guerra ──
  if(other.length){
    html+=`<div class="war-section">
      <div class="war-section-title">${ic('flag')} Outros (${other[0].type}) — ${other.length} batalha${other.length>1?'s':''}</div>
      ${other.map((b,i)=>warBattleCard(b,i,'other')).join('')}
    </div>`
  }

  $('warContent').innerHTML=html

  // Renderizar gráficos de guerra após inserir HTML
  setTimeout(()=>{
    // Resultados
    destroyChart('chartWarResults')
    chartInstances['chartWarResults']=new Chart($('chartWarResults'),{
      type:'doughnut',
      data:{labels:['Vitórias','Derrotas','Empates'],
        datasets:[{data:[wins,losses,draws],
          backgroundColor:['rgba(34,197,94,.8)','rgba(239,68,68,.8)','rgba(122,138,170,.6)'],
          borderColor:['#22c55e','#ef4444','#7a8aaa'],borderWidth:2}]},
      options:{responsive:true,maintainAspectRatio:false,
        plugins:{legend:{position:'bottom'},tooltip:{callbacks:{
          label:ctx=>`${ctx.label}: ${ctx.parsed} (${((ctx.parsed/wars.length)*100).toFixed(1)}%)`
        }}}}
    })

    // Tipos de guerra
    destroyChart('chartWarTypes')
    chartInstances['chartWarTypes']=new Chart($('chartWarTypes'),{
      type:'doughnut',
      data:{labels:['PvP','Barco','Outros'],
        datasets:[{data:[pvp.length,boat.length,other.length],
          backgroundColor:['rgba(245,200,66,.8)','rgba(251,146,60,.8)','rgba(122,138,170,.6)'],
          borderColor:['#f5c842','#fb923c','#7a8aaa'],borderWidth:2}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}}}
    })

    // Coroas por batalha (cronológico)
    const sortedPvp=[...pvp].sort((a,b)=>String(a.battleTime).localeCompare(String(b.battleTime)))
    const crownLabels=sortedPvp.map((b,i)=>i+1)
    const myCrowns=sortedPvp.map(b=>b.team?.[0]?.crowns??0)
    const opCrowns=sortedPvp.map(b=>b.opponent?.[0]?.crowns??0)
    destroyChart('chartWarCrowns')
    if(sortedPvp.length){
      chartInstances['chartWarCrowns']=new Chart($('chartWarCrowns'),{
        type:'bar',
        data:{labels:crownLabels,
          datasets:[
            {label:'Suas Coroas',data:myCrowns,backgroundColor:'rgba(245,200,66,.75)',borderColor:'#f5c842',borderWidth:1},
            {label:'Coroas Sofridas',data:opCrowns,backgroundColor:'rgba(239,68,68,.6)',borderColor:'#ef4444',borderWidth:1},
          ]},
        options:{responsive:true,maintainAspectRatio:false,
          scales:{x:{ticks:{color:'#7a8aaa'},grid:{display:false},title:{display:true,text:'Batalha #',color:'#7a8aaa'}},
                  y:{min:0,max:3,ticks:{stepSize:1,color:'#7a8aaa'},grid:{color:'#2a3a5c'}}},
          plugins:{legend:{position:'bottom'}}
        }
      })
    }
  },50)
}

// ── WAR BATTLE CARD (expansível com deck) ─────────────
function warBattleCard(b,idx,tipo){
  const myC=b.team?.[0]?.crowns??0, opC=b.opponent?.[0]?.crowns??0
  const r=myC>opC?'win':myC<opC?'loss':'draw', l=r==='win'?'V':r==='loss'?'D':'E'
  const opName=b.opponent?.[0]?.name||'Desconhecido', opTag=b.opponent?.[0]?.tag||''
  const myCards=b.team?.[0]?.cards||[]
  const opCards=b.opponent?.[0]?.cards||[]

  // King tower HP
  const myKingHP=b.team?.[0]?.kingTowerHitPoints
  const opKingHP=b.opponent?.[0]?.kingTowerHitPoints
  const myPrincessHP=b.team?.[0]?.princessTowersHitPoints||[]
  const opPrincessHP=b.opponent?.[0]?.princessTowersHitPoints||[]

  // Modo / arena
  const arena=b.arena?.name||''
  const mode=b.gameMode?.name||b.type

  // Calcular elixir médio
  function elixirMedio(cards){ if(!cards.length) return null; return (cards.reduce((s,c)=>s+(c.elixirCost||0),0)/cards.length).toFixed(1) }
  const myElixir=elixirMedio(myCards), opElixir=elixirMedio(opCards)

  const typeIco=tipo==='boat'?ic('boat'):tipo==='pvp'?ic('sword'):ic('flag')
  const id=`wbd-${tipo}-${idx}`

  const towerInfo=(kingHP,princessHP)=>{
    if(!kingHP&&!princessHP.length) return ''
    const pts=[kingHP?`${ic('crown')} ${kingHP}HP`:'',
      ...princessHP.map((h,i)=>`${ic('tower')}${i+1} ${h}HP`)].filter(Boolean).join('  ')
    return `<span style="font-size:10px;color:var(--muted)">${pts}</span>`
  }

  return `<div class="war-battle">
    <div class="war-battle-header" onclick="toggleWarBattle('${id}')">
      <div class="result-box ${r}">${l}</div>
      <div style="min-width:0">
        <div style="font-size:13px;font-weight:700;margin-bottom:2px">
          ${typeIco} vs ${opName}
          <span style="font-size:10px;color:var(--muted);font-family:monospace">${opTag}</span>
        </div>
        <div style="font-size:11px;color:var(--muted);display:flex;gap:8px;flex-wrap:wrap">
          <span>${fmtDate(b.battleTime)}</span>
          ${arena?`<span>${ic('arena')} ${arena}</span>`:''}
          ${myElixir?`<span><span class="elixir-dot"></span>${myElixir} elixir</span>`:''}
          ${myCards.length?`<span>🃏 ${myCards.length} cartas</span>`:''}
        </div>
      </div>
      <div class="crowns"><span style="color:#4ade80">${myC}</span><span style="color:var(--gold)">${ic('crown')}</span><span style="color:#f87171">${opC}</span></div>
      <span style="color:var(--muted);font-size:12px;margin-left:4px" id="arr-${id}">▼</span>
    </div>
    <div class="war-battle-body hidden" id="${id}">
      <!-- Torres -->
      ${(myKingHP||opKingHP)?`<div style="display:flex;gap:16px;margin-bottom:12px;flex-wrap:wrap">
        <div style="font-size:12px"><span style="color:#4ade80;font-weight:700">Suas Torres:</span>
          ${towerInfo(myKingHP,myPrincessHP)||'<span style="color:var(--muted)">—</span>'}</div>
        <div style="font-size:12px"><span style="color:#f87171;font-weight:700">Torres do Oponente:</span>
          ${towerInfo(opKingHP,opPrincessHP)||'<span style="color:var(--muted)">—</span>'}</div>
      </div>`:''}

      <!-- Decks -->
      <div class="grid2" style="gap:12px">
        ${myCards.length?`<div>
          <div style="font-size:11px;font-weight:700;color:#4ade80;text-transform:uppercase;
            letter-spacing:.5px;margin-bottom:8px">🃏 Seu Deck ${myElixir?`<span style="color:#a855f7;margin-left:6px"><span class="elixir-dot"></span>${myElixir} elixir médio</span>`:''}
          </div>
          <div class="deck-grid">${myCards.map(c=>`<div class="deck-card">
            <div class="deck-card-name">${c.name}</div>
            <div><span class="deck-card-lvl">Nv.${c.level||'?'}</span>
              ${c.elixirCost?`<span class="deck-card-elixir"> · ${c.elixirCost}${ic('droplet')}</span>`:''}</div>
          </div>`).join('')}</div>
        </div>`:'<div style="color:var(--muted);font-size:12px">Deck não disponível</div>'}

        ${opCards.length?`<div>
          <div style="font-size:11px;font-weight:700;color:#f87171;text-transform:uppercase;
            letter-spacing:.5px;margin-bottom:8px">🃏 Deck do Oponente ${opElixir?`<span style="color:#a855f7;margin-left:6px"><span class="elixir-dot"></span>${opElixir} elixir médio</span>`:''}
          </div>
          <div class="deck-grid">${opCards.map(c=>`<div class="deck-card">
            <div class="deck-card-name">${c.name}</div>
            <div><span class="deck-card-lvl">Nv.${c.level||'?'}</span>
              ${c.elixirCost?`<span class="deck-card-elixir"> · ${c.elixirCost}${ic('droplet')}</span>`:''}</div>
          </div>`).join('')}</div>
        </div>`:''}
      </div>
    </div>
  </div>`
}

function toggleWarBattle(id){
  const body=$(''+id), arr=$('arr-'+id)
  const isHidden=body.classList.contains('hidden')
  body.classList.toggle('hidden',!isHidden)
  if(arr) arr.textContent=isHidden?'▲':'▼'
}

// ══════════════════════════════════════════════════════════
// GRÁFICOS — JOGADOR (gerais)
// ══════════════════════════════════════════════════════════
function renderPlayerCharts(){
  const battles=filterBattlesByPeriod(allBattleLog)
  if(!battles.length){
    $('pKpis').innerHTML=`<div style="grid-column:1/-1;text-align:center;color:var(--muted);padding:20px">Nenhuma batalha no período.</div>`
    ;['chartTrophies','chartResults','chartCrowns','chartTypes','chartArena','chartWeekday'].forEach(destroyChart)
    return
  }
  const wins=battles.filter(b=>(b.team?.[0]?.crowns??0)>(b.opponent?.[0]?.crowns??0)).length
  const losses=battles.filter(b=>(b.team?.[0]?.crowns??0)<(b.opponent?.[0]?.crowns??0)).length
  const draws=battles.length-wins-losses
  const winRate=battles.length?((wins/battles.length)*100).toFixed(1):0
  const totalCrowns=battles.reduce((s,b)=>s+(b.team?.[0]?.crowns??0),0)

  $('pKpis').innerHTML=[
    {v:battles.length,l:'Batalhas',c:'#60a5fa'},
    {v:`${winRate}%`, l:'Taxa de Vitória',c:'#4ade80'},
    {v:wins,          l:'Vitórias',c:'#4ade80'},
    {v:totalCrowns,   l:'Coroas Marcadas',c:trophyColor(4000)},
  ].map(k=>`<div class="kpi"><div class="kpi-val" style="color:${k.c}">${k.v}</div>
    <div class="kpi-lbl">${k.l}</div></div>`).join('')

  // Troféus
  const trophyData=[...battles]
    .filter(b=>b.team?.[0]?.startingTrophies)
    .sort((a,b)=>String(a.battleTime).localeCompare(String(b.battleTime)))
    .map(b=>({x:parseTs(b.battleTime),y:b.team[0].startingTrophies}))
  destroyChart('chartTrophies')
  if(trophyData.length){
    chartInstances['chartTrophies']=new Chart($('chartTrophies'),{
      type:'line',
      data:{datasets:[{label:'Troféus',data:trophyData,borderColor:'#f5c842',
        backgroundColor:'rgba(245,200,66,.1)',tension:.3,pointRadius:3,pointBackgroundColor:'#f5c842',fill:true}]},
      options:{responsive:true,maintainAspectRatio:false,
        scales:{x:{type:'time',time:{unit:'day',displayFormats:{day:'dd/MM'}},
          ticks:{color:'#7a8aaa'},grid:{color:'#2a3a5c'}},y:{ticks:{color:'#7a8aaa'},grid:{color:'#2a3a5c'}}},
        plugins:{legend:{display:false}}}
    })
  }
  // Resultados
  destroyChart('chartResults')
  chartInstances['chartResults']=new Chart($('chartResults'),{
    type:'doughnut',
    data:{labels:['Vitórias','Derrotas','Empates'],
      datasets:[{data:[wins,losses,draws],
        backgroundColor:['rgba(34,197,94,.8)','rgba(239,68,68,.8)','rgba(122,138,170,.6)'],
        borderColor:['#22c55e','#ef4444','#7a8aaa'],borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'},
      tooltip:{callbacks:{label:ctx=>`${ctx.label}: ${ctx.parsed} (${((ctx.parsed/battles.length)*100).toFixed(1)}%)`}}}}
  })
  // Coroas por dia
  const crownByDay={}
  battles.forEach(b=>{
    const d=parseTs(b.battleTime);if(!d) return
    const key=d.toLocaleDateString('pt-BR')
    if(!crownByDay[key]){crownByDay[key]={mine:0,opp:0}}
    crownByDay[key].mine+=(b.team?.[0]?.crowns??0)
    crownByDay[key].opp +=(b.opponent?.[0]?.crowns??0)
  })
  const crownDays=Object.keys(crownByDay)
  destroyChart('chartCrowns')
  chartInstances['chartCrowns']=new Chart($('chartCrowns'),{
    type:'bar',
    data:{labels:crownDays,datasets:[
      {label:'Suas Coroas',data:crownDays.map(d=>crownByDay[d].mine),backgroundColor:'rgba(245,200,66,.75)',borderColor:'#f5c842',borderWidth:1},
      {label:'Sofridas',data:crownDays.map(d=>crownByDay[d].opp),backgroundColor:'rgba(239,68,68,.6)',borderColor:'#ef4444',borderWidth:1},
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      scales:{x:{ticks:{color:'#7a8aaa',maxRotation:45},grid:{display:false}},y:{ticks:{color:'#7a8aaa'},grid:{color:'#2a3a5c'}}},
      plugins:{legend:{position:'bottom'}}}
  })
  // Tipos
  const typeCounts={}
  battles.forEach(b=>{typeCounts[b.type]=(typeCounts[b.type]||0)+1})
  const typeLabels=Object.keys(typeCounts)
  destroyChart('chartTypes')
  chartInstances['chartTypes']=new Chart($('chartTypes'),{
    type:'doughnut',
    data:{labels:typeLabels,datasets:[{data:typeLabels.map(t=>typeCounts[t]),
      backgroundColor:PALETTE.slice(0,typeLabels.length),borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}}}
  })
  // Arena win rate
  const arenaStats={}
  battles.forEach(b=>{
    const arena=b.arena?.name||'Desconhecida'
    if(!arenaStats[arena]){arenaStats[arena]={w:0,t:0}}
    arenaStats[arena].t++
    if((b.team?.[0]?.crowns??0)>(b.opponent?.[0]?.crowns??0)) arenaStats[arena].w++
  })
  const arenaNames=Object.keys(arenaStats)
  const arenaRates=arenaNames.map(a=>((arenaStats[a].w/arenaStats[a].t)*100).toFixed(1))
  destroyChart('chartArena')
  chartInstances['chartArena']=new Chart($('chartArena'),{
    type:'bar',
    data:{labels:arenaNames,datasets:[{label:'% Vitórias',data:arenaRates,
      backgroundColor:arenaRates.map(r=>r>=50?'rgba(34,197,94,.7)':'rgba(239,68,68,.6)'),
      borderColor:arenaRates.map(r=>r>=50?'#22c55e':'#ef4444'),borderWidth:1}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      scales:{x:{min:0,max:100,ticks:{color:'#7a8aaa',callback:v=>v+'%'},grid:{color:'#2a3a5c'}},
              y:{ticks:{color:'#7a8aaa'},grid:{display:false}}},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>`${ctx.parsed.x}% vitórias`}}}}
  })
  // Dia da semana
  const wdC=[0,0,0,0,0,0,0],wdW=[0,0,0,0,0,0,0]
  battles.forEach(b=>{
    const d=parseTs(b.battleTime);if(!d) return
    const wd=d.getDay();wdC[wd]++
    if((b.team?.[0]?.crowns??0)>(b.opponent?.[0]?.crowns??0)) wdW[wd]++
  })
  destroyChart('chartWeekday')
  chartInstances['chartWeekday']=new Chart($('chartWeekday'),{
    type:'bar',
    data:{labels:WEEKDAYS,datasets:[
      {label:'Total',data:wdC,backgroundColor:'rgba(59,130,246,.5)',borderColor:'#3b82f6',borderWidth:1},
      {label:'Vitórias',data:wdW,backgroundColor:'rgba(34,197,94,.7)',borderColor:'#22c55e',borderWidth:1},
    ]},
    options:{responsive:true,maintainAspectRatio:false,
      scales:{x:{ticks:{color:'#7a8aaa'},grid:{display:false}},y:{ticks:{color:'#7a8aaa'},grid:{color:'#2a3a5c'}}},
      plugins:{legend:{position:'bottom'}}}
  })
}

// ══════════════════════════════════════════════════════════
// BUSCA CLÃ
// ══════════════════════════════════════════════════════════
async function searchClan(){
  if(!apiKey()){showError('Insira sua chave de API.');return}
  const tag=$('clanTag').value.trim().replace(/^#/,'')
  if(!tag){showError('Insira a tag do clã.');return}
  clearError();$('clanResult').classList.add('hidden')
  $('spinnerClan').classList.remove('hidden');$('btnClan').disabled=true
  try{
    const [clan,members,warlog]=await Promise.all([
      apiFetch(`/api/clan/${tag}`),
      apiFetch(`/api/clan/${tag}/members`),
      apiFetch(`/api/clan/${tag}/warlog`)
    ])
    currentClanTag=clan.tag||('#'+tag)
    currentClanData=clan
    allMembers=members.items||[]
    allWarLog=warlog.items||[]
    renderClan(clan,allMembers,allWarLog)
    $('clanResult').classList.remove('hidden')
    switchClanTab('info')
  }catch(e){showError('Erro ao buscar clã: '+e.message)}
  finally{$('spinnerClan').classList.add('hidden');$('btnClan').disabled=false}
}

function renderClan(c,members,warlog){
  $('cName').textContent=c.name;$('cTag').textContent=c.tag
  $('cDesc').textContent=c.description||''
  $('cScore').innerHTML=`<span style="font-size:13px;font-weight:700;color:var(--gold)">${ic('trophy')} ${(c.clanScore||0).toLocaleString()} pts</span>`
  $('cMembers').innerHTML=`${ic('people')} ${c.members}/50`
  $('cWarTrophies').innerHTML=`${ic('anchor')} ${(c.clanWarTrophies||0).toLocaleString()}`
  const typeLabel={open:`${ic('lockOpen')} Aberto`,inviteOnly:`${ic('envelope')} Apenas convite`,closed:`${ic('lock')} Fechado`}
  $('ctInfo').innerHTML=`<div class="card">
    <div class="card-header"><span>${ic('chart')}</span><span class="card-title">Informações do Clã</span></div>
    <div class="card-body">${[
      ['Tipo',typeLabel[c.type]||c.type],['Localização',c.location?`${ic('globe')} ${c.location.name}`:'—'],
      ['Membros',`${ic('people')} ${c.members}/50`],['Pontuação',`${ic('trophy')} ${(c.clanScore||0).toLocaleString()}`],
      ['Troféus de Guerra',`${ic('anchor')} ${(c.clanWarTrophies||0).toLocaleString()}`],
      ['Doações/Semana',`${ic('gift')} ${(c.donationsPerWeek||0).toLocaleString()}`],
      ['Troféus Mínimos',`${ic('medal')} ${(c.requiredTrophies||0).toLocaleString()}`],
    ].map(([l,v])=>`<div style="display:flex;justify-content:space-between;align-items:center;
      padding:8px 12px;background:var(--surface2);border-radius:6px;font-size:13px;margin-bottom:6px">
      <span style="color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:1px">${l}</span>
      <span style="font-weight:700">${v}</span></div>`).join('')}</div></div>`

  $('btnMembers').innerHTML=`${ic('people')} Membros (${members.length})`
  $('ctMembers').innerHTML=`<div class="card">
    <div class="card-header"><span>${ic('people')}</span><span class="card-title">Membros Atuais</span></div>
    <div>${members.map((m,i)=>{
      const rb=m.role==='leader'?'badge-gold':m.role==='coLeader'?'badge-blue':m.role==='elder'?'badge-green':'badge-gray'
      return `<div class="member-row">
        <div class="member-rank">${i+1}</div>
        <div><div class="member-name">${m.name}</div><div class="member-tag">${m.tag}</div></div>
        <div><span class="badge ${rb}" style="font-size:10px">${ROLES[m.role]||m.role}</span></div>
        <div class="member-trophies" style="color:${trophyColor(m.trophies)}">${ic('trophy')} ${(m.trophies||0).toLocaleString()}</div>
      </div>`}).join('')}</div></div>`

  $('btnWarLog').innerHTML=`${ic('anchor')} Guerras (${warlog.length})`
  $('ctWars').innerHTML=warlog.length===0?emptyState(ic('anchor'),'Nenhum histórico de guerra.'):
    warlog.map((race,i)=>{
      const s=race.standings||[],our=s.find(x=>x.clan?.tag===c.tag),oc=our?.clan
      const rb=our?.rank===1?'badge-gold':our?.rank<=3?'badge-blue':'badge-gray'
      const rl=our?.rank===1?`${ic('medal')} 1º`:our?.rank===2?`${ic('medal')} 2º`:our?.rank===3?`${ic('medal')} 3º`:`#${our?.rank}`
      return `<div class="race-card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <div class="race-title">${ic('anchor')} Temporada ${race.seasonId||'#'+(warlog.length-i)}</div>
          ${our?`<span class="badge ${rb}">${rl}</span>`:''}
        </div>
        ${oc?`<div style="background:rgba(245,200,66,.06);border-radius:6px;padding:10px 12px;
          margin-bottom:10px;border:1px solid rgba(245,200,66,.15)">
          <div style="font-size:11px;color:var(--gold);font-weight:700;margin-bottom:6px">NOSSO DESEMPENHO</div>
          <div style="display:flex;gap:20px;font-size:12px;flex-wrap:wrap">
            <div><strong>${(oc.fame||0).toLocaleString()}</strong> <span style="color:var(--muted)">Fama</span></div>
            <div><strong>${(oc.repairPoints||0).toLocaleString()}</strong> <span style="color:var(--muted)">Reparos</span></div>
            <div><strong>${oc.participants?.length||0}</strong> <span style="color:var(--muted)">Participantes</span></div>
          </div></div>`:''}
        ${s.length?`<table class="war-table"><thead><tr><th>Pos</th><th>Clã</th><th>Fama</th><th>Part.</th></tr></thead>
          <tbody>${[...s].sort((a,b)=>a.rank-b.rank).map(x=>`
            <tr ${x.clan?.tag===c.tag?'class="highlight"':''}>
              <td><span class="badge ${x.rank===1?'badge-gold':x.rank<=3?'badge-blue':'badge-gray'}" style="font-size:10px">
                ${x.rank===1?ic('medal'):x.rank===2?ic('medal'):x.rank===3?ic('medal'):`#${x.rank}`}</span></td>
              <td style="font-weight:${x.clan?.tag===c.tag?700:400}">${x.clan?.tag===c.tag?ic('star')+' ':''}${x.clan?.name||'—'}</td>
              <td style="color:var(--gold);font-weight:700">${(x.clan?.fame||0).toLocaleString()}</td>
              <td style="color:var(--muted)">${x.clan?.participants?.length||0}</td>
            </tr>`).join('')}
          </tbody></table>`:''}
      </div>`}).join('')
}

// ══════════════════════════════════════════════════════════
// GRÁFICOS — CLÃ
// ══════════════════════════════════════════════════════════
function renderClanCharts(){
  const warlog=filterWarlog(allWarLog),c=currentClanData
  const ourRaces=warlog.map(r=>(r.standings||[]).find(s=>s.clan?.tag===c.tag)).filter(Boolean)
  const avgFame=ourRaces.length?Math.round(ourRaces.reduce((s,r)=>s+(r.clan?.fame||0),0)/ourRaces.length):0
  const wins1st=ourRaces.filter(r=>r.rank===1).length
  const avgRank=ourRaces.length?(ourRaces.reduce((s,r)=>s+(r.rank||0),0)/ourRaces.length).toFixed(1):'—'

  $('cKpis').innerHTML=[
    {v:warlog.length,l:'Guerras',c:'#60a5fa'},
    {v:avgFame.toLocaleString(),l:'Fama Média',c:'#f5c842'},
    {v:wins1st,l:'1º Lugares',c:'#ffd700'},
    {v:avgRank,l:'Posição Média',c:'#c084fc'},
  ].map(k=>`<div class="kpi"><div class="kpi-val" style="color:${k.c}">${k.v}</div>
    <div class="kpi-lbl">${k.l}</div></div>`).join('')

  const sLabels=warlog.map((r,i)=>`S${r.seasonId||warlog.length-i}`)
  const fameData=warlog.map(r=>{const our=(r.standings||[]).find(s=>s.clan?.tag===c.tag);return our?.clan?.fame||0})
  const rankData=warlog.map(r=>{const our=(r.standings||[]).find(s=>s.clan?.tag===c.tag);return our?.rank||null})
  const partData=warlog.map(r=>{const our=(r.standings||[]).find(s=>s.clan?.tag===c.tag);return our?.clan?.participants?.length||0})

  destroyChart('chartClanFame')
  chartInstances['chartClanFame']=new Chart($('chartClanFame'),{
    type:'bar',
    data:{labels:[...sLabels].reverse(),datasets:[{label:'Fama',data:[...fameData].reverse(),
      backgroundColor:fameData.map(f=>f>=3500?'rgba(245,200,66,.8)':f>=2000?'rgba(59,130,246,.7)':'rgba(122,138,170,.5)').reverse(),
      borderColor:fameData.map(f=>f>=3500?'#f5c842':f>=2000?'#3b82f6':'#7a8aaa').reverse(),
      borderWidth:1,borderRadius:4}]},
    options:{responsive:true,maintainAspectRatio:false,
      scales:{x:{ticks:{color:'#7a8aaa'},grid:{display:false}},y:{ticks:{color:'#7a8aaa'},grid:{color:'#2a3a5c'}}},
      plugins:{legend:{display:false}}}
  })
  destroyChart('chartClanRank')
  chartInstances['chartClanRank']=new Chart($('chartClanRank'),{
    type:'line',
    data:{labels:[...sLabels].reverse(),datasets:[{label:'Posição',data:[...rankData].reverse(),
      borderColor:'#a855f7',backgroundColor:'rgba(168,85,247,.1)',tension:.3,
      pointRadius:5,pointBackgroundColor:'#a855f7',fill:true}]},
    options:{responsive:true,maintainAspectRatio:false,
      scales:{x:{ticks:{color:'#7a8aaa'},grid:{display:false}},
        y:{reverse:true,min:1,max:5,ticks:{stepSize:1,color:'#7a8aaa',callback:v=>`${v}º`},grid:{color:'#2a3a5c'}}},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>`${ctx.parsed.y}º lugar`}}}}
  })
  destroyChart('chartClanParticipants')
  chartInstances['chartClanParticipants']=new Chart($('chartClanParticipants'),{
    type:'bar',
    data:{labels:[...sLabels].reverse(),datasets:[{label:'Participantes',data:[...partData].reverse(),
      backgroundColor:'rgba(34,197,94,.6)',borderColor:'#22c55e',borderWidth:1,borderRadius:4}]},
    options:{responsive:true,maintainAspectRatio:false,
      scales:{x:{ticks:{color:'#7a8aaa'},grid:{display:false}},y:{ticks:{color:'#7a8aaa'},grid:{color:'#2a3a5c'}}},
      plugins:{legend:{display:false}}}
  })
  // Distribuição troféus membros
  const brackets=[{l:'< 2k',mn:0,mx:1999},{l:'2k–3k',mn:2000,mx:2999},{l:'3k–4k',mn:3000,mx:3999},
    {l:'4k–5k',mn:4000,mx:4999},{l:'5k–6k',mn:5000,mx:5999},{l:'6k–7k',mn:6000,mx:6999},{l:'7k+',mn:7000,mx:Infinity}]
  const bC=brackets.map(b=>allMembers.filter(m=>(m.trophies||0)>=b.mn&&(m.trophies||0)<=b.mx).length)
  const bColors=['rgba(122,138,170,.7)','rgba(59,130,246,.7)','rgba(34,197,94,.7)','rgba(245,200,66,.7)','rgba(251,146,60,.8)','rgba(239,68,68,.8)','rgba(255,77,166,.9)']
  destroyChart('chartMemberTrophies')
  chartInstances['chartMemberTrophies']=new Chart($('chartMemberTrophies'),{
    type:'bar',
    data:{labels:brackets.map(b=>b.l),datasets:[{label:'Membros',data:bC,
      backgroundColor:bColors,borderWidth:1,borderRadius:4}]},
    options:{responsive:true,maintainAspectRatio:false,
      scales:{x:{ticks:{color:'#7a8aaa'},grid:{display:false}},y:{ticks:{stepSize:1,color:'#7a8aaa'},grid:{color:'#2a3a5c'}}},
      plugins:{legend:{display:false}}}
  })
  // Top contribuidores
  const fameTotals={}
  allWarLog.forEach(r=>{
    const our=(r.standings||[]).find(s=>s.clan?.tag===c.tag)
    if(!our) return
    ;(our.clan?.participants||[]).forEach(p=>{
      fameTotals[p.name]=(fameTotals[p.name]||0)+(p.fame||0)
    })
  })
  const topC=Object.entries(fameTotals).sort((a,b)=>b[1]-a[1]).slice(0,15)
  destroyChart('chartTopContrib')
  chartInstances['chartTopContrib']=new Chart($('chartTopContrib'),{
    type:'bar',
    data:{labels:topC.map(([n])=>n),datasets:[{label:'Fama Total',data:topC.map(([,v])=>v),
      backgroundColor:topC.map((_,i)=>i===0?'rgba(255,215,0,.85)':i===1?'rgba(192,192,192,.8)':i===2?'rgba(205,127,50,.8)':'rgba(59,130,246,.65)'),
      borderColor:topC.map((_,i)=>i===0?'#ffd700':i===1?'#c0c0c0':i===2?'#cd7f32':'#3b82f6'),
      borderWidth:1,borderRadius:4}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      scales:{x:{ticks:{color:'#7a8aaa'},grid:{color:'#2a3a5c'}},y:{ticks:{color:'#e8eaf6',font:{size:11}},grid:{display:false}}},
      plugins:{legend:{display:false}}}
  })
  // Doações
  const topDon=[...allMembers].sort((a,b)=>(b.donations||0)-(a.donations||0)).slice(0,10)
  destroyChart('chartDonations')
  chartInstances['chartDonations']=new Chart($('chartDonations'),{
    type:'bar',
    data:{labels:topDon.map(m=>m.name),datasets:[{label:'Doações',data:topDon.map(m=>m.donations||0),
      backgroundColor:'rgba(168,85,247,.7)',borderColor:'#a855f7',borderWidth:1,borderRadius:4}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      scales:{x:{ticks:{color:'#7a8aaa'},grid:{color:'#2a3a5c'}},y:{ticks:{color:'#e8eaf6',font:{size:11}},grid:{display:false}}},
      plugins:{legend:{display:false}}}
  })
  // Cargos
  const rc={leader:0,coLeader:0,elder:0,member:0}
  allMembers.forEach(m=>{if(rc[m.role]!==undefined)rc[m.role]++})
  destroyChart('chartRoles')
  chartInstances['chartRoles']=new Chart($('chartRoles'),{
    type:'doughnut',
    data:{labels:['Líder','Co-Líder','Ancião','Membro'],
      datasets:[{data:[rc.leader,rc.coLeader,rc.elder,rc.member],
        backgroundColor:['rgba(245,200,66,.8)','rgba(59,130,246,.8)','rgba(34,197,94,.7)','rgba(122,138,170,.6)'],
        borderColor:['#f5c842','#3b82f6','#22c55e','#7a8aaa'],borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'}}}
  })
}
