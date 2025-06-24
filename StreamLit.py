import streamlit as st
import requests
import oracledb
import pandas as pd

# -------------------- CONFIGURATION -------------------- #
# Groq API Key
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"

# Oracle config
ORACLE_CONFIG = {
    "host": "dataanalytics.apeasternpower.com",
    "port": 1521,
    "service_name": "oracle",
    "user": "EPDAU",
    "password": "EP#Analytics"
}

# Optional: Enable if using Oracle Instant Client
oracledb.init_oracle_client(lib_dir=r"C:\Program Files\Oracle\instant client\instantclient_23_7")

# Table schema (used internally by LLM, not shown in UI)
TABLE_SCHEMA = """
Table: EPDAU.DTR_COORDINATES
- CIRCLE_NAME VARCHAR2(90)
- DIVISION_NAME VARCHAR2(90)
- SUB_DIVISION_NAME VARCHAR2(90)
- SECTION_NAME VARCHAR2(90)
- SUB_STATION_NAME VARCHAR2(40)
- FEEDER_NAME VARCHAR2(50)
- FDR_TYPE VARCHAR2(90)
- FDR_CLASS VARCHAR2(90)
- FEEDER_CODE VARCHAR2(300)
- DTR_STRUC_CODE VARCHAR2(50) NOT NULL
- DTR_LOCATION VARCHAR2(100)
- DTR_CAPACITY VARCHAR2(10)
- LATITUDE VARCHAR2(60)
- LONGITUDE VARCHAR2(60)
"""

# -------------------- FUNCTION: Call Groq AI -------------------- #
def generate_sql_from_prompt(user_prompt):
    try:
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a SQL assistant. Use only this table:\n{TABLE_SCHEMA}\nOnly respond with the Oracle SQL query, no explanation."
                },
                {
                    "role": "user",
                    "content": f"{user_prompt.strip()} Don't use ';' at end of query."
                }
            ],
            "temperature": 0.2
        }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        sql_query = result["choices"][0]["message"]["content"].strip()
        return sql_query

    except Exception as e:
        return f"❌ Error: {str(e)}"

# -------------------- FUNCTION: Execute Oracle Query -------------------- #
def execute_oracle_query(query):
    try:
        dsn = oracledb.makedsn(
            ORACLE_CONFIG["host"],
            ORACLE_CONFIG["port"],
            service_name=ORACLE_CONFIG["service_name"]
        )
        conn = oracledb.connect(
            user=ORACLE_CONFIG["user"],
            password=ORACLE_CONFIG["password"],
            dsn=dsn
        )
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return f"❌ Oracle Error: {str(e)}"

# -------------------- STREAMLIT UI -------------------- #
st.set_page_config(page_title="Oracle SQL Generator", layout="centered")
st.title("🧠 Natural Language to Oracle SQL")

# Prompt input
st.subheader("💬 Enter Your Prompt")
user_prompt = st.text_area("Ask your query in plain English:", placeholder="e.g. List DTRs with capacity above 100")

# Session state for SQL and results
if "sql_output" not in st.session_state:
    st.session_state.sql_output = None
if "query_result" not in st.session_state:
    st.session_state.query_result = None

# Generate SQL button
if st.button("🔄 Generate SQL"):
    if user_prompt.strip() == "":
        st.warning("Please enter a prompt first.")
    else:
        with st.spinner("Generating SQL..."):
            sql = generate_sql_from_prompt(user_prompt)
            st.session_state.sql_output = sql
            st.session_state.query_result = None

# Show generated SQL
if st.session_state.sql_output:
    st.subheader("📝 Generated Oracle SQL Query")
    st.code(st.session_state.sql_output, language="sql")

    # Submit button to execute query
    if st.button("🚀 Submit & Run Query"):
        with st.spinner("Running SQL on Oracle..."):
            result = execute_oracle_query(st.session_state.sql_output)
            st.session_state.query_result = result

# Display query result
if st.session_state.query_result is not None:
    st.subheader("📄 Query Result")
    if isinstance(st.session_state.query_result, str):
        st.error(st.session_state.query_result)
    elif not st.session_state.query_result.empty:
        st.dataframe(st.session_state.query_result)
        st.download_button("📥 Download as CSV", st.session_state.query_result.to_csv(index=False), file_name="oracle_query_result.csv")
    else:
        st.info("No records found.")