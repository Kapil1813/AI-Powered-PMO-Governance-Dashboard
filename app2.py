import streamlit as st
import pandas as pd
import os

# -----------------------------
# OpenAI Setup (Safe)
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
# App Config
# -----------------------------
st.set_page_config(page_title="AI PMO Dashboard", layout="wide")
st.title("🚀 AI-Powered PMO Governance Dashboard")

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
    # RAID Classification
    # -----------------------------
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
    # Context Builder (KEY UPGRADE)
    # -----------------------------
    def prepare_context(df):
        summary = {
            "total_projects": len(df),
            "sla_breaches": int((df['SLA Breach'].astype(str).str.lower() == 'yes').sum()),
            "on_track": int((df['Status'].astype(str).str.lower() == 'on track').sum())
        }

        top_risks = df[df['RAID Type'].str.contains("Risk", na=False)].head(5).to_dict(orient="records")

        return f"""
        Summary: {summary}
        Top Risks: {top_risks}
        Sample Data: {df.head(20).to_dict(orient="records")}
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
    # Chat Section
    # -----------------------------
    st.subheader("💬 Ask PMO AI (Interactive)")

    if not USE_AI:
        st.warning("⚠️ AI not configured. Showing simulated responses.")

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input
    user_question = st.chat_input("Ask about risks, SLA, dependencies...")

    if user_question:

        # Guardrail
        if any(x in user_question.lower() for x in ["weather", "sports", "news"]):
            st.warning("Please ask PMO-related questions.")
            st.stop()

        # Save user question
        st.session_state.chat_history.append({"role": "user", "content": user_question})

        with st.chat_message("user"):
            st.write(user_question)

        # AI Response
        if USE_AI and client:
            try:
                messages = [
                    {"role": "system", "content": "You are a senior PMO consultant. Provide structured answers with Summary, Key Insights, and Recommendations."},
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
            # Fallback response
            answer = """
            Summary: SLA breaches are impacting delivery timelines.

            Key Insights:
            - Vendor dependencies causing delays
            - Manual QC processes slowing delivery

            Recommendations:
            - Automate QC workflows
            - Improve SLA tracking dashboards
            """

        # Save AI response
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

        with st.chat_message("assistant"):
            st.write(answer)

else:
    st.info("Upload a CSV file to start analysis.")

st.markdown("---")
st.markdown("Built for PMO Governance | AI Insights | Interview Demo Ready 🚀")