import streamlit as st
import requests
import psycopg2
import pandas as pd

# -------------------- CONFIGURATION -------------------- #
# Groq API Config
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"

# Railway PostgreSQL Config
POSTGRES_CONFIG = {
    "host": "ballast.proxy.rlwy.net",
    "port": 31593,
    "dbname": "railway",
    "user": "postgres",
    "password": "LgXDJqdbIFlVvmeTURueCqKXaapCOotV"
}

# Updated Table Schema (for LLM prompt)
TABLE_SCHEMA = """
Table: public.train
- Row ID: int
- Order ID: varchar(50)
- Order Date: varchar(50)
- Ship Date: varchar(50)
- Ship Mode: varchar(50)
- Customer ID: varchar(50)
- Customer Name: varchar(50)
- Segment: varchar(50)
- Country: varchar(50)
- City: varchar(50)
- State: varchar(50)
- Postal Code: int
- Region: varchar(50)
- Product ID: varchar(50)
- Category: varchar(50)
- Sub-Category: varchar(50)
- Product Name: varchar(128)
- Sales: float
"""

# -------------------- FUNCTION: Call Groq API -------------------- #
def generate_sql_from_prompt(user_prompt):
    try:
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a SQL assistant. Use only this table:\n{TABLE_SCHEMA}\nOnly respond with the PostgreSQL SQL query, no explanation."
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

# -------------------- FUNCTION: Execute PostgreSQL Query -------------------- #
def execute_postgres_query(query):
    try:
        conn = psycopg2.connect(
            host=POSTGRES_CONFIG["host"],
            port=POSTGRES_CONFIG["port"],
            dbname=POSTGRES_CONFIG["dbname"],
            user=POSTGRES_CONFIG["user"],
            password=POSTGRES_CONFIG["password"]
        )
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return f"❌ PostgreSQL Error: {str(e)}"

# -------------------- STREAMLIT UI -------------------- #
st.set_page_config(page_title="PostgreSQL SQL Generator", layout="centered")
st.title("🧠 Natural Language to SQL (Railway PostgreSQL)")

# Hide schema section (optional)
# st.subheader("📊 Table Structure")
# st.text_area("PostgreSQL Table Schema", value=TABLE_SCHEMA.strip(), height=260, disabled=True)

st.subheader("💬 Enter Your Prompt")
user_prompt = st.text_area("Ask your query in plain English:", placeholder="e.g. List top 10 products by sales")

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

# Show editable SQL
if st.session_state.sql_output:
    st.subheader("📝 Generated SQL (Editable)")
    st.session_state.sql_output = st.text_area("Edit your SQL if needed:", value=st.session_state.sql_output, height=150)

    # Submit & Run Query
    if st.button("🚀 Submit & Run Query"):
        with st.spinner("Running SQL on PostgreSQL..."):
            result = execute_postgres_query(st.session_state.sql_output)
            st.session_state.query_result = result

# Display query result
if st.session_state.query_result is not None:
    st.subheader("📄 Query Result")
    if isinstance(st.session_state.query_result, str):
        st.error(st.session_state.query_result)
    elif not st.session_state.query_result.empty:
        st.dataframe(st.session_state.query_result)
        st.download_button("📥 Download as CSV", st.session_state.query_result.to_csv(index=False), file_name="query_result.csv")
    else:
        st.info("No records found.")
