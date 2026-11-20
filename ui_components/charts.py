"""Detailed, theme-aware Plotly charts for role-fit and skill-gap reports."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from careerlens.ui_style import THEMES


def _theme():
    return THEMES["Dark"]


def _transparent_layout(fig, height=300):
    theme = _theme()
    fig.update_layout(height=height, margin=dict(l=10, r=30, t=28, b=12), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_family="DM Sans", font_color=theme["text"], xaxis=dict(gridcolor=theme["line"], zerolinecolor=theme["line"]), yaxis=dict(gridcolor=theme["line"], zerolinecolor=theme["line"]), showlegend=False)
    return fig


def breakdown_chart(breakdown):
    """Show score components on a consistent 0-100 scale."""
    theme = _theme()
    names = {"required_skill_coverage": "Required skill coverage", "semantic_relevance": "Semantic relevance", "experience_qualifications": "Experience & qualifications"}
    frame = pd.DataFrame({"Component": [names.get(k, k.replace("_", " ").title()) for k in breakdown], "Score": [float(v) for v in breakdown.values()]})
    fig = go.Figure()
    for _, row in frame.iterrows():
        fig.add_trace(go.Bar(y=[row.Component], x=[row.Score], orientation="h", marker_color=theme["green"], showlegend=False, text=[f"{row.Score:.0f}%"], textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>Score: %{x:.1f}%<extra></extra>"))
    fig.update_layout(xaxis=dict(range=[0, 110], tickvals=[0, 25, 50, 75, 100], ticksuffix="%", title="Component score"), yaxis=dict(autorange="reversed", title=None), bargap=.48)
    return _transparent_layout(fig, max(270, 66 * len(frame)))


def score_bar(breakdown):
    return breakdown_chart(breakdown)


def fit_gauge(score):
    theme = _theme()
    fig = go.Figure(go.Indicator(mode="gauge+number", value=score, number={"suffix": "%", "font": {"size": 46, "color": theme["text"]}}, title={"text": "OVERALL COMPATIBILITY", "font": {"size": 12, "color": theme["muted"]}}, gauge={"axis": {"range": [0, 100], "visible": True, "tickvals": [0, 25, 50, 75, 100], "tickfont": {"color": theme["muted"], "size": 10}}, "bar": {"color": theme["green"], "thickness": .28}, "bgcolor": theme["surface"], "borderwidth": 0, "steps": [{"range": [0, 35], "color": "#382724"}, {"range": [35, 70], "color": "#40391f"}, {"range": [70, 100], "color": "#20382a"}] }))
    fig.update_layout(height=275, margin=dict(l=25, r=25, t=42, b=18), paper_bgcolor="rgba(0,0,0,0)", font_color=theme["text"])
    return fig


def skill_gap_chart(skills):
    theme = _theme()
    rows = []
    for label, group in (("Required", [x for x in skills if x.get("required", True)]), ("Preferred", [x for x in skills if not x.get("required", True)])):
        for status, title in (("matched", "Matched"), ("partial", "Related"), ("missing", "Missing")):
            rows.append({"Skill group": label, "Status": title, "Count": sum(x.get("status") == status for x in group)})
    frame = pd.DataFrame(rows)
    fig = px.bar(frame, x="Skill group", y="Count", color="Status", barmode="stack", text="Count", color_discrete_map={"Matched": theme["green"], "Related": "#d6a25c", "Missing": "#bd7568"})
    fig.update_traces(textposition="inside", hovertemplate="%{x}<br>%{data.name}: %{y} skills<extra></extra>")
    fig.update_layout(xaxis_title=None, yaxis_title="Target skills", legend_title="Resume evidence", showlegend=True, legend=dict(orientation="h", y=1.15, x=0))
    return _transparent_layout(fig, 290)


def category_skill_chart(skills):
    theme = _theme()
    if not skills:
        return _transparent_layout(go.Figure(), 260)
    frame = pd.DataFrame(skills)
    if "category" not in frame:
        frame["category"] = "General"
    if "skill" not in frame:
        frame["skill"] = ""
    counts = frame.groupby(["category", "status"], dropna=False).agg(Count=("status", "size"), Skills=("skill", lambda values: ", ".join(map(str, values)))).reset_index().rename(columns={"category": "Category", "status": "Status"})
    counts["Status"] = counts["Status"].map({"matched": "Matched", "partial": "Partial", "missing": "Missing"}).fillna("Missing")
    colors = {"Matched": theme["green"], "Partial": "#d6a25c", "Missing": "#bd7568"}
    fig = px.bar(counts, x="Count", y="Category", color="Status", barmode="stack", orientation="h", color_discrete_map=colors, custom_data=["Skills"])
    fig.update_traces(hovertemplate="%{y}<br>%{fullData.name}: %{x}<br>Skills: %{customdata[0]}<extra></extra>", texttemplate="%{x}", textposition="inside")
    fig.update_layout(xaxis_title="Number of target skills", yaxis_title=None, legend_title="Resume evidence", showlegend=True, legend=dict(orientation="h", y=1.15, x=0), bargap=.35)
    return _transparent_layout(fig, max(290, 52 * frame["category"].nunique()))


def skill_status_chart(skills):
    """Show counts and shares of target skills by evidence status."""
    theme = _theme()
    statuses = [("matched", "Matched", theme["green"]), ("partial", "Partial", "#d6a25c"), ("missing", "Missing", "#bd7568")]
    counts = [sum(item.get("status") == key for item in skills) for key, _, _ in statuses]
    total = sum(counts)
    if not total:
        return _transparent_layout(go.Figure(), 260)
    fig = go.Figure(go.Pie(labels=[label for _, label, _ in statuses], values=counts, hole=.68, sort=False, marker={"colors": [color for _, _, color in statuses], "line": {"color": theme["surface"], "width": 3}}, textinfo="label+value", hovertemplate="%{label}: %{value} skills (%{percent})<extra></extra>"))
    fig.add_annotation(text=f"{total}<br><span style='font-size:11px'>target skills</span>", x=.5, y=.5, showarrow=False, font={"size": 22, "color": theme["text"]})
    fig.update_layout(showlegend=False)
    return _transparent_layout(fig, 290)
