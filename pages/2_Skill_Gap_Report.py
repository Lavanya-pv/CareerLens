import streamlit as st

st.set_page_config(page_title="Skill gap report · CareerLens", page_icon="◈", layout="wide")

from modules.database import get_analysis, get_recent_analyses, initialize_database
from modules.report_generator import generate_report
from careerlens.ui_style import render_sidebar
from ui_components.charts import breakdown_chart, category_skill_chart
from ui_components.widgets import skill_chips


render_sidebar()
st.markdown('<div class="eyebrow">CAREERLENS / YOUR REPORT</div><h1 style="font:700 34px Manrope">A focused view of your skill fit.</h1><p class="subtle">Review matched, related, and missing job requirements.</p>', unsafe_allow_html=True)
initialize_database()
analyses = get_recent_analyses()
if not analyses:
    st.info("Your first report will appear here after you analyze a resume.")
    st.stop()
selected = st.selectbox("Choose an analysis", analyses, format_func=lambda row: f"{row['job_title']} · {round(row['overall_score'])}% · {row['created_at']}")
data = get_analysis(selected["id"])
st.download_button("Download report PDF", generate_report(data), file_name=f"careerlens-report-{data['id']}.pdf", mime="application/pdf")
score_col, chart_col = st.columns([.7, 1.3], gap="large")
with score_col:
    st.metric("Overall compatibility", f"{round(data['overall_score'])}%")
    st.caption("Indicative compatibility measure, not a hiring prediction.")
with chart_col:
    st.plotly_chart(breakdown_chart(data["breakdown"]), use_container_width=True, config={"displayModeBar": False})
st.markdown("#### Skill coverage by category")
st.plotly_chart(category_skill_chart(data["skills"]), use_container_width=True, config={"displayModeBar": False})
groups = data["skill_gaps"]
matched, partial, missing = st.columns(3)
with matched:
    st.markdown(f"#### Matched · {len(groups['matched_skills'])}")
    skill_chips([item.get("skill", item.get("name", "")) for item in groups["matched_skills"]])
with partial:
    st.markdown(f"#### Partial · {len(groups['partially_matched_skills'])}")
    skill_chips([item.get("skill", item.get("name", "")) for item in groups["partially_matched_skills"]], "partial")
with missing:
    st.markdown(f"#### Missing · {len(groups['missing_skills'])}")
    skill_chips([item.get("skill", item.get("name", "")) for item in groups["missing_skills"]], "missing")
with st.expander("Skill classification and score details"):
    for section in ("matched_skills", "partially_matched_skills", "missing_skills"):
        for item in groups[section]:
            explanation = item.get("explanation", item.get("evidence", "Direct canonical skill match."))
            st.write(f"**{item.get('skill', item.get('name', ''))}:** {explanation}")
    st.write("The score weights required skill coverage at 50%, semantic relevance at 30%, and experience/qualification relevance at 20%.")
st.markdown("#### Learning roadmap")
plan = data["recommendations"].get("recommendations", [])
for item in plan:
    with st.container(border=True):
        st.markdown(f"**{item['skill']}** · {item['priority']} priority · {item['level'] or 'Resource needed'}")
        if item["resource_url"]:
            st.markdown(f"[{item['resource_name']}]({item['resource_url']}) · {item['estimated_hours']} hours")
        else:
            st.caption(item["explanation"])
        if item["project_idea"]:
            st.caption("Project: " + item["project_idea"])
