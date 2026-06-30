# 📦 Enterprise Safety Stock Automation System
### Supply Chain Planning & Demand Forecasting Intelligence Platform

A high-fidelity Streamlit web application providing automated inventory planning using Single Exponential Smoothing (SES) demand forecasting, lead time volatility calculations, and capital allocation analysis.

---

## 🚀 Project Overview

This platform transforms raw historical consumption ledgers and lead time master sheets into optimized purchase requisitions and buffer plans. It acts as an executive decision portal for procurement directors and inventory managers, matching standard features in SAP Analytics Cloud, Oracle SCM, and Microsoft Dynamics.

### Key Benefits
- **Automated Data Cleaning:** Resolves missing fields, standardizes headers, and formats monthly consumption entries.
- **Demand Forecasting:** Forecasts next-month demands using dynamic Alpha search SES algorithms.
- **Buffer Optimization:** Establishes material safety stocks based on demand variability and delivery lead times.
- **Financial Analytics:** Estimates purchase orders and total budget expenditures, flagging capital lock-ins.
- **Risk Mitigation:** Identifies stockout threats (Critical Priorities) and supplier latency delays.

---

## 🛠️ Technology Stack

- **Framework:** Streamlit 1.32+ (Stateful routing & dashboard execution)
- **Data Engineering:** Pandas 2.0+, Numpy 1.24+ (Aggregation, clean routines)
- **Visual Analytics:** Plotly Express & Plotly Graph Objects 5.18+ (Transparent glass charts)
- **Statistical Modeling:** Scipy Stats, Statsmodels (SES optimization algorithms)
- **Excel Ingestion:** Openpyxl 3.1+ (Excel workbook conversion)
- **API Extensions:** Requests 2.31+, Streamlit-Lottie (Branding animations)

---

## 📸 Application Screenshots

Here are visual previews of the enterprise SCM planning interfaces:

1. **🏠 Executive Command Center**
   ![Executive Dashboard](assets/dashboard_preview.png)
   *8 responsive stat widgets, operational briefs, and alert indicators.*

2. **📈 Historical Analytics Console**
   ![Historical Analytics](assets/historical_preview.png)
   *Crosstab classification matrices, SMA averages, and Year-over-Year overlay lines.*

3. **📦 Inventory Planning Console**
   ![Inventory Planning](assets/inventory_preview.png)
   *ROP distributions, active stock coverages, and glowing SCM risk cards.*

4. **🔮 Next Month Forecast Engine**
   ![Next Month Forecast](assets/forecast_preview.png)
   *Individual material audits, actuals vs forecast curves, and priority recommendations.*

*Note: Previews can be replaced with PNG files of your actual running application.*

---

## 📁 Folder Structure

```
Final_Deployment/
│
├── streamlit_app/                  ← Streamlit Web App Root
│   ├── app.py                      ← Main Router & Premium Sidebar
│   ├── requirements.txt            ← System dependencies
│   ├── README.md                   ← Systems Manual (this file)
│   ├── PROJECT_CONTEXT.md          ← Local context variables
│   │
│   ├── config/
│   │   └── users.json              ← Secured local credential hashes
│   │
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── auth.py                 ← User access portal & login security
│   │   ├── utils.py                ← Premium CSS theme style tokens and KPI cards
│   │   ├── charts.py               ← Plotly SCM charts library
│   │   ├── pipeline.py             ← Subprocess orchestration (untouched backend)
│   │   ├── dashboard_page.py       ← REDESIGNED Executive Command Center
│   │   ├── upload_page.py          ← Upload files & log-free progress
│   │   ├── forecast_page.py        ← Forecast analytics (4-Tab Planning Suite)
│   │   ├── historical_page.py      ← Historical analytics console (4-Tab Premium)
│   │   ├── inventory_page.py       ← Inventory planning suite (4-Tab Premium)
│   │   ├── download_page.py        ← Download reports center (Multi-format)
│   │   └── settings_page.py        ← System admin settings & SCM Help Manual
│   │   └── profile_page.py         ← User Profile Credentials Manager
│   │
│   └── python_script/              ← Backend execution scripts (untouched)
│       ├── 01_Data_Validation_Cleaning.py
│       ├── 02_Feature_Engineering.py
│       ├── 03_Update_Historical_Data.py
│       ├── 04_SES_Forecasting.py
│       ├── 05_Inventory_Planning.py
│       └── run_pipeline.py
│
├── Monthly_upload/
├── Data/
├── Data_SES/
├── final_month_data/
├── Final_prediction/
└── Client_deliverable/
    └── Prediction.csv              ← Final output
```

---

## 🐍 Requirements

- **Python Version:** Tested on **Python 3.10+**. Python 3.10 or 3.11 is highly recommended.
- **Core Dependencies:** See `requirements.txt`.

---

## ⚙️ Installation & Setup

### Step 1 — Create a Virtual Environment

Open your terminal or command prompt in the `Final_Deployment/streamlit_app` folder:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

Or with Conda:
```bash
conda create -n safetystock python=3.10
conda activate safetystock
```

### Step 2 — Ingest System Dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — How to Run

```bash
streamlit run app.py
```
The app will automatically launch in your browser at `http://localhost:8501`.

---

## 🔐 Authentication & Roles

Local access hashes are stored inside `config/users.json`. The platform supports three permission roles:
1. **Admin (`admin`)**: Access to all panels, settings modifications, and password resets.
2. **Manager (`manager`)**: Full access to dashboard reviews, upload capabilities, and downloads.
3. **Viewer (`viewer`)**: Read-only access to dashboard pages and forecasts. Settings are read-only.

---

## 🔄 Ingestion & Planning Workflows

### Phase 1: Monthly Upload Ingestion
1. Navigate to **Upload Monthly Data** in the sidebar navigation.
2. Ingest two Excel sheets:
   - **Consumption Ledger:** Must have exactly 2 columns: `material_id` and a dynamic month header (e.g. `2023-10` or `Jan-2024`) containing numeric demand values.
   - **Lead Time Master:** Must contain columns: `material_id`, `material_lead_time`, `moving_price`, and `unrestricted` (current stock count).
3. The validator checks schemas and column data types. Correct formats display a green success report; incorrect entries display a descriptive error.
4. Preview top 5 rows dynamically before running calculations.

### Phase 2: Orchestration & Progress Bar
1. Click the **Execute Forecasting Engine** button.
2. The UI hides background stack traces and logs, displaying a clean progress bar alongside active milestones:
   - `✓ Ingestion Completed` -> `✓ Checking Data` -> `✓ Preparing Dataset` -> `✓ Updating Historical Records` -> `✓ Forecasting Demand` -> `✓ Inventory Planning` -> `✓ Prediction Ready`.
3. Success compiles `Prediction.csv` and presents a detailed summary card displaying generated forecast month, total material codes, purchase budgets, and critical alerts.

### Phase 3: Demand Smoothing Forecast (SES)
The background algorithm executes a Single Exponential Smoothing model per material code:
\[Y_{t+1} = \alpha Y_t + (1-\alpha) S_t\]
Alpha searches find values minimizing errors (MASE) to output smoothed demand.

### Phase 4: Inventory ROP calculations
ROP and safety stocks are calculated to buffer supplier lead times:
- \[\text{Safety Stock} = Z \times \sigma_{LT} \times \sqrt{\text{Lead Time}}\]
- \[\text{ROP} = \text{Lead Time Demand} + \text{Safety Stock}\]
- \[\text{Inventory Gap} = \text{ROP} - \text{Current Stock} \quad (\text{if Stock} < \text{ROP})\]

---

## 📊 Dashboard Portals Overview

- 🏠 **Dashboard Command Center:** 8 glassmorphic KPI cards, an executive operations brief summary, and flashing stockout alarm badges.
- 📈 **Historical Analytics Console:** 4 tabs (Demand, Inventory, Materials, Summary) showing heatmaps, rolling averages, YoY overlays, Crosstab classification matrices, and coverage spreads.
- 📦 **Inventory Planning Suite:** 10 KPIs, ROP histograms, interactive paginated requisition grids, and glowing risk cards.
- 🔮 **Next Month Forecast Engine:** 4 tabs isolating planning priorities, single material audits, actuals vs forecast curves, and supplier alert cards.
- 📥 **Download Reports Portal:** Export compiled reorder plans as CSV sheets, Excel workbooks, or txt procurement memos.

---

## 🌐 Production Deployment Guide

### Windows Server Local Deployment
To deploy as a background service on a Windows Local Server:
1. Open PowerShell as Administrator.
2. Install NSSM (Non-Sucking Service Manager): `choco install nssm` (or download binary).
3. Register the service:
   ```bash
   nssm install SafetyStockService "C:\Final_Deployment\streamlit_app\venv\Scripts\streamlit.exe" "run C:\Final_Deployment\streamlit_app\app.py --server.port 80"
   ```
4. Start the service: `Start-Service SafetyStockService`.

---

## ❓ Troubleshooting & FAQ

**Q: "Script Not Found" error during execution**
- *A:* Ensure `modules/pipeline.py` resolves `SCRIPTS_DIR` to `DEPLOYMENT_ROOT / "python_script"`. Verify that all five core `.py` scripts exist inside that folder.

**Q: Page keeps reloading or variables disappear**
- *A:* Streamlit runs top-to-bottom on interaction. Ensure stateful parameters (logins, prediction paths) are stored inside `st.session_state` to prevent session loss.

---

## 🚀 Future Enhancements

- **SSO Authentication:** Integrate Active Directory / LDAP authentication.
- **SQL Database Sync:** Connect database tables to store forecasts and manage credentials.
- **Lottie Cargo animations:** Replace comment placeholders with responsive JSON animations for cargo trucks and box loading.
