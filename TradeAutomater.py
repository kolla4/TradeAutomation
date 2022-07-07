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

#tradeSignalGroupName = 'Support Signals (5 Platinum Batch 5)'
tradeSignalGroupName = 'Trade Pops'
tradeStatusGroupName = 'Dharamik Signals Live'

messageFilter = ['Buy', 'Target']
stockFilter = ['BankNifty', 'Nifty', '#BankNifty', '#Nifty']
stopLossKeyWords = ['stoploss','sl','risk']

weeklyExpiryMonth = {"JAN": "1", "FEB": "2", "MAR": "3", "APR": "4", "MAY": "5", "JUN": "6", "JUL": "7", "AUG": "8", "SEP": "9", "OCT": "O", "NOV": "N", "DEC": "D"}

offlineOrder = False

isLiveOrder = input("Aftermarket? (y/n) : ")

if(isLiveOrder.lower().find('y') != -1):
    offlineOrder = True

def main():
    # session_name = environ.get('TG_SESSION', 'session')
    client = TelegramClient(username, api_id, api_hash)

    fyers_app_id = "W4303K7IOY-100"    

    print(offlineOrder)

    access_token = request_auth()
    #access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE2MzM1NjY4MjQsImV4cCI6MTYzMzY1MzA0NCwibmJmIjoxNjMzNTY2ODI0LCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCaFhrQm9ERGJrbThsSjZ2S3dZSFZPODFJUVhQU1d5QzRjR1hrcmpUaC02MUJ0bXN6NUdvLVBNSENEM3RFRzFDT2RSZEl3bTV1R09DbC0tamFtd3ZzQmF0QlJfZFdSVW84ZnBNemtMUFlHR0o0Rm5Faz0iLCJkaXNwbGF5X25hbWUiOiJSQUhVTCBWQVJNQSIsImZ5X2lkIjoiWFIxMTYwMiIsImFwcFR5cGUiOjEwMCwicG9hX2ZsYWciOiJOIn0.-LAGAvCuoSUsvntwDP25Bb4TAOmPPH6iJS67IqusDBk'
    print(access_token)
    
    fyers = fyersModel.FyersModel(client_id=fyers_app_id, token=access_token)
    
    @client.on(events.NewMessage)
    async def my_handler(event):
        newMessage = event.message.message

        chat_from = event.chat if event.chat else (await event.get_chat()) # telegram MAY not send the chat enity

        chat_title = chat_from.title

        stoploss = 0
        orderExecutedSuccessfully = False

        if(chat_from.title == tradeSignalGroupName):

            isTradeMessage = filtermessage(newMessage)

            if isTradeMessage :
                
                print("Fuck Yeah, this is a trade signal")

                orderRequest = await processTradeSignalMessage(newMessage)

                tradeStatusUpdateMessage = newMessage + '\n \n' + 'Signal Details: ' + '\n \n '

                signalDetails = orderRequest.stock_name + " , " + orderRequest.transaction_type + " , Signal Entry Price - " + str(orderRequest.executedPrice) + " , SL - " + str(orderRequest.stop_loss) + ' Order Type - ' + orderRequest.order_type



                await sendMessagetoTelegram(tradeStatusUpdateMessage + signalDetails)

                #------- Sending order to Fyers

                #orderRequest.stock_symbol = 'NSE:SBIN-EQ'


                if(offlineOrder == False):

                    request = OrderToJsonFyersRequest(orderRequest, 'INTRADAY', 1)
                    

                    orderresponse = fyers.place_order(request)
                    print(orderresponse)


                    if('error'.lower() in orderresponse.get('s')):
                        print('error_code + ' + str(orderresponse.get('code')))
                        print('error_msg ' + orderresponse.get('message'))
                        ErrorMessage = 'error_code is :' + str(orderresponse.get('code')) + '   and   ' + 'error message is : ' + orderresponse.get('message')
                        await sendMessagetoTelegram(ErrorMessage)

                    else:
                        print('order placed successfully')
                        try:
                            orderId = orderresponse.get('id')
                            orderExecutedSuccessfully = True
                            orderRequest.order_id = orderId
                            currentTrades[orderRequest.stock_name] = orderRequest
                        except:
                            orderExecutedSuccessfully = False
                    

                    #---- If the order executed successfully
                    if(orderExecutedSuccessfully):

                        await sendMessagetoTelegram('Order Id ' + str(orderId) +  ' placed successfully for ' + orderRequest.stock_name)

                        stoplossOrder = OrderExecution.OrderExecutionRequest(orderRequest.stock_name, orderRequest.stock_symbol, transactionType, 0, orderRequest.stop_loss, 'StopLossLimitOrder')
                        stoplossFyersRequest = OrderToJsonFyersRequest(stoplossOrder, 'INTRADAY', -1)

                        stoplossorderresponse = fyers.place_order(stoplossFyersRequest)
                        print('StopLoss order Response: ')
                        print(stoplossorderresponse)

                        if('error'.lower() in stoplossorderresponse.get('s')):
                            print('error_code + ' + str(stoplossorderresponse.get('code')))
                            print('error_msg ' + stoplossorderresponse.get('message'))
                            ErrorMessage = 'error_code is :' + str(stoplossorderresponse.get('code')) + '   and   ' + 'error message is : ' + stoplossorderresponse.get('message')
                            await sendMessagetoTelegram("StopLoss Order Creation Error \n" + ErrorMessage)

                        else:
                            print('order placed successfully')
                            try:
                                orderId = stoplossorderresponse.get('id')
                                orderExecutedSuccessfully = True
                                orderRequest.order_id = orderId
                                currentTrades[orderRequest.stock_name] = orderRequest
                            except:
                                orderExecutedSuccessfully = False




                
                else:

                    firstorderSuccess = False

                    #print(offlineOrder)
                    print('First Request:')
                    request = OrderToJsonFyersRequest(orderRequest, 'INTRADAY', 1)
                    
                    #print(request)

                    firstorderresponse = fyers.place_order(request)
                    print(firstorderresponse)

                    if('error'.lower() in firstorderresponse.get('s')):
                        print('error_code + ' + str(firstorderresponse.get('code')))
                        print('error_msg ' + firstorderresponse.get('message'))
                        ErrorMessage = 'error_code is :' + str(firstorderresponse.get('code')) + '   and   ' + 'error message is : ' + firstorderresponse.get('message')
                        await sendMessagetoTelegram(ErrorMessage)

                    else:
                        print('order placed successfully')
                        try:
                            orderId = firstorderresponse.get('id')
                            firstorderSuccess = True
                            orderRequest.order_id = orderId
                            currentTrades[orderRequest.stock_name] = orderRequest
                        except:
                            firstorderSuccess = False

                        if(firstorderSuccess):
                            await sendMessagetoTelegram('Order Id ' + str(orderId) +  ' placed successfully for ' + orderRequest.stock_name)

                    if(firstorderSuccess):

                        secondordersuccess = False
                        SLPrice = orderRequest.stop_loss

                        print('Second Request:')
                        secondorderRequest = OrderExecution.OrderExecutionRequest(orderRequest.stock_name, orderRequest.stock_symbol, transactionType, 0, SLPrice, 'LimitOrder')
                        secondOrderFyersRequest = OrderToJsonFyersRequest(secondorderRequest, 'INTRADAY', -1)

                        
                        #print(secondOrderFyersRequest)

                        secondorderresponse = fyers.place_order(secondOrderFyersRequest)
                        if('error'.lower() in secondorderresponse.get('s')):
                            print('error_code + ' + str(secondorderresponse.get('code')))
                            print('error_msg ' + secondorderresponse.get('message'))
                            ErrorMessage = 'error_code is :' + str(secondorderresponse.get('code')) + '   and   ' + 'error message is : ' + secondorderresponse.get('message')
                            await sendMessagetoTelegram(ErrorMessage)

                        else:
                            print('order placed successfully')
                            print(secondorderresponse)
                            try:
                                orderId = secondorderresponse.get('id')
                                secondordersuccess = True
                                orderRequest.order_id = orderId
                                currentTrades[orderRequest.stock_name] = orderRequest
                            except:
                                secondordersuccess = False

                            if(secondordersuccess):
                                await sendMessagetoTelegram('Order Id ' + str(orderId) +  ' placed successfully for ' + secondorderRequest.stock_name)



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
                        print('Replied to Message:')
                        print(previousmessage)

                        print(filtermessage(previousmessage))
                        print(containsStopLoss(currentMessage))

                        if(filtermessage(previousmessage) and len(currentTrades) > 0):
                            await UpdateStopLoss(currentTrades, currentMessage, previousmessage)

                    else:
                        if(len(currentTrades) == 1):
                            await UpdateStopLoss(currentTrades, currentMessage, previousmessage)

    
    async def ExtractOrderInfo(message):
        order = await processTradeSignalMessage(message)
        return order
        
    def EvaluateStopLossPrice(stoploss, currentTrade):
        tradeEntryPrice = currentTrade.executedPrice

        if(stoploss < 0.3 * tradeEntryPrice):
            stoploss = tradeEntryPrice - stoploss
        
        return stoploss

    async def UpdateStopLoss(currentTrades, currentMessage, previousmessage = ''):
        print('In Update Stoploss Method')
        initialStoploss = 0
        stoploss = 0
        
        try:
            if(previousmessage != ''):

                stockName = ''
                order = await ExtractOrderInfo(previousmessage)
                stockName = order.stock_name

                currentTrade = currentTrades[stockName]
            
            else:
                key = list(currentTrades.keys())[0]
                currentTrade = currentTrades[key]
        except:
            print('Unable to retrieve current trade')


        if (currentTrade and (currentMessage.lower().find('CTC'.lower()) != -1 or currentMessage.find('Cost'.lower()) != -1)):
                stoploss = currentTrade.executedPrice
        elif(currentTrade and containsStopLoss(currentMessage)):

            stoplossPrices = re.findall(r'[0-9]+', currentMessage)
            
            if(len(stoplossPrices) > 1):
                stoploss = int(stoplossPrices[1])
                stoploss = EvaluateStopLossPrice(stoploss, currentTrade)
            elif(len(stoplossPrices) > 0):
                stoploss = int(stoplossPrices[0])
                stoploss = EvaluateStopLossPrice(stoploss, currentTrade)

        currentTrade.stop_loss = stoploss

        await sendUpdateStoplosstoFyers(currentTrade)

        printCurrentTrades()


        # --- Send modify order for SL

    async def sendUpdateStoplosstoFyers(currentTrade):
        stoplossOrderSuccess = False
        cancelData = {"id":currentTrade.order_id}
        cancelOrderResponse = fyers.cancel_order(cancelData)

        if('error'.lower() in cancelOrderResponse.get('s')):
            print('error_code + ' + str(cancelOrderResponse.get('code')))
            print('error_msg ' + cancelOrderResponse.get('message'))
            ErrorMessage = 'Cancel Order before Updating Stoploss failed \n Response error_code is :' + str(cancelOrderResponse.get('code')) + '   and   ' + 'error message is : ' + cancelOrderResponse.get('message')
            await sendMessagetoTelegram(ErrorMessage)

        else:
            print('Existing Stoploss order cancelled successfully')
            newStoplossRequest =  {
                    "symbol": currentTrade.stock_symbol,
                    "qty":25,
                    "type":4,
                    "side":-1,
                    "productType":'INTRADAY',
                    "limitPrice":currentTrade.stop_loss - 2,
                    "stopPrice":currentTrade.stop_loss,
                    "validity":"DAY",
                    "disclosedQty":0,
                    "offlineOrder":offlineOrder,
                    "stopLoss":0,
                    "takeProfit":0
                }

            newStoplossResponse = fyers.place_order(newStoplossRequest)
            

            if('error'.lower() in newStoplossResponse.get('s')):
                print('error_code + ' + str(newStoplossResponse.get('code')))
                print('error_msg ' + newStoplossResponse.get('message'))
                ErrorMessage = 'Creating new Stoploss order failed \n error_code is :' + str(newStoplossResponse.get('code')) + '   and   ' + 'error message is : ' + newStoplossResponse.get('message')
                await sendMessagetoTelegram(ErrorMessage)

            else:
                print('StopLoss order placed successfully')
                try:
                    orderId = newStoplossResponse.get('id')
                    stoplossOrderSuccess = True
                    currentTrade.order_id = orderId
                    
                except:
                    stoplossOrderSuccess = False

                if(stoplossOrderSuccess):
                    await sendMessagetoTelegram('StopLoss Updated to ' + str(currentTrade.stop_loss) +  ' for ' +currentTrade.stock_name + '\n Order Id:' + str(orderId))


    # async def ProcessFyersModificationResponse(orderresponse, stockName, stoploss):
    #     modificationresponse = 'Modification Response -- ' + orderresponse.get('message')
    #     if('error'.lower() in orderresponse.get('s')):
    #         print('error_code + ' + str(orderresponse.get('code')))
    #         print('error_msg ' + orderresponse.get('message'))
    #         ErrorMessage = 'error_code is :' + str(orderresponse.get('code')) + '   and   ' + 'error message is : ' + orderresponse.get('message')
    #         await sendMessagetoTelegram("Update StopLoss to " + str(stoploss) + "  for " + stockName + "\n Error  : " + ErrorMessage)

    #     else:
    #         print('order modified successfully')
    #         try:
    #             orderId = orderresponse.get('id')
    #             currentTrade.order_id = orderId
    #             currentTrades[orderRequest.stock_name] = orderRequest

    #             print('StopLoss Modified successfully')
    #             await sendMessagetoTelegram(modificationresponse + "\n StopLoss Modified successfully")
    #             #await sendMessagetoTelegram('StopLoss Modified from ' + str(initialStoploss) + ' to ' + str(stoploss) + 'for ' + currentTrade.stock_name)
    #         except:
    #             orderExecutedSuccessfully = False

    def containsStopLoss(currentMessage):
        for stoplossPhrase in stopLossKeyWords:
                if(currentMessage.lower().find(stoplossPhrase) != -1):
                    return True
        return False

    def printCurrentTrades():
        print('Currently running Trades are: ')
        for order in currentTrades:
                trade = currentTrades[order]
                print(trade.stock_name + "  ,  " + trade.transaction_type + " ,  SL - " + str(trade.stop_loss) + "  , Executed Price - " + str(trade.executedPrice) + " , Target Price - " + str(trade.target_price) + " OrderId  -" + trade.order_id)

    
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
        orderType_buyAbove = 'StopLossMarketOrder'
        stoploss = 0
        suggestedEntryPrice = 0
        targetPrice = 0        
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
            orderType = orderType_buyAbove

        print(orderType)
        try:
            suggestedEntryPrice = int(re.search(r'\d+', re.search('Buy (.*) For', trademessage).group(1)).group())
        except:
            print("This trade signal doesn't have entry price - it might be an opening trade")

        try:
            prices = re.findall(r'[0-9]+', trademessage.split("Buy", 1)[1])
            targetPrice = prices[1]
            print(targetPrice)
        except:
            targetPrice = suggestedEntryPrice + 100
            print(targetPrice)



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
            stoploss = int(suggestedEntryPrice * 0.8)

        orderRequest = OrderExecution.OrderExecutionRequest(stockName, "NSE:"+stockSymbol, transactionType, stoploss, suggestedEntryPrice, orderType, targetPrice)

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
    options.binary_location = r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    driver = webdriver.Chrome(executable_path=r"C:\chromedriver_win32\chromedriver.exe", chrome_options = options)

    # Authentication
    app_id = "W4303K7IOY-100"
    app_secret = "8XA2P24NMO"
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

    usn = driver.find_element_by_id('fy_client_id')
    usn.send_keys('XS26273')
    time.sleep(3)

    driver.find_element_by_id('clientIdSubmit').click()
    time.sleep(3)

    pwd = driver.find_element_by_id('fy_client_pwd')
    pwd.send_keys('RaviSri#1216')
    time.sleep(3)

    driver.find_element_by_id('loginSubmit').click()
    time.sleep(3)

    # Entering 4 digit pin

    pinContainer = driver.find_element_by_class_name('pin-container')

    first = pinContainer.find_element_by_id('first')
    first.send_keys('2')

    second = pinContainer.find_element_by_id('second')
    second.send_keys('7')

    third = pinContainer.find_element_by_id('third')
    third.send_keys('0')

    fourth = pinContainer.find_element_by_id('fourth')
    fourth.send_keys('2')

    time.sleep(3)

    driver.find_element_by_id('verifyPinSubmit').click()


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
                
        correctStockSymbol = orderRequest.stock_symbol
        #return FyersRequest.FyersRequestModel(correctStockSymbol, qty, marketType, side, 'INTRADAY', limitPrice, offlineOrder=False, stopLoss= orderRequest.stop_loss, takeProfit=orderRequest.target_price)
        return FyersRequest.FyersRequestModel(correctStockSymbol, qty, marketType, side, 'INTRADAY', limitPrice, offlineOrder)


def ModifyOrderToJsonFyersRequest(orderId, stoploss = 0, limitPrice = 0, qty = 25):
        modifydatarequest =  {
                              "id":orderId, 
                              "type":4,
                              "limitPrice": limitPrice,
                              "stopLoss": stoploss,
                              "qty":qty
                            }

        return modifydatarequest

def OrderToJsonFyersRequest(orderRequest, productType, side):
        print(offlineOrder)
        fyersdatarequest =  {
                              "symbol": "",
                              "qty":25,
                              "type":2,
                              "side":side,
                              "productType": productType,
                              "limitPrice":0,
                              "stopPrice":0,
                              "validity":"DAY",
                              "disclosedQty":0,
                              "offlineOrder":offlineOrder,
                              "stopLoss":0,
                              "takeProfit":0
                            }

        if(orderRequest.order_type.lower() == 'MarketOrder'.lower()):
            fyersdatarequest =  {
                              "symbol": orderRequest.stock_symbol,
                              "qty":25,
                              "type":2,
                              "side":side,
                              "productType":productType,
                              "limitPrice":0,
                              "stopPrice":0,
                              "validity":"DAY",
                              "disclosedQty":0,
                              "offlineOrder":offlineOrder,
                              "stopLoss":0,
                              "takeProfit":0
                            }
        elif(orderRequest.order_type.lower() == 'LimitOrder'.lower()):
            fyersdatarequest =  {
                              "symbol": orderRequest.stock_symbol,
                              "qty":25,
                              "type":1,
                              "side":side,
                              "productType":productType,
                              "limitPrice":orderRequest.executedPrice,
                              "stopPrice":0,
                              "validity":"DAY",
                              "disclosedQty":0,
                              "offlineOrder":offlineOrder,
                              "stopLoss":0,
                              "takeProfit":0
                            }

        elif(orderRequest.order_type.lower() == 'StopLossMarketOrder'.lower()):
            orderPrice = float("{0:.2f}".format(orderRequest.executedPrice))
            fyersdatarequest =  {
                              "symbol": orderRequest.stock_symbol,
                              "qty":25,
                              "type":3,
                              "side":side,
                              "productType":productType,
                              "limitPrice":0,
                              "stopPrice":orderPrice,
                              "validity":"DAY",
                              "disclosedQty":0,
                              "offlineOrder":offlineOrder,
                              "stopLoss":0,
                              "takeProfit":0
                            }
        elif(orderRequest.order_type.lower() == 'StopLossLimitOrder'.lower()):
            orderPrice = float("{0:.2f}".format(orderRequest.executedPrice))
            fyersdatarequest =  {
                              "symbol": orderRequest.stock_symbol,
                              "qty":25,
                              "type":4,
                              "side":side,
                              "productType":productType,
                              "limitPrice":orderPrice - 2,
                              "stopPrice":orderPrice,
                              "validity":"DAY",
                              "disclosedQty":0,
                              "offlineOrder":offlineOrder,
                              "stopLoss":0,
                              "takeProfit":0
                            }
        
        print(fyersdatarequest)

        return fyersdatarequest

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