"""Holographic HUD theme: deep-navy glass surfaces, cyan<->magenta neon, and an
animated AI orb as the signature element. Injected once at the top of the app.

Palette
  void   #070b16   background
  panel  rgba(255,255,255,.045) glass
  cyan   #22d3ee   primary neon
  sky    #38bdf8
  violet #a855f7
  magenta#d946ef   secondary neon
  text   #e8eefc / muted #93a4c4
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;800&family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

:root{
  --void:#070b16; --panel:rgba(255,255,255,.045);
  --line:rgba(120,200,255,.16); --cyan:#22d3ee; --sky:#38bdf8;
  --violet:#a855f7; --magenta:#d946ef; --text:#e8eefc; --muted:#93a4c4;
  --neon:linear-gradient(120deg,#22d3ee 0%,#38bdf8 35%,#a855f7 70%,#d946ef 100%);
}

/* ── base ─────────────────────────────────────────────────────────── */
html,body{ background:var(--void); }
.stApp{ background:var(--void); color:var(--text); }
html,body,[class*="css"]{ font-family:'Inter',sans-serif; color:var(--text); }

/* ambient drifting glow behind everything */
.stApp::before{
  content:""; position:fixed; inset:-10%; z-index:0; pointer-events:none;
  background:
    radial-gradient(440px circle at 14% 18%, rgba(34,211,238,.20), transparent 60%),
    radial-gradient(480px circle at 86% 82%, rgba(168,85,247,.20), transparent 60%),
    radial-gradient(360px circle at 60% 40%, rgba(217,70,239,.10), transparent 60%);
  animation:drift 18s ease-in-out infinite alternate;
}
@keyframes drift{ from{transform:translate3d(0,0,0)} to{transform:translate3d(0,-26px,0)} }
/* keep real content above the glow */
[data-testid="stAppViewContainer"]{ position:relative; z-index:1; }

h1,h2,h3{ font-family:'Rajdhani',sans-serif !important; color:var(--text);
  letter-spacing:.02em; font-weight:700; }

/* ── header banner ────────────────────────────────────────────────── */
.vi-header{
  display:flex; align-items:center; justify-content:space-between; gap:22px;
  background:var(--panel); backdrop-filter:blur(14px);
  border:1px solid var(--line); border-radius:20px;
  padding:22px 26px; margin-bottom:22px; position:relative; overflow:hidden;
  box-shadow:0 0 0 1px rgba(34,211,238,.06), 0 24px 60px rgba(3,8,20,.6),
             inset 0 1px 0 rgba(255,255,255,.05);
  animation:rise .7s cubic-bezier(.2,.8,.2,1) both;
}
@keyframes rise{ from{opacity:0; transform:translateY(14px)} to{opacity:1; transform:none} }
/* moving neon hairline across the top */
.vi-header::after{
  content:""; position:absolute; left:0; right:0; top:0; height:2px;
  background:var(--neon); background-size:300% 100%;
  animation:slide 6s linear infinite; opacity:.9;
}
@keyframes slide{ from{background-position:0% 0} to{background-position:300% 0} }

.vi-eyebrow{ font-family:'Rajdhani'; font-weight:600; letter-spacing:.32em;
  font-size:.72rem; text-transform:uppercase; color:var(--cyan); margin:0 0 4px; }
.vi-title{
  font-family:'Orbitron',sans-serif; font-weight:800; font-size:1.95rem;
  line-height:1.05; margin:0; letter-spacing:.01em;
  background:var(--neon); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent;
  filter:drop-shadow(0 0 18px rgba(56,189,248,.35));
}
.vi-chips{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }
.chip{
  display:inline-flex; align-items:center; gap:7px;
  font-family:'Rajdhani'; font-weight:600; font-size:.8rem; letter-spacing:.02em;
  color:#cfe0f5; padding:5px 12px; border-radius:999px;
  background:rgba(255,255,255,.04); border:1px solid var(--line);
}
.chip .dot{ width:7px; height:7px; border-radius:50%; display:inline-block;
  box-shadow:0 0 8px currentColor; }
.dot.c{ background:var(--cyan); color:var(--cyan); }
.dot.m{ background:var(--magenta); color:var(--magenta); }
.dot.v{ background:var(--violet); color:var(--violet); }

/* ── the signature orb ────────────────────────────────────────────── */
.vi-orb{ flex:0 0 auto; }
.vi-orb svg{ width:92px; height:92px; display:block;
  filter:drop-shadow(0 0 14px rgba(34,211,238,.45)); }
.orb-spin{ transform-origin:60px 60px; animation:spin 9s linear infinite; }
.orb-spin-rev{ transform-origin:60px 60px; animation:spin 14s linear infinite reverse; }
.orb-core{ transform-origin:60px 60px; animation:pulse 2.6s ease-in-out infinite; }
@keyframes spin{ to{ transform:rotate(360deg) } }
@keyframes pulse{ 0%,100%{ opacity:.55; transform:scale(.9) } 50%{ opacity:1; transform:scale(1.08) } }

/* ── buttons ──────────────────────────────────────────────────────── */
.stButton>button{
  font-family:'Rajdhani'; font-weight:700; letter-spacing:.04em;
  color:#eaf6ff; background:rgba(34,211,238,.08);
  border:1px solid rgba(34,211,238,.45); border-radius:12px;
  padding:.55rem 1.5rem; transition:all .18s ease;
  box-shadow:0 0 0 1px rgba(34,211,238,.05), 0 0 18px rgba(34,211,238,.12);
}
.stButton>button:hover{
  transform:translateY(-2px); color:#fff; border-color:var(--cyan);
  background:rgba(34,211,238,.16);
  box-shadow:0 0 26px rgba(34,211,238,.45), 0 0 50px rgba(168,85,247,.25);
}
.stButton>button:focus{ box-shadow:0 0 0 3px rgba(34,211,238,.35) !important; }

/* ── chat bubbles as glass cards ──────────────────────────────────── */
[data-testid="stChatMessage"]{
  background:var(--panel); backdrop-filter:blur(10px);
  border:1px solid var(--line); border-left:3px solid var(--cyan);
  border-radius:14px; padding:8px 10px; margin-bottom:10px;
  box-shadow:0 0 22px rgba(34,211,238,.07), 0 14px 30px rgba(3,8,20,.45);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){
  border-left:3px solid var(--magenta);
  box-shadow:0 0 22px rgba(217,70,239,.09), 0 14px 30px rgba(3,8,20,.45);
}

/* ── progress bar ─────────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div > div{ background:rgba(255,255,255,.06); }
[data-testid="stProgress"] > div > div > div > div{
  background:var(--neon) !important;
  box-shadow:0 0 14px rgba(56,189,248,.6);
}

/* ── score metric ─────────────────────────────────────────────────── */
[data-testid="stMetricValue"]{
  font-family:'Orbitron'; font-weight:800;
  background:var(--neon); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent;
  filter:drop-shadow(0 0 16px rgba(56,189,248,.4));
}
[data-testid="stMetricLabel"]{ color:var(--muted) !important;
  font-family:'Rajdhani'; letter-spacing:.06em; text-transform:uppercase; }

/* ── alerts / feedback as glass ───────────────────────────────────── */
[data-testid="stAlert"]{
  background:var(--panel) !important; backdrop-filter:blur(10px);
  border:1px solid var(--line) !important; border-radius:14px;
  color:var(--text) !important;
}

/* audio recorder + sidebar polish */
[data-testid="stAudioInput"]{
  border:1px solid var(--line); border-radius:14px;
  box-shadow:0 0 22px rgba(34,211,238,.10);
}
[data-testid="stSidebar"]{
  background:rgba(8,12,22,.7); backdrop-filter:blur(12px);
  border-right:1px solid var(--line);
}
[data-testid="stExpander"]{ border:1px solid var(--line) !important;
  border-radius:14px; background:var(--panel); }

.vi-gold{ font-family:'Orbitron'; font-weight:700;
  background:var(--neon); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent; }

/* respect reduced-motion */
@media (prefers-reduced-motion: reduce){
  .stApp::before,.vi-header,.vi-header::after,.orb-spin,.orb-spin-rev,.orb-core{
    animation:none !important; }
}
</style>
"""


def inject(st):
    st.markdown(CSS, unsafe_allow_html=True)


def _orb_svg() -> str:
    # concentric holographic rings + pulsing core (the signature element)
    return """
    <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="g1" x1="0" y1="0" x2="120" y2="120">
          <stop offset="0" stop-color="#22d3ee"/>
          <stop offset="1" stop-color="#d946ef"/>
        </linearGradient>
      </defs>
      <circle cx="60" cy="60" r="46" stroke="url(#g1)" stroke-width="1.5"
              stroke-opacity=".55" class="orb-spin"
              stroke-dasharray="8 10"/>
      <circle cx="60" cy="60" r="34" stroke="#38bdf8" stroke-width="1.5"
              stroke-opacity=".5" class="orb-spin-rev"
              stroke-dasharray="3 12"/>
      <circle cx="60" cy="60" r="22" stroke="url(#g1)" stroke-width="2"
              stroke-opacity=".7"/>
      <circle cx="60" cy="60" r="11" fill="url(#g1)" class="orb-core"/>
    </svg>
    """


def header(st, role: str, n: int, language: str, model: str):
    st.markdown(
        f"""
        <div class="vi-header">
          <div class="vi-head-left">
            <p class="vi-eyebrow">◈ Mock Interview System</p>
            <h1 class="vi-title">Voice Interview Agent</h1>
            <div class="vi-chips">
              <span class="chip"><i class="dot c"></i>{role}</span>
              <span class="chip"><i class="dot m"></i>{n} questions</span>
              <span class="chip"><i class="dot v"></i>{language}</span>
              <span class="chip"><i class="dot c"></i>{model}</span>
            </div>
          </div>
          <div class="vi-orb">{_orb_svg()}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
