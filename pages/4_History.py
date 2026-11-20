import streamlit as st

st.set_page_config(page_title="History · CareerLens", page_icon="◈", layout="wide")

from modules.database import get_analysis, get_recent_analyses, initialize_database
from modules.report_generator import generate_report
from careerlens.ui_style import render_sidebar


render_sidebar()
st.markdown('<div class="eyebrow">CAREERLENS / HISTORY</div><h1 style="font:700 34px Manrope">Your analysis history.</h1><p class="subtle">Saved locally. Original resume text is not retained in the new analysis history.</p>', unsafe_allow_html=True)
initialize_database()
records = get_recent_analyses(limit=100)
if not records:
    st.info("Your completed analyses will appear here.")
    st.stop()
for record in records:
    with st.container(border=True):
        left, middle, right = st.columns([2, .8, .9])
        left.markdown(f"**{record['job_title']}**")
        left.caption(f"Analysis #{record['id']} · {record['created_at']}")
        middle.metric("Compatibility", f"{round(record['overall_score'])}%")
        data = get_analysis(record["id"])
        right.download_button("Download PDF", generate_report(data), file_name=f"careerlens-report-{record['id']}.pdf", mime="application/pdf", key=f"history_pdf_{record['id']}")
