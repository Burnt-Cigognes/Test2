# -*- coding: utf-8 -*-
"""
Created on Sun Apr  5 14:55:42 2026

@author: chris
"""

import requests
from edgar import Company, set_identity


EMAIL = 'ENTER_YOUR_ADDRESS_EMAIL'
SEC_HEADERS = {
    'User-Agent': EMAIL
}


class SecClient:
    def __init__(self):
        self.companies_list = None
        self.facts_cache = {}
        set_identity(EMAIL)

    def get_companies_list(self):
        """
        Fetches a list of companies from a public API.
        
        Returns:
        --------
        list
            A list of companies with their tickers and CIKs.
        """
        if self.companies_list:
            return self.companies_list
        
        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers=SEC_HEADERS)
        
        if response.ok:
            companies = response.json()
            self.companies_list = sorted(companies.values(), key=lambda company: company['ticker'])
            return self.companies_list
        
        print("Failed to fetch companies list.", response.status_code, response.text)
        return []

    def get_company_facts(self, cik: str):
        """
        Fetches company facts from the SEC API for a given CIK.
        
        Parameters:
        -----------
        cik : str
            The Central Index Key (CIK) of the company.
        
        Returns:
        --------
        dict
            A dictionary containing company facts.
        """
        company = Company(cik)
        filings = company.get_filings(form="10-K").filter(form="10-K", amendments=False)
        num_filings = min(5, len(filings))
        filings = filings.head(num_filings)
        
        income = company.income_statement().to_llm_context() # or to_llm_string
        balance = company.balance_sheet().to_llm_context()
        cashflow = company.cash_flow().to_llm_context()
        
        ret = {
            'name': company.name,
            'ticker': company.get_ticker(),
            'business_description': filings[0].obj().business[0:1000],
            'income_context': income,
            'balance_context': balance,
            'cashflow_context': cashflow            
        }
        
        return ret