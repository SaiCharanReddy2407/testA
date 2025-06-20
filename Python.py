import streamlit as st
import requests
import cx_Oracle

# -------------------- CONFIGURATION --------------------
# Groq API Key
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"

# Oracle sample connection (replace later with real)
ORACLE_CONFIG = {
    "host": "localhost",
    "port": "1521",
    "service_name": "orclpdb1",
    "username": "system",
    "password": "oracle"
}

# Table schema shown to user and passed to GPT
TABLE_SCHEMA = """
Table: Sales
- Product_id VARCHAR(20)
- Product_name VARCHAR(50)
- Sale_amount INT
- Profit_amount INT
"""

# -------------------- FUNCTION: Call Groq AI --------------------
def generate_sql_from_prompt(user_prompt):
    try:
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": f"You are a SQL assistant. Use only this table:\n{TABLE_SCHEMA}\nOnly respond with the Oracle SQL query, no explanation."},
                {"role": "user", "content": user_prompt}
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

# -------------------- FUNCTION: Execute Oracle Query --------------------
def execute_oracle_query(query):
    try:
        dsn = cx_Oracle.makedsn(
            ORACLE_CONFIG["host"],
            ORACLE_CONFIG["port"],
            service_name=ORACLE_CONFIG["service_name"]
        )
        connection = cx_Oracle.connect(
            ORACLE_CONFIG["username"],
            ORACLE_CONFIG["password"],
            dsn
        )
        cursor = connection.cursor()
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        connection.close()
        return data
    except Exception as e:
        return f"❌ Oracle Error: {str(e)}"

# -------------------- STREAMLIT UI --------------------
st.set_page_config(page_title="Oracle SQL Generator", layout="centered")
st.title("🧠 Natural Language to Oracle SQL (Groq AI)")

# Show schema in read-only textbox
st.subheader("📊 Table Structure")
st.text_area("Oracle Table Schema", value=TABLE_SCHEMA.strip(), height=120, disabled=True)

# Prompt input
st.subheader("💬 Enter Your Prompt")
user_prompt = st.text_area("Ask your query in plain English:", placeholder="e.g. List products with Sale_amount > 1000")

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
        with st.spinner("Executing on Oracle..."):
            result = execute_oracle_query(st.session_state.sql_output)
            st.session_state.query_result = result

# Display query result
if st.session_state.query_result:
    st.subheader("📄 Query Result")
    result = st.session_state.query_result
    if isinstance(result, str):
        st.error(result)
    elif result:
        st.dataframe(result)
    else:
        st.info("No records found.")