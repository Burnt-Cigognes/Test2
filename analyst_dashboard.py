# -*- coding: utf-8 -*-
"""
Created on Sun Apr  5 14:52:46 2026

@author: chris
"""

import streamlit as st
import json
from typing import Dict, Any

# Import the two custom classes that handle SEC data fetching and AI communication
from sec import SecClient
from openrtr import OpenRouterClient

# Configure the Streamlit page — sets the browser tab title, icon, and layout
# This must be the first Streamlit call in the script
st.set_page_config(
    page_title="SEC Financial Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def analyze_with_ai(company_name: str, ticker: str, company_facts: Dict[str, Any], openrtr_client: OpenRouterClient) -> str:
    # Convert the company facts dictionary into a formatted JSON string for inclusion in the prompt
    facts_summary = json.dumps(company_facts, indent=2, default=str)

    # Build a detailed prompt that instructs the AI to act as a financial analyst.
    # The prompt specifies exactly what sections to output so the response is structured
    # and can be reliably rendered in the dashboard.
    prompt = f"""
You are an expert financial analyst. Analyze the following SEC company facts for {company_name} ({ticker})
and provide a comprehensive structured analysis. Use only the data provided. Output only the following sections/data points.
This output is going to be used in an another application, you are not chatting with anyone.

    Company Overview of <company name> (<ticker>)
        - Brief description of business
    Financial Health:
        - Assessment: Strong/Moderate/Weak
        - Explanation of assessment
        - Key metrics like total assets, net income, operating income, debt, and cash/cash equivalents
    Growth Potential:
        - Assessment: High/Moderate/Low
        - Key drivers of this assessment
        - Highest risks affecting this assessment
    Investment Recommendation:
        - Buy/Hold/Sell
        - Descriptive outlook
        - Key catalysts
        - Highest risk factors
    Financial Metrics:
        - Revenue trends
        - Profitability
        - Leverage
        - Liquidity
    Sentiment Analysis:
        - Overall sentiment: Exuberant/Positive/Neutral/Negative/Horrible
        - Confidence level (0 to 100%)
        - Explain what is impacting the confidence score.
        - List key concerns

Company Facts Summary from SEC EDGAR:
{facts_summary}"""

    response = openrtr_client.chat(prompt)

    # Streamlit interprets $...$ as LaTeX math notation.
    # Escape all dollar signs so financial figures render as plain text instead of math formulas.
    response = response.replace("$", "\\$")
    return response


def main():
    # Page title and subtitle displayed at the top of the dashboard
    st.title("🏦 SEC Financial Analyst Dashboard")
    st.markdown("Select a company to analyze SEC filings with AI-powered financial expertise")

    # Instantiate the SEC data client and AI client — one of each for the full session
    sec_client = SecClient()
    openrtr_client = OpenRouterClient()

    # Fetch the full list of SEC-listed companies on load, with a spinner shown to the user
    with st.spinner("Loading companies list..."):
        companies = sec_client.get_companies_list()

    if not companies:
        st.error("Failed to load companies list. Please check your internet connection.")
        return

    # --- Sidebar: Company Selection ---
    st.sidebar.header("Company Selection")

    # Build a dictionary mapping display strings ("Company Name (TICKER)") to their full data.
    # This powers the dropdown while keeping the full company object accessible.
    company_options = {f"{c.get('title', 'Unknown')} ({c.get('ticker', 'N/A')})" : c for c in companies}

    selected_company_str = st.sidebar.selectbox(
        "Select a company to analyze:",
        options=list(company_options.keys()),
        help="Choose a company from the SEC database"
    )

    # Retrieve the full company data object for the selected dropdown entry
    selected_company = company_options[selected_company_str]
    ticker = selected_company.get("ticker")
    company_name = selected_company.get("title")

    # The SEC API requires CIKs to be zero-padded to exactly 10 digits (e.g. 123 → 0000000123)
    cik = str(selected_company.get("cik_str")).zfill(10)

    st.sidebar.write(f"**CIK:** {cik}")

    # --- Analyze Button ---
    # Everything below only runs when the user clicks the button
    if st.sidebar.button("📊 Analyze Company", use_container_width=True):

        # Split the output into two tabs: AI analysis and raw data
        tab1, tab2 = st.tabs(["Analysis", "Raw Data"])

        with tab1:
            st.info("Fetching company facts and performing AI analysis...")

            # Step 1 — Fetch the company's financial data from SEC EDGAR
            with st.spinner("Fetching SEC company facts..."):
                company_facts = sec_client.get_company_facts(cik)

            if not company_facts:
                st.error("Failed to fetch company facts. Please try another company.")
                return

            # Step 2 — Send the financial data to the AI and get back a structured analysis
            with st.spinner("Analyzing with AI expert financial analyst..."):
                analysis = analyze_with_ai(company_name, ticker, company_facts, openrtr_client)

            # Render the AI response as formatted markdown in the dashboard
            st.markdown(analysis)

        with tab2:
            # Display the raw SEC data as an expandable JSON viewer for transparency
            st.subheader("Raw Company Facts")
            st.json(company_facts)


if __name__ == "__main__":
    main()
