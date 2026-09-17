# 1時間および3時間ごとの気象データを取得し、過去分を除外した上で日付の重複を整理した独自変数を生成するスクリプト

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import json
import time
import requests

# 座標（兵庫県加古川市周辺）
LATITUDE = 34.75803345356596
LONGITUDE = 134.8150154875823
JST = timezone(timedelta(hours=9))

# 曜日の漢字変換用リスト
WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

# 日本語変換マッピング定義
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

WARNING_CODE_LEVELS = {
    "00": 0, "10": 2, "14": 2, "18": 2, "19": 2, "29": 2,
    "02": 3, "03": 3, "04": 3, "05": 3, "06": 3, "07": 3, "08": 3, "09": 3,
    "43": 4, "48": 4, "49": 4,
    "32": 5, "33": 5, "35": 5, "36": 5, "37": 5, "38": 5, "39": 5
}


def get_warning_level(w_code):
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


def get_pressure_risk_level(pressure_diff):
    if pressure_diff <= -5:
        return 3
    elif pressure_diff <= -3:
        return 2
    elif pressure_diff <= -1 or pressure_diff >= 2:
        return 1
    else:
        return 0


def parse_datetime_fields(time_str):
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", ""))
        return {
            "時刻": time_str,
            "年": dt.year,
            "月": f"{dt.month:02d}",
            "日": f"{dt.day:02d}",
            "曜日": WEEKDAYS_JP[dt.weekday()],
            "時": f"{dt.hour:02d}"
        }
    except Exception:
        return {
            "時刻": time_str,
            "年": 0,
            "月": "00",
            "日": "00",
            "曜日": "",
            "時": "00"
        }


# 気象庁データ専用のパーサークラス
class JMAHyogoParser:
    def __init__(self, raw_data):
        self.raw_data = raw_data if isinstance(raw_data, list) else []

    def get_prefecture_headers(self):
        headers = []
        for entry in self.raw_data:
            dt_code = entry.get("dataTypeCode")
            headers.append({
                "制御日時": entry.get("controlDatetime"),
                "発表日時": entry.get("reportDatetime"),
                "情報種別": entry.get("infoType"),
                "発表官署": entry.get("publishingOffice"),
                "見出しテキスト": entry.get("headlineText"),
                "データ型コード": dt_code,
                "データ型名称": DATA_TYPE_NAMES.get(dt_code, "不明な情報")
            })
        return headers

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
                        if status in ("継続", "発表"):
                            w_code = k.get("code")
                            results.append({
                                "データ型コード": dt_code,
                                "データ型名称": dt_code_jp,
                                "エリアコード": item.get("areaCode"),
                                "コード": w_code,
                                "警報注意報名": WARNING_CODE_NAMES.get(w_code, "不明なコード"),
                                "警報レベル": get_warning_level(w_code),
                                "ステータス": status,
                                "付加情報": k.get("additions", [])
                            })
        return results


def fetch_hourly(lat, lon):
    try:
        url = (
            f"https://api.open-meteo.com/v1/jma?latitude={lat}&longitude={lon}"
            "&hourly=temperature_2m,precipitation,wind_speed_10m,pressure_msl,weather_code,precipitation_probability"
            "&wind_speed_unit=ms&timezone=Asia%2FTokyo"
            "&past_days=1"
            "&forecast_days=3"
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

            today_str = datetime.now(JST).strftime("%Y-%m-%d")

            base_1h_list = []
            for i, t in enumerate(times):
                date_part = t.split("T")[0]
                if date_part < today_str:
                    continue

                base_1h_list.append({
                    "time_1h": t,
                    "temperature_1h": temps[i] if i < len(temps) and temps[i] is not None else 0.0,
                    "precipitation_1h": precips[i] if i < len(precips) and precips[i] is not None else 0.0,
                    "wind_speed_1h": winds[i] if i < len(winds) and winds[i] is not None else 0.0,
                    "pressure_1h": pressures[i] if i < len(pressures) and pressures[i] is not None else 0.0,
                    "precipitation_probability_1h": pop_list[i] if i < len(pop_list) and pop_list[i] is not None else 0,
                    "weather_code_1h": weather_codes[i] if i < len(weather_codes) and weather_codes[i] is not None else 0,
                })

            my_weather_1h = []
            for i, item in enumerate(base_1h_list):
                if i > 0:
                    prev_pressure = base_1h_list[i - 1]["pressure_1h"]
                    pressure_diff = round(item["pressure_1h"] - prev_pressure)
                else:
                    pressure_diff = 0

                w_code = item["weather_code_1h"]
                time_str = item["time_1h"]
                dt_fields = parse_datetime_fields(time_str)
                
                is_midnight = (dt_fields["時"] == "00")

                my_weather_1h.append({
                    "時刻": dt_fields["時刻"],
                    "年": dt_fields["年"],
                    "詳細": {
                        "月": dt_fields["月"] if is_midnight else "",
                        "日": dt_fields["日"] if is_midnight else "",
                        "曜日": dt_fields["曜日"] if is_midnight else "",
                        "時": dt_fields["時"],
                        "天気リスク": get_weather_risk_level(w_code),
                        "降水量": round(item["precipitation_1h"]),
                        "気温": round(item["temperature_1h"]),
                        "風速": round(item["wind_speed_1h"]),
                        "気圧変化": get_pressure_risk_level(pressure_diff),
                        "天気コード": w_code,
                    }
                })

            my_weather_3h = []
            for i in range(0, len(my_weather_1h), 3):
                chunk = my_weather_1h[i : i + 3]
                if not chunk:
                    break

                avg_temp = sum(c["詳細"]["気温"] for c in chunk) / len(chunk)
                max_precip = max(c["詳細"]["降水量"] for c in chunk)
                max_wind = max(c["詳細"]["風速"] for c in chunk)
                max_pressure_risk = max(c["詳細"]["気圧変化"] for c in chunk)
                rep_weather = max(chunk, key=lambda x: get_weather_risk_level(x["詳細"]["天気コード"]))["詳細"]["天気コード"]
                max_weather_risk = get_weather_risk_level(rep_weather)

                time_str = base_1h_list[i]["time_1h"]
                dt_fields = parse_datetime_fields(time_str)
                is_midnight_3h = (dt_fields["時"] == "00")

                my_weather_3h.append({
                    "時刻": dt_fields["時刻"],
                    "年": dt_fields["年"],
                    "詳細": {
                        "月": dt_fields["月"] if is_midnight_3h else "",
                        "日": dt_fields["日"] if is_midnight_3h else "",
                        "曜日": dt_fields["曜日"] if is_midnight_3h else "",
                        "時": dt_fields["時"],
                        "天気リスク": max_weather_risk,
                        "降水量": round(max_precip),
                        "気温": round(avg_temp),
                        "風速": round(max_wind),
                        "気圧変化": max_pressure_risk,
                        "天気コード": rep_weather,
                    }
                })

            return {"my_weather_1h": my_weather_1h, "my_weather_3h": my_weather_3h}
    except Exception as e:
        print(f"Open-Meteo hourly fetch error: {e}")
    return {}


def fetch_daily(lat, lon):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,pressure_msl_mean,wind_speed_10m_max"
            "&wind_speed_unit=ms&timezone=Asia%2FTokyo"
            "&past_days=1"
            "&forecast_days=10"
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
            d_wind = daily_raw.get("wind_speed_10m_max", [])

            today_str = datetime.now(JST).strftime("%Y-%m-%d")

            my_weather_1day = []
            for i, t in enumerate(d_times):
                date_part = t.split("T")[0] if "T" in t else t
                if date_part < today_str:
                    continue

                w_code = d_codes[i] if i < len(d_codes) and d_codes[i] is not None else 0
                tmax = d_tmax[i] if i < len(d_tmax) and d_tmax[i] is not None else 0
                tmin = d_tmin[i] if i < len(d_tmin) and d_tmin[i] is not None else 0
                p_sum = d_precip_sum[i] if i < len(d_precip_sum) and d_precip_sum[i] is not None else 0
                p_max = d_pop_max[i] if i < len(d_pop_max) and d_pop_max[i] is not None else 0
                wind = d_wind[i] if i < len(d_wind) and d_wind[i] is not None else 0

                dt_fields = parse_datetime_fields(t)

                # 降水確率の下一桁を四捨五入して調整（例: 23 -> 2）
                pop_val = round(p_max / 10) if isinstance(p_max, (int, float)) else 0

                my_weather_1day.append({
                    "時刻": dt_fields["時刻"],
                    "年": dt_fields["年"],
                    "詳細": {
                        "月": dt_fields["月"],
                        "日": dt_fields["日"],
                        "曜日": dt_fields["曜日"],
                        "時": dt_fields["時"],
                        "天気リスク": get_weather_risk_level(w_code),
                        "降水量": round(p_sum) if isinstance(p_sum, (int, float)) else p_sum,
                        "降水確率": pop_val,
                        "最低気温": round(tmin) if isinstance(tmin, (int, float)) else tmin,
                        "最高気温": round(tmax) if isinstance(tmax, (int, float)) else tmax,
                        "風速": round(wind) if isinstance(wind, (int, float)) else wind,
                        "天気コード": w_code,
                    }
                })
            return {"my_weather_1day": my_weather_1day}
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
                "debug_jma_warning": raw_data,
                "my_jma_warning_hyogo": parser.get_prefecture_headers(),
                "my_jma_warning_nanbu": parser.get_warnings_by_area("280010"),
                "my_jma_warning_hokubu": parser.get_warnings_by_area("280020"),
                "my_jma_warning_kakogawa": parser.get_warnings_by_area("2821000")
            }
        else:
            print(f"JMA warning HTTP error: {res.status_code}")
    except Exception as e:
        print(f"JMA warning fetch error: {e}")

    return {
        "debug_jma_warning": [],
        "my_jma_warning_hyogo": [],
        "my_jma_warning_nanbu": [],
        "my_jma_warning_hokubu": [],
        "my_jma_warning_kakogawa": []
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
    data["my_json_updatetime"] = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Successfully generated data.json in {elapsed_time:.2f} seconds with parallel execution.")


if __name__ == "__main__":
    fetch_weather_data()