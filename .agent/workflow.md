---
description: AIoT L3 CWA HW1 — strict five-gate development workflow
---

# Taiwan Weather GIS — Antigravity Workflow

## Governing Rule

嚴格依序執行：

```text
Gate 1 CWA API
 → Gate 2 Database
 → Gate 3 Local Taiwan GIS
 → Gate 4 GitHub
 → Gate 5 Vercel / Deployment
```

**DO NOT BUILD EVERYTHING AT ONCE.**

每個 Gate 必須 `BUILD → RUN → TEST → VERIFY → PASS`。FAIL 時停留在該 Gate 修正。不得使用 mock/fake weather data。

---

## Gate 1 — CWA API

**Goal**: 從 CWA Open Data API 取得真實 Forecast JSON。

1. **Dataset & Endpoint**: 
   - 使用指定資料集 **`F-D0047-093`**（台灣各縣市鄉鎮未來 1 週天氣預報）。
   - Endpoint: `https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-093`
2. **API 金鑰與安全配置**:
   - 從 `.env` 讀取 `CWA_API_KEY`（設定值格式為 `CWA-55FDA6...4FB2`）。
   - ⚠️ **嚴禁**在程式輸出、Log 或 Commit 中印出完整 API 金鑰。
3. **HTTP 請求**:
   - 使用 Python `requests` 發送真實 HTTP GET 請求。
4. **狀態碼驗證**:
   - 驗證 HTTP status code 必須為 `200 OK`。
5. **JSON Response 結構解析**:
   - 依實際 response 解析 JSON 階層，不憑空推測 schema。
6. **地區驗證**:
   - 先驗證單一地區（例如：臺中市或全台特定鄉鎮）。
7. **欄位擷取**:
   - 輸出 Location、Forecast Time、Weather Element (Wx 天氣現象, MinT 最低溫, MaxT 最高溫)；若 Dataset 提供 PoP (降雨機率) 則一併擷取。
8. **涵蓋度確認**:
   - 確認全台其他縣市/鄉鎮預報資料均正常存在於 response 中。
9. **測試驗證與紀錄**:
   - 實際執行 `RUN` 並留下測試驗證日誌與紀錄。

⚠️ **禁止事項**：此階段禁止實作 Database、GIS、GitHub deployment 或 Vercel。

✅ 只有全部成功驗證後才回報：`GATE 1 = PASS`。

---

## Gate 2 — Database

**前提**：Gate 1 PASS。

**Goal**: 將真實 CWA response 進行 ETL 並存入 SQLite 資料庫。

1. 設計 SQLite Schema (`TemperatureForecasts` 資料表)。
2. 定義唯一約束與去重策略 (Idempotent / UPSERT / UNIQUE)。
3. 執行 ETL 流程，將氣溫數據解析後寫入 `data/data.db`。
4. 撰寫 SQL `SELECT` 查詢測試，驗證單一地區與全台多地區資料寫入之正確性。

⚠️ **禁止事項**：此階段禁止開始實作 GIS 或 Web Dashboard 介面。

✅ 只有 SQL 查詢驗證成功後才回報：`GATE 2 = PASS`。

---

## Gate 3 — Local Taiwan GIS

**前提**：Gate 2 PASS。

**Goal**: 建立本地端 Streamlit + Folium 互動式 Web App。

1. 搭建 Streamlit 應用程式結構 (`app.py`)。
2. 從 SQLite 讀取氣象預報數據。
3. 實作區域下拉選單與最高/最低氣溫 (MinT/MaxT) 趨勢折線圖。
4. 整合 Folium 繪製台灣地圖，依據氣溫分級顏色與日期選擇動態展示。
5. 本地執行 `streamlit run app.py` 進行功能測試與驗證。

✅ 只有本地 Web 介面完整正常運行才回報：`GATE 3 = PASS`。

---

## Gate 4 — GitHub

**前提**：Gate 3 PASS。

**Goal**: 專案版控重構與遠端備份。

1. 檢查並整理專案目錄結構、`.gitignore` 及 `requirements.txt`。
2. 撰寫與更新 `README.md` 文件。
3. 將原始碼與設定檔 commit 並 push 至 GitHub 儲存庫 `https://github.com/Lannjiarong/AIoT_L3_CWA_HW1.git`。
4. 驗證遠端 Repository 檔案完整性。

✅ 只有 Git 儲存庫同步成功才回報：`GATE 4 = PASS`。

---

## Gate 5 — Vercel / Deployment

**前提**：Gate 4 PASS。

**Goal**: 線上部署與展示驗證。

1. 設定線上部署環境 (Streamlit Community Cloud / Vercel)。
2. 配置雲端環境變數 (`CWA_API_KEY`)。
3. 驗證線上版本運作狀況與 API 資料刷新機制。

✅ 只有線上部署驗證成功才回報：`GATE 5 = PASS`。
