import os
import requests
import pandas as pd
from datetime import date, timedelta

class DhanClient:
    def __init__(self, securities_csv_path="dhan_securities.csv"):
        self.client_id = os.getenv("DHAN_CLIENT_ID")
        self.access_token = os.getenv("DHAN_ACCESS_TOKEN")
        self.base_url = "https://api.dhan.co"
        self.headers = {
            "Content-Type": "application/json",
            "access-token": self.access_token,
        }
        self.securities_csv_path = securities_csv_path
        self._ensure_securities_file_exists()
        self.security_id_map = self._load_security_id_map()

    def _ensure_securities_file_exists(self):
        if not os.path.exists(self.securities_csv_path):
            print("Downloading Dhan securities file...")
            url = "https://images.dhan.co/api-data/api-scrip-master.csv"
            response = requests.get(url)
            response.raise_for_status()
            with open(self.securities_csv_path, "wb") as f:
                f.write(response.content)
            print("Download complete.")

    def _load_security_id_map(self):
        df = pd.read_csv(self.securities_csv_path, low_memory=False)
        id_map = {}

        # A more scalable way to map common index tickers to their official names
        index_alias_map = {
            "^NSEI": "NIFTY 50",
            "^NSEBANK": "NIFTY BANK"
        }

        for _, row in df.iterrows():
            if row['SEM_INSTRUMENT_NAME'] == 'EQUITY' and row['SEM_EXM_EXCH_ID'] == 'NSE' and row['SEM_SERIES'] == 'EQ':
                id_map[f"{row['SM_SYMBOL_NAME']}.NS"] = (
                    "NSE_EQ", "EQUITY", str(row['SEM_SMST_SECURITY_ID'])
                )
            elif row['SEM_INSTRUMENT_NAME'] == 'INDEX':
                for alias, official_name in index_alias_map.items():
                    if row['SM_SYMBOL_NAME'] == official_name:
                        id_map[alias] = (
                            "NSE_INDEX", "INDEX", str(row['SEM_SMST_SECURITY_ID'])
                        )
        return id_map

    def _make_request(self, method, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_historical_data(self, ticker, from_date, to_date):
        if ticker not in self.security_id_map:
            raise ValueError(f"Ticker {ticker} not found in security ID map.")

        segment, instrument, security_id = self.security_id_map[ticker]

        payload = {
            "securityId": security_id,
            "exchangeSegment": segment,
            "instrument": instrument,
            "fromDate": from_date.strftime("%Y-%m-%d"),
            "toDate": to_date.strftime("%Y-%m-%d"),
        }

        return self._make_request("POST", "/charts/historical", data=payload)

    def get_intraday_data(self, ticker):
        if ticker not in self.security_id_map:
            raise ValueError(f"Ticker {ticker} not found in security ID map.")

        segment, instrument, security_id = self.security_id_map[ticker]

        payload = {
            "securityId": security_id,
            "exchangeSegment": segment,
            "instrument": instrument,
        }

        return self._make_request("POST", "/charts/intraday", data=payload)

if __name__ == '__main__':
    # Example usage for testing
    client = DhanClient()
    if not client.client_id or not client.access_token:
        print("DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN must be set in .env file.")
    else:
        try:
            today = date.today()
            yesterday = today - timedelta(days=1)

            print("--- Testing Historical Data for RELIANCE.NS ---")
            historical_data = client.get_historical_data("RELIANCE.NS", yesterday, today)
            print(historical_data)

            print("\n--- Testing Intraday Data for RELIANCE.NS ---")
            intraday_data = client.get_intraday_data("RELIANCE.NS")
            print(intraday_data)

        except Exception as e:
            print(f"An error occurred: {e}")
