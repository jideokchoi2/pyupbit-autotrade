import time
import pyupbit
import datetime

access = "your-access"
secret = "your-secret"

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# 코인 비율 설정
coin_ratios = {
    "KRW-BTC": 0.4,
    "KRW-TRX": 0.2,
    "KRW-SHIB": 0.2,
    "KRW-XRP": 0.2
}

# 손절 및 추적손절매 설정
stop_loss_prices = {}
trailing_stop_ratios = 0.95  # 5% 손절

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            krw = get_balance("KRW")
            if krw > 5000:
                for ticker, ratio in coin_ratios.items():
                    investment = krw * ratio
                    target_price = get_target_price(ticker, 0.5)
                    current_price = get_current_price(ticker)
                    if target_price < current_price:
                        upbit.buy_market_order(ticker, investment * 0.9995)

                        # 손절 가격 초기 설정
                        stop_loss_prices[ticker] = current_price * trailing_stop_ratios

            for ticker in coin_ratios.keys():
                current_price = get_current_price(ticker)

                # 손절 가격 업데이트 (추적손절매)
                if ticker in stop_loss_prices and current_price > stop_loss_prices[ticker] / trailing_stop_ratios:
                    stop_loss_prices[ticker] = current_price * trailing_stop_ratios

        else:
            for ticker in coin_ratios.keys():
                balance = get_balance(ticker.split("-")[1])
                current_price = get_current_price(ticker)

                # 손절 조건 확인 후 매도
                if balance > 0 and current_price <= stop_loss_prices.get(ticker, 0):
                    upbit.sell_market_order(ticker, balance * 0.9995)

        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
