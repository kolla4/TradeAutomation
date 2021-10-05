#!/usr/bin/env python3
# A simple script to print all updates received
#
# NOTE: To run this script you MUST have 'TG_API_ID' and 'TG_API_HASH' in
#       your environment variables. This is a good way to use these private
#       values. See https://superuser.com/q/284342.

from os import environ

# environ is used to get API information from environment variables
# You could also use a config file, pass them as arguments,
# or even hardcode them (not recommended)
from telethon import TelegramClient, events, utils
import re
import sys
import json
import OrderExecution
import FyersRequest

from fyers_api import fyersModel
from fyers_api import accessToken
import requests

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC

################    FYERS CREDENTIALS ##########################

#access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE2MzMzNzk0OTEsImV4cCI6MTYzMzM5MzgzMSwibmJmIjoxNjMzMzc5NDkxLCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCaFcyU2pZQ242bEQ0bkxaQTBhM0xwNmNsbXkwTDdOaG83WFF4eTB5YWRwZnFjd1NFVGRoR0dGRG1CU3ZuZDBFMC1JX1otdGxZOWUwVmN1MVRMSE9HX0hQbl9BVmtLU25vNGlJSEVpZjVSVDFkSFFjcz0iLCJkaXNwbGF5X25hbWUiOiJSQUhVTCBWQVJNQSIsImZ5X2lkIjoiWFIxMTYwMiIsImFwcFR5cGUiOjEwMCwicG9hX2ZsYWciOiJOIn0.Hw6AI21hmxNA57_1xonAQZ8llKrTmm1fMfMqmH4WMx8'

client_id = '9BPNFGJHZ5-100'
secret_key = 'LJCTDO2WQY'
redirect_url = 'https://tradepop.com/TradeDhar/api-login'


api_id = 8289565
api_hash = '7e958c4c4ea8f0cea7485196733ca4ad'

phone = '+919003199379'
username = '1273828837'

BANK_NIFTY = 'BankNifty'
NIFTY = 'Nifty'
Put = 'PE'
Call = 'CE'
Buy = 'Buy'
Sell = 'Sell'

stockType = ''
optionType = ''
transactionType = ''
suggestedEntryPrice = 0
currentTrades = {}

tradeSignalGroupName = 'Support Signals (Platinum Batch 5)'
tradeStatusGroupName = 'Dharamik Signals Live'

messageFilter = ['Buy', 'Target']
stockFilter = ['BankNifty', 'Nifty', '#BankNifty', '#Nifty']
stopLossKeyWords = ['stoploss','sl','risk']

weeklyExpiryMonth = {"JAN": "1", "FEB": "2", "MAR": "3", "APR": "4", "MAY": "5", "JUN": "6", "JUL": "7", "AUG": "8", "SEP": "9", "OCT": "O", "NOV": "N", "DEC": "D"}

def main():
    # session_name = environ.get('TG_SESSION', 'session')
    client = TelegramClient(username, api_id, api_hash)

    fyers_app_id = "9BPNFGJHZ5-100"

    access_token = request_auth()
    
    fyers = fyersModel.FyersModel(client_id=fyers_app_id, token=access_token)
    
    @client.on(events.NewMessage)
    async def my_handler(event):
        newMessage = event.message.message

        chat_from = event.chat if event.chat else (await event.get_chat()) # telegram MAY not send the chat enity

        chat_title = chat_from.title

        stoploss = 0
        orderExecutedSuccessfully = False

        if(chat_from.title == tradeSignalGroupName):
    
            # print('This is Event.Message Object ----------------------------\n \n')
            # print(event.message)

            isTradeMessage = filtermessage(newMessage)

            if isTradeMessage :
                
                print("Fuck Yeah, this is a trade signal")

                orderRequest = await processTradeSignalMessage(newMessage)

                tradeStatusUpdateMessage = newMessage + '\n \n' + 'Signal Details: ' + '\n \n '

                signalDetails = orderRequest.stock_name + " , " + orderRequest.transaction_type + " , Signal Entry Price - " + str(orderRequest.executedPrice) + " , SL - " + str(orderRequest.stop_loss) + ' Order Type - ' + orderRequest.order_type



                await sendMessagetoTelegram(tradeStatusUpdateMessage + signalDetails)

                #------- Sending order to Fyers

                fyersRequest = MapOrderToFyersRequest(orderRequest)

                fyersdatarequest = fyersRequest.toJSON()

                print(fyersdatarequest)

                orderresponse = fyers.place_order(fyersdatarequest)
                print(orderresponse)

                if('error'.lower() in orderresponse.get('s')):
                    print('error_code + ' + str(orderresponse.get('code')))
                    print('error_msg ' + orderresponse.get('message'))

                else:
                    print('order placed successfully')
                
                

                orderExecutedSuccessfully = True

                #---- If the order executed successfully
                currentTrades[orderRequest.stock_name] = orderRequest

                printCurrentTrades()
                #if(orderExecutedSuccessfully):
                    #--- Send stoploss order to Zerodha
            else :
                if(len(currentTrades) > 0):
                    currentMessage = event.message.message

                    print('\n')
                    print('-----------------------------------------------------------------------------------')
                    print('\n')
                    print('\n')
                    print('Current Message:')
                    print(currentMessage)

                    previousmessage = ''
                    if(event.message.reply_to):
                        previous_msg_id = event.message.reply_to.reply_to_msg_id

                        tradeSignalGroupEntity = await client.get_entity(tradeSignalGroupName)

                        previousMessageObj = await client.get_messages(tradeSignalGroupEntity, ids= previous_msg_id)

                        previousmessage = previousMessageObj.message
                        
                        print('\n')
                        # print('Replied to Message:')
                        # print(previousmessage)

                        if(filtermessage(previousmessage)):
                            if(containsStopLoss(currentMessage) & len(currentTrades)> 0):
                                await UpdateStopLoss(currentMessage, previousmessage)

                    else:
                        if(containsStopLoss(currentMessage) & len(currentTrades)> 0):
                            await UpdateStopLoss(currentMessage, previousmessage)


    
    async def ExtractOrderInfo(message):
        order = await processTradeSignalMessage(message)
        return order
        
    def EvaluateStopLossPrice(stoploss, currentTrade):
        tradeEntryPrice = currentTrade.executedPrice

        if(stoploss < 0.3 * tradeEntryPrice):
            stoploss = tradeEntryPrice - stoploss
        
        return stoploss

    async def UpdateStopLoss(currentMessage, previousmessage = ''):
        initialStoploss = 0
        stoploss = 0
        if(previousmessage != ''):

            stockName = ''
            order = await ExtractOrderInfo(previousmessage)
            stockName = order.stock_name

            currentTrade = currentTrades[stockName]
            initialStoploss = currentTrade.stop_loss

            if(currentTrade):
                stoplossPrices = re.findall(r'[0-9]+', currentMessage)

                if(len(stoplossPrices) > 0):
                    stoploss = int(stoplossPrices[0])
                    stoploss = EvaluateStopLossPrice(stoploss, currentTrade)
                elif (currentMessage.lower().find('CTC'.lower()) != -1 or currentMessage.find('Cost to Cost'.lower()) != -1):
                    stoploss = order.executedPrice
                else:
                    stoploss = initialStoploss

                currentTrade.stop_loss = stoploss
        
        else:
            if(len(currentTrades) > 1):
                printCurrentTrades()
                return
            else:
                key = list(currentTrades.keys())[0]
                currentTrade = currentTrades[key]
                stoplossPrices = re.findall(r'[0-9]+', currentMessage)
                initialStoploss = currentTrade.stop_loss

                if(len(stoplossPrices) > 0):
                    stoploss = int(stoplossPrices[0])
                    stoploss = EvaluateStopLossPrice(stoploss, currentTrade)
                elif (currentMessage.lower().find('CTC'.lower()) != -1 or currentMessage.find('Cost to Cost'.lower()) != -1):
                    stoploss = currentTrade.executedPrice
                else:
                    stoploss = initialStoploss

                currentTrade.stop_loss = stoploss
                await sendMessagetoTelegram('StopLoss Modified from ' + str(initialStoploss) + ' to ' + str(stoploss) + 'for ' + currentTrade.stock_name)
        

        if(currentTrade):
            currentTrade.stop_loss = stoploss

        printCurrentTrades()


        # --- Send modify order for SL

    def containsStopLoss(currentMessage):
        for stoplossPhrase in stopLossKeyWords:
                if(currentMessage.lower().find(stoplossPhrase) != -1):
                    return True
        return False

    def printCurrentTrades():
        print('Currently running Trades are: ')
        for order in currentTrades:
                trade = currentTrades[order]
                print(trade.stock_name + "  ,  " + trade.transaction_type + " ,  SL - " + str(trade.stop_loss) + "  , Executed Price - " + str(trade.executedPrice) + " , Target Price - " + str(trade.target_price))

    
    def getStoploss(tradeSignalMessage):
        stoploss = 0
        trademessageLines = tradeSignalMessage.splitlines()
        
        stoplossline = ''
        for line in trademessageLines:
            if(containsStopLoss(line)):
                stoplossline = line
        
        stoplossPrices = re.findall(r'[0-9]+', stoplossline)
        
        if(len(stoplossPrices) > 0):
            stoploss = int(stoplossPrices[0])
        
        return stoploss

    async def sendMessagetoTelegram(tradeStatusUpdateMessage):

        await client.get_dialogs()

        tradeStatusGroupEntity= await client.get_entity(tradeStatusGroupName)

        await client.send_message(entity=tradeStatusGroupEntity,message=tradeStatusUpdateMessage)

    # --------------------- This is to filter only the trade signal messages --------------------------
    def filtermessage(message):
        isTradeMessage = True
        isDesiredStock = False

        for filter in messageFilter:
            if message.lower().find(filter.lower()) == -1:
                isTradeMessage = False
        
        for filter in stockFilter:
            if message.lower().find(filter.lower()) != -1:
                isDesiredStock = True

        return isTradeMessage & isDesiredStock

    # --------------------- Processing the message to extract the key attributes to be sent to the trading broker ---------
    async def processTradeSignalMessage(trademessage):
        orderType_market = 'MarketOrder'
        orderType_limit = 'LimitOrder'
        stoploss = 0
        suggestedEntryPrice = 0        
        orderType = orderType_market

        if trademessage.find(BANK_NIFTY) != -1:
            stockType = BANK_NIFTY
        elif trademessage.find(NIFTY) != -1:
            stockType = NIFTY

        if trademessage.find(Buy) != -1:
            transactionType = Buy
        else :
            transactionType = Sell
        
        splitstrings = trademessage.split()
        
        #suggestedEntryPrice = int(re.search(r'\d+', re.search('Buy At (.*) For', trademessage).group(1)).group())

        print(trademessage)
        
        if(trademessage.lower().find(('Buy Above').lower()) > -1):
            orderType = orderType_limit

        print(orderType)
        try:
            suggestedEntryPrice = int(re.search(r'\d+', re.search('Buy (.*) For', trademessage).group(1)).group())
        except:
            print("This trade signal doesn't have entry price - it might be an opening trade")

        stockSymbol = ''
        stockName = ''
        if((len(splitstrings[1]) >= 3) and (len(splitstrings[2]) <= 3)):
            #---- Weekly Expiry
            date = splitstrings[1]
            month = weeklyExpiryMonth.get(splitstrings[2].upper())
            optionStrikePrice = splitstrings[3]
            optionType = splitstrings[4]
            
            if(len(date) < 2):
                date = '0' + date
            stockName = date + " " + splitstrings[2].upper() + " " + optionStrikePrice + " " + optionType.upper()
            stockSymbol = stockType.upper() + '21' + month + date.rstrip(date[-2:]) + optionStrikePrice + optionType.upper()

            #print(stockSymbol)
        else:
            #---- Monthly Expiry
            month = splitstrings[1]
            optionStrikePrice = splitstrings[2]
            optionType = splitstrings[3]
            
            stockName = month.upper() + " " + optionStrikePrice + " " + optionType.upper()
            stockSymbol = stockType.upper() + '21' + month.upper() + optionStrikePrice + optionType.upper()
            #print(stockSymbol)

        
        tradeSignal = stockSymbol + ' - ' + transactionType + ' - ' + str(suggestedEntryPrice)
        # print(stockName, optionType, transactionType, suggestedEntryPrice)
        print(tradeSignal)

        stoploss = getStoploss(trademessage)
        

        if(stoploss == 0):
            stoploss = suggestedEntryPrice - 50

        orderRequest = OrderExecution.OrderExecutionRequest(stockName, stockSymbol, transactionType, stoploss, suggestedEntryPrice, orderType)

        stoploss = EvaluateStopLossPrice(stoploss, orderRequest)
        orderRequest.stop_loss = stoploss

        return orderRequest
        

    client.start(phone)

    # client.add_event_handler(update_handler)

    print('(Press Ctrl+C to stop this)')

    client.run_until_disconnected()

# def update_handler(update):
#     print(update)

def request_auth():

    options = Options()
    options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    driver = webdriver.Chrome(executable_path=r"C:\chromedriver_win32\chromedriver.exe", chrome_options = options)

    # Authentication
    app_id = "9BPNFGJHZ5-100"
    app_secret = "LJCTDO2WQY"
    session=accessToken.SessionModel(client_id=app_id, secret_key=app_secret, redirect_uri=redirect_url, response_type='code', grant_type='authorization_code')
    #app_session = accessToken.SessionModel(app_id, app_secret)
    #response = app_session.auth()
    response = session.generate_authcode()
    print('Generate AuthCode response - ' + response)



    # Getting authorized code into a variable
    #authorization_code = response['data']['authorization_code']

    # Setting a Session
    #print(app_session.set_token(authorization_code))

    #access_token_url = app_session.generate_token()

    # Opening Url through Selenium
    driver.get(str(response))

    usn = driver.find_element_by_id('fyers_id')
    usn.send_keys('XR11602')
    time.sleep(2)

    pwd = driver.find_element_by_id('password')
    pwd.send_keys('Hubble2426!')
    time.sleep(2)

    driver.find_element_by_class_name('login-span-pan').click()
    time.sleep(2)

    pan = driver.find_element_by_id('pancard')
    pan.send_keys('AQCPV3101H')
    time.sleep(2)

    driver.find_element_by_id('btn_id').click()


    WebDriverWait(driver,20).until(EC.title_contains('tradepop'))
    # getting access token from browser
    
    authcode = driver.current_url.split('=', 3)[3].split('&', 1)[0]

    session.set_token(authcode)
    response = session.generate_token()
    access_token = response["access_token"]
 

   # Quiting the browser
    driver.quit()

    return access_token

def MapOrderToFyersRequest(orderRequest):
        qty = 25
        side = 1
        marketType = 2
        limitPrice = 0

        if(orderRequest.order_type.lower() == 'Market Order'.lower()):
            marketType = 2
        elif(orderRequest.order_type.lower() == 'LimitOrder'.lower()):
            marketType = 1
        
        if(orderRequest.transaction_type.lower() == 'Buy'.lower()):
            side = 1
        else:
            side = -1

        if(marketType == 1):
            limitPrice = orderRequest.executedPrice
                

        return FyersRequest.FyersRequestModel(orderRequest.stock_symbol, qty, marketType, side, 'INTRADAY', limitPrice, offlineOrder=False, stopLoss= orderRequest.stop_loss, takeProfit=orderRequest.target_price)

if __name__ == '__main__':
    userDetails = ''
    groupType = ''
    if(len(sys.argv) >= 2):
        userDetails = sys.argv[1]
        if(userDetails.lower() == 'rahul'):
            api_id = 8289565
            api_hash = '7e958c4c4ea8f0cea7485196733ca4ad'
            phone = '+919003199379'
            username = '1273828837'
        elif(userDetails.lower() == 'srikanth'):
            api_id = 8648499
            api_hash = 'b635f9d93e1d51a1119029e7a392a483'
            phone = '+919790913870'
            username = '1568072049'
    if(len(sys.argv) >= 3):
        groupType = sys.argv[2]
        if (groupType.lower() == 'test'):
            tradeSignalGroupName = 'Trade Signal Mocker'
            tradeStatusGroupName = "Dharamik Signals Test"

    main()