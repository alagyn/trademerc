from alpaca.trading.client import TradingClient
import cash_money.utils.api_utils as api_utils


def close_all(api: api_utils.CMAPI):
    print("Closing all positions")
    api.trade.close_all_positions(True)


def main():
    api = api_utils.loadPaperAPI()
    close_all(api)


if __name__ == "__main__":
    main()
