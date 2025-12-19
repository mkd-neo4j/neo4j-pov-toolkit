# Analyzing Data Quality Before Code Generation

> **🛑 STOP**: Have you read [AGENT.md](../../AGENT.md)?
>
> If NO → Read it NOW before proceeding. It contains critical context about:
> - Your mission and core principles
> - When to read this file vs others
> - Essential tools and workflows
>
> This supporting agent assumes you've already read AGENT.md.

---

**Reference guide for analyzing raw data quality and structure before generating data loader code.**

---

## 🔧 Persona: You Are The Engineer

**When using this file, you are in Engineer mode.**

**Your focus**:
- Production readiness and defensive code preparation
- Data quality validation before writing code
- Understanding what errors to expect and handle
- Ensuring the code won't crash due to bad data

**What you DO as Engineer**:
- Analyze data quality: nulls, types, invalid values, distributions
- Sample large files strategically (can't load 4GB into memory)
- Check for data issues that will break code execution
- Report findings with specific counts and percentages
- Recommend transformations and defensive handling strategies
- Present analysis results in Cypher-style format showing data quality annotations

**What you DON'T do as Engineer (in this file)**:
- ❌ Schema mapping - that's Architect work (already done in Phase 1)
- ❌ Use case discovery - that's Architect work
- ❌ Write code yet - that comes next in generate_data_loader_code.md

**Critical principle**:
> **"You can't write defensive code if you don't know what you're defending against"** - Pedro Leitao

**When to use this file**:
- **Phase 2 only**: After architectural mapping is complete
- Before generating data_mapper.py code
- When user explicitly asks to validate data
- When switching from Architect mode to Engineer mode

**When NOT to use this file**:
- ❌ Phase 1 (schema mapping) - Architects don't validate data quality
- ❌ When user only asks "how does my data map to the model?"
- ❌ During use case exploration or data model discovery

**Your analysis depth**:
- **Full value analysis**: Count nulls, check types, find invalid values
- **Statistical analysis**: Distributions, outliers, cardinality
- **Production readiness**: What will break? What needs cleaning?
- **Defensive strategy**: How to handle each issue in code?

**Output format**:
```cypher
// Analyzed Mapping with Data Quality Annotations

(:Customer {
  customerId: customer_id,           // ✓ 100% unique, no nulls
  firstName: first_name,             // ✓ No nulls
  signupDate: signup_date            // ⚠️ Parse MM/DD/YYYY, 5 invalid dates (0.05%)
})

(:Email {
  address: email                     // ⚠️ 15 invalid formats (0.15%), skip during load
})

(:Phone {
  phoneNumber: phone                 // ⚠️ 120 nulls (1.2%), skip Phone node creation
})
```

**Next steps after analysis**:
"Data quality analysis complete. Proceeding to code generation with defensive handling for identified issues."

---

## Philosophy: Think Like a Data Scientist

> **"You need to do some thinking yourself like what happens when I execute this and there's a column that's broken, right?"** - Pedro Leitao

### The Professional Standard: Validate → Transform → Load

**Data scientists and data engineers ALWAYS profile and analyze data before production systems.** This is not optional. This is not "analysis for curiosity." This is the standard professional practice that separates production-ready systems from prototypes.

**Why Data Analysis is Critical**:
1. **You can't write defensive code if you don't know what you're defending against**
2. **"Customer is gonna give you is just a load of shite that you're gonna have to fix yourself"** - Pedro
3. **"It's much, much harder to verify once it gets into Neo4j"** - Pedro
4. **Fix issues BEFORE Neo4j, not after** - debugging in a graph database is a nightmare
5. **Your analysis output IS the specification for defensive code** - every finding becomes a requirement

### Think Like a Data Scientist: The ML Preparation Mindset

**Data scientists preparing for machine learning** perform this exact workflow:

1. **Profile the data**: Understand distributions, cardinality, data types, patterns
2. **Assess quality**: Find nulls, outliers, invalid values, type mismatches
3. **Design cleansing strategy**: Plan transformations, standardizations, handling rules
4. **Inform feature engineering**: Understanding data shape drives model decisions

**You're doing the same thing** - except instead of preparing for ML models, you're preparing to:
- Generate robust data loading code
- Handle edge cases and data quality issues
- Transform messy reality into clean Neo4j graph structures
- Build production-ready ingestion pipelines

### The Reality of Customer Data

**"LLMs can't look at the file that's 4 gigabytes"** - Pedro

You need strategic sampling and systematic analysis because:
- Customer data is rarely clean (expect nulls, wrong types, invalid values)
- Files can be massive (4GB+, millions of rows)
- Broken data will crash ingestion code during execution
- Catching issues early prevents hours of debugging later
- **Understanding distributions reveals patterns that drive defensive code decisions**

### This Toolkit "Sits on Shoulders of Giants"

**The toolkit's job**: Transform messy customer data → Proven Neo4j data models

- Neo4j use cases are battle-tested and authoritative
- Data quality validation ensures messy data CAN fit the proven model
- Code generation adapts the shite data to the clean model
- **Data analysis is the bridge between messy reality and the ideal model**

---

## The Three Domains of Data Analysis

**Professional data analysis has three distinct activities**, each building on the previous:

```
1. DATA PROFILING          2. QUALITY ASSESSMENT       3. CLEANSING STRATEGY
   (What you have)            (What's broken)             (How to fix)
         ↓                          ↓                           ↓
   Understanding              Finding Problems          Planning Transformations
         ↓                          ↓                           ↓
   ANALYSIS OUTPUT → → → → DEFENSIVE CODE REQUIREMENTS → → → CODE GENERATION
```

### Domain 1: Data Profiling (Understanding What You Have)

**Purpose**: Build a complete picture of your data's structure, shape, and patterns.

**Activities**:
- **Schema discovery**: What columns/fields exist? What are their names?
- **Type inference**: Are values strings, numbers, dates, booleans?
- **Cardinality analysis**: How many unique values per field? (1 = constant, N = unique identifier)
- **Distribution analysis**: For numerical fields - min, max, mean, median, standard deviation
- **Pattern recognition**: Common formats (dates, phones, emails), encoding (UTF-8, etc.)
- **Size assessment**: Row counts, file sizes, memory requirements

**Key Questions**:
- What's the shape of this data?
- What patterns emerge from the values?
- Which fields are high-cardinality? Low-cardinality?
- What are the value distributions for numerical fields?

**Output**: Complete understanding of data structure that informs both quality checks and transformation strategy.

---

### Domain 2: Data Quality Assessment (Finding What's Broken)

**Purpose**: Identify all data quality issues that will break code execution or corrupt the graph.

**The Four Dimensions of Data Quality**:

1. **Completeness**: Are required values present?
   - Null/empty value detection
   - Missing field identification
   - Percentage of missing data per field

2. **Validity**: Do values conform to expected formats/constraints?
   - Date format validation (can dates be parsed?)
   - Email format validation (contains @, valid structure)
   - Type constraint violations (strings in number fields)
   - Value range violations (negative amounts, impossible dates)

3. **Consistency**: Are values internally coherent?
   - Type consistency (are all values the same type?)
   - Encoding consistency (mixed character encodings)
   - Format consistency (dates in multiple formats)
   - Relationship integrity (foreign keys exist?)

4. **Accuracy**: Are values reasonable and within expected ranges?
   - Outlier detection (values far from mean/median)
   - Business rule violations (transaction amount = $0)
   - Suspicious patterns (all values identical, sequential patterns)

**Key Questions**:
- Which fields have nulls? How many? (Will this break required node properties?)
- Which fields have invalid formats? (Will parsing fail?)
- Are there type mismatches? (Strings where numbers expected?)
- Are there outliers or suspicious values? (Data entry errors? Fraud indicators?)

**Output**: Specific counts and percentages of issues that become defensive code requirements.

---

### Domain 3: Data Cleansing Strategy (Planning How to Fix)

**Purpose**: Design transformation and handling strategies for every identified issue.

**Activities**:
- **Standardization planning**: How to normalize formats (dates, phones, emails, currency)
- **Transformation design**: What parsing/conversion logic is needed?
- **Handling rules**: For each issue, decide: skip record? use default? transform? error?
- **Impact assessment**: How many records will be affected by each transformation?
- **Validation logic**: What checks should the code perform during load?

**The Transformation Playbook**:

| Issue Type | Example | Cleansing Strategy | Code Requirement |
|------------|---------|-------------------|------------------|
| **Null in optional field** | `middle_name: null` (45% nulls) | Accept nulls | Set property to null (no skip) |
| **Null in required field** | `phone: null` (1.2% nulls) | Skip creation | Skip Phone node creation for null values |
| **Invalid format** | `email: "notanemail"` (15 invalid) | Skip or validate | Validate email (contains @), skip if invalid |
| **Type mismatch** | `amount: "$1,250.50"` (string, needs float) | Parse and convert | Strip `$` and `,`, convert to float |
| **Date parsing** | `date: "01/15/2023"` (MM/DD/YYYY) | Parse to datetime | Use `datetime.strptime()` with format |
| **Outliers** | `amount: $10,000,000` (>99.9th percentile) | Log or validate | Log warning, optionally cap value |
| **Encoding issues** | `name: "Ren\xe9"` (mixed encoding) | Standardize encoding | Decode/encode to UTF-8 |

**Key Questions**:
- For each quality issue, what transformation is needed?
- Which issues can be fixed? Which require skipping records?
- What's the expected impact? (How many records skipped/transformed?)
- What validation logic should run during ingestion?

**Output**: Complete cleansing specification that directly drives code generation.

---

## From Analysis to Defensive Code: The Critical Link

> **"Your analysis output IS the specification for defensive code."**

Every finding in your data analysis **directly translates** to a defensive code requirement. This is the whole point of validation.

### The Analysis → Code Mapping

**Quality Issue** → **Code Requirement** → **Implementation**

#### Example 1: Null Values in Optional Fields
```
Analysis Finding:
- phone: 120/10,000 rows null (1.2%)
- Phone is optional for Customer (not required by use case)

Code Requirement:
- Skip Phone node creation when phone is null/empty
- Skip HAS_PHONE relationship creation

Implementation (in generate_data_loader_code.md):
```python
# In create_phone_nodes()
phone_data = [
    {'phoneNumber': record['phone']}
    for record in data
    if record.get('phone') and record['phone'].strip()  # ← Skip nulls/empty
]
```
```

#### Example 2: Type Mismatches (String → Number)
```
Analysis Finding:
- account_balance: Expected float, found string with "$" prefix
- Example values: "$1,250.50", "$45.00"

Code Requirement:
- Strip "$" prefix and commas
- Convert to float
- Handle conversion errors

Implementation:
```python
def clean_currency(value):
    """Remove $ and , from currency strings, convert to float."""
    try:
        return float(value.replace('$', '').replace(',', ''))
    except (ValueError, AttributeError):
        return None  # Or 0.0, depending on business rules

node_data = [
    {'balance': clean_currency(record['account_balance'])}
    for record in data
]
```
```

#### Example 3: Invalid Date Formats
```
Analysis Finding:
- signup_date: Format "MM/DD/YYYY" (needs parsing)
- 5 invalid dates found (0.05%): "2023-13-45", "N/A", "TBD"

Code Requirement:
- Parse dates with format "MM/DD/YYYY"
- Set null for invalid dates
- Log warnings for invalid dates

Implementation:
```python
from datetime import datetime

def parse_date_mmddyyyy(date_str):
    """Parse MM/DD/YYYY format, return None for invalid."""
    try:
        return datetime.strptime(date_str, '%m/%d/%Y')
    except (ValueError, AttributeError):
        log.warning(f"Invalid date format: {date_str}")
        return None

node_data = [
    {'signupDate': parse_date_mmddyyyy(record['signup_date'])}
    for record in data
]
```
```

#### Example 4: Invalid Value Formats (Email Validation)
```
Analysis Finding:
- email: 15 rows with invalid format (0.15%)
- Example invalid: "notanemail", "test@", "@example.com"

Code Requirement:
- Validate email format (must contain @ and domain)
- Skip Email node creation for invalid emails
- Log count of skipped emails

Implementation:
```python
def is_valid_email(email):
    """Basic email validation."""
    return email and '@' in email and '.' in email.split('@')[1]

# Skip invalid emails
email_data = [
    {'address': record['email'].lower()}  # Also: lowercase for consistency
    for record in data
    if is_valid_email(record.get('email'))
]

log.info(f"Skipped {original_count - len(email_data)} invalid emails")
```
```

### The Complete Analysis → Code Flow

```
┌─────────────────────────────────────────────────────────────┐
│  ANALYSIS PHASE (analyze_data_quality.md)                   │
│  ----------------------------------------------------------- │
│  1. Profile: Discover schema, types, distributions           │
│  2. Assess Quality: Find nulls, invalids, type mismatches   │
│  3. Plan Cleansing: Design transformations and handling     │
│                                                              │
│  OUTPUT: Cleansing Specification Report                      │
│  - Field mapping with quality annotations                    │
│  - Transformation requirements per field                     │
│  - Expected skip counts and impacts                          │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  CODE GENERATION PHASE (generate_data_loader_code.md)       │
│  ----------------------------------------------------------- │
│  1. Read analysis findings (cleansing spec)                  │
│  2. Generate transformation functions (parsing, validation)  │
│  3. Implement null handling (skip logic)                     │
│  4. Add error handling and logging                           │
│  5. Create defensive, production-ready code                  │
│                                                              │
│  OUTPUT: workspace/generated/data_mapper.py                  │
│  - Handles all identified quality issues                     │
│  - Implements all required transformations                   │
│  - Logs warnings for skipped/invalid data                    │
└─────────────────────────────────────────────────────────────┘
```

**This is why validation is mandatory** - you literally cannot write good defensive code without understanding what you're defending against.

---

## When to Analyze Data Quality

**ALWAYS analyze data before code generation when**:
1. User provides new/unknown data files
2. Use case has strict requirements (data types, required fields)
3. Data comes from unsophisticated sources (likely to be "a load of shite")
4. Previous loads failed or had warnings

**You can SKIP analysis when**:
1. Regenerating code for already-analyzed data
2. User explicitly says "skip analysis, just generate code"
3. Working with known, clean example datasets

---

## How to Perform the Analysis: Practical Workflow

**IMPORTANT**: The sections below describe *what* to analyze, not *how* to implement it. You decide the implementation approach - the LLM can work out Python details.

### Step 1: File Discovery & Format Detection

**Check**: `workspace/raw_data/` directory

**Discover**:
- What files exist?
- What formats? (.csv, .json, .parquet, .xlsx, etc.)
- What sizes? (impacts sampling strategy)
- What encoding? (UTF-8, Latin-1, etc.)

**Report to user**:
```
Found data files:
- customers.csv (512 KB, 10,000 rows, CSV format)
- transactions.json (2.3 MB, 50,000 records, JSON format)
```

---

### Step 2: Schema Discovery & Type Inference

**Apply Domain 1: Data Profiling**

**Discover for each field/column**:
- Field names and structure
- Data types (string, int, float, date, boolean)
- Example values (show user what data looks like)
- Cardinality (unique values count)

**Report to user** (show schema with examples):
```
Schema for customers.csv:
- customer_id: string, unique (e.g., "C001", "C002") - 100% unique
- email: string (e.g., "john@example.com") - 98.7% unique
- phone: string (e.g., "+1-555-0100") - 99.2% unique
- signup_date: string (e.g., "01/15/2023") - date format MM/DD/YYYY
- account_balance: string (e.g., "$1,250.50") - currency format with $ prefix
```

**Key insight**: Show users what their data *actually* looks like, not what they think it looks like.

---

### Step 3: Data Quality Assessment

**Apply Domain 2: Quality Assessment (The Four Dimensions)**

For each field, assess across all four quality dimensions:

#### Dimension 1: Completeness
- **Count nulls/empty values** per field
- **Percentage** of missing data
- **Impact**: Which fields are required vs optional?

**Report findings**:
```
⚠️ Completeness Issues:
- phone: 120/10,000 rows null (1.2%) - Optional field
- middle_name: 4,500/10,000 rows null (45%) - Optional field
- customer_id: 0 nulls ✓ - Required field
```

#### Dimension 2: Validity
- **Date format validation**: Can dates be parsed?
- **Email format validation**: Contains @, valid structure?
- **Type constraint validation**: Strings in number fields?
- **Value range validation**: Negative amounts? Impossible dates?

**Report findings**:
```
⚠️ Validity Issues:
- signup_date: 5 invalid formats (e.g., "2023-13-45", "N/A") - 0.05%
- email: 15 invalid formats (missing @) - 0.15%
- account_balance: All values have "$" prefix - needs cleaning
```

#### Dimension 3: Consistency
- **Type consistency**: Are all values the same type per field?
- **Format consistency**: Dates in multiple formats? (MM/DD/YYYY vs YYYY-MM-DD)
- **Encoding**: Mixed character encodings?

**Report findings**:
```
⚠️ Consistency Issues:
- signup_date: Format "MM/DD/YYYY" consistent ✓
- phone: Multiple formats detected ("+1-555-0100", "555-0100", "5550100")
```

#### Dimension 4: Accuracy
- **For numerical fields**: Min, max, mean, median, standard deviation
- **Outlier detection**: Values far from mean/median (>3 std devs)
- **Business rule validation**: Transaction amount = $0? Ages > 120?

**Report findings**:
```
⚠️ Accuracy Issues (Statistical Analysis):
Transaction amounts:
- Range: $0.01 to $15,000.00
- Mean: $127.50, Median: $45.00, Std Dev: $520.30
- Outliers: 3 transactions > $10,000 (99.7th percentile) - possible fraud indicators
```

---

### Step 4: Cardinality Analysis (Context for Graph Structure)

**Purpose**: Understand value distributions - informs graph structure decisions.

**For each field, determine**:
- **Low cardinality** (few unique values): Good for categorical properties
- **High cardinality** (many/all unique): Good for identifiers or indexed properties
- **Shared values**: Important for fraud detection (shared emails, phones)

**Report findings**:
```
Cardinality Analysis:
- customer_id: 10,000/10,000 unique (100%) ✓ - Unique identifier
- email: 9,870/10,000 unique (98.7%) - 130 shared emails (fraud indicator)
- phone: 9,920/10,000 unique (99.2%) - 80 shared phones (fraud indicator)
- country: 5 unique values - Low cardinality (categorical property)
```

**Why This Matters for Fraud Detection**:
- Shared emails/phones → Potential fraud rings (important for graph queries)
- High sharing = strong signal for fraud detection use case

---

### Step 5: Sampling Strategy for Large Files

**For files >10MB or >100K rows**:

**Strategic sampling approach**:
1. **Get total row count** (fast scan, don't load full file)
2. **Always sample first 1,000 rows** (catch header/formatting issues)
3. **Random sample from remainder** (representative of overall data)
4. **Use ~10,000 total rows for validation** (balance between coverage and memory)

**Inform user of sampling**:
```
📊 Large file detected: customers.csv (2.3 GB, ~5M rows)
Using stratified sample of 10,000 rows for validation:
- First 1,000 rows (sequential)
- 9,000 random rows from remainder
```

**Why this approach**:
- **"LLMs can't look at 4GB files"** - must sample strategically
- **Representative sample** catches most quality issues
- **Fast execution** vs loading millions of rows

---

### Step 6: Design Cleansing Strategy

**Apply Domain 3: Cleansing Strategy**

**For EVERY quality issue identified**, design the transformation/handling approach:

**Use the Transformation Playbook** (from Domain 3 section above):
- Nulls in optional fields → Accept (set property to null)
- Nulls in required fields → Skip creation (log count)
- Invalid formats → Skip or validate (log count)
- Type mismatches → Parse/convert (handle errors)
- Date parsing → Use appropriate format string
- Outliers → Log warnings, decide on handling

**Report cleansing strategy**:
```
Cleansing Strategy Plan:

1. phone field (120 nulls, 1.2%):
   → Skip Phone node creation for null/empty values
   → Expected impact: Skip 120 Phone nodes, 120 HAS_PHONE relationships

2. signup_date field (5 invalid, 0.05%):
   → Parse with format "MM/DD/YYYY"
   → Set null for invalid dates, log warnings
   → Expected impact: 5 null signup dates

3. email field (15 invalid, 0.15%):
   → Validate email format (contains @)
   → Skip Email node creation for invalid emails
   → Lowercase all emails for consistency
   → Expected impact: Skip 15 Email nodes, 15 HAS_EMAIL relationships

4. account_balance field (all have "$" prefix):
   → Strip "$" and "," characters
   → Convert to float
   → Expected impact: All 10,000 records transformed
```

**This cleansing strategy becomes the INPUT to code generation.**

---

## Analysis Report Format

**Present findings to user in THREE sections**: Schema Mapping, Quality Issues, and Cleansing Strategy.

**This report IS the input specification for code generation.**

---

### Report Template

```markdown
## Data Quality Analysis Report

### Files Analyzed
- customers.csv (512 KB, 10,000 rows)
- transactions.json (2.3 MB, 50,000 records)

---

### 1. Planned Schema Mapping

**Use Case**: Synthetic Identity Fraud Detection

**Mapping** (Cypher format with quality annotations):

```cypher
// Node Mappings with Data Quality Annotations

(:Customer {
  customerId: customer_id,           // Source: customers.csv 'customer_id' - ✓ 100% unique, no nulls

  // Extended properties (beyond base model)
  firstName: first_name,             // Source: customers.csv 'first_name' - ✓ no nulls
  lastName: last_name,               // Source: customers.csv 'last_name' - ✓ no nulls
  signupDate: signup_date            // Source: customers.csv 'signup_date' - ⚠️ parse MM/DD/YYYY, 5 invalid (0.05%)
})

(:Email {
  address: email                     // Source: customers.csv 'email' - ⚠️ 15 invalid formats (0.15%)
})

(:Phone {
  phoneNumber: phone                 // Source: customers.csv 'phone' - ⚠️ 120 nulls (1.2%), 8 invalid formats
})

// Relationships
(:Customer)-[:HAS_EMAIL]->(:Email)   // Create for valid emails only
(:Customer)-[:HAS_PHONE]->(:Phone)   // Skip when phone is null or invalid
```

---

### 2. Data Quality Issues (By Dimension)

#### Completeness
- **phone**: 120/10,000 rows null (1.2%) - Required field for Phone node
- **middle_name**: 4,500/10,000 rows null (45%) - Optional field

#### Validity
- **signup_date**: 5 invalid date formats (0.05%) - Examples: "2023-13-45", "N/A", "TBD"
- **email**: 15 invalid email formats (0.15%) - Examples: "notanemail", "test@", "@example.com"
- **phone**: 8 invalid phone formats (0.08%) - Examples: letters present, too short

#### Consistency
- **signup_date**: Format "MM/DD/YYYY" consistent across valid values ✓
- **phone**: Multiple formats detected ("+1-555-0100", "555-0100", "5550100") - needs standardization

#### Accuracy (Statistical Analysis)
**Cardinality** (Fraud Detection Context):
- **customer_id**: 10,000/10,000 unique (100%) ✓ - Unique identifier
- **email**: 9,870/10,000 unique (98.7%) - **130 shared emails** (fraud ring indicator)
- **phone**: 9,920/10,000 unique (99.2%) - **80 shared phones** (fraud ring indicator)

**Email Sharing Distribution** (Fraud Ring Detection):
- 2 emails shared by 50+ customers (strong fraud ring signal)
- 15 emails shared by 10-49 customers (moderate fraud ring signal)
- 113 emails shared by 2-9 customers (weak fraud ring signal)

**Phone Sharing Distribution** (Fraud Ring Detection):
- 1 phone shared by 35 customers (strong fraud ring signal)
- 10 phones shared by 5-34 customers (moderate fraud ring signal)
- 69 phones shared by 2-4 customers (weak fraud ring signal)

---

### 3. Cleansing Strategy (Input to Code Generation)

**This section specifies EXACTLY what defensive code to generate.**

| Field | Issue | Cleansing Action | Code Requirement | Expected Impact |
|-------|-------|-----------------|------------------|-----------------|
| **phone** | 120 nulls (1.2%) | Skip creation | Skip Phone node and HAS_PHONE relationship for null/empty values | Skip 120 Phone nodes, 120 relationships |
| **phone** | 8 invalid formats | Skip creation | Validate phone format, skip if invalid | Skip 8 Phone nodes, 8 relationships |
| **signup_date** | 5 invalid (0.05%) | Set null | Parse "MM/DD/YYYY", set null if invalid, log warnings | 5 null signup dates |
| **email** | 15 invalid (0.15%) | Skip creation | Validate email (contains @), skip Email node if invalid | Skip 15 Email nodes, 15 relationships |
| **email** | All values | Standardize | Lowercase all emails for consistency | All 10,000 emails lowercased |
| **middle_name** | 4,500 nulls (45%) | Accept | Set property to null (optional field) | 4,500 null middle_name properties |

**Transformation Functions Required**:

1. **parse_date_mmddyyyy()**: Parse "MM/DD/YYYY" format, return None for invalid
2. **is_valid_email()**: Check email contains @ and valid domain
3. **clean_phone()**: Strip non-numeric chars, validate length
4. **clean_currency()**: Strip "$" and ",", convert to float

**Expected Load Results**:
- **Customers**: 10,000 nodes created
- **Emails**: 9,985 nodes created (15 skipped for invalid format)
- **Phones**: 9,872 nodes created (120 nulls + 8 invalid = 128 skipped)
- **HAS_EMAIL relationships**: 9,985 created
- **HAS_PHONE relationships**: 9,872 created

---

### 4. Fraud Detection Opportunities

✅ **Data Quality Supports Use Case**:

- **Shared identifiers present**: 130 shared emails, 80 shared phones
- **Fraud ring patterns detectable**: Multiple accounts sharing contact information
- **Graph queries will reveal**: Connected components of suspicious customers
- **Expected results**: Fraud detection queries will find meaningful patterns

---

### Next Steps

✅ **Safe to Proceed with Code Generation**

Generate `workspace/generated/data_mapper.py` with:
1. **Transformation functions**: parse_date_mmddyyyy, is_valid_email, clean_phone, clean_currency
2. **Null handling**: Skip Phone/Email node creation for null/invalid values
3. **Validation logic**: Email format, phone format, date parsing
4. **Error logging**: Log counts of skipped records (expected: 128 phones, 15 emails)
5. **Progress tracking**: Log every 50K records for large datasets
6. **Defensive error handling**: Handle all identified quality issues

**Input to code generation**: This cleansing strategy specification
```

---

### Key Principles for Report Format

1. **Cypher-style mapping** - Users see exactly what graph structure will be created
2. **Quality annotations inline** - Issues annotated directly on field mappings
3. **Cleansing strategy table** - Explicit Issue → Action → Code → Impact mapping
4. **Expected impacts quantified** - "Skip 128 Phone nodes" not "skip some records"
5. **This report IS the spec** - Code generation reads this to generate defensive code

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


## Key Principles: The Data Scientist Mindset

### Think in Three Domains

1. **Profile** (What you have)
   - Understand structure, types, distributions
   - Reveal patterns, cardinality, value ranges
   - Build complete picture before assessing quality

2. **Assess** (What's broken)
   - Completeness: nulls, missing values
   - Validity: format violations, type mismatches
   - Consistency: encoding, format variations
   - Accuracy: outliers, business rule violations

3. **Cleanse** (How to fix)
   - Standardization: normalize formats
   - Transformation: parsing, conversion logic
   - Handling: skip, default, error strategies
   - Impact: quantify expected results

### Every Finding → Defensive Code Requirement

**Your analysis output IS the specification for defensive code.**

- Null in required field → Skip node creation (code requirement)
- Invalid format → Validation function (code requirement)
- Type mismatch → Parsing function (code requirement)
- Outlier → Logging/handling logic (code requirement)

**This is why validation is mandatory** - you cannot write good defensive code without understanding what you're defending against.

### The Professional Standard (From Pedro's Insights)

1. **"LLMs can't look at 4GB files"**
   - Use strategic sampling (first 1K + random sample)
   - Validate structure, not every row
   - Report findings clearly with counts and percentages

2. **"Customer data will be a load of shite"**
   - Expect nulls, wrong types, invalid values
   - **Profile first** to understand what you're dealing with
   - Build defensive code from validation findings
   - Transform messy reality to clean proven model

3. **"Fix it before Neo4j"**
   - Validate and clean BEFORE loading
   - Easier to debug CSV than graph database
   - Verification is harder once in Neo4j
   - **Analysis prevents debugging later**

4. **"Sits on shoulders of giants"**
   - Use case data model is proven and authoritative
   - **Data profiling** reveals what's in your data
   - **Quality assessment** identifies gaps between data and model
   - **Cleansing strategy** bridges the gap
   - Code generation implements the cleansing strategy

### Remember:
> **"You need to do some thinking yourself like what happens when I execute this and there's a column that's broken, right?"** - Pedro Leitao

**Data quality analysis answers this question BEFORE the code runs.**

That's the entire point - understand the data like a data scientist preparing for production ML, then generate defensive code that handles every identified issue.

---

## See Also

- `generate_data_loader_code.md` - Uses analysis findings (cleansing strategy) to generate defensive code
- `fetch_neo4j_data_models.md` - Defines required fields and authoritative data model
- `../../AGENT.md` - Overall toolkit guidance and workflow
- Working example: Complete data quality analysis with cleansing strategy before code generation
