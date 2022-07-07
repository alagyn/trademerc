from alpaca_trade_api.rest import REST
import cash_money.utils.api_utils as api_utils

def close_all(api: REST):
    api.cancel_all_orders()
    api.close_all_positions()


def main():
    api = api_utils.loadPaperAPI()
    close_all(api)

if __name__ == "__main__":
    main()
