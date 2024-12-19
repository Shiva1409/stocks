import asyncio
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import time
import random
from fake_useragent import UserAgent

# List of NIFTY 50 tickers
nifty_50_tickers = [
    "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS", "TATASTEEL",
    "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO"
]

ua = UserAgent()

# Async function to fetch stock price and PE ratio
async def fetch_price_and_pe(session, ticker, retries=5, delay=1):
    url = f'https://www.screener.in/company/{ticker}/consolidated/'
    for attempt in range(retries):
        try:
            headers = {'user-agent': ua.random}
            async with session.get(url, headers=headers, timeout=15) as response:
                response.raise_for_status()
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

                # Extracting stock price
                price = soup.find('div', class_='flex flex-align-center').text.strip().split()[1].replace(',', '')

                # Extracting PE ratio
                pe_ratio = soup.find_all('li', class_='flex flex-space-between')[3].text.strip().split()[-1]

                return {'Ticker': ticker, 'Price': float(price), 'PE Ratio': float(pe_ratio)}
        except Exception as e:
            if attempt == retries - 1:
                return {'Ticker': ticker, 'Price': None, 'PE Ratio': None}
            await asyncio.sleep(delay + random.uniform(0, 2))  # Random delay for better mimicry

# Async function to fetch all data
async def fetch_all_data(tickers):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_price_and_pe(session, ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks)
        return results

# Streamlit App
st.set_page_config(page_title="NIFTY 50 Stock Prices and PE Ratios", layout="wide")

# Header
st.title("📈 NIFTY 50 Stock Prices and PE Ratios")
st.markdown("An interactive dashboard to view the latest prices and PE ratios of NIFTY 50 stocks. Data is fetched live from [Screener](https://www.screener.in).")

# Add a refresh button
if st.button("🔄 Refresh Data"):
    st.session_state["refresh"] = True  # Trigger a refresh when the button is pressed

# Initialize session state to store the data
if "data" not in st.session_state or st.session_state.get("refresh", False):
    with st.spinner("Fetching stock prices and PE ratios..."):
        data = asyncio.run(fetch_all_data(nifty_50_tickers))

        # Ensure all data is fetched
        valid_data = [item for item in data if item['Price'] is not None and item['PE Ratio'] is not None]
        if len(valid_data) == len(nifty_50_tickers):
            st.session_state["data"] = valid_data
            st.session_state["refresh"] = False  # Reset the refresh state
        else:
            st.error("Failed to fetch complete data. Please try refreshing.")

# Convert to DataFrame
if "data" in st.session_state:
    df = pd.DataFrame(st.session_state["data"])

    # Display the data with a clean design
    st.subheader("📊 Current Stock Prices and PE Ratios")
    st.dataframe(df, height=600)

    # Adding a chart to visualize stock prices
    st.subheader("📉 Stock Price Distribution")
    if not df.empty:
        st.bar_chart(df.set_index('Ticker')['Price'])

    # Adding a chart to visualize PE ratios
    st.subheader("📉 PE Ratio Distribution")
    if not df.empty:
        st.bar_chart(df.set_index('Ticker')['PE Ratio'])
