# ☀️ AI 創新微課程：Taiwan Weather Forecast 互動式天氣預報 Web App

> **從氣象資料到互動式天氣預報應用**  
> *用程式探索天氣 · 用資料看見台灣 · 用 AI 實現更多可能*  
> **Code Smarter, Build a Better Tomorrow!**

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![CWA API](https://img.shields.io/badge/CWA-Open%20Data%20API%20(F--D0047--093)-0080FF?style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-Map%20Visualization-77B800?style=for-the-badge)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75?style=for-the-badge)

---

## 📌 專案簡介 (Project Overview)

本專案為 **AI 創新微課程 (AIoT L3 CWA HW1)** 之實作成果。專案核心目標是透過 **中央氣象署 (CWA) Open Data API**（資料集：`F-D0047-093` 全台灣各鄉鎮市區一週天氣預報）取得真實氣象觀測與預報資料，利用 Python 進行資料結構化解析與清洗，並透過具備冪等性 (Idempotent UPSERT) 的 ETL 流程儲存至 **SQLite 資料庫 (`data/data.db`)**。

前端導入 **類 Windy 風格現代深色模式 (Dark Mode)** 與 **玻璃擬態 (Glassmorphism)** 設計系統（參考 [taiwan-weather-map.vercel.app](https://taiwan-weather-map.vercel.app/)），結合 **Streamlit**、**Folium (CartoDB DarkMatter)** 與 **Plotly**，打造具備專業 9 段漸層溫標、行政區氣溫徽章、一週氣溫雙曲線走勢圖與即時同步機制的 **Taiwan Weather GIS Dashboard**。

---

## 🚦 五階段嚴格開發關卡 (Five-Gate Workflow Status)

本專案依據 [`project_workflow.md`](.agent/workflows/project_workflow.md) 嚴格把關實作品質：

| 關卡 | 模組主題 | 關鍵任務 | 驗證標準 | 狀態 |
| :---: | :--- | :--- | :--- | :---: |
| **Gate 1** | **CWA API 串接** | 串接 `F-D0047-093`，安全讀取 `.env` 金鑰，解析全台 22 縣市預報 | 200 OK，無洩漏金鑰，欄位完整 | 🟢 PASS |
| **Gate 2** | **SQLite 資料庫** | 設計 `TemperatureForecasts` 表，實作冪等性 UPSERT ETL 寫入 | 0 重複死資料，SQL SELECT 正確 | 🟢 PASS |
| **Gate 3** | **Local Taiwan GIS** | 建立 Streamlit 介面、氣溫走勢圖與 Folium 台灣互動地圖 | 類 Windy 深色風格，HTTP 200 OK | 🟢 PASS |
| **Gate 4** | **GitHub 版控管理** | 整理目錄結構、依賴清單與文件，推至 GitHub 儲存庫 | Git 遠端儲存庫同步成功 | 🟢 PASS |
| **Gate 5** | **雲端部署展示** | 部署至 Streamlit Community Cloud / Vercel 並配置環境變數 | 線上訪問與 API 即時查詢正常 | 🟡 PENDING |

---

## 🛠️ 技術棧與工具 (Tech Stack)

| 類別 | 技術 / 工具 | 說明 |
| :--- | :--- | :--- |
| **資料來源** | `CWA Open Data API` | 中央氣象署開放資料平台 (`F-D0047-093`) |
| **程式語言** | `Python 3.9+` | 主要開發語言 |
| **金鑰與憑證** | `python-dotenv`, `truststore` | 安全金鑰讀取與跨平台 SSL 憑證驗證 |
| **資料擷取** | `Requests` | HTTP API Request 請求發送與 JSON 階層解析 |
| **資料處理** | `Pandas` | 資料結構化整理與每日摘要統計 |
| **資料庫儲存**| `SQLite3` | 輕量級關聯式資料庫 (`data/data.db`)，支援 UPSERT |
| **前端 Web App**| `Streamlit` | 快速建構互動式氣象 Web 儀表板 (`app.py`) |
| **地圖視覺化** | `Folium` / `streamlit-folium` | CartoDB DarkMatter 深色台灣分級溫標地圖 |
| **動態圖表** | `Plotly` | 一週最高/最低氣溫雙曲線互動折線圖 |
| **版本控制** | `Git` / `GitHub` | 專案版控與雲端儲存庫管理 |

---

## 💾 資料庫設計 (Database Schema)

資料庫路徑：`data/data.db`  
資料表名稱：`TemperatureForecasts`

```sql
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate TEXT NOT NULL,
    startTime TEXT NOT NULL,
    endTime TEXT NOT NULL,
    weather TEXT,
    weatherCode TEXT,
    minT REAL NOT NULL,
    maxT REAL NOT NULL,
    pop INTEGER,
    updatedAt TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE(regionName, startTime, endTime)
);

CREATE INDEX IF NOT EXISTS idx_region_date ON TemperatureForecasts(regionName, dataDate);
CREATE INDEX IF NOT EXISTS idx_dataDate ON TemperatureForecasts(dataDate);
```

### 冪等性防重複寫入機制 (Idempotent UPSERT)
```sql
INSERT INTO TemperatureForecasts (
    regionName, dataDate, startTime, endTime, weather, weatherCode, minT, maxT, pop, updatedAt
) VALUES (
    :regionName, :dataDate, :startTime, :endTime, :weather, :weatherCode, :minT, :maxT, :pop, datetime('now', 'localtime')
)
ON CONFLICT(regionName, startTime, endTime) DO UPDATE SET
    dataDate = excluded.dataDate,
    weather = excluded.weather,
    weatherCode = excluded.weatherCode,
    minT = excluded.minT,
    maxT = excluded.maxT,
    pop = excluded.pop,
    updatedAt = datetime('now', 'localtime');
```

---

## 📂 專案目錄結構 (Project Structure)

```text
AIoT_L3_CWA_HW1/
├── .streamlit/
│   └── config.toml             # Streamlit 深色主題配置檔
├── data/
│   └── data.db                 # SQLite 氣象資料庫 (被 .gitignore 排除)
├── myplan/
│   ├── README.md               # 五階段關卡開發進度追蹤看板
│   └── style_guide.md          # 視覺風格規範書 (Windy 深色模式與 9 段溫標)
├── src/
│   ├── cwa_api.py              # CWA Open Data API (F-D0047-093) 串接與安全去敏模組
│   ├── db_manager.py           # SQLite Schema 建立、UPSERT 與 SQL 查詢聚合模組
│   ├── etl.py                  # 端對端 ETL 自動化執行模組
│   └── gis_helper.py           # 台灣 22 縣市座標、9 段色碼與 Folium 深色地圖模組
├── app.py                      # Streamlit + Folium + Plotly 互動式 Web App 主程式
├── test_gate1.py               # Gate 1 (CWA API) 自動化檢驗測試腳本
├── test_gate2.py               # Gate 2 (Database & ETL) 自動化檢驗測試腳本
├── test_gate3.py               # Gate 3 (Local Taiwan GIS) 自動化檢驗測試腳本
├── gate1_verification.log      # Gate 1 驗證通過日誌紀錄
├── gate2_verification.log      # Gate 2 驗證通過日誌紀錄
├── gate3_verification.log      # Gate 3 驗證通過日誌紀錄
├── .env.example                # 環境變數設定範本 (不包含敏感資料)
├── .gitignore                  # Git 忽略清單 (嚴格排除 .env, data.db, secrets)
├── requirements.txt            # Python 相依套件清單
└── README.md                   # 專案完整說明文件
```

---

## 🚀 快速開始 (Quick Start)

### 1. 克隆專案 (Clone Repository)

```bash
git clone https://github.com/Lannjiarong/AIoT_L3_CWA_HW1.git
cd AIoT_L3_CWA_HW1
```

### 2. 安裝依賴套件 (Install Dependencies)

建議建立獨立虛擬環境後安裝：
```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
```

### 3. 設定 CWA API Key

於根目錄建立 `.env` 檔案（已在 `.gitignore` 排除，絕不外流）：
```env
CWA_API_KEY=CWA-XXXXXXXXXXXXXXXXXXXXXXXX
CWA_DATASET_ID=F-D0047-093
```

### 4. 執行 ETL 資料擷取並寫入 SQLite

```bash
python -m src.etl
```

### 5. 執行各關卡自動化驗證測試

```bash
python test_gate1.py    # 檢驗 Gate 1 CWA API
python test_gate2.py    # 檢驗 Gate 2 SQLite & ETL
python test_gate3.py    # 檢驗 Gate 3 Streamlit & Folium GIS
```

### 6. 啟動 Streamlit 氣象預報 Web App

```bash
streamlit run app.py
```

瀏覽器訪問：`http://localhost:8501` 即可體驗完整的深色互動式氣象地圖！

---

## 🎨 視覺亮點展示 (Visual Highlights)

- 🌌 **極致深色背景與玻璃擬態**：基於 `#030712` 與 `rgba(17,24,39,0.85)` + `backdrop-filter: blur(8px)`。
- 🌡️ **9 段專業氣象漸層溫標**：
  `linear-gradient(to right, #2c7bb6, #5aa2cf, #abd9e9, #7fcdbb, #d9ef8b, #fee08b, #fdae61, #f46d43, #d73027)`
- 📍 **自訂膠囊溫度徽章**：各地區標籤顯示即時平均氣溫，滑鼠懸浮放大並提供即時天氣狀況、最高/最低溫與降雨機率彈窗。
- 📈 **Plotly 雙曲線動態折線圖**：選取目標行政區即可即時呈現 7 天溫度走勢與氣象摘要。

---

## 💡 延伸應用與未來展望 (Future Enhancements)

- [ ] **Line Bot 氣象提醒**：自動推播每日早晚溫差提示與降雨機率。
- [ ] **智慧旅遊推薦**：結合 LLM 依據天氣預報生成適合的旅遊景點規劃。
- [ ] **農業/防災警示**：高溫極端天氣告警與農作物預防寒害提醒。

---

## 👨‍🏫 導師與致謝 (Credits)

- **專案名稱**：AI 創新微課程 (AIoT L3 CWA HW1) - Taiwan Weather Forecast
- **指導講師**：煥哥 (Huan-Ge)
- **信念宣言**：
  > *"技術可以解決問題，但更重要的是用技術創造更好的未來！"*  
  > *—— Learn Today, Build Tomorrow | AI for Learning, AI for a Better Taiwan*
