from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import json
import time
import requests

# 座標（兵庫県加古川市周辺など）
LATITUDE = 34.75803345356596
LONGITUDE = 134.8150154875823
JST = timezone(timedelta(hours=9))

# ==========================================
# 日本語変換マッピング定義
# ==========================================
DATA_TYPE_NAMES = {
    "VPWW55": "大雨警報・注意報", "VPWW56": "土砂災害警報・注意報",
    "VPWW57": "高潮警報・注意報", "VPWW58": "暴風雪警報・注意報",
    "VPWW59": "波浪警報・注意報", "VPWW60": "大雪警報・注意報",
    "VPWW61": "その他の注意報", "VPFD61": "早期注意情報",
    "VPWP50": "警戒・注意事項時系列", "VPWS50": "警戒・注意事項集約定時通報",
    "VXKOii": "指定河川洪水予報(氾濫警報・注意報)"
}

WARNING_CODE_NAMES = {
    "00": "解除", "02": "暴風雪警報", "03": "大雨警報", "04": "洪水警報",
    "05": "暴風警報", "06": "大雪警報", "07": "波浪警報", "08": "高潮警報",
    "09": "土砂災害警報", "10": "大雨注意報", "12": "大雪注意報",
    "13": "風雪注意報", "14": "雷注意報", "15": "強風注意報", "16": "波浪注意報",
    "17": "融雪注意報", "18": "洪水注意報", "19": "高潮注意報", "20": "濃霧注意報",
    "21": "乾燥注意報", "22": "なだれ注意報", "23": "低温注意報", "24": "霜注意報",
    "25": "着氷注意報", "26": "着雪注意報", "27": "そのほかの注意報", "29": "土砂災害注意報",
    "32": "暴風雪特別警報", "33": "大雨特別警報", "35": "暴風特別警報",
    "36": "大雪特別警報", "37": "波浪特別警報", "38": "高潮特別警報",
    "39": "土砂災害特別警報", "43": "大雨危険警報",
    "48": "高潮危険警報", "49": "土砂災害危険警報"
}

# 警戒レベルの明示的定義（レベル2〜5、および解除）
WARNING_CODE_LEVELS = {
    "00": 0,    # 解除
    
    # レベル2（注意報）
    "10": 2,    # 大雨注意報
    "14": 2,    # 雷注意報
    "18": 2,    # 洪水注意報
    "19": 2,    # 高潮注意報
    "29": 2,    # 土砂災害注意報
    
    # レベル3（警報）
    "02": 3, "03": 3, "04": 3, "05": 3, 
    "06": 3, "07": 3, "08": 3, "09": 3,
    
    # レベル4（危険警報）
    "43": 4, "48": 4, "49": 4,
    
    # レベル5（特別警報）
    "32": 5, "33": 5, "35": 5, "36": 5, 
    "37": 5, "38": 5, "39": 5
}


def get_warning_level(w_code):
    """
    警報コードから警戒レベルを判定する
    """
    if not w_code:
        return None
    if w_code in WARNING_CODE_LEVELS:
        return WARNING_CODE_LEVELS[w_code]
    return 1


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


# ==========================================
# 気象庁データ専用の軽量パーサークラス
# ==========================================
class JMAHyogoParser:
    def __init__(self, raw_data):
        self.raw_data = raw_data if isinstance(raw_data, list) else []

    # 1. 県全体のヘッドライン・メタ情報抽出（headlineText あり）
    def get_prefecture_headers(self):
        headers = []
        for entry in self.raw_data:
            dt_code = entry.get("dataTypeCode")
            headers.append({
                "controlDatetime": entry.get("controlDatetime"),
                "reportDatetime": entry.get("reportDatetime"),
                "infoType": entry.get("infoType"),
                "publishingOffice": entry.get("publishingOffice"),
                "headlineText": entry.get("headlineText"),
                "dataTypeCode": dt_code,
                "dataTypeCode_jp": DATA_TYPE_NAMES.get(dt_code, "不明な情報")
            })
        return headers

    # 2. 指定エリアコードのフラット抽出（status が "継続" または "発表" のものを対象に取得）
    def get_warnings_by_area(self, target_area_code):
        results = []
        for entry in self.raw_data:
            dt_code = entry.get("dataTypeCode")
            dt_code_jp = DATA_TYPE_NAMES.get(dt_code, "不明な情報")
            
            warning_data = entry.get("warning", {})
            if not isinstance(warning_data, dict):
                continue

            for items in warning_data.values():
                if not isinstance(items, list):
                    continue
                
                for item in items:
                    if item.get("areaCode") != target_area_code:
                        continue
                        
                    for k in item.get("kinds", []):
                        status = k.get("status")
                        
                        # "継続" または "発表" の場合のみデータを取得
                        if status in ("継続", "発表"):
                            w_code = k.get("code")
                            results.append({
                                "dataTypeCode": dt_code,
                                "dataTypeCode_jp": dt_code_jp,
                                "areaCode": item.get("areaCode"),
                                "code": w_code,
                                "code_jp": WARNING_CODE_NAMES.get(w_code, "不明なコード"),
                                "code_lv": get_warning_level(w_code),
                                "status": status,
                                "additions": k.get("additions", [])
                            })
        return results


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
                rep_weather = max(chunk_weather, key=get_weather_risk_level) if chunk_weather else 0

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
                    "temperature_max_1day": round(tmax) if isinstance(tmax, (int, float)) else tmax,
                    "temperature_min_1day": round(tmin) if isinstance(tmin, (int, float)) else tmin,
                    "precipitation_sum_1day": round(p_sum) if isinstance(p_sum, (int, float)) else p_sum,
                    "precipitation_probability_max_1day": p_max,
                    "pressure_mean_1day": round(pres) if isinstance(pres, (int, float)) else pres,
                    "wind_speed_max_1day": round(wind) if isinstance(wind, (int, float)) else wind,
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
        print(f"JMA HTTP Status: {res.status_code}")

        if res.status_code == 200:
            raw_data = res.json()
            parser = JMAHyogoParser(raw_data)

            return {
                "jma_warning": raw_data,
                "jma_warning_hyogo": parser.get_prefecture_headers(),
                "jma_warning_nanbu": parser.get_warnings_by_area("280010"),   # 南部
                "jma_warning_hokubu": parser.get_warnings_by_area("280020"),  # 北部
                "jma_warning_kakogawa": parser.get_warnings_by_area("2821000") # 加古川市
            }
        else:
            print(f"JMA warning HTTP error: {res.status_code}")
    except Exception as e:
        print(f"JMA warning fetch error: {e}")

    return {
        "jma_warning": [],
        "jma_warning_hyogo": [],
        "jma_warning_nanbu": [],
        "jma_warning_hokubu": [],
        "jma_warning_kakogawa": []
    }


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

    print(f"Successfully generated data.json in {elapsed_time:.2f} seconds with parallel execution.")


if __name__ == "__main__":
    fetch_weather_data()