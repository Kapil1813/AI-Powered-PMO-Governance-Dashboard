import streamlit as st
import pandas as pd

# ---------------------------
# Load Data
# ---------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("raid_data.csv")
    return df

df = load_data()

# ---------------------------
# KPI Calculations
# ---------------------------
total_projects = df['Project_ID'].nunique()
sla_breaches = df[df['SLA_Status'] == 'Breached'].shape[0]

projects_on_track = df[df['Project_Health'] == 'On Track']['Project_ID'].nunique()
projects_at_risk = df[df['Project_Health'] == 'At Risk']['Project_ID'].nunique()
projects_delayed = df[df['Project_Health'] == 'Delayed']['Project_ID'].nunique()

# ---------------------------
# Dashboard UI
# ---------------------------
st.title("📊 PMO RAID & Risk Dashboard")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Projects", total_projects)
col2.metric("SLA Breaches", sla_breaches)
col3.metric("On Track", projects_on_track)
col4.metric("At Risk", projects_at_risk)
col5.metric("Delayed", projects_delayed)

st.markdown("---")

# ---------------------------
# Filters
# ---------------------------
project_filter = st.selectbox("Select Project", ["All"] + list(df['Project'].unique()))

if project_filter != "All":
    filtered_df = df[df['Project'] == project_filter]
else:
    filtered_df = df

st.dataframe(filtered_df)

# ---------------------------
# AI Assistant (Interactive)
# ---------------------------
st.markdown("## 🤖 Ask PMO AI")

user_question = st.text_input("Ask a question about projects, risks, SLA, etc.")

def simple_ai_response(question, df):
    question = question.lower()

    if "sla" in question:
        return f"There are {sla_breaches} SLA breaches across projects."

    elif "risk" in question:
        high_risks = df[df['Type'] == 'Risk'].shape[0]
        return f"There are {high_risks} identified risks in the portfolio."

    elif "at risk" in question:
        return f"{projects_at_risk} projects are currently at risk."

    elif "on track" in question:
        return f"{projects_on_track} projects are on track."

    elif "delayed" in question:
        return f"{projects_delayed} projects are delayed."

    else:
        return "I can help with SLA, risks, project status, and dependencies. Try asking about those."

if user_question:
    response = simple_ai_response(user_question, df)
    st.success(response)

# ---------------------------
# Insights Section
# ---------------------------
st.markdown("## 📈 Key Insights")

st.write(f"- Total Projects: {total_projects}")
st.write(f"- SLA Breaches: {sla_breaches}")
st.write(f"- Projects At Risk: {projects_at_risk}")
st.write(f"- Projects On Track: {projects_on_track}")
st.write(f"- Projects Delayed: {projects_delayed}")

# ---------------------------
# Risk Breakdown
# ---------------------------
st.markdown("## ⚠️ RAID Breakdown")

raid_counts = df['Type'].value_counts()
st.bar_chart(raid_counts)