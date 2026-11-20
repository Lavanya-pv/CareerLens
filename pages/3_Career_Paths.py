import json

import streamlit as st

st.set_page_config(page_title="Career paths · CareerLens", page_icon="◈", layout="wide")

from careerlens.config import ROLE_PROFILES_PATH
from careerlens.ui_style import render_sidebar
from modules.database import get_analysis, get_recent_analyses, initialize_database
from careerlens.matching.role_matcher import rank_roles
from ui_components.widgets import skill_chips


render_sidebar()
st.markdown('<div class="eyebrow">CAREERLENS / EXPLORE</div><h1 style="font:700 34px Manrope">Explore adjacent career paths.</h1><p class="subtle">Role matches are based on skills you have directly demonstrated in a saved resume analysis.</p>', unsafe_allow_html=True)
initialize_database()
analyses = get_recent_analyses()
if not analyses:
    st.info("Analyze a resume to explore skill-aligned career paths.")
    st.stop()
selected = st.selectbox("Resume analysis", analyses, format_func=lambda row: f"{row['job_title']} · {round(row['overall_score'])}%")
analysis = get_analysis(selected["id"])
matched = [item.get("skill", item.get("name", "")) for item in analysis["skill_gaps"]["matched_skills"]]
profiles = json.loads(ROLE_PROFILES_PATH.read_text(encoding="utf-8"))
ranked = rank_roles(set(matched), profiles)
st.caption(f"Using {len(matched)} directly matched skills from analysis #{analysis['id']}. These are exploratory comparisons, not hiring predictions.")
for role in ranked:
    with st.container(border=True):
        left, right = st.columns([1.2, .8])
        left.markdown(f"### {role['name']}")
        left.caption(next(profile["category"] for profile in profiles if profile["name"] == role["name"]))
        right.progress(role["score"], text=f"{round(role['score'] * 100)}% skill alignment")
        st.markdown("**Skills in common**")
        skill_chips(role["matched"])
        st.markdown("**Skills to develop**")
        skill_chips(role["missing"], "missing")
