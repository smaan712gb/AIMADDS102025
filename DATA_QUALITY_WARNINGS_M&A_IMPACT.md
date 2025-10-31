# Data Quality Warnings - M&A Impact Analysis

**Company:** Palantir (PLTR)  
**Data Quality Grade:** B (94.4% completeness)  
**Status:** VALID but with critical warnings for M&A review

---

## ⚠️ CRITICAL WARNINGS IDENTIFIED

### 1. Missing Cash Field (2024) - CRITICAL FOR M&A ❌

**Warning:** `2024-12-31: Missing cash`

**M&A Impact:**
- **BLOCKS** accurate working capital analysis
- Cannot calculate true net working capital (NWC = Current Assets - Current Liabilities - Cash)
- Working capital peg at closing cannot be determined accurately
- **Risk:** Incorrect purchase price adjustment at close

**Action Required:**
- ✅ System correctly flagged this as missing
- ⚠️  Manual verification needed: Check if FMP API has alternative cash field name
- ⚠️  M&A analyst must validate cash position from 10-K/10-Q directly
- 🔴 **Do not proceed with working capital peg calculations until resolved**

**Fix:**
- Check if `cashAndShortTermInvestments` or `cashAndCashEquivalents` exists
- Fallback to parsing cash from 10-K if FMP data incomplete

---

### 2. Negative Margins (2020) - CONTEXT REQUIRED FOR M&A ⚠️

**Warning:** `2020-12-31: Net margin < -100% (-106.7%) - suspicious`

**M&A Analysis:**

**For Palantir (PLTR) Specifically:**
- ✅ **EXPECTED** for high-growth tech companies in early public years
- 2020 was Palantir's IPO year (September 2020)
- Heavy R&D and S&M investments typical for growth phase
- Stock-based compensation likely driving losses

**M&A Implications:**
- ✅ **NOT a deal-breaker** - part of growth trajectory
- ⚠️  **Requires validation:** Confirm trend improved in 2021-2024
- ⚠️  **Check:** Are margins improving or deteriorating?
- 🔍 **Due diligence:** Understand path to profitability

**What to Check:**
1. Margin trend: Is 2020 (-107%) → 2024 (positive/improving)?
2. Unit economics: Are margins improving as company scales?
3. Burn rate: When does company become cash flow positive?
4. Comparables: How do PLTR margins compare to peers (SNOW, DDOG)?

**Action:**
- ✅ System correctly flagged as outlier
- ✅ Valid for growth companies - document in investment thesis
- ⚠️  Verify margin improvement trajectory (critical for valuation)

---

### 3. Operating Margin Outliers (2020) - SAME AS #2

**Warning:** `2020-12-31: Operating Margin outlier - Value: -107.41%`

**Analysis:** Same issue as net margin above - growth company characteristics

---

## 🎯 M&A DUE DILIGENCE IMPLICATIONS

### What
