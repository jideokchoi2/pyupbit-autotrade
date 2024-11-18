import time
import pyupbit
import datetime

access = ""
secret = ""

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

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

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

# 거래할 코인 목록 및 비중
tickers = {
    "KRW-BTC": 0.80,
    "KRW-XRP": 0.15,
    "KRW-TRX": 0.05
}

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        krw = get_balance("KRW")
        for ticker, ratio in tickers.items():
            start_time = get_start_time(ticker)
            end_time = start_time + datetime.timedelta(days=1)

            if start_time < now < end_time - datetime.timedelta(seconds=10):
                target_price = get_target_price(ticker, 0.5)
                ma15 = get_ma15(ticker)
                current_price = get_current_price(ticker)
                if target_price < current_price and ma15 < current_price:
                    # 투자할 금액 계산 (비율에 따라 자금 분배)
                    invest_amount = krw * ratio * 0.9995  # 수수료 감안
                    if invest_amount > 5000:  # 최소 투자금액 조건
                        upbit.buy_market_order(ticker, invest_amount)
            else:
                symbol = ticker.split("-")[1]  # KRW-BTC에서 'BTC' 추출
                balance = get_balance(symbol)
                if balance > 0.00008:  # 소량 잔고 조건
                    upbit.sell_market_order(ticker, balance * 0.9995)  # 수수료 감안
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
