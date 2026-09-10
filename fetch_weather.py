import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup


def fetch_weather_data():
  data = {}
  data["updated_at"] = datetime.now().strftime("%m.%d %H:%M:%S")

  # 1. Open-Meteo 天気予報データ
  try:
    lat, lon = 34.7658, 134.8437
    meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,wind_speed_10m,precipitation_probability&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,windspeed_10m_max,precipitation_sum&wind_speed_unit=ms&timezone=Asia%2FTokyo"
    res = requests.get(meteo_url, timeout=10)
    if res.status_code == 200:
      data["open_meteo"] = res.json()
  except Exception as e:
    print(f"Open-Meteo fetch error: {e}")

  # 2. 気象庁 天気予報（兵庫県南部）
  try:
    jma_forecast_url = (
        "https://www.jma.go.jp/bosai/forecast/data/forecast/280000.json"
    )
    res = requests.get(jma_forecast_url, timeout=10)
    if res.status_code == 200:
      data["jma_forecast"] = res.json()
  except Exception as e:
    print(f"JMA forecast fetch error: {e}")

  # 3. 気象庁 天気概況（兵庫県）
  try:
    jma_overview_url = (
        "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/280000.json"
    )
    res = requests.get(jma_overview_url, timeout=10)
    if res.status_code == 200:
      data["jma_overview"] = res.json()
  except Exception as e:
    print(f"JMA overview fetch error: {e}")

  # 4. 気象庁 警報・注意報（兵庫県）
  try:
    jma_warning_url = "https://www.jma.go.jp/bosai/warning/data/r8/280000.json"
    res = requests.get(jma_warning_url, timeout=10)
    if res.status_code == 200:
      data["jma_warning"] = res.json()
  except Exception as e:
    print(f"JMA warning fetch error: {e}")

  # 5. Yahoo!路線情報 (JR神戸線運行情報)
  try:
    transit_url = "https://transit.yahoo.co.jp/diainfo/273/0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    res = requests.get(transit_url, headers=headers, timeout=10)
    if res.status_code == 200:
      soup = BeautifulSoup(res.text, "html.parser")
      trouble_element = soup.select_one(
          "#mdServiceStatus .trouble, dd.trouble, #mdServiceStatus"
      )
      if trouble_element:
        data["transit_info"] = trouble_element.get_text(strip=True)
      else:
        data["transit_info"] = "平常運転（または詳細情報を取得できませんでした）"
    else:
      data["transit_info"] = "運行情報の取得に失敗しました"
  except Exception as e:
    print(f"Transit info fetch error: {e}")
    data["transit_info"] = "運行情報の取得に失敗しました"

  # JSONファイルとして出力
  with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

  print("Successfully generated data.json")


if __name__ == "__main__":
  fetch_weather_data()