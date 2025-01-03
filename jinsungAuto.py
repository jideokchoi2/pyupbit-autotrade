import time
import pyupbit
import datetime
import numpy as np
import pandas as pd

access = "your-access"
secret = "your-secret"

def calculate_supertrend(df, period=10, multiplier=3):
    """SuperTrend 지표 계산"""
    hl2 = (df['high'] + df['low']) / 2
    atr = pd.DataFrame()
    atr['tr0'] = abs(df['high'] - df['low'])
    atr['tr1'] = abs(df['high'] - df['close'].shift())
    atr['tr2'] = abs(df['low'] - df['close'].shift())
    atr['tr'] = atr[['tr0', 'tr1', 'tr2']].max(axis=1)
    atr['atr'] = atr['tr'].rolling(period).mean()

    upperband = hl2 + (multiplier * atr['atr'])
    lowerband = hl2 - (multiplier * atr['atr'])
    
    supertrend = pd.Series(index=df.index)
    direction = pd.Series(index=df.index)
    
    for i in range(period, len(df)):
        if df['close'][i] > upperband[i-1]:
            direction.iloc[i] = 1
        elif df['close'][i] < lowerband[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]
            
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lowerband[i]
        else:
            supertrend.iloc[i] = upperband[i]
    
    return supertrend, direction

def calculate_macd(df, fast=12, slow=26, signal=9):
    """MACD 지표 계산"""
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def get_trading_signal(ticker):
    """매매 신호 계산"""
    try:
        # 최근 100개의 데이터 조회
        df = pyupbit.get_ohlcv(ticker, interval="day", count=100)
        
        # 지표 계산
        _, st_direction = calculate_supertrend(df)
        _, _, histogram = calculate_macd(df)
        
        # 변동성 계산
        df['tr'] = pd.DataFrame({
            'tr1': abs(df['high'] - df['low']),
            'tr2': abs(df['high'] - df['close'].shift(1)),
            'tr3': abs(df['low'] - df['close'].shift(1))
        }).max(axis=1)
        df['atr'] = df['tr'].rolling(window=14).mean()
        df['volatility'] = df['atr'] / df['close']
        
        # 최신 신호 확인
        current_direction = st_direction.iloc[-1]
        current_histogram = histogram.iloc[-1]
        prev_histogram = histogram.iloc[-2]
        current_volatility = df['volatility'].iloc[-1]
        
        # 포지션 사이징 (변동성 기반)
        position_size = max(0.2, 1 - current_volatility * 10)  # 20%~100% 사이
        
        # 매수 신호: SuperTrend 상승 + MACD 골든크로스
        if current_direction == 1 and current_histogram > 0 and prev_histogram <= 0:
            return "BUY", position_size
        
        # 매도 신호: SuperTrend 하락 또는 MACD 데드크로스
        elif (current_direction == -1 or 
              (current_histogram < 0 and prev_histogram >= 0)):
            return "SELL", position_size
            
        return "HOLD", position_size
        
    except Exception as e:
        print(f"신호 계산 중 에러 발생: {e}")
        return "ERROR", 0

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
        
        # 매시간 정각에 신호 체크
        if now.minute == 0 and now.second == 0:
            signal, position_size = get_trading_signal("KRW-BTC")
            current_price = get_current_price("KRW-BTC")
            
            if signal == "BUY":
                # 현재 보유 중인 BTC가 없을 때만 매수
                btc = get_balance("BTC")
                if btc < 0.00008:  # 최소 거래량 체크
                    krw = get_balance("KRW")
                    if krw > 5000:  # 최소 주문 금액 체크
                        # position_size만큼만 매수
                        order_amount = krw * position_size * 0.9995  # 수수료 고려
                        upbit.buy_market_order("KRW-BTC", order_amount)
                        print(f"{now}: BTC 매수 - 금액: {order_amount:,.0f}원")
                        
            elif signal == "SELL":
                # 보유 중인 BTC가 있을 때만 매도
                btc = get_balance("BTC")
                if btc > 0.00008:
                    upbit.sell_market_order("KRW-BTC", btc * 0.9995)
                    print(f"{now}: BTC 매도 - 수량: {btc:.8f}")
            
        # 1초 대기
        time.sleep(1)
        
    except Exception as e:
        print(f"에러 발생: {e}")
        time.sleep(1)
