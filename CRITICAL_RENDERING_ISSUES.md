# CRITICAL REPORT RENDERING ISSUES - ACTUAL PROBLEMS

**Date**: October 26, 2025, 6:50 PM  
**Status**: 🔴 CRITICAL - Reports showing raw JSON and zero values  
**Previous Assessment**: INCORRECT - Missed major rendering problems

---

## ACTUAL ISSUES (From User Screenshots)

### Issue 1: Raw JSON Being Displayed in PPT Slides ❌

**Evidence from Screenshot**:
```
• 0,"overall_risk":"Low"},"recession":{"economic_changes":{"gdp_growth":{"change":
• △ risk_assessment (Source: project_manager)
• △ 0,"overall_risk":"Low"},"recession":{"economic_changes":{"gdp_growth":{"change":
```

**Root Cause**: PowerPoint generator is not properly extracting/formatting data from dictionary structures.

**What's Happening**:
```python
# PPT generator is doing something like:
slide.text = str(data_dict)  # WRONG!
# Instead of:
slide.text = data_dict.get('overall_risk', 'Not assessed')  # CORRECT
```

---

### Issue 2: Zero Values for All Financial Ratios ❌

**Evidence**:
- Current Ratio: 0
- Quick Ratio: 0
- EBITDA Margin: 0

**Root Cause**: Financial data not being calculated or extracted properly

**Possible Causes**:
1. Ratios not being calculated by financial_analyst
2. Synthesis not extracting calculated ratios
3. PPT generator not mapping ratio data correctly

---

### Issue 3: SWOT Showing Formulas Instead of Analysis ❌

**Evidence from Screenshot**: Formulas/code visible instead of actual SWOT points

**Root Cause**: SWOT data structure not being properly unpacked in PPT generator

---

## ROOT CAUSE ANALYSIS

### Problem Location: PPT Generator Text Formatting

**File**: `src/outputs/ppt_generator.py` or `src/outputs/ppt_sections/*.py`

**What's Wrong**:

```python
# CURRENT (BROKEN) - Directly inserting data structures
for item in data_list:
    text_frame.text += str(item)  # This outputs raw dict/JSON!
    
# CORRECT - Properly extract and format
for item in data_list:
    if isinstance(item, dict):
        # Extract meaningful text
        text = item.get('description', item.get('text', str(item)))
        text_frame.text += f"• {text}\n"
    else:
        text_frame.text += f"• {item}\n"
```

---

## IMMEDIATE FIXES NEEDED

### Fix 1: PPT Executive Summary - Stop Dumping Raw JSON

**File**: `src/outputs/ppt_sections/executive_slides.py`
**Function**: `add_executive_summary_slide()`

**Current Problem**:
```python
# Somewhere in the code, it's doing:
slide.add_text(str(synthesis_data['some_key']))  # Outputs JSON!
```

**Fix**:
```python
def add_executive_summary_slide(prs, synthesis_data):
    """Add executive summary with PROPER text extraction"""
    
    # Extract recommendation properly
    exec_summary = synthesis_data.get('executive_summary', {})
    recommendation = exec_summary.get('key_recommendation', 'Under review')
    
    # NOT THIS:
    # slide.text = str(exec_summary)  # WRONG!
    
    # THIS:
    slide.text = f"Recommendation: {recommendation}"
    
    # Extract risks properly
    risks = exec_summary.get('top_3_risks', [])
    for risk in risks:
        if isinstance(risk, dict):
            risk_text = risk.get('description', risk.get('risk', 'Unknown risk'))
        else:
            risk_text = str(risk)
        slide.add_bullet(f"△ {risk_text}")
```

---

### Fix 2: Financial Ratios Showing Zero

**File**: `src/outputs/ppt_sections/financial_slides.py`
**Function**: `add_financial_metrics_slide()`

**Problem**: Ratios are zero because:
1. Not being calculated, OR
2. Not being extracted from synthesis, OR
3. Wrong keys being used

**Diagnostic Code**:
```python
# Add to PPT generator to debug
financial_data = synthesis_data.get('detailed_financials', {})
ratio_analysis = financial_data.get('ratio_analysis', {})

print(f"DEBUG financial_data keys: {list(financial_data.keys())}")
print(f"DEBUG ratio_analysis: {ratio_analysis}")

# Check if ratios exist
current_ratio = ratio_analysis.get('current_ratio', 0)
if current_ratio == 0:
    # Try alternative locations
    current_ratio = financial_data.get('liquidity_ratios', {}).get('current_ratio', 0)
    if current_ratio == 0:
        print("WARNING: Current ratio is 0 or missing!")
```

**Fix**:
```python
def extract_financial_ratios(synthesis_data):
    """Extract ratios with fallback logic"""
    
    financial_data = synthesis_data.get('detailed_financials', {})
    
    # Try multiple possible locations
    ratio_sources = [
        financial_data.get('ratio_analysis', {}),
        financial_data.get('ratios_ttm', [{}])[0] if financial_data.get('ratios_ttm') else {},
        financial_data.get('key_metrics', [{}])[0] if financial_data.get('key_metrics') else {}
    ]
    
    current_ratio = None
    for source in ratio_sources:
        if isinstance(source, dict):
            current_ratio = source.get('currentRatio') or source.get('current_ratio')
            if current_ratio:
                break
    
    return {
        'current_ratio': current_ratio or 'Not available',
        'quick_ratio': ... # Similar logic
    }
```

---

### Fix 3: SWOT Analysis Showing Formulas

**File**: `src/outputs/ppt_sections/executive_slides.py` or `financial_slides.py`
**Function**: `add_swot_slide()`

**Problem**: SWOT data is dict/list but being converted to string

**Fix**:
```python
def add_swot_slide(prs, synthesis_data):
    """Add SWOT with proper formatting"""
    
    market_analysis = synthesis_data.get('market_analysis', {})
    swot = market_analysis.get('swot_analysis', {})
    
    # Extract each SWOT component properly
    strengths = swot.get('strengths', [])
    weaknesses = swot.get('weaknesses', [])
    opportunities = swot.get('opportunities', [])
    threats = swot.get('threats', [])
    
    # Format properly - NOT str(strengths)!
    for strength in strengths:
        if isinstance(strength, dict):
            text = strength.get('description', strength.get('text', str(strength)))
        else:
            text = str(strength)
        slide.add_bullet(f"✓ {text}")
```

---

## COMPREHENSIVE FIX APPROACH

### Step 1: Add Data Validation to ALL PPT Sections

**Pattern to apply everywhere**:
```python
def safe_extract_text(data, default="Not available"):
    """Safely extract text from various data types"""
    if data is None:
        return default
    
    if isinstance(data, str):
        return data
    
    if isinstance(data, (int, float)):
        return str(data) if data != 0 else default
    
    if isinstance(data, dict):
        # Try common text keys
        return (data.get('description') or 
                data.get('text') or 
                data.get('value') or 
                default)
    
    if isinstance(data, list):
        if len(data) == 0:
            return default
        # Format as bullet list
        return "\n".join(f"• {safe_extract_text(item)}" for item in data)
    
    # Last resort
    return str(data) if len(str(data))
