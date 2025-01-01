import time
import pyupbit
import datetime

access = ""
secret = ""

# 코인 비율 설정
allocation = {
    "KRW-BTC": 0.5,
    "KRW-TRX": 0.15,
    "KRW-XRP": 0.15,
    "KRW-SHIB": 0.15,
    "KRW-STX": 0.05
}

# 추적 손절매 가격 저장
trailing_stop = {ticker: 0 for ticker in allocation.keys()}

# 변동성 돌파 전략으로 매수 목표가 계산
def get_target_price(ticker, k):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

# 시작 시간 조회
def get_start_time(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

# 잔고 조회
def get_balance(ticker):
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker.replace("KRW-", ""):
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

# 현재가 조회
def get_current_price(ticker):
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 추적 손절매 가격 업데이트
def update_trailing_stop(ticker, current_price):
    global trailing_stop
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    atr = df.iloc[0]['high'] - df.iloc[0]['low']  # 변동폭 계산

    if current_price > trailing_stop[ticker]:
        trailing_stop[ticker] = max(trailing_stop[ticker], current_price - atr)

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        for ticker, ratio in allocation.items():
            start_time = get_start_time(ticker)
            end_time = start_time + datetime.timedelta(days=1)

            if start_time < now < end_time - datetime.timedelta(seconds=10):
                target_price = get_target_price(ticker, 0.5)
                current_price = get_current_price(ticker)
                
                update_trailing_stop(ticker, current_price)

                # 매수 조건 확인
                if target_price < current_price:
                    krw = get_balance("KRW")
                    if krw > 5000:
                        upbit.buy_market_order(ticker, krw * ratio * 0.9995)
            else:
                # 손절매 조건 확인
                current_price = get_current_price(ticker)
                if current_price < trailing_stop[ticker]:
                    coin_balance = get_balance(ticker.replace("KRW-", ""))
                    if coin_balance > 0:
                        upbit.sell_market_order(ticker, coin_balance * 0.9995)

        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
