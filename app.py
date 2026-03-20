import streamlit as st
import pandas as pd
import os

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(page_title="AI PMO Governance Dashboard", layout="wide")
st.title("🚀 AI-Powered PMO Governance Dashboard")

# -----------------------------
# OpenAI Setup
# -----------------------------
USE_AI = False
client = None

try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        USE_AI = True
except:
    USE_AI = False

# -----------------------------
# Chat Memory
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# File Upload
# -----------------------------
uploaded_file = st.file_uploader("Upload PMO Data (CSV)", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    # -----------------------------
    # Data Preparation
    # -----------------------------
    df['Go Live Date'] = pd.to_datetime(df['Go Live Date'], errors='coerce')

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

    # -----------------------------
    # Context Builder (AI)
    # -----------------------------
    def prepare_context(df):
        summary = {
            "total_projects": len(df),
            "sla_breaches": int((df['SLA Breach'].astype(str).str.lower() == 'yes').sum()),
            "on_track": int((df['Status'].astype(str).str.lower() == 'on track').sum())
        }

        return f"""
        Summary: {summary}
        Projects: {df[['Project Name','Owner','Status','Priority','Region','Go Live Date','RAID Type']].to_dict(orient="records")}
        """

    context = prepare_context(df)

    # -----------------------------
    # Metrics
    # -----------------------------
    st.subheader("📊 Key Metrics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Projects", len(df))
    col2.metric("SLA Breaches", (df['SLA Breach'].astype(str).str.lower() == 'yes').sum())
    col3.metric("On Track", (df['Status'].astype(str).str.lower() == 'on track').sum())

    # -----------------------------
    # Program Insights
    # -----------------------------
    st.subheader("🧠 Program Insights")

    # Top Risks
    st.markdown("### 🔴 Top Risks")
    risks_df = df[df['RAID Type'].str.contains("Risk", na=False)].head(5)
    st.dataframe(risks_df if not risks_df.empty else pd.DataFrame({"Info": ["No risks found"]}))

    # Go-Live Blockers
    st.markdown("### ⛔ Go-Live Blockers")
    blockers_df = df[
        (df['Status'].astype(str).str.lower() != 'on track') |
        (df['SLA Breach'].astype(str).str.lower() == 'yes')
    ]
    st.dataframe(blockers_df.head(5) if not blockers_df.empty else pd.DataFrame({"Info": ["No blockers"]}))

    # High Priority
    st.markdown("### 🚨 High Priority Projects")
    high_priority_df = df[df['Priority'].str.lower() == 'high']
    st.dataframe(high_priority_df[['Project Name','Owner','Status','Region']])

    # Upcoming Go-Live Risks
    st.markdown("### 📅 Upcoming Go-Live Risks")
    upcoming_df = df[
        (df['Go Live Date'] <= pd.Timestamp.today() + pd.Timedelta(days=10)) &
        (df['Status'].str.lower() != 'on track')
    ]
    st.dataframe(upcoming_df[['Project Name','Go Live Date','Status','Owner']] if not upcoming_df.empty else pd.DataFrame({"Info": ["No upcoming risks"]}))

    # Regional Summary
    st.markdown("### 🌍 Regional Impact")
    region_summary = df.groupby('Region')['Project ID'].count().reset_index()
    region_summary.columns = ['Region', 'Total Projects']
    st.dataframe(region_summary)

    # -----------------------------
    # AI Recommendations
    # -----------------------------
    st.markdown("### 💡 AI Recommended Actions")

    def generate_recommendations(context):
        if USE_AI and client:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a PMO expert. Provide concise actionable recommendations."},
                        {"role": "user", "content": f"Analyze this PMO data:\n{context}"}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"AI error: {e}"
        else:
            return """
            - Prioritize high-risk projects
            - Resolve SLA breaches
            - Reduce dependency delays
            - Improve metadata & compliance workflows
            """

    st.write(generate_recommendations(context))

    # -----------------------------
    # Chat Section
    # -----------------------------
    st.subheader("💬 Ask PMO AI")

    if not USE_AI:
        st.warning("⚠️ AI not configured. Using fallback insights.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask about risks, delays, priorities...")

    if user_input:

        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        if USE_AI and client:
            try:
                messages = [
                    {"role": "system", "content": "You are a senior PMO consultant. Answer clearly with insights and actions."},
                    {"role": "system", "content": f"Context:\n{context}"}
                ] + st.session_state.chat_history

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages
                )

                answer = response.choices[0].message.content

            except Exception as e:
                answer = f"AI error: {e}"
        else:
            answer = "Focus on resolving risks and SLA breaches to improve delivery."

        st.session_state.chat_history.append({"role": "assistant", "content": answer})

        with st.chat_message("assistant"):
            st.write(answer)

else:
    st.info("Upload a CSV file to begin.")

st.markdown("---")
st.markdown("Built for Program Governance | AI Insights | Interview Demo 🚀")