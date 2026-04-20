# -*- coding: utf-8 -*-
"""
Created on Sun Apr 5 14:55:42 2026

@author: chris
"""

import requests
from edgar import Company, set_identity

EMAIL = "kdkdpd@gmail.com"
SEC_HEADERS = {
    "User-Agent": EMAIL
}


class SecClient:
    def __init__(self):
        self.companies_list = None
        self.facts_cache = {}
        set_identity(EMAIL)

    def get_companies_list(self):
        """
        Fetches the list of companies from SEC.

        Returns
        -------
        list
            A sorted list of companies with ticker / CIK information.
        """
        if self.companies_list is not None:
            return self.companies_list

        url = "https://www.sec.gov/files/company_tickers.json"

        try:
            response = requests.get(url, headers=SEC_HEADERS, timeout=30)
        except requests.RequestException as exc:
            print(f"Failed to fetch companies list: {exc}")
            return []

        if response.ok:
            try:
                companies = response.json()
                self.companies_list = sorted(
                    companies.values(),
                    key=lambda company: company.get("ticker", "")
                )
                return self.companies_list
            except ValueError as exc:
                print(f"Invalid JSON received from SEC companies list endpoint: {exc}")
                return []

        print("Failed to fetch companies list.", response.status_code, response.text)
        return []

    def get_company_facts(self, cik: str):
        """
        Fetches company data for a given CIK and formats it for LLM use.

        Parameters
        ----------
        cik : str
            Zero-padded CIK.

        Returns
        -------
        dict | None
            Dictionary of financial context and metadata, or None if unrecoverable error.
        """
        if not cik:
            return None

        if cik in self.facts_cache:
            return self.facts_cache[cik]

        try:
            company = Company(cik)
        except Exception as exc:
            print(f"Failed to initialize Company for CIK {cik}: {exc}")
            return None

        filings_count = 0
        selected_filings = None

        try:
            filings = company.get_filings(form="10-K").filter(form="10-K", amendments=False)
            filings_count = len(filings)

            if filings_count > 0:
                selected_filings = filings.head(min(5, filings_count))
        except Exception as exc:
            print(f"Failed to fetch 10-K filings for CIK {cik}: {exc}")

        income = None
        balance = None
        cashflow = None

        try:
            income_stmt = company.income_statement()
            if income_stmt is not None:
                income = income_stmt.to_llm_context()
        except Exception as exc:
            print(f"Income statement unavailable for CIK {cik}: {exc}")

        try:
            balance_sheet = company.balance_sheet()
            if balance_sheet is not None:
                balance = balance_sheet.to_llm_context()
        except Exception as exc:
            print(f"Balance sheet unavailable for CIK {cik}: {exc}")

        try:
            cash_flow_stmt = company.cash_flow()
            if cash_flow_stmt is not None:
                cashflow = cash_flow_stmt.to_llm_context()
        except Exception as exc:
            print(f"Cash flow statement unavailable for CIK {cik}: {exc}")

        business_description = "Business description unavailable."

        if selected_filings is not None:
            try:
                if len(selected_filings) > 0:
                    first_filing = selected_filings[0]
                    filing_obj = first_filing.obj()

                    business_text = getattr(filing_obj, "business", None)
                    if business_text:
                        business_description = str(business_text)[:1000]
            except Exception as exc:
                print(f"Business description unavailable for CIK {cik}: {exc}")

        try:
            ticker = company.get_ticker()
        except Exception:
            ticker = None

        try:
            company_name = company.name
        except Exception:
            company_name = None

        result = {
            "name": company_name,
            "ticker": ticker,
            "cik": cik,
            "filings_found": filings_count,
            "business_description": business_description,
            "income_context": income,
            "balance_context": balance,
            "cashflow_context": cashflow,
        }

        self.facts_cache[cik] = result
        return result
