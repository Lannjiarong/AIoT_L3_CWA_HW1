# 📋 Taiwan Weather GIS — 專案開發計畫 (My Plan)

> **專案名稱**：AIoT L3 CWA HW1 — Taiwan Weather Forecast & GIS Web App  
> **核心原則**：嚴格遵守五階段關卡 (Five-Gate Development Workflow)，嚴禁跨階段實作。  
> **規範標準**：每階段遵循 `BUILD → RUN → TEST → VERIFY → PASS` 流程，驗證通過後方可進入下一階段。

---

## 🚦 五大關卡進度看板 (Progress Dashboard)

| 關卡 | 模組主題 | 關鍵任務 | 狀態 |
| :---: | :--- | :--- | :---: |
| **Gate 1** | **CWA API 串接** | 串接 `F-D0047-093`，安全讀取金鑰，解析全台氣象 JSON 資料 | 🟢 通過 (PASS) |
| **Gate 2** | **SQLite 資料庫** | 設計 `TemperatureForecasts` 表，實作冪等性 ETL 寫入與驗證 | 🟢 通過 (PASS) |
| **Gate 3** | **Local Taiwan GIS** | 建立 Streamlit 介面、氣溫趨勢折線圖與 Folium 台灣互動地圖 | 🟢 通過 (PASS) |
| **Gate 4** | **GitHub 版控管理** | 整理目錄結構、依賴清單與文件，推至 GitHub 儲存庫 | 🟡 待執行 (PENDING) |
| **Gate 5** | **雲端部署展示** | 部署至 Streamlit Community Cloud / Vercel 並配置環境變數 | ⚪ 待解鎖 (LOCKED) |

---

## 📌 各階段詳細執行計畫

### 🔹 Gate 1 — CWA API (氣象署開放資料 API 串接)
- [x] **1.1 環境變數與安全配置**
  - 從 `.env` 安全讀取 `CWA_API_KEY` 與資料集編號 `F-D0047-093`。
  - 嚴禁在程式碼、紀錄檔 (Log) 或 Commit 中印出完整金鑰。
- [x] **1.2 發送 HTTP GET 請求**
  - 使用 Python `requests` 模組向 `https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-093` 發送真實請求。
  - 驗證 HTTP Status Code 為 `200 OK`。
- [x] **1.3 JSON 資料結構解析**
  - 依真實 API 回應逐層拆解 JSON 結構。
  - 提取欄位：`Location` (縣市/鄉鎮)、`Forecast Time` (預報時間)、`Wx` (天氣現象)、`MinT` (最低溫)、`MaxT` (最高溫)、`PoP` (降雨機率，若存在)。
- [x] **1.4 涵蓋度確認與測試**
  - 單一地區資料驗證（如：臺中市）。
  - 全台各縣市/鄉鎮預報資料完整性確認。
  - 產出執行日誌與測試驗證紀錄。
- **產出目標**：`GATE 1 = PASS` ✅ (驗證完成於 2026-09-23)

---

### 🔹 Gate 2 — Database (SQLite 資料庫與 ETL Pipeline)
- [x] **2.1 SQLite Schema 設計**
  - 規劃 `TemperatureForecasts` 資料表與索引 (`idx_region_date`, `idx_dataDate`)。
  - 設定唯一約束 `UNIQUE(regionName, startTime, endTime)` 與防重複寫入 (Idempotent / UPSERT) 機制。
- [x] **2.2 ETL 管道建置**
  - 解析 Gate 1 擷取之真實氣溫數據，清理後寫入 `data/data.db`。
- [x] **2.3 資料庫讀取測試與驗證**
  - 執行 SQL `SELECT` 查詢，驗證單一地區與全台各區資料筆數與內容正確性。
  - 驗證二次執行 ETL 零重疊死資料 (Idempotency)。
- **產出目標**：`GATE 2 = PASS` ✅ (驗證完成於 2026-09-23)

---

### 🔹 Gate 3 — Local Taiwan GIS (本地端互動式儀表板)
- [x] **3.1 視覺設計與樣式系統整合**
  - 導入 [視覺風格規範書 (Style Guide)](file:///c:/Users/user/Desktop/L3%20WAC/myplan/style_guide.md)（參照 [taiwan-weather-map.vercel.app](https://taiwan-weather-map.vercel.app/) 之 Windy 風格深色模式、`bg-panel` 玻璃擬態與 9 段溫標漸層色）。
- [x] **3.2 搭建 Streamlit 應用架構 (`app.py`)**
  - 配置深色響應式版面與自訂 CSS 樣式注入。
- [x] **3.3 資料庫讀取與快取整合**
  - 從 SQLite (`data/data.db`) 讀取預報數據。
- [x] **3.4 互動式圖表開發**
  - 縣市/鄉鎮下拉選單 (`st.selectbox`)。
  - 最高/最低溫 (MinT / MaxT) 一週趨勢折線圖 (`plotly` 漸層雙曲線圖)。
- [x] **3.5 Folium 台灣地理資訊圖表**
  - 採用 `CartoDB dark_matter` 深色底圖。
  - 整合自訂 `temp-badge` 氣溫膠囊徽章與玻璃擬態彈窗。
  - 整合右下角 9 段漸層色標圖例 (`#2c7bb6` ~ `#d73027`)。
- [x] **3.6 本地功能驗證**
  - 執行 `streamlit run app.py` 進行端對端完整功能測試（HTTP 200 OK）。
- **產出目標**：`GATE 3 = PASS` ✅ (驗證完成於 2026-09-23)

---

### 🔹 Gate 4 — GitHub (專案版控與重構)
- [ ] **4.1 目錄與依賴整理**
  - 確認 `.gitignore` 完整排除 `.env`、`data/`、`*.db`、`venv/`、`__pycache__/`。
  - 輸出完整且精確的 `requirements.txt`。
- [ ] **4.2 文件完善**
  - 更新 `README.md`，詳述專案架構、功能展示與快速啟動指南。
- [ ] **4.3 提交與推送**
  - 遵循 Conventional Commits 規範撰寫 commit message。
  - 推送程式碼至遠端儲存庫：`https://github.com/Lannjiarong/AIoT_L3_CWA_HW1.git`。
- [ ] **4.4 遠端儲存庫驗證**
  - 檢視 GitHub 遠端檔案與設定完整性。
- **產出目標**：`GATE 4 = PASS`

---

### 🔹 Gate 5 — Vercel / Deployment (雲端部署與展示)
- [ ] **5.1 部署環境設定**
  - 配置 Streamlit Community Cloud 或 Vercel 部署設定檔。
- [ ] **5.2 雲端環境變數配置**
  - 於雲端平台安全填入 `CWA_API_KEY` 等環境變數。
- [ ] **5.3 線上運行檢驗**
  - 驗證線上版本網址訪問、API 即時查詢與地圖渲染功能正常。
- **產出目標**：`GATE 5 = PASS`
