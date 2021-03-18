# https://github.com/PietYsabie/Python-Stock-Options-Loader.git
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 2 2021
@author: Piet Ysabie
"""
# _____________________________________________________________________________________
# Load table option_table1 with stock options using finance.yahoo.com as a data source
# -------------------------------------------------------------------------------------
# make sure the table has been created using this create statement:
#CREATE TABLE `option_table1` (
#  `index_option` int NOT NULL AUTO_INCREMENT,
#  `tick` varchar(10) NOT NULL,
#  `ATREQ_date` date DEFAULT NULL,
#  `ATREQ_stockprice_fromchain` decimal(10,3) DEFAULT NULL,
#  `ATREQ_bid` decimal(10,3) DEFAULT NULL,
#  `ATREQ_ask` decimal(10,3) DEFAULT NULL,
#  `ATREQ_optLastPrice` decimal(10,3) DEFAULT NULL,
#  `ATREQ_LastTradeDate` date DEFAULT NULL,
#  `ATREQ_openint` int DEFAULT NULL,
#  `ATREQ_vol` int DEFAULT NULL,
#  `strike` decimal(10,3) DEFAULT NULL,
#  `callput` varchar(1) DEFAULT NULL,
#  `expdate` date DEFAULT NULL,
#  PRIMARY KEY (`index_option`)
#  ) ENGINE=InnoDB AUTO_INCREMENT=76741 DEFAULT CHARSET=latin1;

# The ATREQ fields (AT the time of REQuesting the option quotation) are filled with one quotation per ticker, strike (expiration) date and strike value
# Note that the yahoo service has been changed and can be altered in the future, eg see https://www.elitetrader.com/et/threads/yahoo-option-chain-web-page-changed.301166/page-2
# Data is not always clean, therefore we check multiple times for empty records in the yahoo data response

import mysql.connector
import pymysql
import pymysql.cursors
import pdb
import datetime
import time
import pytz
import json
import requests
import calendar
import matplotlib.pyplot as plt

# Set-up the connection to the database
conn = pymysql.connect(host = '127.0.0.1', user='option_loader', password = '____', db = 'invest', cursorclass = pymysql.cursors.DictCursor)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# Initialise the date & time so that we can store in the records; quotes should be timestamped, the query timestamp is important for future tracking
date_now = datetime.date.today()
datetime_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# Loop for both calls and puts
optiontypes = ['calls','puts']

# Get option quotes for these tickers; alternatively, select the list from another table or data source
#ticklist = [{'tick': 'MSFT'}, {'tick': 'AAPL'}]
ticklist = [{'tick': 'AERI'}]

#cursor.execute('delete from option_table1')   # --> un-comment this to clear the table first; otherwise additional records are simply inserted

# Loop through all ticker symbols, get the option quotations for each symbol
for mytick in ticklist:

    symbol = mytick['tick']
    print(symbol)

    #Get the expirationdates, using these yahoo services:
    #https://query1.finance.yahoo.com/v7/finance/options/AAPL                   gives all expirations for Options on AAPL
    #https://query2.finance.yahoo.com/v7/finance/options/AAPL?date=1537488000   gives all expirations for one single strike date for Options on AAPL
    #https://finance.yahoo.com/quote/AAPL/key-statistics?p=AAPL                 gives key fundamentals as a web page, and also in JSON format-->
    #https://query2.finance.yahoo.com/v10/finance/quoteSummary/AAPL?formatted=true&lang=en-US&region=US&modules=defaultKeyStatistics%2CfinancialData%2CcalendarEvents&corsDomain=finance.yahoo.com
    url='https://query2.finance.yahoo.com/v7/finance/options/' + symbol
    response = requests.get(url)
    # Load the raw json data into a python data object
    data = response.json()

    # Avoid loading empty data
    if len(data['optionChain']['result']) == 0:
        print('No options for: ' + symbol)
        break  #to exit a loop use break or to stop execution without the interpreter use https://stackoverflow.com/questions/28413104/stop-python-script-without-killing-the-python-process


    # Loop through the expiration dates; request the option details iteratively in the loop
    for i in data['optionChain']['result'][0]['expirationDates']:
        
        # The yahoo json response provides dates in UNIX date-time format --> convert where necessary
        print (str(i) + '  ' + datetime.datetime.fromtimestamp(i).strftime('%Y-%m-%d %H:%M:%S'))

        # This is the 'magic' URL that responds with all option quotations for the given ticker and expiration date
        url_date='https://query2.finance.yahoo.com/v7/finance/options/' + symbol + '?date=' + str(i)
        response_date = requests.get(url_date)
        data_date = response_date.json() #data_date contains all JSON data for one given expiration date
        
        # Avoid loading empty data
        if data_date['optionChain']['result'] == 'null':
            print('EMPTY RETURN for one experation date:  ' + symbol + '  ' + datetime.datetime.fromtimestamp(i).strftime('%Y-%m-%d %H:%M:%S'))
        else:
            #print('index:' + ' ' + str(data_date['optionChain']['result'][0]['options'])) - debug line
            # Now process the response and store it in the database as clean separate records
            # Loop first through all calls then through all puts
            for callputloop in optiontypes:
                # Loop through each of the strike values for the given expiration date
                x = []
                y = []

                # First avoid empty strike records
                if len(data_date['optionChain']['result'][0]['options'][0][callputloop]) == 0:
                    print('EMPTY RETURN ' + symbol + str(i) + ' ' + datetime.datetime.fromtimestamp(i).strftime('%Y-%m-%d %H:%M:%S')
                          + 'strike: ' + str(mystrike['strike']) + ' C/P: ' + callputloop[0])
                    break
                for mystrike in data_date['optionChain']['result'][0]['options'][0][callputloop]:
                    myexpir_date = (datetime.datetime.fromtimestamp(mystrike['expiration'])).date()
                    #print(mystrike['strike'],mystrike['lastTradeDate']) - debug line
                    if mystrike['lastTradeDate'] > 0:
                        mylastTradeDate = (datetime.datetime.fromtimestamp(mystrike['lastTradeDate'])).date()
                        # Now we do the actual insert of the option quotation, together with all available details
                        cursor.execute(""" INSERT INTO option_table1
                        (tick, ATREQ_date,
                        ATREQ_stockprice_fromchain,
                        strike, ATREQ_ask,ATREQ_bid, expdate,callput,
                        ATREQ_optLastPrice,ATREQ_LastTradeDate,ATREQ_openint)
                        VALUES ( %s,%s,
                        %s,
                        %s,%s,%s,%s,%s,
                        %s,%s,%s )
                        """,
                       (symbol,date_now,
                        round(data_date['optionChain']['result'][0]['quote']['regularMarketPrice'],3),
                        mystrike['strike'],mystrike['ask'],mystrike['bid'],myexpir_date,callputloop[0],
                        mystrike['lastPrice'],mylastTradeDate,mystrike['openInterest']))

                        x.append([mystrike['strike']])  
                        y.append([mystrike['ask']])

                # Plot the Option chain for the given ticker, expiration date and option type
                plt.plot(x, y) 
                plt.xlabel('Strike') 
                plt.ylabel('Ask Price') 
                plt.title('Option Chain for '+symbol+ ' ' + str(myexpir_date)+ ' ' + callputloop[0]) 
                plt.show() 

            # Commit the insert for each (symbol,expiration date) combo
            conn.commit()

# Close the database connection
cursor.close()
conn.close()
