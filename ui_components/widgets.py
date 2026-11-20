import streamlit as st
def score_card(score,label="Role fit"):
 st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{score}%</div><div class="metric-note">A guide to help you prioritize</div></div>',unsafe_allow_html=True)
def skill_chips(skills,status="matched"):
 cls={"matched":"","partial":"tag-warn","missing":"tag-miss"}.get(status,"")
 st.markdown(" ".join(f'<span class="tag {cls}">{s}</span>' for s in skills) or '<span class="subtle">None found</span>',unsafe_allow_html=True)
