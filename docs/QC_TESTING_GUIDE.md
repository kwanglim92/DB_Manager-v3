# QC Custom Inspection System - Testing Guide

## 📋 Test Summary

### Automated Logic Test Results ✅

**Test Date**: 2024-01-15  
**Status**: All tests passed successfully

#### Test Results:
```
Total Items:  10
Pass Count:   7 ✅
Fail Count:   3 ❌
Pass Rate:    70.0%
```

#### Detailed Results:

| No. | Item Name      | Min Spec | Max Spec | Measured | Result     | Deviation      |
|-----|----------------|----------|----------|----------|------------|----------------|
| 1   | Temperature    | 20.00    | 25.00    | 22.50    | ✅ Pass    | -              |
| 2   | Humidity       | 40.00    | 60.00    | 45.00    | ✅ Pass    | -              |
| 3   | Pressure       | 100.00   | 105.00   | 101.50   | ✅ Pass    | -              |
| 4   | Voltage        | 4.80     | 5.00     | 5.20     | ❌ Fail    | ▲ 0.200        |
| 5   | Current        | 2.00     | 2.50     | 2.10     | ✅ Pass    | -              |
| 6   | Resistance     | 100.00   | 110.00   | 98.50    | ❌ Fail    | ▼ 1.500        |
| 7   | Frequency      | 59.00    | 61.00    | 60.00    | ✅ Pass    | -              |
| 8   | Power          | 10.00    | 15.00    | 10.50    | ✅ Pass    | -              |
| 9   | Efficiency     | 90.00    | 100.00   | 92.00    | ✅ Pass    | -              |
| 10  | Response Time  | 10.00    | 15.00    | 15.50    | ❌ Fail    | ▲ 0.500        |

### Validation Results:
- ✅ Pass count matches expected: 7
- ✅ Fail count matches expected: 3
- ✅ Pass rate matches expected: 70.0%

---

## 🧪 UI Testing Guide

### Prerequisites
1. **Test Data Created**:
   - ✅ QC Config file: `config/custom_qc_specs.json`
   - ✅ Test DB file: `test_data/test_qc_sample.db`
   - ✅ Equipment Type: "Test Equipment"
   - ✅ 10 QC Specs configured

### Test Scenario 1: QC Spec Management Tab

#### 1.1 View Equipment Types
1. Launch application: `python3 main.py`
2. Navigate to **QC 스펙 관리** tab
3. **Expected**: Radio buttons showing:
   - Standard Model
   - Advanced Model
   - Custom Model
   - Test Configuration
   - Production Line A
   - Production Line B
   - Test Equipment ← should be selected

#### 1.2 View QC Specs
1. Ensure "Test Equipment" is selected
2. **Expected**: Treeview shows 10 items:
   - Temperature (20-25 °C)
   - Humidity (40-60 %)
   - Pressure (100-105 kPa)
   - Voltage (4.8-5.0 V)
   - Current (2.0-2.5 A)
   - Resistance (100-110 Ω)
   - Frequency (59-61 Hz)
   - Power (10-15 W)
   - Efficiency (90-100 %)
   - Response Time (10-15 ms)

#### 1.3 Add New Equipment Type
1. Click **"장비 Type 추가"** button
2. Enter name: "My Custom Equipment"
3. Click OK
4. **Expected**: New radio button appears for "My Custom Equipment"

#### 1.4 Add QC Spec
1. Select "My Custom Equipment"
2. Click **"항목 추가"** button
3. Fill in:
   - Item Name: "Test Item"
   - Min Spec: 10
   - Max Spec: 20
   - Unit: "unit"
   - Description: "Test description"
4. Click Save
5. **Expected**: New spec appears in treeview

#### 1.5 Edit QC Spec
1. Select any spec in treeview
2. Click **"항목 수정"** button
3. Modify Min/Max values
4. Click Save
5. **Expected**: Values updated in treeview

#### 1.6 Delete QC Spec
1. Select one or more specs
2. Click **"선택 항목 삭제"** button
3. Confirm deletion
4. **Expected**: Selected specs removed from treeview

#### 1.7 Search/Filter
1. Enter "Temp" in search box
2. **Expected**: Only "Temperature" items shown
3. Clear search box
4. **Expected**: All items shown again

#### 1.8 Export CSV
1. Select "Test Equipment"
2. Click **"CSV 내보내기"** button
3. Choose save location
4. **Expected**: CSV file created with all specs

#### 1.9 Import CSV
1. Click **"CSV 가져오기"** button
2. Select previously exported CSV
3. **Expected**: Specs imported successfully

---

### Test Scenario 2: QC Inspection Tab

#### 2.1 Load DB File
1. Navigate to **DB 파일 관리** tab (or wherever DB loading is)
2. Click **"파일 열기"** button
3. Select: `test_data/test_qc_sample.db`
4. **Expected**: File loaded, merged_df contains data

#### 2.2 Navigate to QC Inspection Tab
1. Navigate to **QC 검수** tab
2. **Expected**: 
   - Equipment Type radio buttons visible
   - File info shows loaded DB file
   - "QC 검수 실행" button enabled

#### 2.3 Select Equipment Type
1. Select "Test Equipment" radio button
2. **Expected**: Radio button selected

#### 2.4 Run QC Inspection
1. Click **"QC 검수 실행"** button
2. **Expected**: Result treeview populated with:
   - 10 rows (one per spec)
   - 7 items with ✅ Pass in green
   - 3 items with ❌ Fail in red with background:
     - Voltage: ▲ 0.200 (over max)
     - Resistance: ▼ 1.500 (under min)
     - Response Time: ▲ 0.500 (over max)
   - Summary shows:
     - Total: 10
     - Pass: 7
     - Pass Rate: 70.0%
     - Fail: 3

#### 2.5 Verify Color Coding
1. **Expected**:
   - Pass rows: Green text
   - Fail rows: Red text with red background
   - Result column: ✅ or ❌ icons

#### 2.6 Verify Deviation Calculation
1. Check "Voltage" row:
   - **Expected**: Deviation = "▲ 0.200"
   - **Calculation**: Measured (5.2) - Max (5.0) = 0.2
2. Check "Resistance" row:
   - **Expected**: Deviation = "▼ 1.500"
   - **Calculation**: Min (100.0) - Measured (98.5) = 1.5
3. Check "Response Time" row:
   - **Expected**: Deviation = "▲ 0.500"
   - **Calculation**: Measured (15.5) - Max (15.0) = 0.5

#### 2.7 Export Inspection Results
1. Click **"결과 내보내기"** button
2. Choose CSV format
3. Select save location
4. **Expected**: CSV file created with all inspection results

#### 2.8 Navigate to Spec Management
1. Click **"QC 스펙 관리로 이동"** button
2. **Expected**: Navigates to QC Spec Management tab

---

### Test Scenario 3: Integration Test

#### 3.1 Modify Spec and Re-Inspect
1. Go to **QC 스펙 관리** tab
2. Select "Test Equipment"
3. Find "Voltage" spec (Min: 4.8, Max: 5.0)
4. Edit to: Min: 5.0, Max: 5.5
5. Save changes
6. Go to **QC 검수** tab
7. Click **"QC 검수 실행"** button
8. **Expected**: 
   - Voltage now shows ✅ Pass (5.2 is within 5.0-5.5)
   - Pass count increases to 8
   - Fail count decreases to 2
   - Pass rate increases to 80.0%

#### 3.2 Add New Spec and Inspect
1. Go to **QC 스펙 관리** tab
2. Add new spec: "New Item" (Min: 0, Max: 100)
3. Go to **QC 검수** tab
4. Run inspection
5. **Expected**: 
   - New item shows "⚠️ Not Found" or error (not in DB)
   - Other items still show correct results

#### 3.3 Test Multiple Equipment Types
1. Go to **QC 스펙 관리** tab
2. Select "Standard Model"
3. Verify different specs shown
4. Go to **QC 검수** tab
5. Select "Standard Model"
6. Run inspection
7. **Expected**: Uses specs for "Standard Model"

---

## 🐛 Known Issues / Edge Cases

### 1. Non-Numeric Values
- **Test**: Add spec for item with non-numeric value
- **Expected**: Shows error tag with gray color

### 2. Missing Items
- **Test**: Add spec for item not in DB
- **Expected**: Shows "Not found" error

### 3. Empty Specs
- **Test**: Run inspection with Equipment Type having no specs
- **Expected**: Warning message or empty result table

### 4. No DB Loaded
- **Test**: Run inspection without loading DB file
- **Expected**: Error message

---

## 📊 Performance Testing

### Spec Count
- Test with 10 specs: ✅ Passed
- Test with 50 specs: (To be tested)
- Test with 100+ specs: (To be tested)

### DB Size
- Test with 10 rows: ✅ Passed
- Test with 100 rows: (To be tested)
- Test with 1000+ rows: (To be tested)

---

## ✅ Test Checklist

### Phase 1: QC Spec Management Tab
- [x] Equipment Type radio button display
- [x] Add Equipment Type
- [ ] Rename Equipment Type (UI test pending)
- [ ] Delete Equipment Type (UI test pending)
- [x] View QC specs for selected Equipment Type
- [ ] Add QC spec with validation (UI test pending)
- [ ] Edit QC spec (UI test pending)
- [ ] Delete QC spec (UI test pending)
- [ ] Multi-select delete (UI test pending)
- [ ] Search/filter specs (UI test pending)
- [ ] CSV export (UI test pending)
- [ ] CSV import (UI test pending)

### Phase 2: QC Inspection Tab
- [x] Equipment Type radio button display
- [x] Load specs from CustomQCConfig
- [x] Compare measured values against specs
- [x] Pass/Fail determination logic
- [x] Deviation calculation
- [ ] Color coding display (UI test pending)
- [ ] Summary statistics (UI test pending)
- [ ] Export inspection results (UI test pending)
- [ ] Navigate to Spec Management tab (UI test pending)

### Integration
- [x] Spec changes reflect in inspection
- [ ] Equipment Type changes sync between tabs (UI test pending)
- [x] JSON persistence

---

## 🎯 Next Steps

1. **Manual UI Testing**: Run application and perform UI tests
2. **Edge Case Testing**: Test error handling scenarios
3. **Performance Testing**: Test with large datasets
4. **User Acceptance Testing**: Get user feedback
5. **Documentation**: Update user manual

---

## 📝 Test Log

| Date       | Tester | Scenario | Result | Notes |
|------------|--------|----------|--------|-------|
| 2024-01-15 | Auto   | Logic Test | ✅ Pass | All 10 items tested correctly |
| ...        | ...    | ...      | ...    | ...   |

---

## 🔧 Test Environment

- **Python Version**: 3.x
- **OS**: Linux
- **Dependencies**: pandas, tkinter, openpyxl, sqlite3
- **Test Data**:
  - Config: `config/custom_qc_specs.json`
  - DB: `test_data/test_qc_sample.db`

---

**Last Updated**: 2024-01-15  
**Test Status**: ✅ Automated logic tests passed. UI tests pending.
