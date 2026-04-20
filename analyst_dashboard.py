# -*- coding: utf-8 -*-
"""
Created on Sun Apr 5 14:52:46 2026

@author: chris
"""

import json
from typing import Dict, Any

import streamlit as st

from sec import SecClient
from openrtr import OpenRouterClient, OpenRouterError


st.set_page_config(
    page_title="SEC Financial Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def get_sec_client():
    return SecClient()


@st.cache_resource
def get_openrouter_client():
    return OpenRouterClient()


def analyze_with_ai(
    company_name: str,
    ticker: str,
    company_facts: Dict[str, Any],
    openrtr_client: OpenRouterClient
) -> str:
    """
    Builds a financial analysis prompt and sends it to OpenRouter.
    """
    facts_summary = json.dumps(company_facts, indent=2, default=str)

    prompt = f"""
You are an expert financial analyst. Analyze the following SEC company facts for {company_name} ({ticker})
and provide a comprehensive structured analysis. Use only the data provided. Output only the following sections/data points.
This output is going to be used in another application, you are not chatting with anyone.

Company Overview of {company_name} ({ticker})
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
- Explain what is impacting the confidence score
- List key concerns

Company Facts Summary from SEC EDGAR:
{facts_summary}
"""

    response = openrtr_client.chat(prompt)

    # Escape dollar signs so Streamlit does not interpret them as LaTeX
    response = response.replace("$", "\\$")
    return response


def main():
    st.title("🏦 SEC Financial Analyst Dashboard")
    st.markdown("Select a company to analyze SEC filings with AI-powered financial expertise")

    sec_client = get_sec_client()
    openrtr_client = get_openrouter_client()

    with st.spinner("Loading companies list..."):
        companies = sec_client.get_companies_list()

    if not companies:
        st.error("Failed to load companies list. Please check your internet connection.")
        return

    st.sidebar.header("Company Selection")

    company_options = {
        f"{c.get('title', 'Unknown')} ({c.get('ticker', 'N/A')})": c
        for c in companies
    }

    selected_company_str = st.sidebar.selectbox(
        "Select a company to analyze:",
        options=list(company_options.keys()),
        help="Choose a company from the SEC database"
    )

    selected_company = company_options[selected_company_str]
    ticker = selected_company.get("ticker", "N/A")
    company_name = selected_company.get("title", "Unknown")
    cik = str(selected_company.get("cik_str")).zfill(10)

    st.sidebar.write(f"**CIK:** {cik}")

    if st.sidebar.button("📊 Analyze Company", use_container_width=True):
        tab1, tab2 = st.tabs(["Analysis", "Raw Data"])

        company_facts = None

        with tab1:
            st.info("Fetching company facts and performing AI analysis...")

            with st.spinner("Fetching SEC company facts..."):
                try:
                    company_facts = sec_client.get_company_facts(cik)
                except Exception as exc:
                    st.exception(exc)
                    return

            if not company_facts:
                st.error("Failed to fetch company facts. Please try another company.")
                return

            if company_facts.get("filings_found", 0) == 0:
                st.warning(
                    "No 10-K filings were found for this company. "
                    "The analysis may be partial or less reliable."
                )

            with st.spinner("Analyzing with AI expert financial analyst..."):
                try:
                    analysis = analyze_with_ai(
                        company_name=company_name,
                        ticker=ticker,
                        company_facts=company_facts,
                        openrtr_client=openrtr_client
                    )
                except OpenRouterError as exc:
                    st.error(f"OpenRouter error: {exc}")
                    return
                except Exception as exc:
                    st.exception(exc)
                    return

            st.markdown(analysis)

        with tab2:
            st.subheader("Raw Company Facts")
            if company_facts:
                st.json(company_facts)
            else:
                st.info("No raw data available.")


if __name__ == "__main__":
    main()
