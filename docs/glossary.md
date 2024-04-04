### Trader:
The core trading logic. Abstract class, manages internal representations of stocks/positions etc.
Calls abstract functions to retrieve data and accomplish actions, but has no knowldge of *how* that happens.

### Broker:
Concrete implementation of the Trader that implements connections to actually accomplish actions requested
by the base Trader

### Stock:
A single tradable commodity. Referenced by a "symbol" aka the name (TSLA, QQQ, APL, ... etc)

### Bar:
Statistics related to a specific stock for some arbitrary time unit.
low (lo): the lowest price the stock reached
close: the current price
high (hi): the highest price the stock reached
volume (vol): the number of stocks traded

### Order:
A request to the broker to buy/sell some quantity. Comes in 3 flavors:
Buy: A request to buy
Sell: A request to sell
Stop: A request to update the Stop-Limit price

### Position:
Represents an actively owned quantity of a specific Stock

### Strategy:
Object that recieves the current state of trader (Stock closes, volume, etc) and returns a single action to take.
Each stock of interest is allocated a copy of the Strategy.
