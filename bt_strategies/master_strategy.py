import backtrader as bt
import backtrader.indicators as btI
from datetime import timedelta as TD
from cmErrors import StrategyError


# Standard trading strategy for trend trading, see commented section above for sudo code
class MasterStrategy(bt.Strategy):

    # Function to initialize all variables and indicators of this strategy
    # noinspection PyArgumentList
    def __init__(self, variables):
        self.dataclose = self.datas[0].close  # Defines closing price for each day
        self.confidence = 0
        # Sets initial state of "action" taken, either None, Buy, Hold, or Sell
        self.action = None
        # Sets initial state of an order
        self.order = None
        # Sets initial state of a buy_price to be None
        self.buy_price = None
        # Sets the initial date for the stop price
        self.stop_date = None
        # Sets the initial stop for the stop price
        self.stop_price = 0
        # Sets the initial stop for the new stop price
        self.new_stop_price = 0
        # Defines initial stop ORDER as None
        self.stop_loss_order = None
        # Defines initial profit exit as None
        self.profit_exit = None
        self.profit_exit_order = None

        self.sell_date = None

        def getVar(*path):
            cur = variables
            try:
                for x in path:
                    cur = cur[x]
                return cur
            except KeyError:
                p = ''
                for idx, x in enumerate(path):
                    p += x
                    if idx + 1 < len(path):
                        p += '->'

                raise StrategyError(f'Missing Strategy Variable: {p}')

        self.safety_factor = float(getVar('safety'))
        self.days_to_update_stop_price = int(getVar('days_to_update'))
        # Indicators
        plots = False
        self.emafast = btI.ExponentialMovingAverage(period=int(getVar('ema', 'fast')), plot=plots)
        self.emaslow = btI.ExponentialMovingAverage(period=int(getVar('ema', 'slow')), plot=plots)
        self.emalong = btI.ExponentialMovingAverage(period=int(getVar('ema', 'long')), plot=plots)
        self.macd = btI.MACD(
            period_me1=int(getVar('macd', 'fast')),
            period_me2=int(getVar('macd', 'slow')),
            period_signal=int(getVar('macd', 'signal')),
            plot=plots
        )
        self.macdX = btI.CrossOver(self.macd.macd, self.macd.signal, plot=plots)
        self.stoch = btI.Stochastic(
            period=int(getVar('stoch', 'p')),
            period_dfast=int(getVar('stoch', 'fast')),
            period_dslow=int(getVar('stoch', 'slow')),
            plot=plots
        )
        self.stochX = btI.CrossOver(self.stoch.percK, self.stoch.percD, plot=plots)
        self.parabolic = btI.ParabolicSAR(
            af=float(getVar('parabolic', 'af')),
            afmax=float(getVar('parabolic', 'afmax')),
            plot=plots
        )
        self.atr = btI.AverageTrueRange(period=int(getVar('atr')), plot=plots)

    # Logs the information
    def log(self):
        # Prints the date, action, and closing price
        x = f'{self.datas[0].datetime.date(0)}, {self.action}, ${self.dataclose[0]:.2f}, {self.confidence * 100:.0f}%, '
        x += f'Value:${self.broker.getvalue():.2f}, Stop date: {self.stop_date}, Stop price:${self.stop_price:.2f}'
        print(x)

    # Orders status needs to be determined
    def notify_order(self, order):
        # If order has been submitted or accepted, do nothing.
        if order.status in [order.Submitted, order.Accepted]:
            return

        if not order.alive():
            self.order = None  # indicate no order is pending

        # Check if an order has been completed (could be rejected if not enough cash)
        if order.status == order.Completed:
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
        self.sell_date = self.datetime.date(0)
        self.stop_date = None
        self.stop_price = 0
        # TODO remove ref?
        # print('PROFIT: $%.2f, CASH: $%.2f' % (trade.pnl, cerebro.broker.getvalue()))

    # Main section of the strategy, to run on each instance of data feed (essentially a loop)
    def next(self):
        # Logic test weights
        w1 = 0.35
        w2 = 0.05
        w3 = 0.15
        w4 = 0.05
        w5 = 0.15
        w6 = 0.05
        w7 = 0.20

        # Confidence logic
        if self.emafast > self.emaslow:
            self.confidence += w1
        if self.emafast < self.emaslow:
            self.confidence -= w1

        if self.emafast > self.emalong:
            self.confidence += w2
        if self.emafast < self.emalong:
            self.confidence -= w2

        if self.macdX > 0:
            self.confidence += w3
        if self.macdX < 0:
            self.confidence -= w3

        if self.macd > 0:
            self.confidence += w4
        if self.macd < 0:
            self.confidence -= w4

        if self.stoch > 50:
            self.confidence += w5
        if self.stoch < 50:
            self.confidence -= w5

        if self.stochX > 0:
            self.confidence += w6
        if self.stochX < 0:
            self.confidence -= w6

        if self.parabolic < self.data.close[0]:
            self.confidence += w7
        if self.parabolic > self.data.close[0]:
            self.confidence -= w7

        # Checks to see if an order is pending. If it is, function is closed,
        # wait for order to finish.
        if self.order:
            return

        # NOT IN MARKET
        if not self.position:
            self.action = None

            # Wait X days before buying again to ensure confidence is not whipsawing
            if self.sell_date is None or self.sell_date + TD(days=3) < self.datetime.date(0):

                # Long Position
                if self.confidence > 0.65:
                    self.stop_price = self.dataclose[0] - (self.atr[0] * self.safety_factor)

                    # Market order
                    self.order = self.buy(
                        price=None,
                        exectype=bt.Order.Market,
                        transmit=False
                    )

                    # Stop loss order
                    self.stop_loss_order = self.sell(
                        price=self.stop_price,
                        exectype=bt.Order.Stop,
                        transmit=True,
                        parent=self.order
                    )
                    self.stop_date = self.datas[0].datetime.date(0)
                    self.action = 'Buy'

        # IN MARKET
        else:
            # If this condition is met sell
            if self.confidence < 0.45:
                self.broker.cancel(self.stop_loss_order)
                self.stop_date = None
                self.stop_price = 0
                # Sell if confidence has dropped below level
                self.order = self.sell()
                self.sell_date = self.datetime.date(0)
                self.action = 'Sell'

            # If condition has not been met to sell, keep holding
            else:
                self.action = 'Hold'

            # Update Stop order
            if self.stop_date is not None:
                if self.datetime.date(0) > self.stop_date + TD(days=self.days_to_update_stop_price):
                    self.new_stop_price = self.dataclose[0] - (self.atr[0] * self.safety_factor)
                    # print("It's 15 days later, the new stop price would be: " + str(round(self.new_stop_price,2)))
                    if self.new_stop_price > self.stop_price:
                        self.broker.cancel(self.stop_loss_order)
                        self.stop_loss_order = self.sell(price=self.new_stop_price,
                                                         exectype=bt.Order.Stop,
                                                         transmit=True)

                        self.stop_price = self.new_stop_price
                        self.stop_date = self.datas[0].datetime.date(0)

        #               else:
        #                   print("DON'T UPDATE THE STOP PRICE")

        # Prints the date, action, and closing price
        self.log()
        self.confidence = 0
