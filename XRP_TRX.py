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

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        # TRX 거래 로직
        start_time_trx = get_start_time("KRW-TRX")
        end_time_trx = start_time_trx + datetime.timedelta(days=1)

        if start_time_trx < now < end_time_trx - datetime.timedelta(seconds=10):
            target_price_trx = get_target_price("KRW-TRX", 0.5)
            ma15_trx = get_ma15("KRW-TRX")
            current_price_trx = get_current_price("KRW-TRX")
            if target_price_trx < current_price_trx and ma15_trx < current_price_trx:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-TRX", krw*0.49975)  # 50%로 비율 조정
        else:
            trx = get_balance("TRX")
            if trx > 0.00008:
                upbit.sell_market_order("KRW-TRX", trx*0.9995)

        # XRP 거래 로직
        start_time_xrp = get_start_time("KRW-XRP")
        end_time_xrp = start_time_xrp + datetime.timedelta(days=1)

        if start_time_xrp < now < end_time_xrp - datetime.timedelta(seconds=10):
            target_price_xrp = get_target_price("KRW-XRP", 0.5)
            ma15_xrp = get_ma15("KRW-XRP")
            current_price_xrp = get_current_price("KRW-XRP")
            if target_price_xrp < current_price_xrp and ma15_xrp < current_price_xrp:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-XRP", krw*0.49975)  # 50%로 비율 조정
        else:
            xrp = get_balance("XRP")
            if xrp > 0.00008:
                upbit.sell_market_order("KRW-XRP", xrp*0.9995)

        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
