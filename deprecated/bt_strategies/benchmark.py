import backtrader as bt
import backtrader.indicators as btI


# Buy and hold strategy
class Benchmark(bt.Strategy):
    def __init__(self):
        self.dataclose = self.datas[0].close  # Defines closing price for each day
        self.order = None  # Sets initial state of an order
        self.action = None  # Sets initial state of "action" taken, either None, Buy, Hold, or Sell
        self.buy_price = None

        self.ema50 = btI.ExponentialMovingAverage(period=50, plot=False)
        return

    # Logs the information
    def log(self):
        # Prints the date, action, and closing price
        print('%s, %s, $%.2f' % (self.datas[0].datetime.date(0),
                                 self.action,
                                 self.dataclose[0],))

    # Orders status needs to be determined
    def notify_order(self, order):
        # If order has been submitted or accepted, do nothing.
        if order.status in [order.Submitted, order.Accepted]:
            return

        # Check if an order has been completed (could be rejected if not enough cash)
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                print('%s, Buy created at $%.2f' % (self.datas[0].datetime.date(0), order.executed.price))

            else:  # Sell
                print('%s, Sell created at $%.2f' % (self.datas[0].datetime.date(0), order.executed.price))

        elif order.status in [order.Canceled]:
            print('Order Canceled')
        elif order.status in [order.Rejected]:
            print('Order Rejected')

        # Write down: no pending order
        self.order = None

    # Notifies when a trade is closed and the profit from the trade
    def notify_trade(self, trade):
        # If the trade is not closing, then close function
        if not trade.isclosed:
            return

        print('PROFIT: $%.2f, CASH: $%.2f' % (trade.pnl, cerebro.broker.getvalue()))

    # Main section of the strategy, to run on each instance of data feed (essentially a loop)
    def next(self):
        # Checks to see if an order is pending. If it is, function is closed, to wait for order to finish
        if self.order:
            return

        # NOT IN MARKET
        if not self.position:
            self.buy()
            self.action = 'Buy'

        # IN MARKET
        else:
            self.action = 'Hold'

        # Prints the date, action, and closing price
        self.log()
