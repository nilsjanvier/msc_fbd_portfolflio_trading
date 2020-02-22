#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import decimal
import hmac
from datetime import datetime
import numpy as np
from pandas_datareader import data as pdr
import bs4 as bs
import os 


class Data:

    def __init__(self):

        self.base = 'https://finance.yahoo.com/'
        self.endpoints = {
            "klines": '/api/v3/klines',
            "cryptocurrencies": '/cryptocurrencies',
        }
        self.startdate = datetime(2000, 1, 1)
        self.enddate = datetime.today()
        self.path = os.getcwd() + '/'
        self.rsi_period = 14

    def getSymbols(self):

        url = self.base + self.endpoints["cryptocurrencies"]

        resp = requests.get(url)
        soup = bs.BeautifulSoup(resp.text, 'lxml')
        table = soup.find('table', {'class': 'W(100%)'})  # find table in this page
        tickers = []  # save tickers column here

        for row in table.findAll('tr')[1:]:  # each row is identified by header('tr') in html code
            ticker = row.findAll('td')[0].text  # find the first cell and extract from the text
            tickers.append(ticker)

        return tickers
    
    def getData(self, tickers):
        
        return pdr.get_data_yahoo(tickers, self.startdate, self.enddate).reset_index().drop(columns= {'Adj Close'})
    
    def computeIndicators(self, df):
    
        #get moving average
        df['20_sma'] = df['Close'].rolling(20).mean()
        df['50_sma'] = df['Close'].rolling(50).mean()
        df['200_sma'] = df['Close'].rolling(200).mean()

        #get bollinger bands
        df['low_boll'] =  df['50_sma'] - 1 * np.std(df['200_sma'])
        df['high_boll'] = df['50_sma'] + 1 * np.std(df['200_sma'])
        
        #get returns
        df['daily_returns'] = df['Close'].pct_change(1)
        df['monthly_returns'] = df['Close'].pct_change(20)
        df['annual_returns'] = df['Close'].pct_change(240)
    
        #Compute RSI
        delta = df['Close'].diff().dropna()
        delta = delta.diff().dropna()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        roll_up = up.rolling(self.rsi_period).mean()
        roll_down = down.abs().rolling(self.rsi_period).mean()
        rs = roll_up / roll_down
        df['rsi'] = 100.0 - (100.0 / (1.0 + rs))
        
        return df
    
    def stratMA(self, df):
        
        df['signal_ma'] = None
        buy_auto = True
        
        for i in range(len(df)):
            
            if (buy_auto == True) & (df['20_sma'].iloc[i] > df['50_sma'].iloc[i]):
                buy_auto = False
                df['signal_ma'].iloc[i] = "buy"
               
            if (buy_auto == False) & (df['20_sma'].iloc[i] < df['50_sma'].iloc[i]):
                buy_auto = True
                df['signal_ma'].iloc[i] = "sell"
                
        return df
    
    def stratBO(self, df):
        
        df['signal_bo'] = None
        buy_auto = True
        
        for i in range(len(df)):
            
            if (buy_auto == True) & (df['low_boll'].iloc[i] > df['Close'].iloc[i]):
                buy_auto = False
                df['signal_bo'].iloc[i] = "buy"
               
            if (buy_auto == False) & ((df['high_boll'].iloc[i] < df['Close'].iloc[i])):
                buy_auto = True
                df['signal_bo'].iloc[i] = "sell"
                
        return df
    
    def stratRSI(self, df):
        
        df['signal_rsi'] = None
        buy_auto = True
        
        for i in range(len(df)):
            
            if (buy_auto == True) & (df['rsi'].iloc[i] < 30):
                buy_auto = False
                df['signal_rsi'].iloc[i] = "buy"
               
            if (buy_auto == False) & (df['rsi'].iloc[i] > 70):
                buy_auto = True
                df['signal_rsi'].iloc[i] = "sell"
                
        return df
    
    def computeStrategies(self, df):
        
        df = self.stratBO(df)
        df = self.stratMA(df)
        df = self.stratRSI(df)
        
        return df
    
    def exportData(self, df, ticker):
        
        df.to_csv(self.path + ticker + '.csv')
    
def Main():
    
    data = Data()
    tickers = data.getSymbols()
    
    #On prend juste les 10 premiers pour le moment 
    for i in range(5):
        
        df = data.getData(tickers[i])
        df = data.computeIndicators(df)
        df = data.computeStrategies(df)
        
        data.exportData(df, tickers[i])
    
    
if __name__ == '__main__':

    Main()




