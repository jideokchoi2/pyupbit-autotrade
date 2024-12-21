import os
from dotenv import load_dotenv
import python_bithumb
import json
from openai import OpenAI
import time
import re

# 환경 변수 로드
load_dotenv()

# Gemini API Key 및 Base URL
API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/"

# OpenAI Library 초기화 (Gemini API 활용)
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 코인별 매매 비율 설정 (KRW 비율)
COIN_RATIOS = {
    "KRW-BTC": 0.4,  # 40% 비트코인
    "KRW-DOGE": 0.2, # 20% 도지코인
    "KRW-TRX": 0.2,  # 20% 트론
    "KRW-XRP": 0.2   # 20% 리플
}

def ai_trading():
    try:
        decisions = {}

        for coin, ratio in COIN_RATIOS.items():
            # 1. 빗썸 차트 데이터 가져오기 (30일 일봉)
            df = python_bithumb.get_ohlcv(coin, interval="day", count=30)

            # 2. Gemini API를 통해 데이터 제공 및 판단 요청
            response = client.chat.completions.create(
                model="gemini-1.5-flash",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert in Bitcoin investing. "
                            "Tell me whether to buy, sell, or hold at the moment based on the chart data provided. "
                            "Response in JSON format.\n\n"
                            "Response Example:\n"
                            "{\"decision\": \"buy\", \"reason\": \"some technical reason\"}\n"
                            "{\"decision\": \"sell\", \"reason\": \"some technical reason\"}\n"
                            "{\"decision\": \"hold\", \"reason\": \"some technical reason\"}"
                        )
                    },
                    {
                        "role": "user",
                        "content": df.to_json()
                    }
                ]
            )

            # AI 판단 결과 처리
            raw_result = response.choices[0].message.content

            # JSON 데이터만 추출
            json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                decisions[coin] = result
            else:
                raise ValueError(f"JSON response could not be extracted for {coin}.")

        # 빗썸 API 초기화
        access = os.getenv("BITHUMB_ACCESS_KEY")
        secret = os.getenv("BITHUMB_SECRET_KEY")
        bithumb = python_bithumb.Bithumb(access, secret)

        # 전체 잔액 확인
        my_krw = bithumb.get_balance("KRW")

        for coin, decision in decisions.items():
            print(f"### AI Decision for {coin}: {decision['decision'].upper()} ###")
            print(f"### Reason: {decision['reason']} ###")

            if decision["decision"] == "buy":
                amount_to_invest = my_krw * COIN_RATIOS[coin]
                if amount_to_invest > 5000:
                    print(f"### Buy Order Executed for {coin} ###")
                    bithumb.buy_market_order(coin, amount_to_invest * 0.997)
                else:
                    print(f"### Buy Order Failed for {coin}: Insufficient KRW (less than 5000 KRW) ###")

            elif decision["decision"] == "sell":
                my_coin_balance = bithumb.get_balance(coin.split("-")[1])
                current_price = python_bithumb.get_current_price(coin)
                if my_coin_balance * current_price > 5000:
                    print(f"### Sell Order Executed for {coin} ###")
                    bithumb.sell_market_order(coin, my_coin_balance)
                else:
                    print(f"### Sell Order Failed for {coin}: Insufficient {coin.split('-')[1]} (less than 5000 KRW worth) ###")

            elif decision["decision"] == "hold":
                print(f"### Hold Position for {coin} ###")

    except Exception as e:
        print("### Error Occurred: ", str(e), "###")

# 반복 실행
while True:
    time.sleep(160)
    ai_trading()
