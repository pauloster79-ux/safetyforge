// Direction 03 — SITE BOARD
// Rugged, high-contrast, jobsite-ready.
// Inverted chrome: dark shell, light card. Yellow is dominant.
// Big touch targets, depth, bold custom glyphs.

const SB = {
  bg:     '#17181a',
  bg2:    '#1f2023',
  bg3:    '#292a2e',
  card:   '#fafaf7',
  card2:  '#f3f2ec',
  ink:    '#0e0f10',
  ink2:   '#3a3b3e',
  muted:  '#9da0a5',
  mutedD: '#6a6c70',
  rule:   '#333438',
  ruleL:  '#e6e3d8',
  machine:'#F5B800',
  machineD:'#c98f00',
  pass:   '#39b56a',
  passW:  'rgba(57,181,106,0.16)',
  fail:   '#ff5a47',
  failW:  'rgba(255,90,71,0.14)',
  warn:   '#ffb547',
  warnW:  'rgba(255,181,71,0.14)',
  sans:   "'IBM Plex Sans', system-ui, sans-serif",
  mono:   "'IBM Plex Mono', ui-monospace, monospace",
};

const hazardStripe = `repeating-linear-gradient(-45deg, ${SB.machine} 0 10px, #0e0f10 10px 20px)`;

const sbKick = (c = SB.muted) => ({
  fontFamily: SB.mono, fontSize: 10, fontWeight: 600, letterSpacing: 1.6,
  textTransform:'uppercase', color: c,
});

function SbBadge({tone='muted', children}) {
  const m = {
    machine:{bg: SB.machine, fg: SB.ink},
    pass:   {bg: SB.passW,   fg: SB.pass},
    fail:   {bg: SB.failW,   fg: SB.fail},
    warn:   {bg: SB.warnW,   fg: SB.warn},
    muted:  {bg: SB.bg3,     fg: SB.muted},
    ink:    {bg: SB.ink,     fg: '#fff'},
    paper:  {bg: SB.card2,   fg: SB.ink},
  }[tone];
  return <span style={{
    fontFamily: SB.mono, fontSize: 10, fontWeight: 700, letterSpacing: 1,
    textTransform: 'uppercase', background: m.bg, color: m.fg,
    padding: '3px 8px', borderRadius: 4,
  }}>{children}</span>;
}

function SbBtn({children, primary, dark, icon: I, big}) {
  const dim = big ? {padding: '14px 20px', fontSize: 14} : {padding: '10px 16px', fontSize: 13};
  const style = primary
    ? {background: SB.machine, color: SB.ink, border: `2px solid #0e0f10`, boxShadow: '0 3px 0 #0e0f10, 0 6px 14px rgba(0,0,0,0.35)'}
    : dark ? {background: SB.bg3, color: '#fff', border: `1px solid ${SB.rule}`}
    : {background: SB.card, color: SB.ink, border: `1.5px solid ${SB.ink}`, boxShadow: '0 2px 0 #0e0f10'};
  return <button style={{
    fontFamily: SB.sans, fontWeight: 700, letterSpacing: 0.2,
    borderRadius: 6, display:'inline-flex', alignItems:'center', gap: 8,
    cursor:'pointer', ...dim, ...style,
  }}>{I && <I s={big?18:15} sw={2.2}/>} {children}</button>;
}

// ── SYSTEM ──
function SiteBoardSystem() {
  return (
    <div style={{height:'100%', background: SB.bg, color:'#fff', fontFamily: SB.sans, display:'flex', flexDirection:'column'}}>
      <div style={{height: 6, background: hazardStripe, opacity: 0.9}}/>
      <div style={{padding:'22px 26px 16px'}}>
        <div style={sbKick(SB.machine)}>SITE BOARD · SYSTEM</div>
        <div style={{fontSize: 34, fontWeight: 800, letterSpacing: -0.9, lineHeight: 1, marginTop: 8, textTransform: 'uppercase', fontStretch: 'condensed'}}>Built for gloves.</div>
        <div style={{fontSize: 13, color: SB.muted, marginTop: 8, maxWidth: 520, lineHeight: 1.5}}>
          High-contrast, big touch, yellow everywhere it counts. Designed for the truck at 5:30&nbsp;AM and the jobsite trailer at 4:30&nbsp;PM.
        </div>
      </div>

      <div style={{padding:'8px 26px 24px', display:'flex', flexDirection:'column', gap: 20, overflow:'auto'}}>
        {/* type */}
        <div>
          <div style={sbKick()}>TYPE · PLEX + MONO · HEAVY SCALE</div>
          <div style={{marginTop: 10}}>
            <div style={{fontSize: 44, fontWeight: 800, letterSpacing: -1.2, lineHeight: 1}}>DISPLAY · 44 · 800</div>
            <div style={{fontSize: 26, fontWeight: 700, letterSpacing: -0.5, marginTop: 6, color: SB.machine}}>HEADING · 26 · 700</div>
            <div style={{fontSize: 15, fontWeight: 500, marginTop: 6}}>Subhead 15 · 500</div>
            <div style={{fontSize: 14, color: '#d4d6da', marginTop: 4, lineHeight: 1.55, maxWidth: 540}}>Body 14 — weighted slightly heavier than default. Designed to survive sun glare and cracked screens.</div>
          </div>
        </div>

        {/* color */}
        <div>
          <div style={sbKick()}>COLOR</div>
          <div style={{marginTop: 10, display:'grid', gridTemplateColumns:'repeat(8,1fr)', gap: 6}}>
            {[
              ['#17181a','Shell'],['#1f2023','Shell-2'],['#292a2e','Shell-3'],['#fafaf7','Card'],
              ['#F5B800','Machine'],['#39b56a','Pass'],['#ffb547','Warn'],['#ff5a47','Fail'],
            ].map(([c,l]) => (
              <div key={l}>
                <div style={{height: 52, background: c, borderRadius: 5, border: `1px solid ${SB.rule}`}}/>
                <div style={{...sbKick(), marginTop: 5}}>{l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* elevation */}
        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap: 14}}>
          <div>
            <div style={sbKick()}>DEPTH · TACTILE SHADOW + BEVEL</div>
            <div style={{marginTop: 10, display:'flex', gap: 10}}>
              <div style={{flex:1, background: SB.card, color: SB.ink, borderRadius: 6, padding: 12, boxShadow: '0 2px 0 #0e0f10, 0 8px 18px rgba(0,0,0,0.5)', fontSize: 12, fontWeight: 600}}>Card · raised</div>
              <div style={{flex:1, background: SB.machine, color: SB.ink, borderRadius: 6, padding: 12, boxShadow: '0 3px 0 #0e0f10, 0 8px 18px rgba(245,184,0,0.3)', fontSize: 12, fontWeight: 700}}>Primary · stamped</div>
            </div>
          </div>
          <div>
            <div style={sbKick()}>RADIUS · 4 / 6 / 12</div>
            <div style={{marginTop: 10, display:'flex', gap: 10}}>
              {[4,6,12].map(r => (
                <div key={r} style={{flex:1, background: SB.bg3, color:'#fff', height: 50, borderRadius: r, display:'grid', placeItems:'center', fontSize: 11, fontFamily: SB.mono, border: `1px solid ${SB.rule}`}}>{r}px</div>
              ))}
            </div>
          </div>
        </div>

        {/* badges, buttons */}
        <div>
          <div style={sbKick()}>COMPONENTS</div>
          <div style={{marginTop: 10, display:'flex', gap: 6, flexWrap:'wrap'}}>
            <SbBadge tone="machine">Priority</SbBadge>
            <SbBadge tone="pass">Cleared</SbBadge>
            <SbBadge tone="warn">Soon</SbBadge>
            <SbBadge tone="fail">Stop work</SbBadge>
            <SbBadge tone="ink">On site</SbBadge>
            <SbBadge tone="muted">Draft</SbBadge>
          </div>
          <div style={{marginTop: 14, display:'flex', gap: 10, flexWrap:'wrap'}}>
            <SbBtn primary icon={IcMic}>START SITE WALK</SbBtn>
            <SbBtn dark icon={IcClip}>DAILY LOG</SbBtn>
            <SbBtn icon={IcArrow}>VIEW</SbBtn>
          </div>
        </div>

        {/* input */}
        <div>
          <div style={sbKick()}>CHAT · BIG TAP TARGET</div>
          <div style={{marginTop: 10, display:'flex', gap: 10, alignItems:'center', background: SB.bg2, border: `1px solid ${SB.rule}`, borderRadius: 8, padding: 10}}>
            <div style={{flex:1, fontSize: 14, color: SB.muted, paddingLeft: 6}}>Ask or hold to speak…</div>
            <button style={{width: 44, height: 44, borderRadius: 6, background: SB.bg3, color: '#fff', border: `1px solid ${SB.rule}`, display:'grid', placeItems:'center'}}><IcMic s={20}/></button>
            <button style={{width: 44, height: 44, borderRadius: 6, background: SB.machine, color: SB.ink, border: 'none', display:'grid', placeItems:'center', boxShadow: '0 3px 0 #0e0f10'}}><IcSend s={20}/></button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── HOME ──
function SiteBoardHome() {
  return (
    <div style={{height:'100%', background: SB.bg, color:'#fff', fontFamily: SB.sans, display:'flex'}}>
      {/* rail */}
      <div style={{width: 64, background: '#0e0f10', borderRight: `1px solid ${SB.rule}`, display:'flex', flexDirection:'column', alignItems:'center', padding:'14px 0', gap: 4}}>
        <div style={{width: 40, height: 40, background: SB.machine, borderRadius: 6, display:'grid', placeItems:'center', boxShadow: '0 3px 0 #000', marginBottom: 10}}>
          <IcCheck s={22} sw={3} color="#0e0f10"/>
        </div>
        {[{I:IcSun,on:true},{I:IcChat},{I:IcFolder},{I:IcCal},{I:IcClip},{I:IcUsers},{I:IcWrench},{I:IcShield},{I:IcDoc}].map((x,i) => (
          <div key={i} style={{width: 44, height: 44, borderRadius: 6, display:'grid', placeItems:'center', color: x.on?SB.machine:SB.mutedD, background: x.on?'rgba(245,184,0,0.12)':'transparent', position:'relative'}}>
            <x.I s={20}/>
            {x.on && <div style={{position:'absolute', left: -8, top: 8, bottom: 8, width: 3, background: SB.machine, borderRadius: 2}}/>}
          </div>
        ))}
      </div>

      {/* chat pane */}
      <div style={{width: 440, borderRight: `1px solid ${SB.rule}`, display:'flex', flexDirection:'column', background: SB.bg2}}>
        <div style={{height: 4, background: hazardStripe}}/>
        <div style={{padding:'14px 20px', borderBottom: `1px solid ${SB.rule}`, display:'flex', alignItems:'center', gap: 10}}>
          <div style={{fontSize: 16, fontWeight: 800, letterSpacing: 0.5}}>KERF</div>
          <SbBadge tone="machine">LIVE · 05:32</SbBadge>
          <div style={{marginLeft:'auto', fontSize: 11, fontFamily: SB.mono, color: SB.mutedD}}>TUE · 04.17</div>
        </div>

        <div style={{flex: 1, padding:'18px 20px', display:'flex', flexDirection:'column', gap: 16, overflow:'hidden'}}>
          <div>
            <div style={sbKick(SB.machine)}>MORNING BRIEF · STREAMING</div>
            <div style={{fontSize: 22, fontWeight: 800, letterSpacing: -0.5, lineHeight: 1.2, marginTop: 8}}>
              Morning, Marco.<br/>
              <span style={{color: SB.machine}}>3 things before the pour.</span>
            </div>
          </div>

          <div style={{background: SB.card, color: SB.ink, borderRadius: 8, overflow:'hidden', boxShadow: '0 4px 0 #0e0f10, 0 10px 24px rgba(0,0,0,0.4)'}}>
            <div style={{padding:'10px 16px', background: SB.ink, color: '#fff', display:'flex', alignItems:'center', gap: 10}}>
              <IcAlert s={16} color={SB.fail}/>
              <div style={{fontWeight: 700, fontSize: 13}}>Riverside Tower</div>
              <div style={{marginLeft:'auto', display:'flex', alignItems:'center', gap: 6}}>
                <span style={{fontSize: 20, fontWeight: 800, color: SB.fail}}>72</span>
                <span style={{...sbKick(SB.muted)}}>RISK</span>
              </div>
            </div>
            {[
              {k:'CERT', t:"Javier's OSHA-30 expires Wednesday.", sub:'Scaffold work blocks.', s:'fail', cta:'RENEW'},
              {k:'WX',   t:'82°F · 68% humidity.', sub:'Hydration TBT before 9 AM.', s:'warn', cta:'START TBT'},
              {k:'SUB',  t:'Peterson GC insurance lapses 12d.', sub:'Send renewal request.', s:'machine', cta:'SEND'},
            ].map((r,i,a) => (
              <div key={i} style={{padding: '14px 16px', borderTop: `1px solid ${SB.ruleL}`, display:'grid', gridTemplateColumns:'58px 1fr auto', gap: 12, alignItems:'center'}}>
                <SbBadge tone={r.s==='machine'?'machine':r.s}>{r.k}</SbBadge>
                <div>
                  <div style={{fontSize: 14, fontWeight: 700, color: SB.ink, lineHeight: 1.3}}>{r.t}</div>
                  <div style={{fontSize: 12, color: SB.ink2, marginTop: 3}}>{r.sub}</div>
                </div>
                <button style={{background: SB.ink, color: '#fff', border: 'none', padding: '7px 11px', fontFamily: SB.mono, fontSize: 11, fontWeight: 700, borderRadius: 4}}>{r.cta}</button>
              </div>
            ))}
            <div style={{padding:'10px 16px', background: SB.card2, borderTop: `1px solid ${SB.ruleL}`, display:'flex', alignItems:'center', gap: 8}}>
              <IcScope s={13} color={SB.ink2}/>
              <div style={{fontFamily: SB.mono, fontSize: 10, color: SB.ink2, letterSpacing: 0.4}}>PROJECT → CERTS → OSHA 1926.451</div>
            </div>
          </div>

          <div style={{marginTop:'auto', display:'flex', gap: 8}}>
            <SbBtn primary big icon={IcMic}>SITE WALK</SbBtn>
            <SbBtn dark icon={IcClip}>LOG</SbBtn>
            <SbBtn dark icon={IcHat}>CREW</SbBtn>
          </div>
        </div>

        <div style={{padding: 12, borderTop: `1px solid ${SB.rule}`, background: '#0e0f10'}}>
          <div style={{display:'flex', gap: 8, alignItems:'center', background: SB.bg3, border: `1px solid ${SB.rule}`, borderRadius: 8, padding: 8}}>
            <div style={{flex:1, fontSize: 13, color: SB.muted, paddingLeft: 6}}>Hold the mic. Speak. Done.</div>
            <button style={{width: 38, height: 38, borderRadius: 6, background: '#0e0f10', color: '#fff', border: `1px solid ${SB.rule}`, display:'grid', placeItems:'center'}}><IcMic s={17}/></button>
            <button style={{width: 38, height: 38, borderRadius: 6, background: SB.machine, color: SB.ink, border: 'none', display:'grid', placeItems:'center', boxShadow: '0 2px 0 #000'}}><IcSend s={17}/></button>
          </div>
        </div>
      </div>

      {/* canvas — light over dark */}
      <div style={{flex:1, background: SB.bg, padding:'22px 26px', display:'flex', flexDirection:'column', gap: 16, overflow:'hidden'}}>
        <div style={{display:'flex', alignItems:'end', justifyContent:'space-between'}}>
          <div>
            <div style={sbKick(SB.machine)}>CANVAS · TODAY</div>
            <div style={{fontSize: 36, fontWeight: 800, letterSpacing: -1, lineHeight: 1, marginTop: 4, textTransform: 'uppercase'}}>TUE · 04.17</div>
          </div>
          <div style={{display:'flex', gap: 8}}>
            <SbBtn dark icon={IcClip}>DAILY LOG</SbBtn>
            <SbBtn primary icon={IcMic}>SITE WALK</SbBtn>
          </div>
        </div>

        {/* KPIs — dark cards with yellow accent */}
        <div style={{display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap: 10}}>
          {[
            {k:'PROJECTS',v:'3',sub:'active',color:'#fff'},
            {k:'OPEN',v:'11',sub:'4 today',color: SB.machine},
            {k:'CERTS',v:'2',sub:'1 expired',color: SB.fail},
            {k:'TRIR',v:'2.4',sub:'below target',color: SB.pass},
            {k:'HOURS',v:'412',sub:'of 480',color:'#fff'},
          ].map((t,i) => (
            <div key={i} style={{background: SB.bg2, border: `1px solid ${SB.rule}`, borderRadius: 8, padding: '14px 16px', boxShadow: '0 2px 0 #0e0f10'}}>
              <div style={sbKick()}>{t.k}</div>
              <div style={{fontSize: 40, fontWeight: 800, letterSpacing: -1.4, lineHeight: 1, color: t.color, marginTop: 8}}>{t.v}</div>
              <div style={{fontSize: 11, color: SB.muted, marginTop: 4, fontFamily: SB.mono, letterSpacing: 0.5, textTransform: 'uppercase'}}>{t.sub}</div>
            </div>
          ))}
        </div>

        <div style={{display:'grid', gridTemplateColumns:'1.35fr 1fr', gap: 12, flex: 1, minHeight: 0}}>
          <div style={{background: SB.card, color: SB.ink, borderRadius: 8, display:'flex', flexDirection:'column', boxShadow: '0 2px 0 #0e0f10, 0 10px 24px rgba(0,0,0,0.35)', overflow:'hidden'}}>
            <div style={{padding:'14px 18px', display:'flex', alignItems:'center', borderBottom: `1px solid ${SB.ruleL}`}}>
              <div style={{fontSize: 15, fontWeight: 800, letterSpacing: 0.3, textTransform:'uppercase'}}>Active jobs</div>
              <div style={{marginLeft:'auto'}}><SbBadge tone="paper">3</SbBadge></div>
            </div>
            {[
              {name:'Riverside Tower', addr:'1420 Riverside Dr', score: 72, s:'warn', meta:'Pour · 18 crew'},
              {name:'Maple Ridge II', addr:'820 Maple Way', score: 94, s:'pass', meta:'Framing · 11 crew'},
              {name:'4th Street Retail', addr:'402 4th St', score: 88, s:'pass', meta:'Estimate'},
            ].map((p,i,a) => (
              <div key={i} style={{padding: '14px 18px', borderBottom: i<a.length-1 ? `1px solid ${SB.ruleL}` : 'none', display:'grid', gridTemplateColumns: '6px 1fr auto auto', gap: 14, alignItems:'center'}}>
                <div style={{width: 6, height: 40, background: p.s==='pass'?SB.pass:SB.machine, borderRadius: 3}}/>
                <div>
                  <div style={{fontSize: 15, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.2}}>{p.name}</div>
                  <div style={{fontSize: 12, color: SB.ink2, marginTop: 3, fontFamily: SB.mono, letterSpacing: 0.3}}>{p.addr} · {p.meta}</div>
                </div>
                <div style={{fontSize: 28, fontWeight: 800, letterSpacing: -1, color: SB.ink}}>{p.score}<span style={{color: SB.ink2, fontSize: 14}}>%</span></div>
                <SbBadge tone={p.s}>{p.s==='pass'?'GO':'RISK'}</SbBadge>
              </div>
            ))}
          </div>

          <div style={{background: SB.bg2, border: `1px solid ${SB.rule}`, borderRadius: 8, display:'flex', flexDirection:'column'}}>
            <div style={{padding:'14px 18px', display:'flex', alignItems:'center', borderBottom: `1px solid ${SB.rule}`}}>
              <div style={{fontSize: 15, fontWeight: 800, letterSpacing: 0.3, textTransform:'uppercase', color:'#fff'}}>Crew</div>
              <SbBadge tone="muted">22 TOTAL</SbBadge>
            </div>
            {[
              {n:'Javier Ortega', r:'Foreman', exp:'WED 04.19', s:'fail'},
              {n:'Carlos Mendez', r:'Carpenter', exp:'FRI 04.26', s:'warn'},
              {n:'Luis Salas', r:'Laborer', exp:'MAY 12', s:'pass'},
              {n:'Dani Park', r:'Scaffold', exp:'MAY 18', s:'pass'},
            ].map((w,i,a) => (
              <div key={i} style={{padding:'12px 18px', borderBottom: i<a.length-1 ? `1px solid ${SB.rule}` : 'none', display:'grid', gridTemplateColumns:'1fr auto auto', gap: 12, alignItems:'center'}}>
                <div>
                  <div style={{fontSize: 14, fontWeight: 700, color:'#fff'}}>{w.n}</div>
                  <div style={{...sbKick()}}>{w.r}</div>
                </div>
                <div style={{fontFamily: SB.mono, fontSize: 11, color: SB.muted, letterSpacing: 0.5}}>{w.exp}</div>
                <SbBadge tone={w.s}>{w.s==='pass'?'VALID':w.s==='warn'?'SOON':'EXPIRED'}</SbBadge>
              </div>
            ))}
            <div style={{marginTop:'auto', padding: '10px 18px', borderTop: `1px solid ${SB.rule}`, background: '#0e0f10', display:'flex', alignItems:'center', gap: 8}}>
              <IcScope s={13} color={SB.machine}/>
              <div style={{fontFamily: SB.mono, fontSize: 10, color: SB.muted, letterSpacing: 0.5}}>PROJECT → 22 WORKERS → 38 CERTS</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { SiteBoardSystem, SiteBoardHome });
