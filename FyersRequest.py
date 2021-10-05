import OrderExecution
import json

class FyersRequestModel:

    def __init__(self, symbol, qty, marketType, side, productType, limitPrice = 0, stopPrice = 0, disclosedQty = 0, validity = 'DAY', offlineOrder = False, stopLoss = 0, takeProfit = 0):
        self.symbol = symbol
        self.qty = qty
        self.type = marketType
        self.side = side
        self.productType = productType
        self.limitPrice = limitPrice
        self.stopPrice = stopPrice
        self.validity = validity
        self.disclosedQty = disclosedQty
        self.offlineOrder = offlineOrder
        self.stopLoss = stopLoss
        self.takeProfit = takeProfit
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

        