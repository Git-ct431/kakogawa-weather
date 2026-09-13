let currentPage = 1;
const totalPages = 4;

function switchPage() {
    document.getElementById(`page-${currentPage}`).classList.remove('active');
    currentPage = currentPage >= totalPages ? 1 : currentPage + 1;
    document.getElementById(`page-${currentPage}`).classList.add('active');

    const nextTarget = currentPage >= totalPages ? 1 : currentPage + 1;
    document.getElementById('nav-btn').innerText = `ページ${nextTarget}へ`;

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function formatCustomDate(dateObj) {
    const m = String(dateObj.getMonth() + 1).padStart(2, '0');
    const d = String(dateObj.getDate()).padStart(2, '0');
    const h = String(dateObj.getHours()).padStart(2, '0');
    const min = String(dateObj.getMinutes()).padStart(2, '0');
    const s = String(dateObj.getSeconds()).padStart(2, '0');
    return `${m}.${d} ${h}:${min}:${s}`;
}

function formatTwoDigits(val) {
    if (val == null || isNaN(val)) return '--';
    const rounded = Math.round(val);
    return String(rounded).padStart(2, '0');
}

function formatInteger(val) {
    if (val == null || isNaN(val)) return '--';
    return Math.round(val);
}

function formatPopValue(val) {
    if (val == null || isNaN(val)) return '--';
    const rounded = Math.round(val / 10) * 10;
    return Math.min(Math.max(rounded, 0), 100);
}

function convertWeatherCode(code) {
    switch (code) {
        case 0: return '晴れ';
        case 1: case 2: return '晴れ時々曇り';
        case 3: return '曇り';
        case 45: case 48: return '霧';
        case 51: case 53: case 55: case 56: case 57: 
        case 61: case 63: case 65: case 66: case 67: 
        case 80: case 81: case 82: return '雨';
        case 71: case 73: case 75: case 77: case 85: case 86: return '雪';
        case 95: case 96: case 99: return '雷雨';
        default: return '曇り';
    }
}

function getPopBackgroundColor(val) {
    if (val == null || isNaN(val) || val < 40) return 'background-color: #F3F3F3;';
    const ratio = Math.min(Math.max((val - 40) / 60, 0), 1);
    const r = Math.round(222 + (74 - 222) * ratio);
    const g = Math.round(228 + (134 - 228) * ratio);
    const b = Math.round(241 + (232 - 241) * ratio);
    return `background-color: rgb(${r}, ${g}, ${b});`;
}

function getRainBackgroundColor(val) {
    if (val == null || isNaN(val) || val === 0) return 'background-color: #F3F3F3;';
    if (val >= 1 && val <= 9) return 'background-color: #d0e1fd;';
    if (val >= 10 && val <= 19) return 'background-color: #99c2ff;';
    if (val >= 20 && val <= 29) return 'background-color: #6fa8dc;';
    if (val >= 30 && val <= 49) return 'background-color: #ffe599;';
    if (val >= 50 && val <= 79) return 'background-color: #f1c232;';
    if (val >= 80) return 'background-color: #cc0000; color: #fff; font-weight: bold;';
    return 'background-color: #F3F3F3;';
}

function getTempBackgroundColor(val) {
    if (val == null || isNaN(val)) return 'background-color: #F3F3F3;';
    if (val <= 0)   return 'background-color: #6fa8dc;';
    if (val <= 6)   return 'background-color: #a4c2f4;';
    if (val <= 9)   return 'background-color: #cfe2f3;';
    if (val <= 12)  return 'background-color: #d0e1fd;';
    if (val <= 15)  return 'background-color: #d9ead3;';
    if (val <= 18)  return 'background-color: #fce5cd;';
    if (val <= 21)  return 'background-color: #f9cb9c;';
    if (val <= 24)  return 'background-color: #f6b26b;';
    if (val <= 27)  return 'background-color: #e69138;';
    if (val <= 30)  return 'background-color: #c27ba0;';
    if (val <= 33)  return 'background-color: #cc4125;';
    if (val <= 36)  return 'background-color: #e06666; color: #fff; font-weight: bold;';
    if (val <= 39)  return 'background-color: #cc0000; color: #fff; font-weight: bold;';
    if (val >= 40)  return 'background-color: #990000; color: #fff; font-weight: bold;';
    return 'background-color: #F3F3F3;';
}

function getWindBackgroundColor(val) {
    if (val == null || isNaN(val)) return 'background-color: #F3F3F3;';
    const v = Math.round(val);
    if (v <= 4) return 'background-color: #F3F3F3; color: #94a3b8;';
    if (v <= 10) return 'background-color: #d9ead3;';
    if (v <= 15) return 'background-color: #b6d7a8;';
    if (v <= 20) return 'background-color: #ffe599;';
    if (v <= 25) return 'background-color: #e06666; color: #fff; font-weight: bold;';
    if (v <= 30) return 'background-color: #cc4125; color: #fff; font-weight: bold;';
    return 'background-color: #990000; color: #fff; font-weight: bold;';
}

function getWarningName(code) {
    const codeMap = {
        '10': '大雨注意報', '03': '大雨警報', '43': '大雨危険警報', '33': '大雨特別警報',
        '29': '土砂災害注意報', '09': '土砂災害警報', '49': '土砂災害危険警報', '39': '土砂災害特別警報',
        '19': '高潮注意報', '08': '高潮警報', '48': '高潮危険警報', '38': '高潮特別警報',
        '15': '強風注意報', '05': '暴風警報', '35': '暴風特別警報',
        '13': '風雪注意報', '02': '暴風雪警報', '32': '暴風雪特別警報',
        '16': '波浪注意報', '07': '波浪警報', '37': '波浪特別警報',
        '12': '大雪注意報', '06': '大雪警報', '36': '大雪特別警報',
        '17': '融雪注意報', '14': '雷注意報', '20': '濃霧注意報', '21': '乾燥注意報',
        '22': 'なだれ注意報', '23': '低温注意報', '24': '霜注意報', '25': '着氷注意報',
        '26': '着雪注意報', '27': 'その他の注意報'
    };
    return codeMap[code] || `警報(${code})`;
}

function getAlertLevel(code) {
    const specialWarnings = ['33', '43', '39', '49', '38', '48', '32', '37', '36'];
    const warnings = ['03', '09', '08', '05', '02', '07', '06'];
    if (specialWarnings.includes(code)) return '特別警報';
    if (warnings.includes(code)) return '警報';
    return '注意報';
}

function isWarning(code) {
    return getAlertLevel(code) === '警報' || getAlertLevel(code) === '特別警報';
}

function generateTableHtml(hourly3hData, daysCount) {
    if (!hourly3hData || !Array.isArray(hourly3hData)) return '<tr><td colspan="6">データがありません</td></tr>';

    const timeSlots = [0, 3, 6, 9, 12, 15, 18, 21];
    const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
    const now = new Date();
    const currentHour = now.getHours();
    
    let dataByDate = {};
    hourly3hData.forEach(item => {
        const t = new Date(item.time);
        const dateKey = `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`;
        if (!dataByDate[dateKey]) {
            dataByDate[dateKey] = {};
        }
        dataByDate[dateKey][t.getHours()] = item;
    });

    let forecastHtml = '';
    const startDate = new Date();

    for (let dayOffset = 0; dayOffset < daysCount; dayOffset++) {
        const targetDate = new Date(startDate);
        targetDate.setDate(startDate.getDate() + dayOffset);
        
        const m = String(targetDate.getMonth() + 1).padStart(2, '0');
        const d = String(targetDate.getDate()).padStart(2, '0');
        const w = weekdays[targetDate.getDay()];
        const dateKey = `${targetDate.getFullYear()}-${m}-${d}`;
        
        const dayData = dataByDate[dateKey] || {};

        let representativeCode = 3;
        if (dayData[12] && dayData[12].weather_code != null) {
            representativeCode = dayData[12].weather_code;
        } else {
            const firstHour = Object.keys(dayData)[0];
            if (firstHour && dayData[firstHour].weather_code != null) {
                representativeCode = dayData[firstHour].weather_code;
            }
        }
        const weatherText = convertWeatherCode(representativeCode);
        
        let verticalWeatherHtml = '';
        for (let char of weatherText) {
            verticalWeatherHtml += `${char}<br>`;
        }

        const dateStr = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: flex-start;">
                <div style="line-height: 1.1; text-align: center; margin-bottom: 3px;">
                    <span style="color: #64748b; font-size: 0.7rem; font-weight: normal; display: block;">${m}</span>
                    <span style="font-size: 0.95rem; font-weight: bold; display: block;">${d}</span>
                    <span style="font-size: 0.85rem; font-weight: bold; display: block;">${w}</span>
                </div>
                <div style="font-size: 0.8rem; font-weight: normal; line-height: 1.1; text-align: center; color: #475569; letter-spacing: -1px;">${verticalWeatherHtml}</div>
            </div>
        `;

        timeSlots.forEach((slotHour, slotIndex) => {
            const slotItem = dayData[slotHour];

            let avgTemp = slotItem ? slotItem.temperature : null;
            let maxWind = slotItem ? slotItem.wind_speed : null;
            let maxPop = slotItem ? slotItem.precipitation_probability : null;
            let maxRain = slotItem ? slotItem.precipitation : null;

            let tempNum = (avgTemp != null && !isNaN(avgTemp)) ? Math.round(avgTemp) : null;
            let valTemp = formatTwoDigits(avgTemp);
            let tempStyle = getTempBackgroundColor(tempNum);
            if (tempNum === 0) tempStyle += '; color: #94a3b8;';

            let maxWindNum = (maxWind != null && !isNaN(maxWind)) ? maxWind : null;
            let valWind = formatInteger(maxWind);
            let windStyle = getWindBackgroundColor(maxWindNum);
            
            let popNum = formatPopValue(maxPop);
            let valPop = (popNum !== '--') ? String(popNum) : '--';
            let popStyle = getPopBackgroundColor(popNum);
            if (popNum === 0) popStyle += '; color: #94a3b8;';

            let rainNum = (maxRain != null && !isNaN(maxRain)) ? Math.round(maxRain) : null;
            let valRain = formatInteger(maxRain);
            let rainStyle = getRainBackgroundColor(rainNum);
            if (rainNum === 0) rainStyle += '; color: #94a3b8;';

            const isPast = (dayOffset < 0) || (dayOffset === 0 && (slotHour + 2) < currentHour);

            let topBorder = slotIndex === 0 ? '1px solid #707070' : 'none';
            let bottomBorder = slotIndex === timeSlots.length - 1 ? '1px solid #707070' : 'none';

            const rowClass = isPast ? 'past-slot' : '';
            forecastHtml += `<tr class="${rowClass}">`;
            
            if (slotIndex === 0) {
                forecastHtml += `<td class="date-cell" style="border-top: 1px solid #707070; border-bottom: 1px solid #707070; border-left: 1px solid #707070; border-right: 1px solid #dcdcdc;" rowspan="${timeSlots.length}">${dateStr}</td>`;
            }
            
            forecastHtml += `<td style="border-top: ${topBorder}; border-bottom: ${bottomBorder}; border-left: none; border-right: 1px solid #dcdcdc; background-color: #F3F3F3;">${slotHour}</td>`;
            forecastHtml += `<td style="border-top: ${topBorder}; border-bottom: ${bottomBorder}; border-left: none; border-right: 1px solid #dcdcdc; text-align: right; ${tempStyle}">${valTemp}</td>`;
            forecastHtml += `<td style="border-top: ${topBorder}; border-bottom: ${bottomBorder}; border-left: none; border-right: 1px solid #dcdcdc; text-align: right; ${windStyle}">${valWind}</td>`;
            forecastHtml += `<td style="border-top: ${topBorder}; border-bottom: ${bottomBorder}; border-left: none; border-right: 1px solid #dcdcdc; text-align: right; ${popStyle}">${valPop}</td>`;
            forecastHtml += `<td style="border-top: ${topBorder}; border-bottom: ${bottomBorder}; border-left: none; border-right: 1px solid #707070; text-align: right; ${rainStyle}">${valRain}</td>`;
            forecastHtml += `</tr>`;
        });
    }
    return forecastHtml;
}

function generateDailyTableHtml(dailyData) {
    if (!dailyData || !dailyData.time) return '<tr><td colspan="6">データがありません</td></tr>';

    const times = dailyData.time;
    const maxTemps = dailyData.temperature_2m_max;
    const minTemps = dailyData.temperature_2m_min;
    const winds = dailyData.wind_speed_10m_max;
    const pops = dailyData.precipitation_probability_max;
    const rains = dailyData.precipitation_sum;
    const weathercodes = dailyData.weather_code || dailyData.weathercode || [];

    const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
    let html = '';

    for (let i = 0; i < times.length; i++) {
        const targetDate = new Date(times[i]);
        const m = String(targetDate.getMonth() + 1).padStart(2, '0');
        const d = String(targetDate.getDate()).padStart(2, '0');
        const w = weekdays[targetDate.getDay()];

        const weatherText = convertWeatherCode(weathercodes[i]);

        let minT = minTemps[i] != null ? Math.round(minTemps[i]) : null;
        let maxT = maxTemps[i] != null ? Math.round(maxTemps[i]) : null;
        let tempStr = (minT != null && maxT != null) ? `${minT}-${maxT}` : '--';
        
        let tempStyle = getTempBackgroundColor(maxT);
        if (maxT === 0) tempStyle += '; color: #94a3b8;';

        let maxWind = winds[i] != null ? Math.round(winds[i]) : null;
        let valWind = formatInteger(maxWind);
        let windStyle = getWindBackgroundColor(maxWind);

        let maxPopNum = pops[i] != null ? formatPopValue(pops[i]) : null;
        let valPop = (maxPopNum !== '--') ? String(maxPopNum) : '--';
        let popStyle = getPopBackgroundColor(maxPopNum);
        if (maxPopNum === 0) popStyle += '; color: #94a3b8;';

        let rainSum = rains[i] != null ? Math.round(rains[i]) : 0;
        let valRain = formatInteger(rains[i]);
        let rainStyle = getRainBackgroundColor(rainSum);
        if (rainSum === 0) rainStyle += '; color: #94a3b8;';

        html += `
            <tr>
                <td style="background-color: #F3F3F3; font-weight: bold; white-space: nowrap;">${m}.${d} ${w}</td>
                <td style="background-color: #F3F3F3;">${weatherText}</td>
                <td style="text-align: right; ${tempStr !== '--' ? tempStyle : ''}">${tempStr}</td>
                <td style="text-align: right; ${windStyle}">${valWind}</td>
                <td style="text-align: right; ${popStyle}">${valPop}</td>
                <td style="text-align: right; ${rainStyle}">${valRain}</td>
            </tr>
        `;
    }
    return html;
}

async function fetchDashboardData() {
    try {
        const response = await fetch('./data.json?t=' + new Date().getTime());
        if (!response.ok) throw new Error("data.jsonの読み込みに失敗しました");
        const data = await response.json();

        const sourceUpdateTime = data.updated_at || '--';
        const pageUpdateTime = formatCustomDate(new Date());

        document.getElementById('page-update-time-1').innerText = pageUpdateTime;
        document.getElementById('page-update-time-2').innerText = pageUpdateTime;
        document.getElementById('page-update-time-3').innerText = pageUpdateTime;
        document.getElementById('page-update-time-4').innerText = pageUpdateTime;

        document.getElementById('source-update-time-1').innerText = sourceUpdateTime;
        document.getElementById('source-update-time-2').innerText = sourceUpdateTime;

        const transitContainer = document.getElementById('transit-container');
        if (data.transit_info) {
            let statusText = data.transit_info;
            transitContainer.innerHTML = `<div>${statusText}</div> <div style="font-size: 0.8rem; color: #1d4ed8; text-align: right; margin-top: 4px;">詳細 ↗</div>`;
        } else {
            transitContainer.innerHTML = `<div>平常運転</div> <div style="font-size: 0.8rem; color: #1d4ed8; text-align: right; margin-top: 4px;">詳細 ↗</div>`;
        }

        if (data.jma_warning) {
            const warnArray = data.jma_warning;
            let hyogoWarnings = new Set();
            let hyogoAdvisories = new Set();
            let kakogawaWarnings = [];
            let kakogawaAdvisories = [];
            let areaAlerts = {};

            warnArray.forEach(report => {
                if (report.warning && report.warning.class20Items) {
                    report.warning.class20Items.forEach(item => {
                        const areaName = item.areaName || item.areaCode;
                        if (!areaAlerts[areaName]) {
                            areaAlerts[areaName] = { warnings: [], advisories: [] };
                        }
                        if (item.kinds) {
                            item.kinds.forEach(k => {
                                if ((k.status === '発表' || k.status === '継続') && k.code) {
                                    const name = getWarningName(k.code);
                                    const warningCheck = isWarning(k.code);

                                    if (warningCheck) {
                                        hyogoWarnings.add(name);
                                        areaAlerts[areaName].warnings.push(name);
                                    } else {
                                        hyogoAdvisories.add(name);
                                        areaAlerts[areaName].advisories.push(name);
                                    }

                                    if (item.areaCode === '2821000') {
                                        if (warningCheck) {
                                            kakogawaWarnings.push(name);
                                        } else {
                                            kakogawaAdvisories.push(name);
                                        }
                                    }
                                }
                            });
                        }
                    });
                }
            });

            const hyogoContainer = document.getElementById('hyogo-warning-container');
            if (hyogoWarnings.size > 0 || hyogoAdvisories.size > 0) {
                let hyogoHtml = '';
                if (hyogoWarnings.size > 0) {
                    hyogoHtml += `<div style="background-color: #fef2f2; border: 1px solid #f87171; padding: 6px; border-radius: 6px; color: #991b1b; margin-bottom: 4px;"><strong>⚠️ 警報:</strong> ${[...hyogoWarnings].join('、')}</div>`;
                }
                if (hyogoAdvisories.size > 0) {
                    hyogoHtml += `<div style="background-color: #fefce8; border: 1px solid #facc15; padding: 6px; border-radius: 6px; color: #854d0e;"><strong>注意報:</strong> ${[...hyogoAdvisories].join('、')}</div>`;
                }
                hyogoContainer.innerHTML = hyogoHtml;
            } else {
                hyogoContainer.innerHTML = `<div style="background-color: #f0fdf4; border: 1px solid #86efac; padding: 6px; border-radius: 6px; color: #166534; font-size: 0.9rem;">現在、兵庫県内に発表されている警報・注意報はありません。</div>`;
            }

            const kakogawaContainer = document.getElementById('kakogawa-warning-container');
            if (kakogawaWarnings.length > 0 || kakogawaAdvisories.length > 0) {
                let kakogawaHtml = '';
                if (kakogawaWarnings.length > 0) {
                    kakogawaHtml += `<div style="background-color: #fef2f2; border: 1px solid #f87171; padding: 6px; border-radius: 6px; color: #991b1b; margin-bottom: 4px;"><strong>⚠️ 警報:</strong> ${[...new Set(kakogawaWarnings)].join('、')}</div>`;
                }
                if (kakogawaAdvisories.length > 0) {
                    kakogawaHtml += `<div style="background-color: #fefce8; border: 1px solid #facc15; padding: 6px; border-radius: 6px; color: #854d0e;"><strong>注意報:</strong> ${[...new Set(kakogawaAdvisories)].join('、')}</div>`;
                }
                kakogawaContainer.innerHTML = kakogawaHtml;
            } else {
                kakogawaContainer.innerHTML = `<div style="background-color: #f0fdf4; border: 1px solid #86efac; padding: 6px; border-radius: 6px; color: #166534; font-size: 0.9rem;">現在、加古川市に発表されている警報・注意報はありません。</div>`;
            }

            const alertMapContainer = document.getElementById('alert-map-container');
            const areaKeys = Object.keys(areaAlerts);
            if (areaKeys.length > 0) {
                let listHtml = '';
                areaKeys.forEach(areaName => {
                    const itemData = areaAlerts[areaName];
                    const hasWarn = itemData.warnings.length > 0;
                    const hasAdv = itemData.advisories.length > 0;
                    
                    let statusBadge = '';
                    let cardBg = '#f8fafc';
                    let borderColor = '#cbd5e1';
                    let titleColor = '#1e293b';

                    if (hasWarn) {
                        statusBadge = `<span style="background-color: #fee2e2; color: #991b1b; border: 1px solid #f87171; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">警報発令中</span>`;
                        cardBg = '#fff5f5';
                        borderColor = '#fca5a5';
                        titleColor = '#dc2626';
                    } else if (hasAdv) {
                        statusBadge = `<span style="background-color: #fef9c3; color: #854d0e; border: 1px solid #facc15; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">注意報発表中</span>`;
                        cardBg = '#fefde8';
                        borderColor = '#fde047';
                        titleColor = '#ca8a04';
                    } else {
                        statusBadge = `<span style="background-color: #f0fdf4; color: #166534; border: 1px solid #86efac; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">発表なし</span>`;
                    }

                    let detailsHtml = (hasWarn || hasAdv) 
                        ? `<div style="margin-top: 6px; font-size: 0.85rem; color: #334155;">${[...new Set([...itemData.warnings, ...itemData.advisories])].join('、')}</div>`
                        : `<div style="margin-top: 6px; font-size: 0.85rem; color: #64748b;">気象警報・注意報は発表されていません</div>`;

                    listHtml += `
                        <div style="background: ${cardBg}; border: 1px solid ${borderColor}; border-radius: 6px; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-weight: bold; font-size: 1.05rem; color: ${titleColor}; margin-bottom: 2px;">${areaName}</div>
                                ${detailsHtml}
                            </div>
                            <div>${statusBadge}</div>
                        </div>
                    `;
                });
                alertMapContainer.innerHTML = listHtml;
            } else {
                alertMapContainer.innerHTML = `<div style="background-color: #f0fdf4; border: 1px solid #86efac; padding: 12px; border-radius: 6px; color: #166534;">現在、兵庫県内の各地域に発表されている警報・注意報はありません。</div>`;
            }
        }

        const overviewContainer = document.getElementById('overview-container');
        overviewContainer.innerHTML = '加古川市加古川町稲屋の気象データ（Open-Meteo & 気象庁防災API連携）';

        if (data.hourly_3h) {
            document.querySelector('#forecast-table-1 tbody').innerHTML = generateTableHtml(data.hourly_3h, 3);
        } else {
            throw new Error("hourly_3h data missing in data.json");
        }

        if (data.daily_forecast) {
            document.querySelector('#forecast-table-10days tbody').innerHTML = generateDailyTableHtml(data.daily_forecast);
        } else {
            throw new Error("daily_forecast data missing in data.json");
        }

    } catch (err) {
        console.error("データ読み込みエラー:", err);
        document.getElementById('overview-container').innerText = '天気データの読み込みに失敗しました。';
        document.querySelector('#forecast-table-1 tbody').innerHTML = `<tr><td colspan="6">天気データの取得に失敗しました。</td></tr>`;
        document.querySelector('#forecast-table-10days tbody').innerHTML = `<tr><td colspan="6">天気データの取得に失敗しました。</td></tr>`;
    }
}

fetchDashboardData();
setInterval(fetchDashboardData, 300000);
document.querySelector('.pagination-container').addEventListener('click', switchPage);