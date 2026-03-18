import streamlit as st
import pandas as pd
import numpy as np
import os


# -----------------------------
# Optional OpenAI Setup (safe)
# -----------------------------
USE_AI = False
client = None
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        USE_AI = True
except Exception:
    USE_AI = False

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(page_title="AI PMO Dashboard", layout="wide")
st.title("🚀 AI-Powered PMO Governance Dashboard")

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader("Upload PMO Data (CSV)", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    if df.empty:
        st.warning("Uploaded file is empty.")
        st.stop()

    # -----------------------------
    # GLOBAL TEXT DATA
    # -----------------------------
    text_data = df.to_string() if not df.empty else "No data available"

    # -----------------------------
    # Key Metrics
    # -----------------------------
    st.subheader("📊 Key Metrics")

    total_projects = len(df)
    status_series = df.get('Status', pd.Series(dtype=str)).astype(str).str.lower()
    sla_series = df.get('SLA Breach', pd.Series(dtype=str)).astype(str).str.lower()
    on_time = (status_series == 'on track').sum()
    sla_breach = (sla_series == 'yes').sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Projects", total_projects)
    col2.metric("On-Time Delivery", f"{on_time}/{total_projects}")
    col3.metric("SLA Breaches", sla_breach)

    # -----------------------------
    # Cycle Time Chart
    # -----------------------------
    st.subheader("📈 Cycle Time Analysis")
    if 'Cycle Time' in df.columns:
        st.line_chart(df['Cycle Time'])

    # -----------------------------
    # RAID Classification
    # -----------------------------
    st.subheader("⚠️ RAID Classification")

    def classify_raid(row):
        raid = []
        if pd.notna(row.get('Risk')) and str(row.get('Risk')).lower() != 'none':
            raid.append('Risk')
        if pd.notna(row.get('Issue')) and str(row.get('Issue')).lower() != 'none':
            raid.append('Issue')
        if pd.notna(row.get('Dependency')) and str(row.get('Dependency')).lower() != 'none':
            raid.append('Dependency')
        return ", ".join(raid) if raid else "None"

    df['RAID Type'] = df.apply(classify_raid, axis=1)
    st.dataframe(df, use_container_width=True)

    # -----------------------------
    # Predictive Risk Scoring Feature
    # -----------------------------
    st.subheader("📊 Predictive Risk Scoring")

    # Simple predictive model based on SLA breach, cycle time, and RAID type
    def risk_score(row):
        score = 0
        if str(row.get('SLA Breach','No')).lower() == 'yes':
            score += 50
        if 'Risk' in str(row.get('RAID Type','')):
            score += 30
        if 'Issue' in str(row.get('RAID Type','')):
            score += 20
        if 'Dependency' in str(row.get('RAID Type','')):
            score += 10
        if pd.notna(row.get('Cycle Time')):
            score += min(row['Cycle Time'],20)  # cap to 20
        return score

    df['Risk Score'] = df.apply(risk_score, axis=1)

    st.bar_chart(df[['Project','Risk Score']].set_index('Project'))

    # -----------------------------
    # AI Insights
    # -----------------------------
    st.subheader("🤖 AI Insights")
    if st.button("Generate AI Insights"):
        if USE_AI and client:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a PMO expert."},
                        {"role": "user", "content": f"Analyze this PMO data and provide risks, root causes, and improvements:\n{text_data}"}
                    ]
                )
                st.write(response.choices[0].message.content)
            except Exception as e:
                st.error(f"AI error: {e}")
        else:
            st.warning("AI not configured. Showing sample insights.")
            st.write("Top Risks: Content delays, metadata issues")
            st.write("Root Cause: Manual workflows, vendor dependency")
            st.write("Improvement: Automate QC, improve SLA tracking")

    # -----------------------------
    # Ask PMO AI
    # -----------------------------
    st.subheader("💬 Ask PMO AI")
    user_question = st.text_input("Ask a question about your PMO data")
    if user_question and text_data:
        if USE_AI and client:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a PMO analyst."},
                        {"role": "user", "content": f"Data:\n{text_data}\nQuestion: {user_question}"}
                    ]
                )
                st.write(response.choices[0].message.content)
            except Exception as e:
                st.error(f"AI error: {e}")
        else:
            st.write("Sample Answer: SLA breaches are driven by delays and QC failures.")

    # -----------------------------
    # Survey Sentiment Analysis
    # -----------------------------
    st.subheader("📋 Survey Sentiment Analysis")
    if 'Survey Feedback' in df.columns:
        def simple_sentiment(text):
            if isinstance(text, str):
                t = text.lower()
                if 'good' in t:
                    return 'Positive'
                elif 'bad' in t:
                    return 'Negative'
            return 'Neutral'
        df['Sentiment'] = df['Survey Feedback'].apply(simple_sentiment)
        st.bar_chart(df['Sentiment'].value_counts())

    # -----------------------------
    # Downtime Tracker
    # -----------------------------
    st.subheader("⏱️ Downtime Impact Tracker")
    if 'Downtime (hrs)' in df.columns:
        total_downtime = df['Downtime (hrs)'].sum()
        st.metric("Total Downtime (hrs)", total_downtime)
        st.bar_chart(df['Downtime (hrs)'])

else:
    st.info("Upload a CSV file to get started.")

st.markdown("---")
st.markdown("Built for PMO Governance, Process Improvement, Predictive Risk Scoring, and AI Insights")