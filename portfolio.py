import pandas as pd
import yfinance as yf
import datetime
import numpy as np
import matplotlib.pyplot as plt
from pandas_datareader import data as pdr
import seaborn as sns

yf.pdr_override()

# Importing Excel File
user_input = input("Enter excel filename: ")
portfolio_df = pd.read_excel(user_input, sheet_name="Sheet1")

# Defining start and end date
start_date = datetime.datetime(2019, 1, 2)
end_date = datetime.datetime(2020, 5, 8) + datetime.timedelta(days=1)

# Formatting SP500 dataset and stocks data set
tickers = portfolio_df['Ticker'].unique().tolist()
sp500_data = pdr.get_data_yahoo('^GSPC', start_date, end_date)
sp500_data_adj_close = sp500_data[['Adj Close']].reset_index()
sp500_start_adj_close = sp500_data_adj_close.loc[sp500_data_adj_close['Date']
                                                 == start_date, 'Adj Close'].iloc[0]
sp500_end_adj_close = sp500_data_adj_close.loc[sp500_data_adj_close['Date']
                                               == end_date - datetime.timedelta(days=1), 'Adj Close'].iloc[0]
all_stocks = yf.download(tickers, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
adj_close = all_stocks[['Adj Close']].reset_index()

# Creating dataframe for Adj Close values on end date
adj_close_latest = adj_close[adj_close['Date'] == end_date - datetime.timedelta(days=1)]
adj_close_latest.columns = adj_close_latest.columns.get_level_values(1)
adj_close_latest = adj_close_latest.drop(adj_close_latest.columns[0], axis=1).T
adj_close_latest.rename(columns={(list(adj_close_latest.columns))[0]: "Adj Close Latest"}, inplace=True)
adj_close_latest.index.name = "Ticker"

# Creating dataframe for Adj Close values on start date
adj_close_start = adj_close[adj_close['Date'] == start_date]
adj_close_start.columns = adj_close_start.columns.get_level_values(1)
adj_close_start = adj_close_start.drop(adj_close_start.columns[0], axis=1).T
adj_close_start.rename(columns={(list(adj_close_start.columns))[0]: "Adj Close Start"}, inplace=True)
adj_close_start.index.name = "Ticker"

# Merging dataframes and adding SP500 adj close values
portfolio_df.set_index(['Ticker'], inplace=True)
merged_portfolio_part = pd.merge(portfolio_df, adj_close_start, left_index=True, right_index=True)
merged_portfolio = pd.merge(merged_portfolio_part, adj_close_latest, left_index=True, right_index=True)
merged_portfolio["SP 500 start Adj Close"] = sp500_start_adj_close
merged_portfolio["SP 500 end Adj Close"] = sp500_end_adj_close
merged_portfolio.reset_index(level=0, inplace=True)

# Calculating Returns
merged_portfolio["Ticker Returns"] = merged_portfolio["Adj Close Latest"] / merged_portfolio[
    "Adj Close Start"] - 1
merged_portfolio["SP500 Returns"] = merged_portfolio["SP 500 end Adj Close"] / merged_portfolio[
    "SP 500 start Adj Close"] - 1
merged_portfolio["Weight"] = merged_portfolio["Quantity"] / merged_portfolio["Quantity"].sum()


def Portfolio_vs_SP500_returns():
    ''' produces a bar-line plot comparing the return of
     every ticker to the return of S&P 500.
    '''
    fig, ax = plt.subplots()
    x = merged_portfolio['Ticker']
    y = merged_portfolio['Ticker Returns'] * 100
    y1 = merged_portfolio["SP500 Returns"] * 100
    ax.plot(x, y1, color='c', marker='o')
    ax.bar(x, y)
    ax.set_ylabel('Returns (%)')
    ax.set_xlabel("Ticker")
    ax.set_title("Ticker vs SP 500 Returns")
    ax.legend(["SP 500 Returns", "Ticker Returns"])
    plt.show()


# Finding the cumulative_returns
def cumulative_returns(stock_df, weight_list):
    '''
    consumes, stock_df, a dataframe of ticker data downloaded from yfinance and
    weight_list, a list containing the weights of each ticker in the same order it
    appears in stock_df.
    returns the cumulative_returns of the portfolio of the tickers in stock_df
    '''
    daily_returns = stock_df['Adj Close'].pct_change()[1:]
    weighted_returns = daily_returns * weight_list
    port_ret = weighted_returns.sum(axis=1)
    cumulative_ret = ((port_ret + 1).cumprod() - 1) * 100
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    ax.plot(cumulative_ret)
    ax.set_xlabel('Date')
    plt.xticks(rotation=25)
    ax.set_ylabel("Cumulative Returns (%)")
    ax.set_title("Portfolio Cumulative Returns")
    plt.show()


# Finding correlation
def corr_coeff(df):
    ''' consumes df, a dataframe which contains the tickers and the Adj_Close values
    and produces a heatmap of the correlation between the tickers
    '''
    df.columns = df.columns.get_level_values(1)
    df.rename(columns={(list(df.columns))[0]: "Date"}, inplace=True)
    corr_df = df.corr(method='pearson')
    corr_df.reset_index()
    mask = np.zeros_like(corr_df)
    mask[np.triu_indices_from(mask)] = True
    sns.heatmap(corr_df, cmap='RdYlGn', vmax=1.0, vmin=-1.0, mask=mask, linewidths=2.5)
    plt.yticks(rotation=0)
    plt.xticks(rotation=90)
    plt.show()


cumulative_returns(all_stocks, merged_portfolio["Weight"].tolist())
Portfolio_vs_SP500_returns()
corr_coeff(adj_close)
