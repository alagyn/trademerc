### TODO:
1) Setup a GUI to perform a backtest with a strategy
2) Reporting
   1) Alert for stock meeting buy criteria and is bought @ X% of portfolio
   2) Alert for stock meeting sell criteria and sale is triggered
   3) Weekly update on: number of trades (buy and sold) and portfolio size, and portfolio change

3) Setup GUI to create strategies - This is fairly complicated given the number of indicators and variables 

### STRATEGY 1

### BUY CONDITIONS
1) Confidence GREATER THAN 60% for X days
    
### SELL CONDITIONS
1) Confidence LESS THAN 45%
2) Stop is reached
3) Profit exit is reached
4) The symbol has fallen some % within one day, that is indicating a correction (but not necessarily a trend reversal, but still best to get out) (WIP)
    
### Confidence
* ema3 > ema20: confidence =+ 0.20  
* ema3 > ema50: confidence =+ 0.05  
* macd(10|20) > macdEMA(20): confidence =+ 0.15  
* macd(10|20) > 0: confidence =+ 0.05  
* stochfast(P20|%K10) > stochslow(P20|%D10): confidence =+ 0.15  
* stochfast(P20|%K10) > 50: confidence =+0.05  
* parablicsar(0.02|0.07) > price =+ 0.20  
* XXXXX =+ 0.15  <--- NEED ANOTHER CRITERION   

### Stop conditions
* Price - ATR (15 OR 30) * 1.5
* Update Stop every 7 days if new stop price is above current stop price

### MISC INFO 

SQN or SystemQualityNumber. Defined by Van K. Tharp to categorize trading systems.
SquareRoot(NumberTrades) * Average(TradesProfit) / StdDev(TradesProfit)
The sqn value should be deemed reliable when the number of trades >= 30

1.6 - 1.9 Below average  
2.0 - 2.4 Average  
2.5 - 2.9 Good  
3.0 - 5.0 Excellent  
5.1 - 6.9 Superb  
7.0 - Holy Grail  