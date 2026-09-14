from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import json
import time
import requests

# 座標（兵庫県加古川市周辺など）
LATITUDE = 34.75803345356596
LONGITUDE = 134.8150154875823
JST = timezone(timedelta(hours=9))


def get_weather_risk_level(code):
  if code in [95, 96, 99]:
    return 4
  elif code in [65, 66, 67, 75, 81, 82, 85, 86]:
    return 3
  elif code in [61, 63, 71, 73, 77, 80]:
    return 2
  elif code in [45, 48, 51, 53, 55, 56, 57]:
    return 1
  else:
    return 0


def translate_warning_code(code):
  """気象庁の2桁防災情報コードを解析し、簡潔なレベルと種別を返す"""
  if not code:
    return {"alert_level": 0, "alert_type": "なし"}

  code_str = str(code).zfill(2)
  tens = code_str[0]
  ones = code_str[1]

  # 独自の体系を持つ個別コード
  special_mapping = {
      "10": {"level": 3, "alert_type": "大雨"},
      "14": {"level": 2, "alert_type": "雷・竜巻"},
      "15": {"level": 3, "alert_type": "風"},
      "16": {"level": 3, "alert_type": "波"},
      "48": {"level": 0, "alert_type": "解除"},
  }
  if code_str in special_mapping:
    return special_mapping[code_str]

  # 十の位による警戒レベルの数値化
  level_map = {"4": 4, "3": 5, "2": 2, "0": 3}
  alert_level = level_map.get(tens, 0)

  # 一の位による災害種別の簡易表記
  phenomenon_map = {"3": "大雨", "9": "土砂"}
  phenomenon = phenomenon_map.get(ones, "その他")

  return {
      "alert_level": alert_level,
      "alert_type": f"LV{alert_level} {phenomenon}",
  }


def parse_kinds(kinds_list):
  """kinds リストを走査して alert_level と alert_type を追加する"""
  parsed_kinds = []
  for kind in kinds_list:
    code_val = kind.get("code")
    decoded = translate_warning_code(code_val)

    kind_data = {
        "code": code_val,
        "alert_level": decoded["alert_level"],
        "alert_type": decoded["alert_type"],
        "status": kind.get("status"),
        "properties": kind.get("properties"),
        "significancyPart": kind.get("significancyPart"),
        "criteriaPeriod": kind.get("criteriaPeriod"),
    }
    parsed_kinds.append(kind_data)
  return parsed_kinds


def fetch_hourly(lat, lon):
  try:
    url = (
        f"https://api.open-meteo.com/v1/jma?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m,precipitation,wind_speed_10m,pressure_msl,weather_code,precipitation_probability"
        "&wind_speed_unit=ms&timezone=Asia%2FTokyo&forecast_days=3"
    )
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
      hourly_raw = res.json().get("hourly", {})
      times = hourly_raw.get("time", [])
      temps = hourly_raw.get("temperature_2m", [])
      precips = hourly_raw.get("precipitation", [])
      winds = hourly_raw.get("wind_speed_10m", [])
      pressures = hourly_raw.get("pressure_msl", [])
      weather_codes = hourly_raw.get("weather_code", [])
      pop_list = hourly_raw.get("precipitation_probability", [])

      data_1h_list = []
      for i, t in enumerate(times):
        temp = temps[i] if i < len(temps) and temps[i] is not None else 0.0
        precip = precips[i] if i < len(precips) and precips[i] is not None else 0.0
        wind = winds[i] if i < len(winds) and winds[i] is not None else 0.0
        pressure = pressures[i] if i < len(pressures) and pressures[i] is not None else 0.0
        pop = pop_list[i] if i < len(pop_list) and pop_list[i] is not None else 0
        w_code = weather_codes[i] if i < len(weather_codes) and weather_codes[i] is not None else 0

        data_1h_list.append({
            "time_1h": t,
            "temperature_1h": round(temp),
            "precipitation_1h": round(precip),
            "wind_speed_1h": round(wind),
            "pressure_1h": round(pressure),
            "precipitation_probability_1h": pop,
            "weather_code_1h": w_code,
            "weather_risk_level_1h": get_weather_risk_level(w_code),
        })

      data_3h_list = []
      for i in range(0, len(times), 3):
        chunk_times = times[i : i + 3]
        if not chunk_times:
          break

        chunk_temps = [temps[idx] for idx in range(i, min(i + 3, len(temps))) if temps[idx] is not None] if i < len(temps) else []
        chunk_precips = [precips[idx] for idx in range(i, min(i + 3, len(precips))) if precips[idx] is not None] if i < len(precips) else []
        chunk_winds = [winds[idx] for idx in range(i, min(i + 3, len(winds))) if winds[idx] is not None] if i < len(winds) else []
        chunk_pressures = [pressures[idx] for idx in range(i, min(i + 3, len(pressures))) if pressures[idx] is not None] if i < len(pressures) else []
        chunk_pops = [pop_list[idx] for idx in range(i, min(i + 3, len(pop_list))) if pop_list[idx] is not None] if i < len(pop_list) else []
        chunk_weather = [weather_codes[idx] for idx in range(i, min(i + 3, len(weather_codes))) if weather_codes[idx] is not None] if i < len(weather_codes) else []

        avg_temp = sum(chunk_temps) / len(chunk_temps) if chunk_temps else 0
        max_precip = max(chunk_precips) if chunk_precips else 0
        max_wind = max(chunk_winds) if chunk_winds else 0
        max_pop = max(chunk_pops) if chunk_pops else 0
        min_pressure = min(chunk_pressures) if chunk_pressures else 0
        rep_weather = (
            max(chunk_weather, key=get_weather_risk_level)
            if chunk_weather
            else 0
        )

        data_3h_list.append({
            "time_3h": chunk_times[0],
            "temperature_3h": round(avg_temp),
            "precipitation_3h": round(max_precip),
            "wind_speed_3h": round(max_wind),
            "pressure_3h": round(min_pressure),
            "precipitation_probability_3h": max_pop,
            "weather_code_3h": rep_weather,
            "weather_risk_level_3h": get_weather_risk_level(rep_weather),
        })

      return {"hourly_1h": data_1h_list, "hourly_3h": data_3h_list}
  except Exception as e:
    print(f"Open-Meteo hourly fetch error: {e}")
  return {}


def fetch_daily(lat, lon):
  try:
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,pressure_msl_mean,wind_speed_10m_max,sunrise,sunset"
        "&wind_speed_unit=ms&timezone=Asia%2FTokyo&forecast_days=10"
    )
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
      daily_raw = res.json().get("daily", {})
      d_times = daily_raw.get("time", [])
      d_codes = daily_raw.get("weather_code", [])
      d_tmax = daily_raw.get("temperature_2m_max", [])
      d_tmin = daily_raw.get("temperature_2m_min", [])
      d_precip_sum = daily_raw.get("precipitation_sum", [])
      d_pop_max = daily_raw.get("precipitation_probability_max", [])
      d_pressure = daily_raw.get("pressure_msl_mean", [])
      d_wind = daily_raw.get("wind_speed_10m_max", [])
      d_sunrise = daily_raw.get("sunrise", [])
      d_sunset = daily_raw.get("sunset", [])

      data_1day_list = []
      for i, t in enumerate(d_times):
        w_code = d_codes[i] if i < len(d_codes) and d_codes[i] is not None else 0
        tmax = d_tmax[i] if i < len(d_tmax) and d_tmax[i] is not None else 0
        tmin = d_tmin[i] if i < len(d_tmin) and d_tmin[i] is not None else 0
        p_sum = d_precip_sum[i] if i < len(d_precip_sum) and d_precip_sum[i] is not None else 0
        p_max = d_pop_max[i] if i < len(d_pop_max) and d_pop_max[i] is not None else 0
        pres = d_pressure[i] if i < len(d_pressure) and d_pressure[i] is not None else 0
        wind = d_wind[i] if i < len(d_wind) and d_wind[i] is not None else 0
        sr = d_sunrise[i] if i < len(d_sunrise) and d_sunrise[i] is not None else ""
        ss = d_sunset[i] if i < len(d_sunset) and d_sunset[i] is not None else ""

        data_1day_list.append({
            "time_1day": t,
            "temperature_max_1day": (
                round(tmax) if isinstance(tmax, (int, float)) else tmax
            ),
            "temperature_min_1day": (
                round(tmin) if isinstance(tmin, (int, float)) else tmin
            ),
            "precipitation_sum_1day": (
                round(p_sum) if isinstance(p_sum, (int, float)) else p_sum
            ),
            "precipitation_probability_max_1day": p_max,
            "pressure_mean_1day": (
                round(pres) if isinstance(pres, (int, float)) else pres
            ),
            "wind_speed_max_1day": (
                round(wind) if isinstance(wind, (int, float)) else wind
            ),
            "weather_code_1day": w_code,
            "weather_risk_level_1day": get_weather_risk_level(w_code),
            "sunrise_1day": sr,
            "sunset_1day": ss,
        })
      return {"daily_1day": data_1day_list}
  except Exception as e:
    print(f"Open-Meteo daily fetch error: {e}")
  return {}


def fetch_jma():
  try:
    url = "https://www.jma.go.jp/bosai/warning/data/r8/280000.json"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    res = requests.get(url, headers=headers, timeout=10)
    print(f"JMA HTTP Status: {res.status_code}")

    if res.status_code == 200:
      data = res.json()
      class10_target_codes = {"280010", "280020"}  # 南部、北部
      class20_target_codes = {"2821000"}           # 加古川市
      extracted_reports = []

      reports = data if isinstance(data, list) else [data]
      for report in reports:
        data_type_code = report.get("dataTypeCode")
        warning_data = report.get("warning", {})
        
        class10_items = warning_data.get("class10Items", [])
        class20_items = warning_data.get("class20Items", [])

        matched_items = []

        # 北部・南部（class10Items）の抽出
        for item in class10_items:
          area_code = str(item.get("areaCode", ""))
          if area_code in class10_target_codes:
            kinds = parse_kinds(item.get("kinds", []))
            matched_items.append({"areaCode": area_code, "level": "class10", "kinds": kinds})

        # 加古川市（class20Items）の抽出
        for item in class20_items:
          area_code = str(item.get("areaCode", ""))
          if area_code in class20_target_codes:
            kinds = parse_kinds(item.get("kinds", []))
            matched_items.append({"areaCode": area_code, "level": "class20", "kinds": kinds})

        extracted_reports.append({
            "control_datetime": report.get("controlDatetime"),
            "report_datetime": report.get("reportDatetime"),
            "info_type": report.get("infoType"),
            "publishing_office": report.get("publishingOffice"),
            "headline_text": report.get("headlineText"),
            "data_type_code": data_type_code,
            "target_area_items": matched_items,
        })

      return {"jma_warning": extracted_reports}
    else:
      print(f"JMA warning HTTP error: {res.status_code}")
  except Exception as e:
    print(f"JMA warning fetch error: {e}")

  return {"jma_warning": []}


def fetch_weather_data():
  start_time = time.time()
  data = {}

  with ThreadPoolExecutor(max_workers=3) as executor:
    future_hourly = executor.submit(fetch_hourly, LATITUDE, LONGITUDE)
    future_daily = executor.submit(fetch_daily, LATITUDE, LONGITUDE)
    future_jma = executor.submit(fetch_jma)

    data.update(future_hourly.result())
    data.update(future_daily.result())
    data.update(future_jma.result())

  elapsed_time = time.time() - start_time

  data["json_updatetime"] = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

  with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

  print(
      f"Successfully generated data.json in {elapsed_time:.2f} seconds with"
      " parallel execution."
  )


if __name__ == "__main__":
  fetch_weather_data()