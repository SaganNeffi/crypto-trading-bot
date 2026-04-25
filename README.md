# 📈 Crypto Trading Backtest System

## 📌 專案介紹
本專案是一個使用 Python 開發的加密貨幣量化交易回測系統，  
針對 BTCUSDT 歷史行情進行策略測試與績效分析。

系統會自動從 Binance 取得歷史 K 線資料，  
並透過多種技術指標（RSI、ADX、EMA）建立交易策略，  
模擬實際交易流程並評估策略的獲利能力與風險。

---

## ⚙️ 使用技術
- Python
- Pandas / NumPy（資料處理）
- TA-Lib（技術指標計算）
- QuantStats（績效分析）
- Matplotlib（視覺化）

---

## 🚀 功能特色
- 📊 自動抓取 Binance 歷史 K 線資料
- 📈 建立交易策略（RSI + ADX + EMA）
- 💰 模擬交易與資金變化（Backtest）
- 📉 計算績效指標：
  - Sharpe Ratio
  - 最大回撤（Drawdown）
  - 勝率（Win Rate）
  - 盈利因子（Profit Factor）
- 📉 繪製資金曲線圖

---

## 🧠 策略邏輯（簡單說明）
- RSI：判斷市場是否過熱（超買/超賣）
- ADX：判斷趨勢強度
- EMA：判斷整體趨勢方向

👉 多個條件同時成立才進場，提高策略穩定性

---

## ▶️ 如何執行

### 1️⃣ 安裝套件
```bash
pip install -r requirements.txt
