document.addEventListener('DOMContentLoaded', () => {
    // ページ切り替え用ロジック（4ページ対応）
    const pages = document.querySelectorAll('.page-section');
    const navBtn = document.getElementById('nav-btn');
    let currentPageIndex = 0;

    const pageTitles = ["ページ2へ", "ページ3へ", "ページ4へ", "ページ1へ（最初に戻る）"];

    if (navBtn) {
        navBtn.addEventListener('click', () => {
            pages[currentPageIndex].classList.remove('active');
            currentPageIndex = (currentPageIndex + 1) % pages.length;
            pages[currentPageIndex].classList.add('active');
            navBtn.textContent = pageTitles[currentPageIndex];
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // 気象データ読み込みとDOMへの反映
    // （実際の運用では fetch('data_3.json') などに置き換えてください）
    const weatherData = {
        "updated_at": "2026-09-13 06:20:00",
        "transit_info": "【テストデータ】JR神戸線：平常運転",
        "overview": "現在の気温は 24.9°C、天候は晴れ。南部では強風や高波に注意してください。",
        "daily_forecast": {
            "time": ["2026-09-13", "2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17", "2026-09-18", "2026-09-19", "2026-09-20", "2026-09-21", "2026-09-22"],
            "weather_code": [51, 63, 63, 51, 1, 1, 2, 3, 61, 1],
            "temperature_2m_max": [29.3, 29.2, 24.8, 28.3, 29.0, 28.5, 27.2, 26.8, 25.5, 27.0],
            "temperature_2m_min": [23.5, 22.2, 21.4, 21.2, 20.5, 21.0, 19.8, 19.2, 18.5, 19.0],
            "precipitation_sum": [0.2, 4.8, 44.3, 0.1, 0.0, 0.0, 1.2, 5.0, 12.0, 0.0],
            "precipitation_probability_max": [84, 96, 73, 39, 10, 20, 40, 60, 85, 15],
            "wind_speed_10m_max": [3.9, 4.1, 4.07, 5.3, 3.5, 3.8, 4.2, 4.5, 5.0, 3.2]
        },
        "hourly_raw": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00", "2026-09-13T06:00"],
            "temperature_2m": [24.9, 24.4, 24.1, 23.8, 24.5],
            "precipitation": [0.0, 0.0, 0.0, 0.0, 0.0],
            "wind_speed_10m": [1.44, 0.94, 0.89, 1.10, 1.50],
            "weather_code": [1, 1, 1, 1, 1]
        },
        "jma_warning": {
            "kakogawa": "現在、加古川市に発表されている警報・注意報はありません（平常通り）。",
            "hyogo_general": "兵庫県南部では強風や高波に注意してください。全域で急な強い雨や落雷に注意。"
        }
    };

    // 1. 更新日時の反映
    const nowStr = new Date().toLocaleString('ja-JP');
    document.querySelectorAll('.page-update-time').forEach(el => el.textContent = nowStr);
    const sourceTimeElems = document.querySelectorAll('#source-update-time-1, #source-update-time-2');
    sourceTimeElems.forEach(el => el.textContent = weatherData.updated_at);

    // 2. ページ1: 概要・交通情報・3日天気（時系列）の描画
    const overviewContainer = document.getElementById('overview-container');
    if (overviewContainer) overviewContainer.textContent = weatherData.overview;

    const transitContainer = document.getElementById('transit-container');
    if (transitContainer) transitContainer.textContent = weatherData.transit_info;

    const forecastTable1Body = document.querySelector('#forecast-table-1 tbody');
    if (forecastTable1Body) {
        forecastTable1Body.innerHTML = '';
        const hourly = weatherData.hourly_raw;
        for (let i = 0; i < hourly.time.length; i++) {
            const dateParts = hourly.time[i].split('T');
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${dateParts[0]}</td>
                <td>${dateParts[1]}</td>
                <td>${hourly.temperature_2m[i]} ℃</td>
                <td>${hourly.wind_speed_10m[i]} m/s</td>
                <td>-</td>
                <td>${hourly.precipitation[i]} mm</td>
            `;
            forecastTable1Body.appendChild(tr);
        }
    }

    // 3. ページ2: 10日間週間予報テーブルの描画
    const table10DaysBody = document.querySelector('#forecast-table-10days tbody');
    if (table10DaysBody) {
        table10DaysBody.innerHTML = '';
        const daily = weatherData.daily_forecast;
        for (let i = 0; i < daily.time.length; i++) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${daily.time[i]}</td>
                <td>${daily.weather_code[i]}</td>
                <td>${daily.temperature_2m_min[i]}</td>
                <td>${daily.temperature_2m_max[i]}</td>
                <td>${daily.wind_speed_10m_max[i]}</td>
                <td>${daily.precipitation_probability_max[i]}</td>
                <td>${daily.precipitation_sum[i]}</td>
            `;
            table10DaysBody.appendChild(tr);
        }
    }

    // 4. ページ3: 警報・注意報情報の描画
    const kakogawaWarning = document.getElementById('kakogawa-warning-container');
    if (kakogawaWarning) kakogawaWarning.textContent = weatherData.jma_warning.kakogawa;

    const hyogoWarning = document.getElementById('hyogo-warning-container');
    if (hyogoWarning) hyogoWarning.textContent = weatherData.jma_warning.hyogo_general;

    const alertMapContainer = document.getElementById('alert-map-container');
    if (alertMapContainer) {
        alertMapContainer.innerHTML = `
            <div style="padding: 8px; background: #fff3cd; border: 1px solid #ffeeba; border-radius: 4px;">
                <strong>神戸地方気象台エリア:</strong> 強風注意報、高波注意報発令中
            </div>
        `;
    }
});