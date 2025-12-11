# Example: Multi-File Banking Fraud Detection Dataset

**Complexity Level:** Advanced
**Data Sources:** 5 interconnected files (CSV + JSON)
**Source:** [Kaggle - Transactions Fraud Dataset](https://www.kaggle.com/datasets/computingvictor/transactions-fraud-datasets)

---

## Overview

This example demonstrates how to handle a **complex, multi-file dataset** where different aspects of the data (customers, cards, transactions, merchants, fraud labels) are spread across separate files that must be joined together into a cohesive Neo4j graph model.

**Key Learning Points:**
- How to discover and understand relationships across multiple data files
- How to collaborate with the LLM to design an appropriate data model
- How to extend Neo4j standard models while maintaining best practices
- How to validate the model before writing code
- How to handle large-scale data transformations

---

## The Challenge

### Dataset Components

The dataset consists of **5 separate files** with different formats and purposes:

1. **`users_data.csv`** (161KB) - Customer demographic information
   - Customer ID, age, income, credit score, address with lat/long
   - ~2,000 customer records

2. **`cards_data.csv`** (498KB) - Credit/debit card details
   - Card numbers, types, limits, activation dates
   - ~5,000 card records
   - Links to customers via `client_id`

3. **`transactions_data.csv`** (1.2GB) - Transaction records
   - Transaction amounts, dates, merchant details
   - ~23 million transaction records
   - Links to cards via `card_id`
   - Links to merchants via `merchant_id`

4. **`mcc_codes.json`** (4.6KB) - Merchant category codes
   - Standard MCC code descriptions
   - Used to enrich merchant data

5. **`train_fraud_labels.json`** (152MB) - Fraud labels
   - Binary fraud flags for each transaction
   - Format: `{"target": {"txn_id": "Yes"/"No", ...}}`

### The Complexity

Unlike a simple single-file import, this requires:
- **Understanding implicit relationships** between files
- **Joining data** from multiple sources
- **Enriching data** with lookup tables (MCC codes)
- **Handling different formats** (CSV, JSON)
- **Managing scale** (23M+ transactions)
- **Extending a standard model** to fit the actual data

---

## The LLM Interaction Flow

### Phase 1: Data Discovery

**User Initial Request:**
```
I want to work on the data in the raw data and I want to load it into
Neo4j like is described in the prompt. However, the data that sits in
there is a little bit more complicated than just like a single file.
```

**What Happened:**
The LLM immediately recognized it needed to understand the data structure before proceeding. It:

1. **Listed all files** to see what's available
2. **Inspected file headers** to understand columns
3. **Examined sample data** from each file
4. **Analyzed JSON structures** for nested data
5. **Identified relationships** between files

**Key Commands Run:**
```bash
ls -lh workspace/raw_data/
head -5 workspace/raw_data/transactions_data.csv
head -5 workspace/raw_data/cards_data.csv
head -5 workspace/raw_data/users_data.csv
head -20 workspace/raw_data/train_fraud_labels.json
```

**Critical Discovery:** The LLM identified the join keys:
- `users_data.id` → `cards_data.client_id`
- `cards_data.id` → `transactions_data.card_id`
- `transactions_data.merchant_id` → (creates Merchant nodes)
- `transactions_data.id` → `fraud_labels["target"]` keys

---

### Phase 2: Model Design Collaboration

**User Provided Context:**
```
The dataset includes transaction records, customer information, card data,
merchant details, and fraud labels. I want it to align to the Neo4j
transactional data model as well.

Make sure we align it as closely as we can to:
https://neo4j.com/developer/industry-use-cases/_attachments/llm-transaction-base-model.txt

If we need to add some new fields or nodes, that's absolutely fine.
We're more than happy to extend it, but make sure you follow the same
standards as defined in the data model.
```

**What the LLM Did:**

1. **Fetched the reference model** to understand the standard structure
2. **Proposed an initial mapping** from source data to Neo4j nodes
3. **Entered Plan Mode** to discuss the model before writing code

**Initial Proposal:**

The LLM presented this mapping:

```
Core Mappings:

1. Customer ← users_data.csv
   - customerId ← id
   - dateOfBirth ← derive from birth_year + birth_month
   - Extensions: gender, creditScore, yearlyIncome, totalDebt

2. Account ← cards_data.csv
   - accountNumber ← card_number
   - accountType ← card_type (Debit/Credit)
   - Extensions: cardBrand, creditLimit, hasChip, cardOnDarkWeb

3. Transaction ← transactions_data.csv
   - transactionId ← id
   - amount, date, currency
   - Extensions: isFraud (from labels), errors, type

4. Merchant (NEW NODE - not in base model)
   - merchantId, merchantCity, merchantState
   - mccCode + description from mcc_codes.json

5. Address ← users_data.csv
   - addressLine1 ← address
   - latitude, longitude
```

**Key Discussion Point:** The LLM proposed using `Account` nodes (from the base model) to represent cards.

---

### Phase 3: Model Refinement

**User Feedback:**
```
Let's change that to card. So instead of being account number, the node
would be Card. It'd be card number, card type. We'll keep open date.
We can remove the internal label because it's a card, but then keep the
card brand limit, etc. So let's update account so that it reflects it
being a Card.

For this use case, because of it being test data, let's also drop the
Country nodes as everything is going to be connected to everything else.
```

**What This Shows:**

This is a **critical collaboration moment**. The user:
- ✅ **Refined the model** to better match domain semantics (Card vs Account)
- ✅ **Kept Neo4j conventions** (camelCase properties, clear node names)
- ✅ **Simplified for the use case** (removed Country for single-country data)
- ✅ **Extended beyond the base model** (added Card-specific properties)

**Revised Model:**

```
Final Node Design:

(:Card {                          // Changed from :Account
  cardId: String,                 // Not accountNumber
  cardNumber: String,
  cardBrand: String,              // Extension (Visa, Mastercard)
  cardType: String,               // Debit/Credit
  creditLimit: Float,             // Extension
  hasChip: Boolean,               // Extension
  cardOnDarkWeb: Boolean,         // Extension (risk indicator)
  openDate: DateTime,
  expires: String,
  cvv: String
})
```

**This demonstrates:**
- The model **extends** the base model appropriately
- Properties follow Neo4j naming conventions (camelCase)
- Domain-specific fields are added where they make sense
- The LLM maintains standards while being flexible

---

### Phase 4: Data Model Validation

Before writing any code, the LLM presented a complete plan showing:

**Nodes to Create:**
- Customer (2,000 nodes)
- Card (5,000 nodes) - **Modified from base model**
- Transaction (23M nodes)
- Merchant (67,000 nodes) - **New node type**
- Address (2,000 nodes)

**Relationships to Create:**
- Customer-[:HAS_CARD]->Card - **Modified from :HAS_ACCOUNT**
- Card-[:PERFORMS]->Transaction
- Transaction-[:AT_MERCHANT]->Merchant - **New relationship**
- Customer-[:HAS_ADDRESS]->Address

**Data Transformations Required:**
```python
# Amount parsing (handle "$" and negatives)
"$-77.00" → 77.00 (absolute value, float)

# Date parsing (multiple formats)
"2010-01-01 00:01:00" → ISO datetime
"09/2002" → first day of month

# Boolean conversions
"YES" → true
"NO" → false

# Fraud label joining
fraud_labels["target"]["7475327"] → Transaction.isFraud
```

**User Approved:** The plan was reviewed and confirmed before any code generation.

---

## The Implementation

### Code Structure

The generated `data_mapper.py` follows a clear pattern:

```python
# 1. Data Loading Functions (one per file)
load_users_data()
load_cards_data()
load_transactions_data()
load_mcc_codes()
load_fraud_labels()

# 2. Data Transformation Helpers
parse_amount(amount_str)          # "$100.00" → 100.0
parse_date(date_str)              # "YYYY-MM-DD HH:MM:SS" → ISO
parse_account_open_date(date_str) # "MM/YYYY" → ISO
str_to_bool(value)                # "YES" → true

# 3. Schema Creation
create_constraints(query)
create_indexes(query)

# 4. Node Creation Functions (one per node type)
create_customer_nodes(query, users_data)
create_address_nodes(query, users_data)
create_card_nodes(query, cards_data)
create_merchant_nodes(query, transactions_data, mcc_codes)
create_transaction_nodes(query, transactions_data, fraud_labels)

# 5. Relationship Creation Functions
create_customer_address_relationships(query, users_data)
create_customer_card_relationships(query, cards_data)
create_card_transaction_relationships(query, transactions_data)
create_transaction_merchant_relationships(query, transactions_data)

# 6. Verification
verify_load(query)
```

### Key Implementation Details

#### Handling Multi-File Joins

**Merchant Creation** (from transaction data + MCC lookup):
```python
def create_merchant_nodes(query, transactions_data, mcc_codes):
    # Extract unique merchants from transactions
    merchants = {}
    for record in transactions_data:
        merchant_id = record.get('merchant_id')
        if merchant_id and merchant_id not in merchants:
            mcc_code = record.get('mcc', '')
            merchants[merchant_id] = {
                'merchantId': merchant_id,
                'merchantCity': record.get('merchant_city'),
                'mccCode': mcc_code,
                'mccDescription': mcc_codes.get(mcc_code, 'Unknown')  # Lookup!
            }
```

**Fraud Label Integration:**
```python
def create_transaction_nodes(query, transactions_data, fraud_labels):
    transaction_data = []
    for record in transactions_data:
        txn_id = record['id']
        transaction_data.append({
            'transactionId': txn_id,
            'amount': parse_amount(record.get('amount')),
            'isFraud': fraud_labels.get(txn_id, False)  # Join via dict lookup
        })
```

#### Efficient Batching for 23M Records

```python
cypher = """
UNWIND $batch AS row
MERGE (t:Transaction {transactionId: row.transactionId})
SET t.amount = row.amount,
    t.currency = row.currency,
    t.date = datetime(row.date),
    t.isFraud = row.isFraud
"""

# Process in 1000-record batches
query.run_batched(cypher, transaction_data, batch_size=1000)
```

---

## Key Lessons from This Example

### 1. **Data Discovery is Critical**

Before designing the model, you must understand:
- What files exist
- What columns/fields each contains
- How files relate to each other
- Data formats and edge cases

**LLM Pattern:** The assistant automatically inspected files before proposing a model.

### 2. **Model Design is Collaborative**

The LLM proposed an initial model based on the base template, but the user refined it:
- Changed Account → Card (better domain fit)
- Removed Country nodes (simplified for use case)
- Kept extensions that added value

**This is the correct workflow** - validate before implementing.

### 3. **Extensions are Expected and Encouraged**

The final model includes many properties not in the base model:
- `Card.cardBrand`, `Card.cardOnDarkWeb`, `Card.hasChip`
- `Transaction.isFraud`, `Transaction.errors`
- `Customer.creditScore`, `Customer.yearlyIncome`
- `Merchant` node type (entirely new)

**Standards were maintained:**
- Property names use camelCase
- Node labels use PascalCase
- Relationship types use UPPER_SNAKE_CASE
- Constraints ensure data integrity

### 4. **Complex Data Requires Helper Functions**

The code includes numerous transformation helpers:
```python
parse_amount("$-77.00") → 77.0
parse_date("2010-01-01 00:01:00") → ISO format
parse_account_open_date("09/2002") → ISO format
str_to_bool("YES") → true
```

These handle the messy reality of real-world data.

### 5. **Verification Provides Confidence**

The final verification step confirms:
```
✓ 2,000 Customer nodes
✓ 5,000 Card nodes
✓ 23,853,658 Transaction nodes
✓ 67,890 Merchant nodes
✓ 8,007 Fraudulent transactions
✓ 5,000 HAS_CARD relationships
✓ 23,853,658 PERFORMS relationships
✓ 23,853,658 AT_MERCHANT relationships
```

---

## Prompting Tips for Complex Multi-File Scenarios

### ✅ DO:

1. **Provide Dataset Context Early**
   ```
   "This dataset has multiple files - users, cards, transactions,
   and fraud labels. They link together via IDs."
   ```

2. **Share Dataset Documentation**
   Include descriptions from Kaggle, README files, or data dictionaries.

3. **Request Data Discovery First**
   ```
   "Can you examine the files and help me understand how they
   relate before we design the model?"
   ```

4. **Validate the Model Before Coding**
   ```
   "Let's discuss the data model first. I want to make sure
   we get it right before writing code."
   ```

5. **Be Specific About Extensions**
   ```
   "I want to use Card nodes instead of Account nodes,
   and add properties for card brand and dark web status."
   ```

6. **Simplify When Appropriate**
   ```
   "Since this is all US data, we can skip Country nodes."
   ```

### ❌ DON'T:

1. **Don't Rush to Code**
   Bad: "Just load this data into Neo4j"
   Good: "Help me understand this data, then we'll design a model"

2. **Don't Assume the LLM Knows Your Data**
   Provide file names, descriptions, and key relationships.

3. **Don't Force a Perfect Match to Base Models**
   The base model is a starting point, not a rigid requirement.

4. **Don't Skip Verification**
   Always include verification queries to confirm the load worked.

---

## Example Prompting Sequence

Here's how the user successfully navigated this complex scenario:

### Step 1: Set Context
```
"I have banking transaction data from Kaggle. It's split across
5 files: users, cards, transactions, merchant codes, and fraud labels.
I want to load this into Neo4j following the transaction base model."
```

### Step 2: Request Discovery
```
"The data is more complicated than a single file. Can you help
me understand the structure before we build the model?"
```

**LLM Response:** Inspects files, identifies relationships, shows sample data

### Step 3: Provide Reference Model
```
"Let's align to this Neo4j model:
https://neo4j.com/developer/industry-use-cases/.../llm-transaction-base-model.txt

But we can extend it where needed to match our actual data."
```

### Step 4: Review and Refine Model
```
"I like the approach, but let's use Card nodes instead of Account
nodes - that's more accurate for this data. Also, drop Country nodes
since everything is US-based."
```

### Step 5: Confirm Before Implementation
**LLM:** Presents revised plan with Card nodes, new properties, Merchant nodes
**User:** Approves the plan
**LLM:** Generates the implementation code

---

## The Result

A production-ready data mapper that:
- ✅ Loads 23M+ transactions efficiently
- ✅ Joins data from 5 different sources
- ✅ Extends the base model appropriately
- ✅ Maintains Neo4j best practices
- ✅ Includes fraud detection properties
- ✅ Provides verification and logging
- ✅ Handles data transformation edge cases

**Final Graph Structure:**
```
(Customer)-[:HAS_CARD]->(Card)-[:PERFORMS]->(Transaction)-[:AT_MERCHANT]->(Merchant)
    |                                          |
    |                                          |
    +--[:HAS_ADDRESS]->(Address)          [isFraud: true/false]
```

---

## Key Takeaway

**Complex multi-file datasets require collaboration between the user and the LLM.**

The workflow is:
1. **Discover** - Understand the data structure
2. **Design** - Collaborate on the model (extend base models as needed)
3. **Validate** - Confirm the model before coding
4. **Implement** - Generate transformation code
5. **Verify** - Confirm the data loaded correctly

This example shows that the toolkit is **not limited to exact matches** with base models. It's designed to help you build **the right model for your data** while maintaining Neo4j standards and best practices.
