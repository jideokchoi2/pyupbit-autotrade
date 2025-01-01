import time
import pyupbit
import datetime

access = ""  # 여기에 자신의 access key를 입력하세요
secret = ""  # 여기에 자신의 secret key를 입력하세요

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
    if df is None:
        print(f"Error: {ticker}의 OHLCV 데이터를 가져올 수 없습니다.")
        return None
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

# 시작 시간 조회
def get_start_time(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    if df is None or df.empty:
        print(f"Error: {ticker}의 시작 시간을 가져올 수 없습니다.")
        return None
    start_time = df.index[0]
    return start_time

# 잔고 조회
def get_balance(ticker):
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker.replace("KRW-", ""):
            if b['balance'] is not None:
                return float(b['balance'])
    return 0

# 현재가 조회
def get_current_price(ticker):
    orderbook = pyupbit.get_orderbook(ticker=ticker)
    if orderbook is None:
        print(f"Error: {ticker}의 현재가 데이터를 가져올 수 없습니다.")
        return None
    return orderbook["orderbook_units"][0]["ask_price"]

# 추적 손절매 가격 업데이트
def update_trailing_stop(ticker, current_price):
    global trailing_stop
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    if df is None:
        return
    atr = df.iloc[0]['high'] - df.iloc[0]['low']  # 변동폭 계산
    atr_multiplier = 0.8  # 손절매 비율 조정
    trailing_stop[ticker] = max(trailing_stop[ticker], current_price - atr * atr_multiplier)
    print(f"[DEBUG] {ticker} - 손절매 기준 갱신: {trailing_stop[ticker]} (현재가: {current_price})")

# 로그인
try:
    upbit = pyupbit.Upbit(access, secret)
    print("Upbit API 연결 성공")
except Exception as e:
    print("Upbit API 연결 실패:", e)
    exit()

print("autotrade start")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        for ticker, ratio in allocation.items():
            start_time = get_start_time(ticker)
            if start_time is None:
                continue
            end_time = start_time + datetime.timedelta(days=1)

            if start_time < now < end_time - datetime.timedelta(seconds=10):
                target_price = get_target_price(ticker, 0.5)
                if target_price is None:
                    continue
                current_price = get_current_price(ticker)
                if current_price is None:
                    continue

                # 매수 조건 확인
                if target_price < current_price:
                    krw = get_balance("KRW")
                    if krw > 5000:
                        print(f"{ticker} 매수 시도: {krw * ratio * 0.9995} KRW")
                        upbit.buy_market_order(ticker, krw * ratio * 0.9995)
            else:
                # 손절매 조건 확인
                current_price = get_current_price(ticker)
                if current_price is None:
                    continue
                if current_price < trailing_stop[ticker]:
                    coin_balance = get_balance(ticker.replace("KRW-", ""))
                    if coin_balance > 0:
                        print(f"{ticker}: 손절매 실행 - 현재가: {current_price}, 손절매 기준: {trailing_stop[ticker]}")
                        upbit.sell_market_order(ticker, coin_balance * 0.9995)
                else:
                    update_trailing_stop(ticker, current_price)

            time.sleep(0.2)  # 각 티커 처리 후 대기

        time.sleep(1)  # 전체 루프 종료 후 추가 대기
    except Exception as e:
        if "요청 수 제한" in str(e):
            print("요청 수 제한에 걸렸습니다. 1초 대기합니다...")
            time.sleep(1)  # 요청 제한 초과 시 대기
        else:
            print(f"예외 발생: {e}")
        time.sleep(1)
