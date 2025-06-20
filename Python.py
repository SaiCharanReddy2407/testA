import streamlit as st
import requests

# Set page config
st.set_page_config(page_title="Oracle SQL Generator", layout="centered")

# Groq API Key
GROQ_API_KEY = "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"

# Oracle Sales table schema
TABLE_SCHEMA = """
You are a SQL assistant. Convert the user's natural language question into a valid **Oracle SQL query**.

Use the following table schema:

Table: Sales
- Product_id VARCHAR(20)
- Product_name VARCHAR(50)
- Sale_amount INT
- Profit_amount INT

Respond with **only the SQL query** without any explanation or formatting.
"""

# Groq AI call function
def generate_sql_from_prompt(user_prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": TABLE_SCHEMA},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        sql_query = response.json()["choices"][0]["message"]["content"].strip()
        return sql_query
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Streamlit UI
st.title("🧠 Natural Language to Oracle SQL (Groq AI)")
st.markdown("Enter your question in plain English. It will be converted into a valid Oracle SQL query.")

user_prompt = st.text_area("Enter your prompt:", placeholder="e.g. Show products with sale amount > 5000", height=100)

if st.button("Generate SQL"):
    if user_prompt.strip() == "":
        st.warning("Please enter a prompt before clicking Generate.")
    else:
        with st.spinner("Generating Oracle SQL..."):
            sql_output = generate_sql_from_prompt(user_prompt)
            st.success("Here is the SQL query:")
            st.code(sql_output, language="sql")
