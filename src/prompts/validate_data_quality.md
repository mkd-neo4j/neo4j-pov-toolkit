# Data Quality Validation Before Code Generation

> **🛑 STOP**: Have you read [PROMPT.md](../../PROMPT.md)?
>
> If NO → Read it NOW before proceeding. It contains critical context about:
> - Your mission and core principles
> - When to read this file vs others
> - Essential tools and workflows
>
> This supporting prompt assumes you've already read PROMPT.md.

---

**Reference guide for validating raw data quality and structure before generating data mapper code.**

---

## Philosophy: This is What Professionals Do

> **"You need to do some thinking yourself like what happens when I execute this and there's a column that's broken, right?"** - Pedro Leitao

### The Professional Standard: Validate → Transform → Load

**Data engineers and data scientists ALWAYS validate data quality before production loads.** This is not optional. This is not "analysis for fun." This is the standard professional practice.

**Why**:
1. **You can't write defensive code if you don't know what you're defending against**
2. **"Customer is gonna give you is just a load of shite that you're gonna have to fix yourself"** - Pedro
3. **"It's much, much harder to verify once it gets into Neo4j"** - Pedro
4. **Fix issues BEFORE Neo4j, not after** - debugging in a graph database is a nightmare

### What You MUST Understand Before Code Generation

- **Data Quality**: Are there nulls, invalid values, or type mismatches?
- **Data Shape**: What are the distributions, outliers, and patterns?
- **Data Compatibility**: Does this data actually match the use case requirements?
- **Transformation Requirements**: What cleaning, parsing, and validation is needed?

### The Reality of Customer Data

**"LLMs can't look at the file that's 4 gigabytes"** - Pedro

You need strategic sampling and validation because:
- Customer data is rarely clean (expect nulls, wrong types, invalid values)
- Files can be massive (4GB+, millions of rows)
- Broken data will crash ingestion code during execution
- Catching issues early prevents hours of debugging later

### This Toolkit "Sits on Shoulders of Giants"

**The toolkit's job**: Transform messy customer data → Proven Neo4j data models

- Neo4j use cases are battle-tested and authoritative
- Data quality validation ensures messy data CAN fit the proven model
- Code generation adapts the shite data to the clean model
- **Validation is the bridge between reality and the ideal**

---

## When to Run Data Quality Validation

**ALWAYS validate data before code generation when**:
1. User provides new/unknown data files
2. Use case has strict requirements (data types, required fields)
3. Data comes from unsophisticated sources (likely to be "a load of shite")
4. Previous loads failed or had warnings

**You can SKIP validation when**:
1. Regenerating code for already-validated data
2. User explicitly says "skip validation, just generate code"
3. Working with known, clean example datasets

---

## Core Validation Steps

### 1. File Discovery & Format Detection

**Check**: `workspace/raw_data/` directory

```python
# Discover files
import os
files = os.listdir('workspace/raw_data/')

# Identify formats
- .csv → CSV reader
- .json → JSON reader
- .parquet → Parquet reader
- .xlsx → Excel reader
```

**Report to user**:
```
Found data files:
- customers.csv (512 KB, CSV)
- transactions.json (2.3 MB, JSON)
```

### 2. Schema Discovery

**For CSV files**:
```python
import csv

with open('workspace/raw_data/data.csv', 'r') as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    sample = [next(reader) for _ in range(5)]  # First 5 rows
```

**For JSON files**:
```python
import json

with open('workspace/raw_data/data.json', 'r') as f:
    data = json.load(f)
    if isinstance(data, list):
        sample = data[:5]
    else:
        sample = [data]  # Single object
```

**Report to user**:
```
Schema for customers.csv:
- customer_id (e.g., "C001", "C002")
- email (e.g., "john@example.com")
- phone (e.g., "+1-555-0100")
- signup_date (e.g., "2023-01-15")
- account_balance (e.g., "1250.50")
```

### 3. Data Quality Checks

**Essential validations**:

#### A. Required Field Presence
```python
# Check if use case required fields exist in data
required_fields = ['customer_id', 'email']  # From use case
missing = [f for f in required_fields if f not in headers]

if missing:
    # CRITICAL ERROR - can't proceed
    log.error(f"Missing required fields: {missing}")
```

#### B. Null/Empty Value Detection
```python
# Sample-based null check (first 1000 rows or less)
null_counts = {}
for field in headers:
    null_count = sum(1 for row in sample if not row.get(field) or row[field].strip() == '')
    if null_count > 0:
        null_counts[field] = f"{null_count}/{len(sample)} rows"
```

**Report to user**:
```
⚠️  Null/Empty Values Detected:
- phone: 12/1000 rows (1.2%)
- middle_name: 450/1000 rows (45%)
```

#### C. Data Type Validation
```python
# Check if fields match expected types from use case
def infer_type(value):
    if value is None or value == '':
        return 'null'
    try:
        int(value)
        return 'integer'
    except:
        try:
            float(value)
            return 'float'
        except:
            return 'string'

type_issues = {}
for field, expected_type in use_case_types.items():
    sample_types = [infer_type(row[field]) for row in sample[:100]]
    actual_type = max(set(sample_types), key=sample_types.count)

    if actual_type != expected_type:
        type_issues[field] = f"Expected {expected_type}, found {actual_type}"
```

**Report to user**:
```
⚠️  Type Mismatches:
- account_balance: Expected float, found string (contains "$" signs)
- signup_date: Expected date, found string (format "MM/DD/YYYY")
```

#### D. Date/Datetime Validation
```python
from datetime import datetime

def validate_date(date_str, formats=['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y']):
    for fmt in formats:
        try:
            datetime.strptime(date_str, fmt)
            return True, fmt
        except:
            continue
    return False, None

# Check date fields
invalid_dates = []
for row in sample:
    date_val = row.get('signup_date')
    if date_val:
        valid, fmt = validate_date(date_val)
        if not valid:
            invalid_dates.append(date_val)
```

**Report to user**:
```
⚠️  Invalid Dates Found:
- signup_date: 5 invalid values (e.g., "2023-13-45", "N/A")
```

### 4. Statistical Analysis (For Numerical Fields)

**Purpose**: Detect outliers, understand distributions (for feature engineering later)

```python
import statistics

def analyze_numeric_field(values):
    clean_values = [float(v) for v in values if v and v != '']

    return {
        'count': len(clean_values),
        'min': min(clean_values),
        'max': max(clean_values),
        'mean': statistics.mean(clean_values),
        'median': statistics.median(clean_values),
        'stdev': statistics.stdev(clean_values) if len(clean_values) > 1 else 0
    }

# Example: transaction amounts
amounts = [row['amount'] for row in sample]
stats = analyze_numeric_field(amounts)
```

**Report to user**:
```
Transaction Amount Analysis:
- Count: 1000
- Range: $0.01 to $15,000.00
- Mean: $127.50
- Median: $45.00
- Std Dev: $520.30

⚠️  Potential outliers detected:
- 3 transactions > $10,000 (99.7th percentile)
```

**Why This Matters**:
- Identifies data quality issues (amounts of $0 or $10,000,000)
- Informs transformations (normalization, log scaling)
- Helps detect fraud patterns (unusual transaction sizes)

### 5. Cardinality & Uniqueness

**Check unique value counts**:

```python
def check_cardinality(field_values):
    unique = len(set(field_values))
    total = len(field_values)
    return {
        'unique': unique,
        'total': total,
        'ratio': unique / total if total > 0 else 0
    }

# Example: customer_id should be unique
customer_ids = [row['customer_id'] for row in sample]
cardinality = check_cardinality(customer_ids)

if cardinality['ratio'] < 1.0:
    # Duplicates found - potential data quality issue
    duplicates = total - unique
```

**Report to user**:
```
Uniqueness Analysis:
- customer_id: 1000/1000 unique (100%) ✓
- email: 987/1000 unique (98.7%) - 13 shared emails detected
- phone: 992/1000 unique (99.2%) - 8 shared phones detected

ℹ️  Shared identifiers are expected for fraud detection use cases
```

---

## Sample Size Strategy

**For large files** (>10MB or >100K rows):

```python
# Don't load entire file into memory
def sample_large_file(file_path, sample_size=1000):
    """
    Sample first N rows + random rows from file.
    Avoids loading multi-GB files entirely.
    """
    import random

    # Get total row count (fast)
    with open(file_path) as f:
        total_rows = sum(1 for _ in f) - 1  # Exclude header

    # Always include first 1000 rows (catch header issues)
    # Then random sample of remaining
    sample_rows = set(range(min(1000, total_rows)))

    if total_rows > 1000:
        random_rows = random.sample(range(1000, total_rows),
                                     min(sample_size - 1000, total_rows - 1000))
        sample_rows.update(random_rows)

    # Read only sampled rows
    sampled_data = []
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i in sample_rows:
                sampled_data.append(row)

    return sampled_data
```

**Inform user of sampling**:
```
📊 Validating large file (2.3 GB, ~5M rows)
Using stratified sample of 10,000 rows for validation...
```

---

## Validation Report Format

**Present findings clearly to user**:

```markdown
## Data Quality Validation Report

### Files Validated
- customers.csv (512 KB, 10,000 rows)
- transactions.json (2.3 MB, 50,000 records)

### Schema Compatibility with Use Case: Synthetic Identity Fraud

✅ **Required Fields Present**:
- customer_id ✓
- email ✓
- phone ✓

✅ **Optional Fields Available**:
- first_name, last_name (can be added to Customer node)
- signup_date (can be added to Customer node)

### Data Quality Issues

⚠️ **Issues Found**:

1. **Null Values**:
   - phone: 120/10,000 rows (1.2%) - MUST handle in code
   - middle_name: 4,500/10,000 rows (45%) - Optional field, safe to ignore

2. **Type Mismatches**:
   - signup_date: String format "MM/DD/YYYY" - needs parsing

3. **Invalid Values**:
   - email: 15 rows with malformed emails (missing @)
   - phone: 8 rows with invalid format (letters present)

4. **Duplicates**:
   - customer_id: 100% unique ✓
   - email: 98.7% unique - 130 shared emails (expected for fraud detection)
   - phone: 99.2% unique - 80 shared phones (expected for fraud detection)

### Statistical Summary

**Email Sharing Distribution**:
- 2 emails shared by 50+ customers (potential fraud ring)
- 15 emails shared by 10-49 customers
- 113 emails shared by 2-9 customers

**Phone Sharing Distribution**:
- 1 phone shared by 35 customers (potential fraud ring)
- 10 phones shared by 5-34 customers
- 69 phones shared by 2-4 customers

### Recommendations

✅ **Safe to Proceed** with the following adaptations:

1. **Handle Null Phones**:
   - Skip creating Phone nodes for rows with null/empty phone
   - Log count of skipped Phone relationships

2. **Parse Dates**:
   - Convert "MM/DD/YYYY" to ISO format for Neo4j
   - Set null for invalid dates (log warnings)

3. **Clean Email/Phone Values**:
   - Validate email format, skip invalid entries
   - Strip non-numeric characters from phone numbers

4. **Fraud Detection Opportunity**:
   - Shared identifiers already present in data
   - Expect fraud ring detection queries to find results

### Next Steps

Generate data_mapper.py with:
- Null handling for phone field
- Date parsing for signup_date
- Email/phone validation and cleaning
- Progress logging for 10K+ records
```

---

## Decision Tree: Proceed or Block?

### ✅ Safe to Generate Code When:
- All required fields present (even if some nulls)
- Data types are compatible (or easily convertible)
- Schema matches use case structure
- Issues can be handled in code (cleaning, parsing, skipping nulls)

### ⚠️ Warn User But Allow When:
- High percentage of nulls (>20%) in important fields
- Significant outliers detected
- Data quality is poor but recoverable

### 🛑 Block Code Generation When:
- Required fields completely missing from data
- File format unreadable/corrupted
- Data structure fundamentally incompatible with use case
- All rows have critical errors (100% bad data)

---

## Integration with Code Generation

**After validation, pass findings to generate_mapper.md**:

1. **Field Mapping**:
   - Source field → Use case property mappings
   - Which fields need transformations

2. **Data Cleaning Instructions**:
   - Null handling strategy per field
   - Date parsing formats
   - Type conversions needed

3. **Expected Warnings**:
   - How many rows might be skipped (nulls)
   - What cleaning will be logged

**Example handoff**:
```python
# Validation findings inform code generation:
mappings = {
    'customer_id': ('Customer', 'customerId', str),
    'email': ('Email', 'address', str, validate_email),
    'phone': ('Phone', 'phoneNumber', str, clean_phone),
    'signup_date': ('Customer', 'signupDate', parse_date_mmddyyyy)
}

null_handling = {
    'phone': 'skip_relationship',  # Don't create HAS_PHONE if null
    'middle_name': 'set_null'      # Optional property, can be null
}
```

---

## Key Principles

### The Professional Standard (From Pedro's Insights)

1. **"LLMs can't look at 4GB files"**
   - Use strategic sampling
   - Validate structure, not every row
   - Report findings clearly

2. **"Customer data will be a load of shite"**
   - Expect nulls, wrong types, invalid values
   - Build defensive code from validation findings
   - Transform data to proven model format

3. **"Fix it before Neo4j"**
   - Validate and clean BEFORE loading
   - Easier to debug CSV than graph database
   - Verification is harder once in Neo4j

4. **"Sits on shoulders of giants"**
   - Use case data model is proven and authoritative
   - Validation ensures data CAN fit that model
   - Code generation adapts messy data to clean model

### Remember:
> **"What happens when I execute this and there's a column that's broken?"**

Data quality validation answers this question BEFORE the code runs.

---

## See Also

- `generate_mapper.md` - Uses validation findings to generate code
- `discover_usecase.md` - Defines required fields and data model
- Working example: Sample data quality validation before generation
