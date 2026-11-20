"""Dedicated resume/JD analysis view using the same modules as the dashboard."""
import streamlit as st

st.set_page_config(page_title="Analyze resume · CareerLens", page_icon="◈", layout="wide")

from modules.analysis_service import analyze_resume
from modules.report_generator import generate_report
from careerlens.ui_style import render_sidebar
from ui_components.charts import breakdown_chart, category_skill_chart, fit_gauge
from ui_components.widgets import skill_chips


render_sidebar()
st.markdown('<div class="eyebrow">CAREERLENS / ANALYZE</div><h1 style="font:700 34px Manrope">Resume to role fit.</h1><p class="subtle">Add a resume and a target job description for an explainable local analysis.</p>', unsafe_allow_html=True)
resume_col, target_col = st.columns([.9, 1.1], gap="large")
with resume_col:
    upload = st.file_uploader("Resume PDF", type=["pdf"], key="dedicated_resume_pdf")
with target_col:
    title = st.text_input("Job title", placeholder="e.g. Data Scientist", key="dedicated_job_title")
    description = st.text_area("Job description (optional)", height=190, placeholder="Paste role requirements for a tailored comparison, or leave blank to use a supported role profile...", key="dedicated_job_description", help="Title-only analysis is available for roles in CareerLens' built-in role catalog.")
submitted = st.button("Analyze resume", type="primary", use_container_width=True)

if submitted:
    if upload is None:
        st.error("Upload a PDF resume first.")
    elif not title.strip():
        st.error("Enter the job title to continue.")
    else:
        try:
            with st.spinner("Extracting skills and comparing your experience…"):
                result = analyze_resume(upload, title, description)
            st.session_state["active_analysis_id"] = result["analysis_id"]
            if result.get("used_role_profile"):
                st.info("No job description supplied. Results use CareerLens' built-in profile for this role.")
            for warning in result["warnings"]:
                st.warning(warning)
            st.success("Analysis saved to local history.")
            st.download_button("Download PDF report", generate_report(result), file_name=f"careerlens-report-{result['analysis_id']}.pdf", mime="application/pdf")
            col_score, col_breakdown = st.columns([.75, 1.25], gap="large")
            with col_score:
                st.plotly_chart(fit_gauge(result["overall_score"]), use_container_width=True, config={"displayModeBar": False})
                st.caption(result["disclaimer"])
            with col_breakdown:
                st.markdown("#### Component scores")
                st.plotly_chart(breakdown_chart(result["component_scores"]), use_container_width=True, config={"displayModeBar": False})
            st.markdown("#### Skill gaps by category")
            st.plotly_chart(category_skill_chart(result["skills"]), use_container_width=True, config={"displayModeBar": False})
            matched, partial, missing = st.columns(3)
            with matched:
                st.markdown(f"#### Matched · {len(result['gap_analysis']['matched_skills'])}")
                skill_chips([item["skill"] for item in result["gap_analysis"]["matched_skills"]])
            with partial:
                st.markdown(f"#### Partial · {len(result['gap_analysis']['partially_matched_skills'])}")
                skill_chips([item["skill"] for item in result["gap_analysis"]["partially_matched_skills"]], "partial")
            with missing:
                st.markdown(f"#### Missing · {len(result['gap_analysis']['missing_skills'])}")
                skill_chips([item["skill"] for item in result["gap_analysis"]["missing_skills"]], "missing")
            st.markdown("#### Learning roadmap")
            for item in result["recommendations"]["recommendations"]:
                with st.container(border=True):
                    st.markdown(f"**{item['skill']}** · {item['priority']} priority · {item['level'] or 'Resource needed'}")
                    if item["resource_url"]:
                        st.markdown(f"[{item['resource_name']}]({item['resource_url']}) · {item['estimated_hours']} hours")
                    else:
                        st.caption(item["explanation"])
                    if item["project_idea"]:
                        st.caption("Project: " + item["project_idea"])
        except Exception as exc:
            st.error(str(exc))
