"""Shared visual system for CareerLens Streamlit pages."""
import streamlit as st

THEMES = {
    "Dark": {
        "ink": "#eef4f0", "muted": "#a0afa6", "line": "#2d3b33",
        "paper": "#101713", "surface": "#17211b", "sidebar": "#131c16",
        "green": "#8fd1a7", "mint": "#22372a", "text": "#eef4f0",
        "input": "#1b2820",
    },
}


def apply_style():
    c = THEMES["Dark"]
    st.markdown(f'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{{--ink:{c['ink']};--muted:{c['muted']};--line:{c['line']};--paper:{c['paper']};--surface:{c['surface']};--sidebar:{c['sidebar']};--green:{c['green']};--mint:{c['mint']};--text:{c['text']};--input:{c['input']}}}
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif;color:var(--text)}}.stApp{{background:radial-gradient(ellipse at 78% 0%,#1b2a20 0%,var(--paper) 42%);}}
.block-container{{max-width:1420px;padding-top:2.2rem;padding-bottom:3rem}}section[data-testid="stSidebar"]{{background:var(--sidebar);border-right:1px solid var(--line)}}
.eyebrow,.step-label{{font:600 10px 'DM Sans',sans-serif;text-transform:uppercase;letter-spacing:1.55px;color:var(--green)}}.brand{{font:800 22px Manrope,sans-serif;letter-spacing:-.8px}}.brand span{{color:var(--green)}}
.subtle,.section-help{{color:var(--muted);font-size:13px;line-height:1.55}}.section-title{{font:750 23px Manrope,sans-serif;letter-spacing:-.55px;margin:0 0 3px}}.metric,.panel,[data-testid="stVerticalBlockBorderWrapper"]{{background:var(--surface);border-color:var(--line);color:var(--text);border-radius:15px}}
.metric{{padding:18px 20px;min-height:108px}}.metric-label{{font:600 10px 'DM Sans',sans-serif;text-transform:uppercase;letter-spacing:1.2px;color:var(--muted)}}.metric-value{{font:800 30px Manrope,sans-serif;letter-spacing:-1px;margin:5px 0}}.metric-note{{font-size:12px;color:var(--muted)}}
.tag{{display:inline-block;background:var(--mint);color:var(--green);font-size:12px;font-weight:600;padding:6px 10px;border-radius:99px;margin:3px 4px 3px 0}}.tag-warn{{background:#49391f;color:#f0c775}}.tag-miss{{background:#472b29;color:#e49a8c}}
div.stButton>button[kind="primary"]{{background:#28734f;border:1px solid #398461;border-radius:10px;font-weight:700;color:#fff;min-height:44px}}div.stButton>button{{border-radius:9px}}div[data-testid="stFileUploader"]{{background:var(--surface);border:1px dashed #496454;border-radius:12px;padding:10px}}
div[data-baseweb="select"]>div,textarea,input{{background-color:var(--input)!important;color:var(--text)!important;border-color:var(--line)!important}}.stApp,[data-testid="stMarkdownContainer"]{{color:var(--text)}}[data-testid="stMarkdownContainer"] :is(h1,h2,h3,h4,h5,p,li,strong,em){{color:var(--text)}}
.stApp label,.stApp label p,[data-testid="stWidgetLabel"],[data-testid="stWidgetLabel"] p,[data-testid="stMetricLabel"],[data-testid="stMetricValue"]{{color:var(--text)!important}}[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{{color:var(--muted)!important}}
textarea::placeholder,input::placeholder{{color:var(--muted)!important;opacity:1}}[data-testid="stFileUploaderDropzoneInstructions"]{{color:var(--muted)!important}}[data-testid="stAlert"] p{{color:inherit!important}}footer,#MainMenu{{visibility:hidden}}
@media(max-width:720px){{.block-container{{padding:1.2rem 1rem 2rem}}.section-title{{font-size:20px}}}}
</style>''', unsafe_allow_html=True)


def render_sidebar():
    st.session_state["career_theme"] = "Dark"
    with st.sidebar:
        st.markdown('<div class="brand">◈ Career<span>Lens</span></div><div class="subtle">Your next move, made clearer.</div><br><div class="eyebrow">WORKSPACE</div>', unsafe_allow_html=True)
        st.page_link("app.py", label="⌂  Overview")
        st.page_link("pages/1_Analyze_Resume.py", label="↗  Analyze resume")
        st.page_link("pages/2_Skill_Gap_Report.py", label="◫  Skill gap report")
        st.page_link("pages/3_Career_Paths.py", label="⌁  Career paths")
        st.page_link("pages/4_History.py", label="◷  History")
        st.markdown('<br><br><div class="panel"><div class="eyebrow">PRIVATE BY DESIGN</div><p class="subtle">Your resume is analyzed locally. Your data stays on this device.</p></div>', unsafe_allow_html=True)
    apply_style()
