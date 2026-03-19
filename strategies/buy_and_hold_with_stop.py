import backtrader as bt
import backtrader.indicators as btI
from datetime import timedelta as TD


# Buy and hold with moving stop. Buy when price > SMA40 & EMA10.
class BuyAndHoldWithStop(bt.Strategy):
    params = (
        ('ema', 10),
        ('sma', 40),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close  # Defines closing price for each day
        self.order = None  # Sets initial state of an order
        self.action = None  # Sets initial state of "action" taken, either None, Buy, Hold, or Sell
        self.buy_price = None
        self.stop_price = 0
        self.stop_loss_order = None
        self.stop_date = None
        self.new_stop_price = 0

        self.ema = btI.ExponentialMovingAverage(period=self.params.ema)
        self.sma = btI.MovingAverageSimple(period=self.params.sma)
        self.atr = btI.AverageTrueRange(period=20, plot=False)
        return

    # Logs the information
    def log(self):
        # Prints the date, action, and closing price
        print('%s, %s, $%.2f, Value:$%.2f, Stop date:%s, Stop price:$%.2f' % (self.datas[0].datetime.date(0),
                                                                              self.action,
                                                                              self.dataclose[0],
                                                                              self.broker.getvalue(),
                                                                              self.stop_date,
                                                                              self.stop_price))

    # Orders status needs to be determined
    def notify_order(self, order):
        # If order has been submitted or accepted, do nothing.
        if order.status in [order.Submitted, order.Accepted]:
            return

        # Check if an order has been completed (could be rejected if not enough cash)
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
        #           print('%s, Buy created at $%.2f' % (self.datas[0].datetime.date(0), order.executed.price))

        #       else:  # Sell
        #           print('%s, Sell created at $%.2f' % (self.datas[0].datetime.date(0), order.executed.price))

        #   elif order.status in [order.Canceled]:
        #       print('Order Canceled')
        #   elif order.status in [order.Rejected]:
        #       print('Order Rejected')

        # Write down: no pending order
        self.order = None

    # Notifies when a trade is closed and the profit from the trade
    def notify_trade(self, trade):
        # If the trade is not closing, then close function
        if not trade.isclosed:
            return

        # TODO remove ref?
        print('PROFIT: $%.2f, CASH: $%.2f' % (trade.pnl, cerebro.broker.getvalue()))

    # Main section of the strategy, to run on each instance of data feed (essentially a loop)
    def next(self):
        # Checks to see if an order is pending. If it is, function is closed, to wait for order to finish
        if self.order:
            return

        # NOT IN MARKET
        if not self.position:
            self.action = None

            if self.dataclose > self.sma:
                if self.dataclose > self.ema:
                    self.stop_price = self.dataclose[0] - (self.atr[0] * 2)

                    # Market order
                    self.order = self.buy(price=None,
                                          exectype=bt.Order.Market,
                                          transmit=False)

                    # Stop loss order
                    self.stop_loss_order = self.sell(price=self.stop_price,
                                                     exectype=bt.Order.Stop,
                                                     transmit=True,
                                                     parent=self.order)

                    self.stop_date = self.datas[0].datetime.date(0)
                    self.action = 'Buy'

        # IN MARKET
        else:
            self.action = 'Hold'

            # Update Stop order
            if self.stop_date is not None:
                if self.datas[0].datetime.date(0) > self.stop_date + TD(days=7):
                    self.new_stop_price = self.dataclose[0] - (self.atr[0] * 2)
                    # print("It's 15 days later, the new stop price would be: " + str(round(self.new_stop_price,2)))
                    if self.new_stop_price > self.stop_price:
                        self.broker.cancel(self.stop_loss_order)
                        self.stop_loss_order = self.sell(price=self.new_stop_price,
                                                         exectype=bt.Order.Stop,
                                                         transmit=True)

                        self.stop_price = self.new_stop_price
                        self.stop_date = self.datas[0].datetime.date(0)

        #            else:
        #                print("DON'T UPDATE THE STOP PRICE")

        # Prints the date, action, and closing price
        # self.log()
