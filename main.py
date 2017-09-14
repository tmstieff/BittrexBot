import time
import requests
import hashlib
import hmac

TICK_INTERVAL = 60  # seconds
API_KEY = 'my-api-key'
API_SECRET_KEY = b'my-secret-key'


def main():
    print('Starting trader bot...')

    while True:
        start = time.time()
        tick()
        end = time.time()

        # Sleep the thread if needed
        if end - start < TICK_INTERVAL:
            time.sleep(TICK_INTERVAL - (end - start))


def tick():
    print('Running routine')

    market_summaries = simple_request('https://bittrex.com/api/v1.1/public/getmarketsummaries')
    for summary in market_summaries['result']:
        market = summary['MarketName']
        day_close = summary['PrevDay']
        last = summary['Last']

        if day_close > 0:
            percent_chg = ((last / day_close) - 1) * 100
        else:
            print('day_close zero for ' + market)

        print(market + ' changed ' + str(percent_chg))

        if 40 < percent_chg < 60:
            # Fomo strikes! Let's buy some
            if has_open_order(market, 'LIMIT_BUY'):
                print('Order already opened to buy 5 ' + market)
            else:
                print('Purchasing 5 units of ' + market + ' for ' + str(format_float(last)))
                res = buy_limit(market, 5, last)
                print(res)

        if percent_chg < -20:
            # Do we have any to sell?
            balance_res = get_balance_from_market(market)
            current_balance = balance_res['result']['Available']

            if current_balance > 5:
                # Ship is sinking, get out!
                if has_open_order(market, 'LIMIT_SELL'):
                    print('Order already opened to sell 5 ' + market)
                else:
                    print('Selling 5 units of ' + market + ' for ' + str(format_float(last)))
                    res = sell_limit(market, 5, last)
                    print(res)
            else:
                print('Not enough ' + market + ' to open a sell order')


def buy_limit(market, quantity, rate):
    url = 'https://bittrex.com/api/v1.1/market/buylimit?apikey=' + API_KEY + '&market=' + market + '&quantity=' + str(quantity) + '&rate=' + format_float(rate)
    return signed_request(url)


def sell_limit(market, quantity, rate):
    url = 'https://bittrex.com/api/v1.1/market/selllimit?apikey=' + API_KEY + '&market=' + market + '&quantity=' + str(quantity) + '&rate=' + format_float(rate)
    return signed_request(url)


def get_balance_from_market(market_type):
    markets_res = simple_request('https://bittrex.com/api/v1.1/public/getmarkets')
    markets = markets_res['result']
    for market in markets:
        if market['MarketName'] == market_type:
            return get_balance(market['MarketCurrency'])

    # Return a fake response of 0 if not found
    return {'result': {'Available': 0}}


def get_balance(currency):
    url = 'https://bittrex.com/api/v1.1/account/getbalance?apikey=' + API_KEY + '&currency=' + currency
    res = signed_request(url)

    if res['result'] is not None and len(res['result']) > 0:
        return res

    # If there are no results, than your balance is 0
    return {'result': {'Available': 0}}


def get_open_orders(market):
    url = 'https://bittrex.com/api/v1.1/market/getopenorders?apikey=' + API_KEY + '&market=' + market
    return signed_request(url)


def has_open_order(market, order_type):
    orders_res = get_open_orders(market)
    orders = orders_res['result']

    if orders is None or len(orders) == 0:
        return False

    # Check all orders for a LIMIT_BUY
    for order in orders:
        if order['OrderType'] == order_type:
            return True

    return False


def signed_request(url):
    now = time.time()
    url += '&nonce=' + str(now)
    signed = hmac.new(API_SECRET_KEY, url.encode('utf-8'), hashlib.sha512).hexdigest()
    headers = {'apisign': signed}
    r = requests.get(url, headers=headers)
    return r.json()


def simple_request(url):
    r = requests.get(url)
    return r.json()


def format_float(f):
    return "%.8f" % f


if __name__ == "__main__":
    main()

