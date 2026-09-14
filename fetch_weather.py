"""
【変数名の命名規則】
- すべての変数名および辞書キーはハイフンではなくアンダースコア（_）で結合する。
- 時間の粒度を表すサフィックスを明確に付与する：
  - 1時間ごとのデータ・項目: _1h
  - 3時間ごとのデータ・項目: _3h
  - 1日ごとのデータ・項目: _1day
- グループ名と粒度を統一し、エディタの補完やデータアクセスの視認性を最適化する。
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import json
import subprocess
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
        temp = temps[i] if i < len(temps) else 0
        precip = precips[i] if i < len(precips) else 0
        wind = winds[i] if i < len(winds) else 0
        pressure = pressures[i] if i < len(pressures) else 0
        pop = pop_list[i] if i < len(pop_list) else 0
        w_code = weather_codes[i] if i < len(weather_codes) else 0

        data_1h_list.append({
            "time_1h": t,
            "temperature_1h": round(temp, 1),
            "precipitation_1h": round(precip, 1),
            "wind_speed_1h": round(wind, 1),
            "pressure_1h": round(pressure, 1),
            "precipitation_probability_1h": pop,
            "weather_code_1h": w_code,
            "weather_risk_level_1h": get_weather_risk_level(w_code),
        })

      data_3h_list = []
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
            max(chunk_weather, key=get_weather_risk_level)
            if chunk_weather
            else 0
        )

        data_3h_list.append({
            "time_3h": chunk_times[0],
            "temperature_3h": round(avg_temp, 1),
            "precipitation_3h": round(max_precip, 1),
            "wind_speed_3h": round(max_wind, 1),
            "pressure_3h": round(min_pressure, 1),
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
        w_code = d_codes[i] if i < len(d_codes) else 0
        tmax = d_tmax[i] if i < len(d_tmax) else 0
        tmin = d_tmin[i] if i < len(d_tmin) else 0
        p_sum = d_precip_sum[i] if i < len(d_precip_sum) else 0
        p_max = d_pop_max[i] if i < len(d_pop_max) else 0
        pres = d_pressure[i] if i < len(d_pressure) else 0
        wind = d_wind[i] if i < len(d_wind) else 0
        sr = d_sunrise[i] if i < len(d_sunrise) else ""
        ss = d_sunset[i] if i < len(d_sunset) else ""

        data_1day_list.append({
            "time_1day": t,
            "temperature_max_1day": (
                round(tmax, 1) if isinstance(tmax, (int, float)) else tmax
            ),
            "temperature_min_1day": (
                round(tmin, 1) if isinstance(tmin, (int, float)) else tmin
            ),
            "precipitation_sum_1day": (
                round(p_sum, 1) if isinstance(p_sum, (int, float)) else p_sum
            ),
            "precipitation_probability_max_1day": p_max,
            "pressure_mean_1day": (
                round(pres, 1) if isinstance(pres, (int, float)) else pres
            ),
            "wind_speed_max_1day": (
                round(wind, 1) if isinstance(wind, (int, float)) else wind
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
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
      return {"jma_warning": res.json()}
  except Exception as e:
    print(f"JMA warning fetch error: {e}")
  return {}


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

  # 実行環境のタイムゾーンに依存せず確実に日本時間（JST）で記録
  data["json_updatetime"] = datetime.now(JST).strftime("%m.%d %H:%M:%S")

  with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

  print(
      f"Successfully generated data.json in {elapsed_time:.2f} seconds with"
      " parallel execution."
  )

  # Git操作＆コミットメッセージに反映
  try:
    commit_message = f"Update weather data, create time {elapsed_time:.2f}s"
    subprocess.run(
        ["git", "config", "--local", "user.name", "github-actions[bot]"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "config",
            "--local",
            "user.email",
            "github-actions[bot]@users.noreply.github.com",
        ],
        check=True,
    )
    subprocess.run(["git", "add", "data.json"], check=True)

    diff_check = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], capture_output=True
    )
    if diff_check.returncode != 0:
      subprocess.run(["git", "commit", "-m", commit_message], check=True)
      subprocess.run(["git", "push"], check=True)
      print(f"Successfully committed with message: '{commit_message}'")
    else:
      print("No changes to commit.")
  except Exception as e:
    print(f"Git commit/push error: {e}")


if __name__ == "__main__":
  fetch_weather_data()