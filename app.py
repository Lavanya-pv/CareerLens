"""CareerLens dashboard: local resume analysis, actionable gaps, and progress history."""
import streamlit as st

st.set_page_config(page_title="CareerLens AI", page_icon="◈", layout="wide")

from modules.analysis_service import analyze_resume
from modules.database import get_analysis, get_recent_analyses, initialize_database
from modules.report_generator import generate_report
from careerlens.ui_style import render_sidebar
from ui_components.charts import breakdown_chart, category_skill_chart, fit_gauge, skill_status_chart
from ui_components.widgets import skill_chips


st.markdown('''<style>
.brand{font:800 20px Manrope,sans-serif;letter-spacing:-.8px}.brand span{color:var(--green)}
.dash-hero{background:linear-gradient(115deg,#19372a,#28533e);border-radius:20px;padding:34px 40px;color:#fff;margin:2px 0 24px;position:relative;overflow:hidden}
.dash-hero:after{content:'◈';position:absolute;right:44px;top:-44px;font-size:190px;color:#ffffff0b}.dash-hero h1{font:750 36px Manrope,sans-serif;letter-spacing:-1.4px;color:white;margin:8px 0}.dash-hero p{color:#d0ddd4;margin:0;max-width:670px}
.section-title{font:700 21px Manrope,sans-serif;letter-spacing:-.4px;margin:0 0 4px}.section-help{color:var(--muted);font-size:13px;margin-bottom:15px}
.metric{border:1px solid var(--line);border-radius:15px;padding:19px 21px;min-height:116px}.metric-label{font:500 10px 'DM Mono',monospace;text-transform:uppercase;letter-spacing:1.2px;color:var(--muted)}.metric-value{font:750 30px Manrope,sans-serif;letter-spacing:-1px;margin:5px 0}.metric-note{font-size:12px;color:var(--muted)}
.panel{border:1px solid var(--line);border-radius:16px;padding:20px 22px;background:var(--surface)}.panel h3{font:700 16px Manrope,sans-serif;margin:0 0 5px}.step-label{font:500 10px 'DM Mono',monospace;text-transform:uppercase;letter-spacing:1.2px;color:var(--green)}
@media(max-width:700px){.dash-hero{padding:25px 23px}.dash-hero h1{font-size:28px}.dash-hero:after{right:4px;font-size:120px}}
</style>''', unsafe_allow_html=True)

render_sidebar()
initialize_database()
recent = get_recent_analyses(limit=50)

st.markdown('''<div class="dash-hero"><div class="eyebrow" style="color:#d9f081">YOUR PRIVATE CAREER WORKSPACE</div><h1>Find your next opportunity.</h1><p>Turn your resume into a clear view of your strengths, role fit, and the skills that will move you forward.</p></div>''', unsafe_allow_html=True)

metric_cols = st.columns(3)
metric_data = [
    ("ANALYSES", str(len(recent)), "Saved on this device"),
    ("LATEST ROLE FIT", f"{round(recent[0]['overall_score'])}%" if recent else "—", recent[0]["target_name"] if recent else "Run your first analysis"),
    ("SKILLS TO BUILD", str(recent[0]["missing_count"]) if recent else "—", "From your latest report" if recent else "Your gaps become a plan"),
]
for col, (label, value, note) in zip(metric_cols, metric_data):
    with col:
        st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)
if notice := st.session_state.pop("analysis_notice", None):
    st.success(notice)
if warning := st.session_state.pop("analysis_warning", None):
    st.warning(warning)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Start an analysis</div><div class="section-help">Upload a resume and paste the target job description. Analysis stays on this device.</div>', unsafe_allow_html=True)
with st.container(border=True):
    upload_col, target_col = st.columns([.9, 1.1], gap="large")
    with upload_col:
        st.markdown('<div class="step-label">01 &nbsp; YOUR RESUME</div>', unsafe_allow_html=True)
        upload = st.file_uploader("Upload a text-based PDF", type=["pdf"], help="Files are processed and stored locally on this device.")
    with target_col:
        st.markdown('<div class="step-label">02 &nbsp; YOUR TARGET</div>', unsafe_allow_html=True)
        target_name = st.text_input("Job title", placeholder="e.g. Product Data Analyst", key="dashboard_target_title")
        jd_text = st.text_area("Job description (optional)", placeholder="Paste the full job description for a tailored skill comparison, or leave blank to use a supported role profile...", height=150, key="dashboard_job_description", help="When blank, CareerLens uses its built-in profile for the selected supported job title.")
    submitted = st.button("Analyze my resume  →", type="primary", use_container_width=True)

if submitted:
    if upload is None:
        st.error("Upload a PDF resume to get started.")
    elif not target_name.strip():
        st.error("Enter a target title to continue.")
    else:
        try:
            with st.spinner("Reading your resume and matching your experience…"):
                result = analyze_resume(upload, target_name.strip(), jd_text)
            st.session_state["active_analysis_id"] = result["analysis_id"]
            st.session_state["analysis_notice"] = f"Analysis saved for {result['target_name']}. Your report is ready below."
            st.session_state["analysis_warning"] = result["warnings"][0] if result["warnings"] else None
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

active_id = st.session_state.get("active_analysis_id")
if not active_id and recent:
    active_id = recent[0]["id"]
analysis = get_analysis(active_id) if active_id else None

if analysis:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">Your match overview</div><div class="section-help">{analysis["filename"]} &nbsp;·&nbsp; Targeting {analysis["target_name"]}</div>', unsafe_allow_html=True)
    st.download_button(
        "Download analysis report (PDF)",
        data=generate_report(analysis),
        file_name=f"careerlens-report-{analysis['id']}.pdf",
        mime="application/pdf",
        key=f"download_report_{analysis['id']}",
    )
    top_left, top_right = st.columns([.72, 1.28], gap="large")
    with top_left:
        with st.container(border=True):
            st.plotly_chart(fit_gauge(analysis["overall_score"]), use_container_width=True, config={"displayModeBar": False})
            st.caption("An indicative score based on required skill coverage, semantic relevance, and experience/qualification relevance.")
    with top_right:
        with st.container(border=True):
            st.markdown("#### Score breakdown")
            st.caption("See what contributes to your overall fit.")
            st.plotly_chart(breakdown_chart(analysis["breakdown"]), use_container_width=True, config={"displayModeBar": False})

    skills = analysis["skills"]
    matched = [skill["skill"] for skill in skills if skill["status"] == "matched"]
    partial = [skill["skill"] for skill in skills if skill["status"] == "partial"]
    missing = [skill["skill"] for skill in skills if skill["status"] == "missing"]
    skill_left, skill_right = st.columns([1, 1], gap="large")
    with skill_left:
        with st.container(border=True):
            st.markdown("#### Skill coverage")
            st.caption("Distribution of target skills by resume evidence, with category-level detail on hover.")
            st.plotly_chart(skill_status_chart(skills), use_container_width=True, config={"displayModeBar": False})
        with st.container(border=True):
            st.markdown("#### Coverage by category")
            st.plotly_chart(category_skill_chart(skills), use_container_width=True, config={"displayModeBar": False})
    with skill_right:
        with st.container(border=True):
            st.markdown(f"#### What you bring · {len(matched)} matched")
            skill_chips(matched)
        with st.container(border=True):
            st.markdown(f"#### Related experience · {len(partial)} skills")
            skill_chips(partial, "partial")
        with st.container(border=True):
            st.markdown(f"#### Skills to build · {len(missing)} gaps")
            skill_chips(missing, "missing")

    st.markdown("<br>", unsafe_allow_html=True)
    roadmap_col, history_col = st.columns([1.15, .85], gap="large")
    with roadmap_col:
        st.markdown('<div class="section-title">Your learning roadmap</div><div class="section-help">Focused resources and portfolio ideas for your next steps.</div>', unsafe_allow_html=True)
        learning_plan = analysis["recommendations"].get("recommendations", [])
        if learning_plan:
            for index, item in enumerate(learning_plan[:6], 1):
                with st.container(border=True):
                    st.markdown(f"**{index:02d} &nbsp; {item['skill']}** · {item['priority']} priority")
                    if item.get("resource_name"):
                        st.markdown(f"[{item['resource_name']}]({item['resource_url']}) · {item['level']} · {item['estimated_hours']} hours")
                    else:
                        st.caption(item["explanation"])
                    if item.get("project_idea"):
                        st.caption("Portfolio idea: " + item["project_idea"])
        else:
            st.info("Your current skill profile aligns well. Review the role report for resume tips.")
    with history_col:
        st.markdown('<div class="section-title">Recent analyses</div><div class="section-help">Your reports, saved locally.</div>', unsafe_allow_html=True)
        if recent:
            for row in recent[:6]:
                with st.container(border=True):
                    c1, c2 = st.columns([1.6, .6])
                    c1.markdown(f"**{row['target_name']}**")
                    c1.caption(row["filename"] + " · " + row["created_at"])
                    c2.metric("Fit", f"{round(row['overall_score'])}%")
                    if st.button("View report", key=f"view_{row['id']}", use_container_width=True):
                        st.session_state["active_analysis_id"] = row["id"]
                        st.rerun()
        else:
            st.info("Your analysis history will appear here after your first run.")
else:
    st.info("Upload your resume above to see your match score, skill gaps, roadmap, and analysis history together.")
