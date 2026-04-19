// Site Board — Contract / Quote tab  (chat-left + canvas-right)
// Dark shell, yellow dominant, trailer-ready. Chat on the left IS the primary
// interface; every canvas block on the right has a chat-bubble origin on the
// left. Data comes from foreman-contract.jsx (FM_QUOTE etc).

const sbC = (n) => '$' + n.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0});
const sbK = (c = SB.muted) => ({
  fontFamily: SB.mono, fontSize: 10, fontWeight: 700,
  letterSpacing: 1.4, textTransform: 'uppercase', color: c,
});

const SB_Q  = FM_QUOTE;
const SB_TL = FM_TL, SB_TI = FM_TI, SB_TS = FM_TS, SB_MA = FM_MA;

// ── flag chip ────────────────────────────────────────────────────
function SbFlag({flag}) {
  if (!flag) return null;
  const m = {
    inherited:{ I: I2Plumb,      t:'PEACHTREE',      c: SB.muted },
    insight:  { I: I2Anvil,      t:'+15% INSIGHT',   c: SB.machine },
    stated:   { I: I2Assumption, t:'YOU SAID',       c: '#8a6700' },
  }[flag];
  return (
    <span style={{
      display:'inline-flex', alignItems:'center', gap: 4,
      fontFamily: SB.mono, fontSize: 9.5, fontWeight: 700, letterSpacing: 0.6,
      color: m.c, padding:'1px 5px', border:`1px dashed ${m.c}`, borderRadius: 3,
    }}><m.I s={10.5} sw={2}/> {m.t}</span>
  );
}

// ── chat primitives (dark) ───────────────────────────────────────
function SbTurn({ who='kerf', time, children }) {
  const isUser = who === 'user';
  return (
    <div style={{display:'flex', gap: 10, flexDirection: isUser ? 'row-reverse' : 'row'}}>
      <div style={{
        width: 28, height: 28, flexShrink: 0,
        background: isUser ? SB.machine : '#0e0f10',
        color: isUser ? SB.ink : SB.machine,
        border: `1px solid ${isUser ? SB.machineD : SB.rule}`,
        borderRadius: 4, display:'grid', placeItems:'center',
        fontFamily: SB.mono, fontSize: 11, fontWeight: 800, letterSpacing: 0.5,
      }}>{isUser ? 'S' : 'K'}</div>
      <div style={{flex:1, minWidth:0, display:'flex', flexDirection:'column', gap: 6, alignItems: isUser ? 'flex-end' : 'stretch'}}>
        {time && <div style={{...sbK(SB.mutedD), fontSize: 9, color:'#8a8b8e'}}>{isUser ? 'SARAH' : 'KERF'} · {time}</div>}
        <div style={{maxWidth:'100%', display:'flex', flexDirection:'column', gap: 8, alignItems: isUser ? 'flex-end' : 'stretch', width:'100%'}}>
          {children}
        </div>
      </div>
    </div>
  );
}
function SbBubble({ user, children }) {
  return (
    <div style={{
      background: user ? SB.machine : '#0e0f10',
      color: user ? SB.ink : '#eceef1',
      border: user ? 'none' : `1px solid ${SB.rule}`,
      borderRadius: 4,
      padding: '10px 14px',
      fontSize: 13.5, lineHeight: 1.5,
      maxWidth: user ? '88%' : '100%',
      fontWeight: user ? 600 : 400,
      boxShadow: user ? '0 2px 0 rgba(0,0,0,0.4)' : 'none',
    }}>{children}</div>
  );
}
// "Card in chat" — inline LIFTED dark card against the chat surface
function SbChatCard({ kicker, title, right, children }) {
  return (
    <div style={{
      background: SB.bg3, color:'#fff',
      border: `1px solid #0a0b0c`,
      borderRadius: 4, overflow:'hidden',
      boxShadow: [
        'inset 0 1px 0 rgba(255,255,255,0.06)',
        '0 2px 0 #000',
        '0 10px 20px rgba(0,0,0,0.55)',
      ].join(', '),
    }}>
      <div style={{
        padding:'8px 12px',
        background:'linear-gradient(#242528, #1e1f22)',
        borderBottom:`1px solid rgba(0,0,0,0.5)`,
        boxShadow:'inset 0 -1px 0 rgba(255,255,255,0.04)',
        display:'flex', alignItems:'center', gap: 8,
      }}>
        <div style={sbK(SB.machine)}>{kicker}</div>
        <div style={{fontSize: 12.5, fontWeight: 800, color:'#fff', letterSpacing:0.2, textTransform:'uppercase'}}>{title}</div>
        <div style={{marginLeft:'auto'}}>{right}</div>
      </div>
      {children}
    </div>
  );
}

// ── stencil numeric plate ────────────────────────────────────────
// Used as the "01 / 02 / 03" kicker next to panel titles. Reads as a
// stamped metal plate: inset highlight, dark recess, mono numerals.
function SbNum({ n }) {
  return (
    <div style={{
      flexShrink: 0,
      minWidth: 26, height: 22, padding: '0 6px',
      borderRadius: 3,
      background: 'linear-gradient(#0b0c0d, #17181b)',
      border: '1px solid #000',
      boxShadow: [
        'inset 0 1px 0 rgba(255,255,255,0.07)',
        'inset 0 -1px 0 rgba(0,0,0,0.6)',
      ].join(', '),
      display:'grid', placeItems:'center',
      fontFamily: SB.mono, fontSize: 12, fontWeight: 800,
      letterSpacing: 1, color: SB.machine,
      textShadow: '0 1px 0 rgba(0,0,0,0.6)',
    }}>{String(n).padStart(2,'0')}</div>
  );
}

// ── right-pane panel shell (LIFTED dark card) ────────────────────
// Cards sit one surface up from the bg. Real shadow + a 1px top highlight
// gives them depth without chrome tricks.
function SbPanel({ title, kicker, icon: I, right, children }) {
  return (
    <section style={{
      background: SB.bg3,
      color: '#fff',
      border: `1px solid #0a0b0c`,
      borderRadius: 6,
      boxShadow: [
        'inset 0 1px 0 rgba(255,255,255,0.06)',
        '0 1px 0 rgba(255,255,255,0.03)',
        '0 2px 0 #000',
        '0 12px 24px rgba(0,0,0,0.55)',
      ].join(', '),
      overflow: 'hidden',
      transition: 'transform 160ms ease, box-shadow 160ms ease',
    }} className="sb-panel">
      <header style={{
        padding:'12px 16px',
        borderBottom: `1px solid rgba(0,0,0,0.5)`,
        boxShadow: 'inset 0 -1px 0 rgba(255,255,255,0.04)',
        display:'flex', alignItems:'center', gap: 10,
        background: 'linear-gradient(#242528, #1e1f22)',
      }}>
        {kicker && <SbNum n={kicker}/>}
        {I && <I s={15} sw={2} color={SB.machine}/>}
        <div style={{fontSize: 13, fontWeight: 800, letterSpacing: 0.4, textTransform:'uppercase', color: '#fff'}}>{title}</div>
        <div style={{marginLeft:'auto', display:'flex', gap: 6}}>{right}</div>
      </header>
      {children}
    </section>
  );
}

// DARK table tokens — header is ink, rows alternate bg3 / slightly lighter
const sbThD = {
  padding:'9px 12px', textAlign:'left',
  ...sbK(SB.muted), color: SB.muted,
  background:'#16171a',
  borderBottom:`1px solid rgba(0,0,0,0.6)`,
  boxShadow: 'inset 0 -1px 0 rgba(255,255,255,0.04)',
};
const sbTdD = {
  padding:'10px 12px', fontSize: 12.5,
  borderBottom:`1px solid rgba(255,255,255,0.06)`,
  color:'#eceef1',
};
// row backgrounds for striping (transparent on bg3 base)
const sbRowA = 'rgba(255,255,255,0.00)';
const sbRowB = 'rgba(255,255,255,0.03)';

// ── CONTRACT — chat-left + canvas-right ──────────────────────────
function SiteBoardContract() {
  return (
    <div style={{
      height:'100%', background: SB.bg, color:'#fff', fontFamily: SB.sans,
      display:'flex', flexDirection:'column',
    }}>
      {/* scoped styles: scrollbar, hover lift, typing pulse, caret beat */}
      <style>{`
        .sb-feed::-webkit-scrollbar { width: 8px; }
        .sb-feed::-webkit-scrollbar-track { background: transparent; }
        .sb-feed::-webkit-scrollbar-thumb {
          background: rgba(255,255,255,0.06);
          border-radius: 100px;
          border: 2px solid transparent;
          background-clip: padding-box;
        }
        .sb-feed:hover::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.14); background-clip: padding-box; }
        .sb-feed { scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.10) transparent; }

        .sb-panel:hover {
          transform: translateY(-1px);
          box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.08),
            0 1px 0 rgba(255,255,255,0.04),
            0 3px 0 #000,
            0 18px 30px rgba(0,0,0,0.6) !important;
        }

        @keyframes sbDot {
          0%, 80%, 100% { opacity: 0.2; transform: scale(0.9); }
          40% { opacity: 1; transform: scale(1); }
        }
        .sb-dot { animation: sbDot 1.2s ease-in-out infinite; }
        .sb-dot:nth-child(2) { animation-delay: 0.15s; }
        .sb-dot:nth-child(3) { animation-delay: 0.30s; }

        @keyframes sbBeat {
          0% { opacity: 0; transform: translateY(4px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .sb-beat { animation: sbBeat 420ms cubic-bezier(.2,.8,.2,1) both; }

        @keyframes sbCaret {
          0%, 49% { opacity: 1; }
          50%, 100% { opacity: 0; }
        }
        .sb-caret::after {
          content: '_';
          margin-left: 2px;
          color: ${SB.machine};
          animation: sbCaret 900ms steps(1) infinite;
        }

        .sb-row { transition: background 140ms ease; }
        .sb-row:hover { background: rgba(255,212,38,0.06) !important; }
      `}</style>

      {/* slim project strip */}
      <div style={{
        padding:'10px 22px',
        borderBottom: `1px solid ${SB.rule}`,
        background: SB.bg2,
        display:'flex', alignItems:'center', gap: 14, flexWrap:'wrap',
        boxShadow: 'inset 0 -1px 0 rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03)',
        position: 'relative',
      }}>
        {/* subtle yellow hairline along the bottom */}
        <div style={{position:'absolute', left: 0, right: 0, bottom: -1, height: 2, background: `linear-gradient(90deg, transparent, ${SB.machine} 20%, ${SB.machine} 80%, transparent)`, opacity: 0.5}}/>

        {/* KERF wordmark lockup */}
        <div style={{display:'flex', alignItems:'center', gap: 10, paddingRight: 14, borderRight: `1px solid ${SB.rule}`}}>
          <div style={{
            width: 26, height: 26,
            background: SB.machine, borderRadius: 3,
            display:'grid', placeItems:'center',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.4), 0 1px 0 #000',
            position:'relative',
          }}>
            {/* K monogram — bold ink on yellow */}
            <svg viewBox="0 0 26 26" width={26} height={26}>
              <path d="M7 6 L7 20 M7 13 L15 6 M7 13 L16 20" stroke={SB.ink} strokeWidth={3.2} strokeLinecap="square" fill="none"/>
            </svg>
          </div>
          <div style={{
            fontFamily: SB.mono, fontSize: 15, fontWeight: 800,
            letterSpacing: 3.2, color: '#fff',
            textShadow: '0 1px 0 rgba(0,0,0,0.5)',
          }}>KERF</div>
        </div>

        <div style={{display:'flex', alignItems:'baseline', gap: 8}}>
          <div style={{fontSize: 16, fontWeight: 800, letterSpacing: 0, textTransform:'uppercase'}}>{SB_Q.name}</div>
          <div style={sbK()}>· {SB_Q.code} · {SB_Q.client}</div>
        </div>
        <SbBadge tone="warn">VALID · {SB_Q.validUntil.toUpperCase()}</SbBadge>
        <SbBadge tone="muted">{SB_Q.contractType.toUpperCase()}</SbBadge>
        <SbBadge tone="machine">QUOTING · DRAFT A</SbBadge>
        <div style={{marginLeft:'auto', display:'flex', alignItems:'center', gap: 14}}>
          <div style={{textAlign:'right'}}>
            <div style={sbK(SB.machine)}>QUOTE TOTAL</div>
            <div style={{fontSize: 22, fontWeight: 800, fontFamily: SB.mono, letterSpacing:-0.7, lineHeight:1, color: SB.machine}}>{sbC(SB_TS)}</div>
          </div>
          <SbBtn primary icon={I2Proposal}>GENERATE PROPOSAL</SbBtn>
        </div>
      </div>

      {/* two-pane body */}
      <div style={{flex:1, display:'grid', gridTemplateColumns:'minmax(420px, 460px) 1fr', minHeight: 0}}>

        {/* ================== CHAT (LEFT) =================== */}
        <div style={{borderRight: `1px solid ${SB.rule}`, background: SB.bg, display:'flex', flexDirection:'column', minHeight: 0}}>
          <div style={{padding:'11px 16px', borderBottom: `1px solid ${SB.rule}`, display:'flex', alignItems:'center', gap: 8, background: SB.bg2}}>
            <I2Chat s={14} color={SB.machine} sw={2}/>
            <div style={{fontSize: 13, fontWeight: 800, letterSpacing: 0.4, textTransform:'uppercase', color:'#fff'}}>CONVERSATION</div>
            <div style={{...sbK(), marginLeft: 6}}>CONTRACT · MAPLE RIDGE</div>
            <div style={{marginLeft:'auto', display:'flex', gap: 4}}>
              <SbBtn dark icon={I2Refresh} small/>
              <SbBtn dark icon={I2Dots} small/>
            </div>
          </div>

          {/* feed */}
          <div className="sb-feed" style={{flex:1, overflow:'auto', padding:'16px 16px 10px', display:'flex', flexDirection:'column', gap: 14}}>

            <div style={{display:'flex', alignItems:'center', gap: 8}}>
              <div style={{flex:1, height:1, background: SB.rule}}/>
              <div style={sbK()}>TUE · APR 17 · 05:48</div>
              <div style={{flex:1, height:1, background: SB.rule}}/>
            </div>

            <SbTurn who="user" time="05:48">
              <SbBubble user>PULL UP MAPLE RIDGE PHASE II. SAME SCOPE AS LAST YEAR — START FROM PEACHTREE.</SbBubble>
            </SbTurn>

            <SbTurn who="kerf" time="05:48">
              <SbBubble>
                Pulled. Peachtree had <strong style={{color: SB.machine}}>5 items</strong> — I brought them over and added <strong style={{color: SB.machine}}>2 new</strong> from the updated drawings. Margins look healthy.
              </SbBubble>

              <SbChatCard kicker="WORK ITEMS" title="7 items · $121,200" right={<SbBadge tone="pass">{FM_MA}% avg</SbBadge>}>
                <table style={{width:'100%', borderCollapse:'collapse', fontVariantNumeric:'tabular-nums'}}>
                  <thead>
                    <tr>
                      <th style={{...sbThD, width: 30, textAlign:'center'}}>#</th>
                      <th style={sbThD}>ITEM</th>
                      <th style={{...sbThD, width: 56, textAlign:'right'}}>MARGIN</th>
                      <th style={{...sbThD, width: 80, textAlign:'right'}}>SELL</th>
                    </tr>
                  </thead>
                  <tbody>
                    {SB_Q.workItems.slice(0,4).map((w,i)=>(
                      <tr key={w.id} style={{background: i%2===0 ? sbRowA : sbRowB}}>
                        <td style={{...sbTdD, textAlign:'center', fontFamily: SB.mono, color: SB.muted, fontSize: 11, fontWeight: 700}}>{w.code}</td>
                        <td style={sbTdD}>
                          <div style={{fontWeight: 700, color:'#fff'}}>{w.desc}</div>
                          {w.flag && <div style={{marginTop: 3}}><SbFlag flag={w.flag}/></div>}
                        </td>
                        <td style={{...sbTdD, textAlign:'right', fontFamily: SB.mono, color: w.margin<20?SB.warn:SB.pass, fontWeight: 800}}>{w.margin}%</td>
                        <td style={{...sbTdD, textAlign:'right', fontFamily: SB.mono, fontWeight: 800, color: SB.machine}}>{sbC(w.sell)}</td>
                      </tr>
                    ))}
                    <tr>
                      <td colSpan={4} style={{padding:'8px 12px', textAlign:'center', color: SB.muted, fontSize: 10.5, background:'#16171a', fontFamily: SB.mono, letterSpacing: 0.5, fontWeight: 700, textTransform: 'uppercase', borderTop:`1px solid rgba(0,0,0,0.5)`, boxShadow:'inset 0 1px 0 rgba(255,255,255,0.04)'}}>+ 3 MORE ON CANVAS →</td>
                    </tr>
                  </tbody>
                </table>
              </SbChatCard>
            </SbTurn>

            <SbTurn who="user" time="05:52">
              <SbBubble user>THE FLOOR-BOX INSIGHT — WHERE DID THAT 15% COME FROM?</SbBubble>
            </SbTurn>

            <SbTurn who="kerf" time="05:52">
              <SbBubble>
                From your last three low-ceiling projects. <strong style={{color: SB.machine}}>Floor boxes + unistrut below 9′ run ~15% over standard labour.</strong> You told me after Alder St. I applied it to item 04.
              </SbBubble>

              <SbChatCard kicker="INSIGHT APPLIED" title="+15% labour · low ceiling"
                right={<SbBadge tone="machine">3 JOBS</SbBadge>}>
                <div style={{padding:'10px 14px', fontSize: 12.5, color:'#d4d6da', lineHeight: 1.55}}>
                  Evidence: Alder St., Hollis Warehouse, Peterson Unit B. Avg actual vs. catalog: <strong style={{color: SB.pass}}>+14.8%</strong>.
                </div>
              </SbChatCard>
            </SbTurn>

            <SbTurn who="user" time="06:01">
              <SbBubble user>WEEKDAYS ONLY, GC PROVIDES HOIST 7:30–9:30. FIRE ALARM OUT OF SCOPE, PERMITS REIMBURSABLE.</SbBubble>
            </SbTurn>

            <SbTurn who="kerf" time="06:01">
              <SbBubble>Captured. Two trigger a variation if violated — I've marked them.</SbBubble>

              <SbChatCard kicker="ASSUMPTIONS + EXCLUSIONS" title="4 + 3" right={<SbBadge tone="warn">2 VARIATIONS</SbBadge>}>
                <div style={{padding:'10px 14px', display:'flex', flexDirection:'column', gap: 8}}>
                  {SB_Q.assumptions.slice(0,2).map(a=>(
                    <div key={a.id} style={{display:'grid', gridTemplateColumns:'84px 1fr', gap: 8}}>
                      <SbBadge tone="warn">{a.cat.toUpperCase()}</SbBadge>
                      <div style={{fontSize: 12.5, lineHeight: 1.45, color:'#eceef1'}}>
                        {a.text}
                        {a.variation && <div style={{fontSize: 10, color: SB.fail, fontFamily: SB.mono, marginTop: 2, letterSpacing: 0.4, fontWeight: 700}}>→ VARIATION · {a.trigger.toUpperCase()}</div>}
                      </div>
                    </div>
                  ))}
                  <div style={{fontSize: 10.5, color: SB.mutedD, paddingTop: 8, borderTop: `1px dashed rgba(255,255,255,0.12)`, fontFamily: SB.mono, letterSpacing: 0.5, fontWeight: 700, textTransform:'uppercase'}}>+ 2 MORE, 3 EXCLUSIONS ON CANVAS →</div>
                </div>
              </SbChatCard>
            </SbTurn>

            <SbTurn who="user" time="06:08">
              <SbBubble user>MILESTONE PAYMENTS. 5% RETENTION, NET 30.</SbBubble>
            </SbTurn>

            <SbTurn who="kerf" time="06:08">
              <SbBubble>Five milestones tied to inspection gates. Retention and terms set.</SbBubble>

              <SbChatCard kicker="PAYMENT SCHEDULE" title="5 milestones · Net 30">
                <div>
                  {SB_Q.milestones.map((m,i,a)=>{
                    const amt = Math.round(SB_TS * m.pct/100);
                    return (
                      <div key={m.name} style={{
                        padding:'8px 14px', display:'grid', gridTemplateColumns:'34px 1fr 48px 78px', gap: 8, alignItems:'center',
                        borderBottom: i<a.length-1 ? `1px solid rgba(255,255,255,0.06)` : 'none',
                        background: i%2===0 ? sbRowA : sbRowB,
                      }}>
                        <div style={{fontFamily: SB.mono, fontWeight: 800, fontSize: 11, color: SB.machine}}>M{i+1}</div>
                        <div>
                          <div style={{fontSize: 12.5, fontWeight: 700, color:'#fff'}}>{m.name}</div>
                          <div style={{fontSize: 10, color: SB.muted, fontFamily: SB.mono, letterSpacing: 0.4, textTransform: 'uppercase', fontWeight: 700}}>{m.trigger}</div>
                        </div>
                        <div style={{textAlign:'right', fontFamily: SB.mono, fontWeight: 800, fontSize: 13, color: SB.machine}}>{m.pct}%</div>
                        <div style={{textAlign:'right', fontFamily: SB.mono, fontWeight: 800, fontSize: 12.5, color:'#fff'}}>{sbC(amt)}</div>
                      </div>
                    );
                  })}
                </div>
              </SbChatCard>
            </SbTurn>

            <SbTurn who="user" time="06:15">
              <SbBubble user>GOOD. GENERATE THE PROPOSAL.</SbBubble>
            </SbTurn>

            <SbTurn who="kerf" time="06:15">
              <SbBubble>
                Before I do — <strong style={{color: SB.machine}}>2 stated rates</strong> aren't in your catalog yet (hoist time, low-ceiling floor boxes). Capture them so the next walkthrough starts smarter?
              </SbBubble>
              <div style={{display:'flex', gap: 6, paddingLeft: 2}}>
                <SbBtn primary icon={I2CheckBadge} small>CAPTURE BOTH</SbBtn>
                <SbBtn dark icon={I2Proposal} small>SKIP — GENERATE</SbBtn>
              </div>
            </SbTurn>

            {/* typing */}
            <div style={{display:'flex', gap: 10, alignItems:'center'}}>
              <div style={{width: 28, height: 28, flexShrink:0, background: '#0e0f10', border: `1px solid ${SB.rule}`, borderRadius: 4, display:'grid', placeItems:'center', fontFamily: SB.mono, fontSize: 11, fontWeight: 800, color: SB.machine}}>K</div>
              <div style={{display:'flex', gap: 4, padding:'8px 12px', background: SB.bg2, border:`1px solid ${SB.rule}`, borderRadius: 4, alignItems:'center'}}>
                <div className="sb-dot" style={{width: 6, height: 6, borderRadius: '50%', background: SB.machine}}/>
                <div className="sb-dot" style={{width: 6, height: 6, borderRadius: '50%', background: SB.machine}}/>
                <div className="sb-dot" style={{width: 6, height: 6, borderRadius: '50%', background: SB.machine}}/>
                <span className="sb-caret" style={{marginLeft: 6, fontFamily: SB.mono, fontSize: 10, fontWeight: 700, color: SB.muted, letterSpacing: 0.8}}>KERF IS TYPING</span>
              </div>
            </div>
          </div>

          {/* composer */}
          <div style={{padding: 12, borderTop: `1px solid ${SB.rule}`, background: SB.bg2}}>
            <div style={{display:'flex', gap: 6, marginBottom: 8, flexWrap:'wrap'}}>
              {['TIGHTEN MARGINS','ADD VARIATION','VS PEACHTREE','CHANGE RETENTION'].map(c=>(
                <button key={c} style={{
                  background:'transparent', border:`1px solid ${SB.rule}`, borderRadius: 100,
                  padding:'4px 10px', fontFamily: SB.mono, fontSize: 10.5, fontWeight: 700,
                  color: SB.mutedD, letterSpacing: 0.5, cursor:'pointer',
                }}>{c}</button>
              ))}
            </div>
            <div style={{display:'flex', alignItems:'center', gap: 8, background:'#0e0f10', border:`1px solid ${SB.rule}`, borderRadius: 4, padding: '7px 7px 7px 12px'}}>
              <span style={sbK(SB.machine)}>ASK</span>
              <div style={{flex:1, fontSize: 13, color: SB.muted}}>Reply — or hold to speak</div>
              <button style={{border:`1px solid ${SB.rule}`, background: SB.bg2, color:'#fff', borderRadius: 3, padding:'6px 10px', display:'inline-flex', alignItems:'center', gap:4, fontFamily: SB.mono, fontSize: 10.5, fontWeight: 800, cursor:'pointer', letterSpacing: 0.5}}><I2Mic s={12} sw={2}/> HOLD</button>
              <button style={{background: SB.machine, color: SB.ink, border: 'none', borderRadius: 3, padding:'7px 12px', display:'inline-flex', alignItems:'center', gap: 4, fontFamily: SB.mono, fontSize: 10.5, fontWeight: 800, cursor:'pointer', letterSpacing: 0.5, boxShadow:'0 2px 0 #000'}}><I2Send s={12} sw={2.2}/> SEND</button>
            </div>
          </div>
        </div>

        {/* ================== CANVAS (RIGHT) ==================== */}
        <div className="sb-feed" style={{padding: 18, overflow:'auto', background: SB.bg, display:'flex', flexDirection:'column', gap: 14, minHeight: 0}}>

          {/* summary strip — lifted dark card with yellow total */}
          <div style={{
            background: SB.bg3, border:`1px solid #0a0b0c`, borderRadius: 6, overflow:'hidden',
            display:'grid', gridTemplateColumns:'1.3fr 1fr 1fr 1fr',
            boxShadow: [
              'inset 0 1px 0 rgba(255,255,255,0.06)',
              '0 2px 0 #000',
              '0 12px 24px rgba(0,0,0,0.55)',
            ].join(', '),
          }}>
            {[
              {k:'QUOTE TOTAL', v: sbC(SB_TS), sub:`${SB_Q.workItems.length} ITEMS`, big:true},
              {k:'LABOUR',      v: sbC(SB_TL), sub:'EST. COST'},
              {k:'ITEMS',       v: sbC(SB_TI), sub:'EST. COST'},
              {k:'AVG MARGIN',  v: `${SB_MA}%`, sub:'WEIGHTED', color: SB.pass},
            ].map((t,i,a)=>(
              <div key={i} style={{
                padding:'16px 18px',
                borderRight: i<a.length-1 ? '1px solid rgba(0,0,0,0.5)' : 'none',
                boxShadow: i<a.length-1 ? 'inset -1px 0 0 rgba(255,255,255,0.04)' : 'none',
                background: t.big ? SB.machine : 'transparent',
                color: t.big ? SB.ink : '#fff',
              }}>
                <div style={sbK(t.big ? 'rgba(0,0,0,0.6)' : SB.mutedD)}>{t.k}</div>
                <div style={{fontSize: t.big ? 32 : 22, fontWeight: 800, fontFamily: SB.mono, letterSpacing: t.big ? -1.1 : -0.4, color: t.color || (t.big ? SB.ink : '#fff'), lineHeight: 1, marginTop: 8}}>{t.v}</div>
                <div style={{...sbK(t.big ? 'rgba(0,0,0,0.55)' : SB.mutedD), fontSize: 10, marginTop: 4}}>{t.sub}</div>
              </div>
            ))}
          </div>

          {/* WORK ITEMS */}
          <SbPanel title="Work items" kicker="01" icon={I2Receipt}
            right={<>
              <div style={{display:'flex', alignItems:'center', gap: 6, border: `1px solid ${SB.rule}`, borderRadius: 3, padding: '4px 8px', background: '#0e0f10'}}>
                <I2Search s={13} color={SB.muted}/>
                <input placeholder="Filter…" style={{border:'none', outline:'none', background:'transparent', fontSize: 12, fontFamily: SB.sans, width: 110, color: '#fff'}}/>
              </div>
              <button style={{fontFamily: SB.mono, fontSize: 10.5, fontWeight: 800, background: SB.machine, color: SB.ink, border: 'none', padding:'6px 10px', borderRadius: 3, display:'inline-flex', alignItems:'center', gap: 4, letterSpacing: 0.5, boxShadow:'0 2px 0 #000'}}><I2Plus s={12} sw={2.5}/> ITEM</button>
            </>}>
            <div style={{overflow:'auto'}}>
              <table style={{width:'100%', borderCollapse:'collapse', fontVariantNumeric:'tabular-nums'}}>
                <thead>
                  <tr>
                    <th style={{...sbThD, width: 40, textAlign:'center'}}>#</th>
                    <th style={sbThD}>DESCRIPTION</th>
                    <th style={{...sbThD, width: 54, textAlign:'right'}}>QTY</th>
                    <th style={{...sbThD, width: 46}}>UNIT</th>
                    <th style={{...sbThD, width: 86, textAlign:'right'}}>LABOUR</th>
                    <th style={{...sbThD, width: 86, textAlign:'right'}}>ITEMS</th>
                    <th style={{...sbThD, width: 64, textAlign:'right'}}>MARGIN</th>
                    <th style={{...sbThD, width: 100, textAlign:'right'}}>SELL</th>
                    <th style={{...sbThD, width: 72}}>STATE</th>
                  </tr>
                </thead>
                <tbody>
                  {SB_Q.workItems.map((w,i)=>(
                    <tr key={w.id} className="sb-row" style={{background: i%2===0 ? sbRowA : sbRowB}}>
                      <td style={{...sbTdD, textAlign:'center', fontFamily: SB.mono, color: SB.muted, fontSize: 11, fontWeight: 700}}>{w.code}</td>
                      <td style={sbTdD}>
                        <div style={{fontWeight: 700, color:'#fff', letterSpacing: 0.1}}>{w.desc}</div>
                        {w.flag && <div style={{marginTop: 4}}><SbFlag flag={w.flag}/></div>}
                      </td>
                      <td style={{...sbTdD, textAlign:'right', fontFamily: SB.mono, fontWeight: 600}}>{w.qty}</td>
                      <td style={{...sbTdD, fontFamily: SB.mono, color: SB.muted, fontSize: 11, fontWeight: 700}}>{w.unit.toUpperCase()}</td>
                      <td style={{...sbTdD, textAlign:'right', fontFamily: SB.mono}}>{sbC(w.labour)}</td>
                      <td style={{...sbTdD, textAlign:'right', fontFamily: SB.mono}}>{sbC(w.items)}</td>
                      <td style={{...sbTdD, textAlign:'right', fontFamily: SB.mono, fontWeight: 800, color: w.margin<20?SB.warn:SB.pass}}>{w.margin}%</td>
                      <td style={{...sbTdD, textAlign:'right', fontFamily: SB.mono, fontWeight: 800, fontSize: 14, color: SB.machine}}>{sbC(w.sell)}</td>
                      <td style={sbTdD}><SbBadge tone={w.state==='ready' ? 'pass' : 'warn'}>{w.state.toUpperCase()}</SbBadge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SbPanel>

          {/* ASSUMPTIONS / EXCLUSIONS */}
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap: 12}}>
            <SbPanel title="Assumptions" kicker="02" icon={I2Assumption}
              right={<SbBadge tone="warn">{SB_Q.assumptions.filter(a=>a.variation).length} VARIATION</SbBadge>}>
              <div>
                {SB_Q.assumptions.map((a,i,arr)=>(
                  <div key={a.id} style={{padding:'11px 16px', borderBottom: i<arr.length-1 ? `1px solid ${SB.rule}` : 'none', display:'grid', gridTemplateColumns:'90px 1fr', gap: 10}}>
                    <SbBadge tone="warn">{a.cat.toUpperCase()}</SbBadge>
                    <div>
                      <div style={{fontSize: 12.5, color:'#fff', lineHeight: 1.45}}>{a.text}</div>
                      {a.variation && (
                        <div style={{display:'flex', gap: 5, alignItems:'center', marginTop: 4, fontSize: 10, color: SB.fail, fontFamily: SB.mono, letterSpacing: 0.5, fontWeight: 700}}>
                          <I2Variation s={11} sw={2}/> VARIATION · {a.trigger.toUpperCase()}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </SbPanel>

            <SbPanel title="Exclusions" kicker="03" icon={I2Ban}>
              <div>
                {SB_Q.exclusions.map((e,i,arr)=>(
                  <div key={e.id} style={{padding:'11px 16px', borderBottom: i<arr.length-1 ? `1px solid ${SB.rule}` : 'none', display:'grid', gridTemplateColumns:'74px 1fr', gap: 10}}>
                    <SbBadge tone="muted">{e.cat.toUpperCase()}</SbBadge>
                    <div>
                      <div style={{fontSize: 12.5, color:'#fff', lineHeight: 1.45}}>{e.text}</div>
                      {e.partial && <div style={{fontSize: 11, color: SB.muted, marginTop: 3, fontStyle:'italic'}}>{e.partial}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </SbPanel>
          </div>

          {/* MILESTONES */}
          <SbPanel title="Payment schedule" kicker="04" icon={I2Gavel}
            right={<SbBadge tone="machine">{SB_Q.milestones.reduce((s,x)=>s+x.pct,0)}%</SbBadge>}>
            <table style={{width:'100%', borderCollapse:'collapse', fontVariantNumeric:'tabular-nums'}}>
              <tbody>
                {SB_Q.milestones.map((m,i,arr)=>{
                  const amt = Math.round(SB_TS * m.pct/100);
                  return (
                    <tr key={m.name} style={{borderBottom: i<arr.length-1 ? `1px solid ${SB.rule}` : 'none'}}>
                      <td style={{padding:'12px 16px', width: 42, fontFamily: SB.mono, color: SB.machine, fontSize: 11, fontWeight: 800}}>M{i+1}</td>
                      <td style={{padding:'12px 16px', fontSize: 13.5, fontWeight: 700, color:'#fff'}}>{m.name}</td>
                      <td style={{padding:'12px 16px', fontSize: 10.5, color: SB.mutedD, fontFamily: SB.mono, letterSpacing: 0.5, textTransform:'uppercase', fontWeight: 700}}>{m.trigger}</td>
                      <td style={{padding:'12px 16px', width: 60, textAlign:'right', fontFamily: SB.mono, fontSize: 13.5, fontWeight: 800, color: SB.machine}}>{m.pct}%</td>
                      <td style={{padding:'12px 16px', width: 100, textAlign:'right', fontFamily: SB.mono, fontSize: 13.5, fontWeight: 800, color:'#fff'}}>{sbC(amt)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </SbPanel>

          {/* WARRANTY + RETENTION + SOURCES */}
          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap: 12}}>
            <SbPanel title="Warranty" kicker="05" icon={I2Stamp}>
              <div style={{padding:'12px 16px', display:'grid', gridTemplateColumns:'74px 1fr', gap: 8, rowGap: 8}}>
                <div style={sbK()}>PERIOD</div>
                <div style={{fontSize: 12.5, fontWeight: 700, color:'#fff'}}>{SB_Q.warranty.period}</div>
                <div style={sbK()}>FROM</div>
                <div style={{fontSize: 12, color:'#d4d6da'}}>{SB_Q.warranty.start}</div>
                <div style={sbK()}>SCOPE</div>
                <div style={{fontSize: 12, color:'#d4d6da', lineHeight: 1.5}}>{SB_Q.warranty.scope}</div>
              </div>
            </SbPanel>

            <SbPanel title="Retention & terms" kicker="06" icon={I2Scaffold}>
              <div style={{padding:'12px 16px', display:'flex', gap: 12}}>
                <div style={{flex:1, background:'#0e0f10', border:`1px solid ${SB.rule}`, borderRadius: 4, padding:'10px 12px'}}>
                  <div style={sbK()}>RETENTION</div>
                  <div style={{display:'flex', alignItems:'baseline', gap: 3, marginTop: 4}}>
                    <div style={{fontSize: 28, fontWeight: 800, fontFamily: SB.mono, letterSpacing:-0.9, color: SB.machine}}>{SB_Q.retentionPct}</div>
                    <div style={{fontSize: 14, color: SB.muted, fontFamily: SB.mono}}>%</div>
                  </div>
                  <div style={{...sbK(), fontSize: 9, marginTop: 4}}>≈ {sbC(Math.round(SB_TS * SB_Q.retentionPct/100))}</div>
                </div>
                <div style={{flex:1, background:'#0e0f10', border:`1px solid ${SB.rule}`, borderRadius: 4, padding:'10px 12px'}}>
                  <div style={sbK()}>PAYMENT</div>
                  <div style={{display:'flex', alignItems:'baseline', gap: 3, marginTop: 4}}>
                    <div style={{fontSize: 28, fontWeight: 800, fontFamily: SB.mono, letterSpacing:-0.9, color:'#fff'}}>{SB_Q.paymentDays}</div>
                    <div style={{fontSize: 10.5, color: SB.muted, fontFamily: SB.mono, fontWeight: 700, letterSpacing: 0.5}}>DAYS NET</div>
                  </div>
                </div>
              </div>
            </SbPanel>

            <SbPanel title="Sources" kicker="07" icon={I2Plumb}
              right={<SbBadge tone="pass">94 / 100</SbBadge>}>
              <div style={{padding:'10px 16px', display:'flex', flexDirection:'column', gap: 8}}>
                {[
                  {I: I2Ledger,     n:7, t:'From catalog',      c: SB.pass},
                  {I: I2Plumb,      n:4, t:'From Peachtree',    c:'#fff'},
                  {I: I2Anvil,      n:3, t:'Insights applied',  c: SB.machine},
                  {I: I2Assumption, n:2, t:'Stated — capture?', c: SB.warn},
                ].map((r,i)=>(
                  <div key={i} style={{display:'flex', alignItems:'center', gap: 8, fontSize: 12.5}}>
                    <r.I s={13} sw={2} color={r.c}/>
                    <div style={{flex:1, color:'#d4d6da'}}>{r.t}</div>
                    <div style={{fontFamily: SB.mono, fontWeight: 800, fontSize: 13, color:'#fff'}}>{r.n}</div>
                  </div>
                ))}
              </div>
            </SbPanel>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { SiteBoardContract });
