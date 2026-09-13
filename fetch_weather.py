from datetime import datetime
import json
import requests


def get_weather_severity(code):
  # WMO天気コードを荒天度（0〜4）に分類
  if code in [95, 96, 99]:
    return 4  # 雷雨・嵐
  elif code in [65, 66, 67, 75, 81, 82, 85, 86]:
    return 3  # 強い雨・雪
  elif code in [61, 63, 71, 73, 77, 80]:
    return 2  # 通常の雨・雪
  elif code in [45, 48, 51, 53, 55, 56, 57]:
    return 1  # 霧・小雨
  else:
    return 0  # 晴れ・曇り


def fetch_weather_data():
  data = {}
  jst_now = datetime.now()
  data["updated_at"] = jst_now.strftime("%m.%d %H:%M:%S")

  # 加古川市加古川町稲屋の座標
  lat, lon = 34.75803345356596, 134.8150154875823

  # 1 & 2. Open-Meteo 1時間ごとデータ（3日先まで）＆ 3時間ごとへの集約
  try:
    hourly_url = (
        f"https://api.open-meteo.com/v1/jma?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m,precipitation,wind_speed_10m,pressure_msl,weather_code,precipitation_probability"
        "&wind_speed_unit=ms&timezone=Asia%2FTokyo&forecast_days=3"
    )
    res = requests.get(hourly_url, timeout=10)
    if res.status_code == 200:
      raw_hourly = res.json().get("hourly", {})
      data["hourly_raw"] = raw_hourly

      aggregated_3h = []
      times = raw_hourly.get("time", [])
      temps = raw_hourly.get("temperature_2m", [])
      precips = raw_hourly.get("precipitation", [])
      winds = raw_hourly.get("wind_speed_10m", [])
      pressures = raw_hourly.get("pressure_msl", [])
      weather_codes = raw_hourly.get("weather_code", [])
      pop_list = raw_hourly.get("precipitation_probability", [])

      for i in range(0, len(times), 3):
        chunk_times = times[i : i + 3]
        if not chunk_times:
          break

        chunk_temps = temps[i : i + 3]
        chunk_precips = precips[i : i + 3]
        chunk_winds = winds[i : i + 3]
        chunk_pressures = pressures[i : i + 3]
        chunk_pops = pop_list[i : i + 3] if pop_list else [0] * len(chunk_times)
        chunk_weather = weather_codes[i : i + 3]

        avg_temp = sum(chunk_temps) / len(chunk_temps) if chunk_temps else 0
        max_precip = max(chunk_precips) if chunk_precips else 0
        max_wind = max(chunk_winds) if chunk_winds else 0
        max_pop = max(chunk_pops) if chunk_pops else 0
        min_pressure = min(chunk_pressures) if chunk_pressures else 0
        rep_weather = (
            max(chunk_weather, key=get_weather_severity)
            if chunk_weather
            else 0
        )

        aggregated_3h.append({
            "time": chunk_times[0],
            "temperature": round(avg_temp, 1),
            "precipitation": round(max_precip, 1),
            "wind_speed": round(max_wind, 1),
            "pressure": round(min_pressure, 1),
            "precipitation_probability": max_pop,
            "weather_code": rep_weather,
        })

      data["hourly_3h"] = aggregated_3h
  except Exception as e:
    print(f"Open-Meteo hourly fetch error: {e}")

  # 3. Open-Meteo 1日ごとデータ（10日先まで）
  try:
    daily_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,pressure_msl_mean,wind_speed_10m_max,sunrise,sunset"
        "&wind_speed_unit=ms&timezone=Asia%2FTokyo&forecast_days=10"
    )
    res = requests.get(daily_url, timeout=10)
    if res.status_code == 200:
      data["daily_forecast"] = res.json().get("daily", {})
  except Exception as e:
    print(f"Open-Meteo daily fetch error: {e}")

  # 4. 気象庁 警報・注意報（加古川市エリア判定用）
  try:
    jma_warning_url = "https://www.jma.go.jp/bosai/warning/data/r8/280000.json"
    res = requests.get(jma_warning_url, timeout=10)
    if res.status_code == 200:
      data["jma_warning"] = res.json()
  except Exception as e:
    print(f"JMA warning fetch error: {e}")

  # 5. 運行情報（テストデータに置き換え）
  # 実際のリクエストを行わず、プレビュー用のダミーテキストを格納します
  data["transit_info"] = "【テストデータ】JR神戸線：平常運転"

  # JSONファイルとして出力
  with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

  print("Successfully generated data.json with safe test transit data.")


if __name__ == "__main__":
  fetch_weather_data()