class OrderExecutionRequest:

    def __init__(self, stock_name, stock_symbol, transaction_type, stop_loss, executedPrice = 0, order_type = 'Market Order', target_price = 0):
        self.stock_name = stock_name
        self.stock_symbol = stock_symbol
        self.transaction_type = transaction_type
        self.order_type = order_type
        self.stop_loss = stop_loss
        self.target_price = target_price
        self.executedPrice = executedPrice