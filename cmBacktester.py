from alpaca_trade_api.rest import REST, TimeFrame, URL, TimeFrameUnit
from dotenv import dotenv_values

from indicators.indicator import getSetupTime, addData, clearIndicators

from strategies.hardStrategy import HardStrategy
from strategies.strategy import Position, ActionEnum

from backtester import loadStratFile

# %%

PAPER_ENDPOINT = 'https://paper-api.alpaca.markets'

config = dotenv_values('ignore/.env')

api_key = config['PAPER_API_KEY_ID']
api_secret = config['PAPER_SECRET']

api = REST(api_key, api_secret, URL(PAPER_ENDPOINT), 'v2')

# %%
SYMBOL = 'QQQ'

bars = api.get_bars(SYMBOL, TimeFrame(1, TimeFrameUnit.Day),
                    '2018-01-01', '2021-11-01', adjustment='raw').df
# %%
lows = bars['low']
closes = bars['close']
highs = bars['high']

# %%

clearIndicators()

stratVars = loadStratFile('config/strat1.json')['variables']

strat = HardStrategy(SYMBOL, stratVars)

# %% Setup

setuptime = getSetupTime()

for i in range(setuptime):
    addData(SYMBOL, lows[i], closes[i], highs[i])

# %% Backtest

pos = Position.OutMarket
currentStop = None

startingVal = 10000
value = startingVal
stocks = 0

valueBeforeBuy = 0

wins = 0
losses = 0
lossTotal = 0
winTotal = 0


def updateWL(newVal):
    global wins, losses, lossTotal, winTotal

    delta = abs(valueBeforeBuy - newVal)

    if newVal < valueBeforeBuy:
        losses += 1
        lossTotal += delta
    else:
        wins += 1
        winTotal += delta


for i in range(setuptime, len(closes)):
    addData(SYMBOL, lows[i], closes[i], highs[i])

    act = strat.nextAction(i, pos)
    if act.action == ActionEnum.Buy:
        pos = Position.InMarket
        currentStop = act.args['stopPrice']

        stocks = int(value / closes[i])

        valueBeforeBuy = value
        value -= stocks * closes[i]
        continue

    elif act.action == ActionEnum.Sell:
        pos = Position.OutMarket
        currentStop = None

        value += stocks * closes[i]
        stocks = 0
        updateWL(value)
        continue
    elif act.action == ActionEnum.UpdateStop:
        currentStop = act.args['stopPrice']
        continue

    if currentStop is not None and lows[i] < currentStop:
        print('Stop Activated')
        pos = Position.OutMarket

        value += stocks * currentStop
        updateWL(value)
        stocks = 0

if stocks > 0:
    value += stocks * closes[-1]

print('Starting Value:', startingVal)
print(f'Ending Value: {value:.2f}')
print(f'Profit: {value - startingVal:.2f}')
print(f'Wins: {wins}, Losses: {losses}, W/L: {wins / losses}')
print(f'Win %: {wins / (wins + losses):.2%}')
print(f'Avg Gain: ${winTotal / wins:.2f}')
print(f'Avg Loss: ${lossTotal / losses:.2f}')


# %%

stocks = ['QQQ', 'DIA']

snaps = api.get_snapshots(stocks)

# %%

for x in snaps:
    snap = snaps[x]
    db = snap.daily_bar
    mb = snap.minute_bar

    print(f'MB: {mb.l}  DB:{db.l}')
