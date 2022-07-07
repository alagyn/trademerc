from cash_money.trading.notifiers.emailer import CMEmailer
from cash_money.trading.notifiers.notfier import NotifyKeys
from cash_money.utils.run_utils import loadSystem

if __name__ == "__main__":
    config = loadSystem()

    emailer = CMEmailer(config['Email'])

    trades = [
        {
            NotifyKeys.Trade.Symbol: "QQQ",
            NotifyKeys.Trade.Value: 100,
            NotifyKeys.Trade.Price: 10,
            NotifyKeys.Trade.Qty: 10,
            NotifyKeys.Trade.Side: "Buy"
        },
        {
            NotifyKeys.Trade.Symbol: "TSLA",
            NotifyKeys.Trade.Value: 500,
            NotifyKeys.Trade.Price: 20,
            NotifyKeys.Trade.Qty: 25,
            NotifyKeys.Trade.Side: "Sell"
        },
        {
            NotifyKeys.Trade.Symbol: "ASDF",
            NotifyKeys.Trade.Value: 10.25,
            NotifyKeys.Trade.Price: 12.5,
            NotifyKeys.Trade.Qty: 63,
            NotifyKeys.Trade.Side: "Sell"
        },
    ]

    positions = [
        {
            NotifyKeys.Position.Symbol: "QQQ",
            NotifyKeys.Position.Qty: 100,
            NotifyKeys.Position.PL: 25,
            NotifyKeys.Position.Price: 10,
            NotifyKeys.Position.Value: 100,
            NotifyKeys.Position.PurchaseValue: 25,
            NotifyKeys.Position.PurchaseDate: "10/10/22",
            NotifyKeys.Position.StopPrice: 20,
            NotifyKeys.Position.LastStop: "10/9/22",
            NotifyKeys.Position.NextStop: "10/11/22",
        },
        {
            NotifyKeys.Position.Symbol: "TSLA",
            NotifyKeys.Position.Qty: 100,
            NotifyKeys.Position.PL: 25,
            NotifyKeys.Position.Price: 10,
            NotifyKeys.Position.Value: 100,
            NotifyKeys.Position.PurchaseValue: 25,
            NotifyKeys.Position.PurchaseDate: "10/10/22",
            NotifyKeys.Position.StopPrice: 20,
            NotifyKeys.Position.LastStop: "10/9/22",
            NotifyKeys.Position.NextStop: "10/11/22",
        },
        {
            NotifyKeys.Position.Symbol: "ASDF",
            NotifyKeys.Position.Qty: 100,
            NotifyKeys.Position.PL: 25,
            NotifyKeys.Position.Price: 10,
            NotifyKeys.Position.Value: 100,
            NotifyKeys.Position.PurchaseValue: 25,
            NotifyKeys.Position.PurchaseDate: "10/10/22",
            NotifyKeys.Position.StopPrice: 20,
            NotifyKeys.Position.LastStop: "10/9/22",
            NotifyKeys.Position.NextStop: "10/11/22",
        }
    ]

    content = emailer.generate(100, 200, 100, trades, positions)

    with open("temp.html", mode='w') as f:
        f.write(content)

    print("Done")