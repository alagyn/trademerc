"""
An algorithm to backtest strategies in the stock market for TREND trading

@ JStarke
last update: 9/10/20
last update details:
    Started thinking about including "short position" trades
"""

# Strategy
"""
BUY CONDITIONS
    1) Confidence GREATER THAN 60% for X days
    
SELL CONDITIONS
    1) Confidence LESS THAN 45%
    2) Stop is reached
    3) Profit exit is reached
    4) The symbol has fallen some % within one day, that is indicating a correction (but not necessarily a trend reversal, but still best to get out) (WIP)
    
Confidence
    -ema3 > ema20: confidence =+ 0.20
    -ema3 > ema50: confidence =+ 0.05
    -macd(10|20) > macdEMA(20): confidence =+ 0.15
    -macd(10|20) > 0: confidence =+ 0.05
    -stochfast(P20|%K10) > stochslow(P20|%D10): confidence =+ 0.15
    -stochfast(P20|%K10) > 50: confidence =+0.05
    -parablicsar(0.02|0.07) > price =+ 0.20
    -XXXXX =+ 0.15  <--- NEED ANOTHER CRITERION 


Stop conditions
    -Price - ATR (15 OR 30) * 1.5
    -Update Stop every 7 days if new stop price is above current stop price

*** MISC INFO ***

SQN or SystemQualityNumber. Defined by Van K. Tharp to categorize trading systems.
    SquareRoot(NumberTrades) * Average(TradesProfit) / StdDev(TradesProfit)
    The sqn value should be deemed reliable when the number of trades >= 30

    1.6 - 1.9 Below average
    2.0 - 2.4 Average
    2.5 - 2.9 Good
    3.0 - 5.0 Excellent
    5.1 - 6.9 Superb
    7.0 - Holy Grail
"""

from datetime import datetime
from datetime import timedelta as TD
from collections import OrderedDict
import backtrader as bt
import backtrader.indicators as btI
import csv
import os.path
import time

""" ***** INITIALIZE ***** """
cerebro = bt.Cerebro()  # Create a cerebro entity

cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")  # Adds trade analyzer
cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")  # Adds SQN analyzer

""" ***** STRATEGIES ***** """


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


# Buy and hold with moving stop. Buy when price > SMA40 & EMA10.
class Buy_and_hold_with_stop(bt.Strategy):
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


# Standard trading strategy for trend trading, see commented section above for sudo code
class Strategy(bt.Strategy):
    # Parameters for the different indicators
    params = (
        ('emafast', 3),
        ('emaslow', 20),
        ('emalong', 60),
        ('macdfast', 10),
        ('macdslow', 20),
        ('macdsignal', 20),
        ('stochp', 20),
        ('stochfast', 10),
        ('stochslow', 10),
        ('parabolicaf', 0.02),
        ('parabolicafmax', 0.07),
        ('atr', 5),
        ('safety_factor', 2),
        ('days_to_update_stop_price', 7),
    )

    # Function to initialize all variables and indicators of this strategy
    def __init__(self):
        self.dataclose = self.datas[0].close  # Defines closing price for each day
        self.confidence = 0
        self.action = None  # Sets initial state of "action" taken, either None, Buy, Hold, or Sell
        self.order = None  # Sets initial state of an order
        self.buy_price = None  # Sets initial state of a buy_price to be None
        self.stop_date = None  # Sets the initial date for the stop price
        self.stop_price = 0  # Sets the initial stop for the stop price
        self.new_stop_price = 0  # Sets the initial stop for the new stop price
        self.stop_loss_order = None  # Defines initial stop ORDER as None
        self.profit_exit = None  # Defines initial profit exit as None
        self.profit_exit_order = None
        self.days_to_update_stop_price = 0
        self.safety_factor = 0
        self.sell_date = None

        # Indicators
        plots = False
        self.emafast = btI.ExponentialMovingAverage(period=self.params.emafast, plot=plots)
        self.emaslow = btI.ExponentialMovingAverage(period=self.params.emaslow, plot=plots)
        self.emalong = btI.ExponentialMovingAverage(period=self.params.emalong, plot=plots)
        self.macd = btI.MACD(period_me1=self.params.macdfast, period_me2=self.params.macdslow,
                             period_signal=self.params.macdsignal, plot=plots)
        self.macdX = btI.CrossOver(self.macd.macd, self.macd.signal, plot=plots)
        self.stoch = btI.Stochastic(period=self.params.stochp, period_dfast=self.params.stochfast,
                                    period_dslow=self.params.stochslow, plot=plots)
        self.stochX = btI.CrossOver(self.stoch.percK, self.stoch.percD, plot=plots)
        self.parabolic = btI.ParabolicSAR(af=self.params.parabolicaf, afmax=self.params.parabolicafmax, plot=plots)
        self.atr = btI.AverageTrueRange(period=self.params.atr, plot=plots)

    # Logs the information
    def log(self):
        # Prints the date, action, and closing price
        print('%s, %s, $%.2f, %.0f%%, Value:$%.2f, Stop date:%s, Stop price:$%.2f' % (self.datas[0].datetime.date(0),
                                                                                      self.action,
                                                                                      self.dataclose[0],
                                                                                      self.confidence * 100,
                                                                                      self.broker.getvalue(),
                                                                                      self.stop_date,
                                                                                      self.stop_price,
                                                                                      ))

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
        print('PROFIT: $%.2f, CASH: $%.2f' % (trade.pnl, cerebro.broker.getvalue()))

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

        # Checks to see if an order is pending. If it is, function is closed, to wait for order to finish
        if self.order:
            return

        # NOT IN MARKET
        if not self.position:
            self.action = None

            # Wait X days before buying again to ensure confidence is not whipsawing
            if self.sell_date is None or self.sell_date + TD(days=3) < self.datetime.date(0):

                # Long Position
                if self.confidence > 0.65:
                    self.stop_price = self.dataclose[0] - (self.atr[0] * self.params.safety_factor)

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
            if self.confidence < 0.45:  # If this condition is met sell
                self.broker.cancel(self.stop_loss_order)
                self.stop_date = None
                self.stop_price = 0
                self.order = self.sell()  # Sell if confidence has dropped below level
                self.sell_date = self.datetime.date(0)
                self.action = 'Sell'

            else:  # If condition has not been met to sell, keep holding
                self.action = 'Hold'

            # Update Stop order
            if self.stop_date is not None:
                if self.datetime.date(0) > self.stop_date + TD(days=self.params.days_to_update_stop_price):
                    self.new_stop_price = self.dataclose[0] - (self.atr[0] * self.params.safety_factor)
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


# ADD STRATEGY TO CEREBRO
cerebro.addstrategy(Strategy)

""" ***** BROKER ***** """


def add_broker():
    cerebro.broker.setcash(10000)  # Sets initial portfolio amount
    cerebro.addsizer(bt.sizers.PercentSizer, percents=100)  # Sets the amount willing to risk per trade


""" ***** ANALYZERS ***** """


# Analyzes the efficiency of trade
def TradeAnalysis(analyzer):
    global tt
    global win
    tt = analyzer.won.total + analyzer.lost.total
    win = round((analyzer.won.total / (analyzer.won.total + analyzer.lost.total)), 2)

    print('Total Trades: %s' % (analyzer.won.total + analyzer.lost.total))
    # print('Win percentage: %.2f' % (analyzer.won.total / (analyzer.won.total + analyzer.lost.total) * 100) + '%')
    # print('Won: %s' % analyzer.won.total)
    # print('Lost: %s' % analyzer.lost.total)
    # print('Opened: %s' % analyzer.total.open)
    # print('Closed: %s' % analyzer.total.closed)
    # print('Win Streak: %s' % analyzer.streak.won.longest)
    # print('Lose Streak: %s' % analyzer.streak.lost.longest)
    # print('P&L: %.2f' % analyzer.pnl.net.total)
    return win


# System Quality Number. Goal is above 3
def SQN(analyzer):
    global sqn
    sqn = round(analyzer.sqn, 2)
    return sqn


""" ***** RECORD KEEPING ***** """


# Record information to excel file
def record():
    filename = 'record.csv'
    file_exists = os.path.isfile(filename)
    with open(filename, 'a',
              newline="") as backtest_record:  # updates the history file to write into it, if "a" value was a "w" the function would write over the existing data
        fieldnames = ["Stock", "Value", "Profit($)", "Percent Gained(%)", "Total Trades", "Win %",
                      "SQN"]  # sets up the field names
        writer = csv.DictWriter(backtest_record, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header
        writer.writerow({'Stock': stock,
                         'Value': ending_value,
                         'Profit($)': str(round(ending_value - starting_value, 2)),
                         'Percent Gained(%)': str(round(((ending_value - starting_value) / starting_value), 2)),
                         'Total Trades': tt,
                         'Win %': win,
                         'SQN': sqn
                         })


""" ***** MAIN***** """
if __name__ == "__main__":
    add_broker()
    start_date = datetime(2018, 1, 1)
    end_date = datetime.today()

    stocks = [
        ['QQQ'],
        # ['DIA'],
        # ['SPY'],
        # ['SOXL'],
        # ['FVRR'],
        # ['TSLA'],
        # ['AAPL'],
        # ['DOCU'],
        # ['NVDA'],
        # ['AMD'],
        # ['TQQQ'],
        # ['SQQQ'],
    ]

    # with open('../data/Stock list2.txt') as stock_symbols:
        # stock_list = csv.reader(stock_symbols, delimiter=',')
        # Switch list between "stocks" or "stock_list" to reference local list or external txt file
    for stock in stocks:
        print(stock[0])
        # Try statement is if stock doesn't work

        """ ***** DATA FEED ***** """
        """
        data = bt.feeds.YahooFinanceData(dataname=stock[0],
                                         fromdate=start_date,
                                         todate=end_date,
                                     )
                                     """
        import yfinance as yf
        fmt = '%Y-%m-%d'
        sd = start_date.strftime(fmt)
        ed = end_date.strftime(fmt)
        data = bt.feeds.PandasData(dataname=yf.download(stock, sd, ed, auto_adjust=True))
        # Add the Data Feed to Cerebro
        cerebro.adddata(data)

        """ ***** RUN BACKTEST ***** """
        starting_value = cerebro.broker.getvalue()  # Starting Position
        start_time = time.time()
        results = cerebro.run()
        Strat = results[0]  # Runs over everything
        ending_value = cerebro.broker.getvalue()  # Ending Position
        print("")
        print("Run Time: " + str(round(time.time() - start_time, 2)) + " secs")
        print("Stock: " + stock[0])
        print("Ending Value: %.2f" % ending_value)
        print('Profit: %.2f ' % (ending_value - starting_value))
        print('Percent Gained: ' + str(round(((ending_value - starting_value) / starting_value) * 100, 2)) + '%')

        # Try statement is for if now sells were ever created
        try:
            print("Win Percentage: " + str(TradeAnalysis(Strat.analyzers.ta.get_analysis()) * 100) + '%')
            print("SQN: " + str(SQN(Strat.analyzers.sqn.get_analysis())))
        except:
            print("No losses")

        cerebro.plot()
        # record()
        print("")

        # except:
        #    print("Stock doesn't work")
