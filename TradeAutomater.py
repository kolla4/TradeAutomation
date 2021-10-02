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
import OrderExecution

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

                signalDetails = orderRequest.stock_name + " , " + orderRequest.transaction_type + " , Signal Entry Price - " + str(orderRequest.executedPrice) + " , SL - " + str(orderRequest.stop_loss)

                await sendMessagetoTelegram(tradeStatusUpdateMessage + signalDetails)
                #---- Send the order for execution to the broker

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

        stoploss = 0
        suggestedEntryPrice = 0        

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
        try:
            suggestedEntryPrice = int(re.search(r'\d+', re.search('Buy At (.*) For', trademessage).group(1)).group())
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
            stockSymbol = stockType.upper() + '20' + month + date.rstrip(date[-2:]) + optionStrikePrice + optionType.upper()

            #print(stockSymbol)
        else:
            #---- Monthly Expiry
            month = splitstrings[1]
            optionStrikePrice = splitstrings[2]
            optionType = splitstrings[3]
            
            stockName = month.upper() + " " + optionStrikePrice + " " + optionType.upper()
            stockSymbol = stockType.upper() + '20' + month.upper() + optionStrikePrice + optionType.upper()
            #print(stockSymbol)

        
        tradeSignal = stockSymbol + ' - ' + transactionType + ' - ' + str(suggestedEntryPrice)
        # print(stockName, optionType, transactionType, suggestedEntryPrice)
        print(tradeSignal)

        stoploss = getStoploss(trademessage)
        

        if(stoploss == 0):
            stoploss = suggestedEntryPrice - 50

        orderRequest = OrderExecution.OrderExecutionRequest(stockName, stockSymbol, transactionType, stoploss, suggestedEntryPrice)

        stoploss = EvaluateStopLossPrice(stoploss, orderRequest)
        orderRequest.stop_loss = stoploss

        return orderRequest
        

    client.start(phone)

    # client.add_event_handler(update_handler)

    print('(Press Ctrl+C to stop this)')

    client.run_until_disconnected()


# def update_handler(update):
#     print(update)


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