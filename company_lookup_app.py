import streamlit as st
import os
import requests
import pandas as pd
from dotenv import load_dotenv
from io import StringIO

# Load API key from .env if available
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# App setup
st.set_page_config(page_title="Company Contact Finder (Live AI)", layout="centered")
st.title("📇 Company Contact Finder (OpenRouter + Web Search)")
st.caption("🔍 Uses Perplexity.ai via OpenRouter to find real contacts and leadership data")

# Allow key entry fallback
if not api_key:
    api_key = st.text_input("🔐 OpenRouter API Key", type="password")
    if not api_key:
        st.warning("Please enter your API key to continue.")
        st.stop()

# Get available models from OpenRouter
@st.cache_data
def get_available_models(api_key):
    try:
        resp = requests.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        models = resp.json()["data"]
        return [model["id"] for model in models if "perplexity" in model["id"] or "online" in model["id"]]
    except Exception as e:
        st.error("Model loading error. Please check your API key or network.")
        return []

models = get_available_models(api_key)
preferred_model = "perplexity/llama-3-sonar-large-online"
default_model = preferred_model if preferred_model in models else models[0] if models else None

# Model selector
if default_model:
    model = st.selectbox("🧠 Choose an AI Model with Web Access", models, index=models.index(default_model))
else:
    st.error("❌ No valid models found.")
    st.stop()

# User input
st.markdown("### 🔎 Enter Company Details")
company = st.text_input("🏢 Company Name", placeholder="e.g. SHS Consulting")
website = st.text_input("🌐 Company Website", placeholder="e.g. shs-co.de")
country = st.text_input("📍 Country", value="Germany")
run = st.button("Find Real Leadership Contacts")

# Query OpenRouter
def query_openrouter(api_key, model, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

# Table parser from markdown
def parse_markdown_table(text):
    table_lines = [line for line in text.split("\n") if "|" in line and "---" not in line]
    if not table_lines:
        return None
    headers = [cell.strip() for cell in table_lines[0].split("|") if cell.strip()]
    rows = [[cell.strip() for cell in row.split("|") if cell.strip()] for row in table_lines[1:]]
    return pd.DataFrame(rows, columns=headers)

# Citations parser
def extract_citations(text):
    import re
    matches = re.findall(r"\[([^\]]+)\]\((https?://[^\)]+)\)", text)
    return matches

# Main logic
if run:
    if not company or not website or not country:
        st.warning("⚠️ Please fill in all fields.")
    else:
        with st.spinner("🔎 Searching the web for real contacts..."):

            domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

            prompt = f"""
You're a research AI with browsing capability. Find publicly listed or known C-level, Director, or Department Head contact info
for **{company}** (website: {website}) based in {country}. Use LinkedIn, company websites, or articles.

Return a markdown table with:
- Name | Role | LinkedIn | Email | General Company Email

👉 If something is not found, leave it blank or guess format like j.doe@{domain}.
Please cite source URLs under the table.
"""

            try:
                output = query_openrouter(api_key, model, prompt)
                st.markdown("### 📋 Results")
                st.markdown(output)

                # Parse and show export UI
                df = parse_markdown_table(output)
                if df is not None and not df.empty:
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button("⬇️ Download CSV", data=csv, file_name=f"{company.lower().replace(' ', '_')}_contacts.csv", mime="text/csv")

                    # Clipboard copy area
                    st.text_area("📎 Copy as CSV", df.to_csv(index=False), height=200)

                # Citation display
                citations = extract_citations(output)
                if citations:
                    st.markdown("### 📚 References")
                    for name, url in citations:
                        st.markdown(f"- [{name}]({url})")
                else:
                    st.info("ℹ️ No citations were found in the response.")

                st.caption("✅ AI-generated, real-time data with source links. Always double-check for accuracy or GDPR compliance.")
            except Exception as e:
                st.error(f"❌ Error from OpenRouter: {e}")