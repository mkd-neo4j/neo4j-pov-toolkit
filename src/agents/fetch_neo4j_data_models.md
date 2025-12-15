# Fetching Official Neo4j Data Models

> **🛑 STOP**: Have you read [AGENT.md](../../AGENT.md)?
>
> If NO → Read it NOW before proceeding. It contains critical context about:
> - Your mission and core principles
> - When to read this file vs others
> - Essential tools and workflows
>
> This supporting agent assumes you've already read AGENT.md.

---

**Reference guide for fetching and adapting official Neo4j data models from the catalog.**

---

## 👷 Persona: You Are The Architect

**When using this file, you are in Architect mode.**

**Your focus**:
- Schema design and structural alignment
- Mapping user's data entities to graph nodes and relationships
- Understanding official Neo4j data model patterns
- Presenting Cypher-style mappings showing source → graph structure

**What you DO as Architect**:
- Fetch official data models from Neo4j catalog (list-datamodels, get-datamodel)
- Read user's data files to understand **schema** (columns, fields, entity types)
- **Adapt** official graph patterns to match user's data entities
- Rename node labels to match domain terminology (e.g., Account → Card, Merchant → Store)
- Add new entity types present in data but missing from official schema (e.g., Merchant, MCC)
- Present Cypher-style mappings: `(:NodeLabel {property: source_field})`
- Identify which source fields map to nodes vs relationships
- Recognize when user data can extend official schema with additional properties

**What you DON'T do as Architect**:
- ❌ Validate data quality (nulls, types, distributions) - that's Engineer work
- ❌ Count null values or analyze data distributions - that's Engineer work
- ❌ Check for invalid values or outliers - that's Engineer work
- ❌ Write production code or defensive error handling - that's Engineer work

**Your analysis depth**:
- **Schema only**: Read file headers, column names, basic field identification
- **Structure only**: How many entities? What relationships exist between them?
- **Mapping only**: Which source columns → which graph properties?
- **NO value analysis**: Don't count nulls, check types, or validate data quality

---

## 🛑 Pre-Mapping Validation Checklist

**MANDATORY: Before presenting ANY mapping to the user, answer these questions:**

### 1. Label Semantic Check
- [ ] For EACH node label from official schema: Does this label semantically match my data?
- [ ] Example: If data has "cards" but official schema says "Account" → RENAME to `:Card`
- [ ] Example: If data has "stores" but official schema says "Merchant" → RENAME to `:Store`
- [ ] **Rule**: If your property name contradicts your node label (e.g., `card_number` property on `:Account` node) → WRONG LABEL
- [ ] ❌ NEVER use official labels that don't match domain terminology

### 2. Entity Extraction Check
- [ ] For EACH repeated group of columns in source data: Should this be a separate entity?
- [ ] Example: `merchant_id, merchant_name, merchant_city` in transactions → CREATE `:Merchant` entity
- [ ] Example: `mcc_code, mcc_description` → CREATE `:MCC` lookup entity
- [ ] **Rule**: If 3+ related columns appear together and represent a distinct concept → Extract to entity
- [ ] ❌ NEVER bury entities as properties on other nodes

### 3. Data Duplication Test
- [ ] Will this property value repeat across multiple nodes? → Extract to separate entity
- [ ] Example: Same merchant info on 1000s of transactions → `:Merchant` entity needed
- [ ] Example: Same MCC description on 100s of merchants → `:MCC` entity needed
- [ ] **Rule**: If the same data appears in 10+ rows → Normalize to separate entity
- [ ] ❌ NEVER duplicate the same data across thousands of nodes

**If you answer "unsure" to ANY checkbox above → STOP and re-read the "Most Common Mistakes" section below**

---

**Output format**:
```cypher
// Mapping: source_files → Adapted Neo4j Data Model
// Started from: Customer 360 official model (adapted for card transaction data)

// ✅ Official entity - semantically correct, extended with properties
(:Customer {
  customerId: customer_id,        // Source: users.csv 'customer_id' column
  firstName: first_name,          // Source: users.csv 'first_name' column

  // Extended properties (beyond official schema)
  age: age,                       // Additional field from source data
  creditScore: credit_score       // Additional field from source data
})

// ✅ Official concept renamed - Account → Card (matches domain)
(:Card {
  cardNumber: card_number,        // Source: cards.csv 'card_number'
  cardType: card_type,            // Source: cards.csv 'card_type'
  creditLimit: credit_limit       // Source: cards.csv 'credit_limit'
})

// ✅ NEW entity - not in official schema, fundamental to data
(:Merchant {
  merchantId: merchant_id,        // Source: transactions.csv 'merchant_id'
  name: merchant_name,            // Source: transactions.csv 'merchant_name'
  city: merchant_city             // Source: transactions.csv 'merchant_city'
})

// Relationships - kept official patterns where applicable
(:Customer)-[:HAS_CARD]->(:Card)              // Adapted from official: HAS_ACCOUNT
(:Card)-[:PERFORMED]->(:Transaction)          // Official pattern
(:Transaction)-[:AT_MERCHANT]->(:Merchant)    // NEW relationship for data reality
```

**After presenting the mapping**:

The Cypher-style mapping above IS your complete Phase 1 deliverable. Present it directly to the user - do NOT call ExitPlanMode or treat this as a "plan to execute."

When user explicitly requests multi-phase work (e.g., "Phase 1: mapping, Phase 2: code generation"):
- **Phase 1 (Architect)**: Present the Cypher mapping, confirm completion with simple text like "Phase 1 complete. Ready to iterate or move to Phase 2?"
- **Phase 2 (Engineer)**: Switch personas only when user explicitly requests it. Read analyze_data_quality.md and generate_data_loader_code.md first.

**CRITICAL**: Architects present schema mappings as deliverables, not as plans. The mapping is the work product itself.

---

## Using Official Models as Starting Points, Not Rigid Contracts

**Official Neo4j data models are battle-tested starting points, not rigid contracts.**

### The Right Approach: Adapt Official Patterns to Your Data

**Official models provide**:
- ✅ Proven relationship patterns (how entities connect)
- ✅ Property naming conventions (standardized schema)
- ✅ Graph structure best practices (efficient traversals)
- ✅ Foundation for common domains (transactions, customers, fraud, etc.)

**You MUST adapt them to your data reality**:
- ✅ Rename node labels to match your domain (Account → Card, Merchant → Store)
- ✅ Add entities present in your data but missing from official schema
- ✅ Extend properties beyond official schema to capture your data
- ✅ Keep proven relationship patterns where they apply

### ❌ NEVER Do This:
- Invent entire domain models from scratch without checking Neo4j catalog first
- Ignore official patterns when they clearly apply to your domain
- Force your data into labels that don't make semantic sense
- Skip the catalog because "my data is unique"

### ✅ ALWAYS Do This:
- Start with `python3 cli.py list-datamodels` to find relevant official models
- Use official patterns as **starting points**, then adapt to your data entities
- Rename labels semantically: if official schema says "Account" but your data has "Cards" → use `:Card`
- Add entities from your data: if official schema lacks "Merchant" but your data has merchants → add `:Merchant`
- Keep relationship patterns: if official schema uses `PERFORMS` for transactions, keep that pattern

---

## 🚨 Most Common Mistakes (You WILL Make These If Not Careful)

**These are the exact mistakes LLMs make when mapping data to official schemas. Review BEFORE presenting any mapping.**

### Mistake #1: Using Official Labels That Don't Match Domain Semantics

**Symptom**: Property names contradict node labels

```cypher
// ❌ WRONG - Label says "Account" but properties scream "Card"
(:Account:Internal {
  accountNumber: card_number,      // Property: "card_number"
  accountType: card_type,          // Property: "card_type"
  cardBrand: card_brand,           // Property: "card_brand"
  creditLimit: credit_limit,       // Property: "credit_limit"
  expires: expires,                // Cards expire, accounts don't
  cvv: cvv                         // CVV is card-specific
})
```

**Why this is wrong**:
- Property names reveal truth: this is card data, not account data
- "Account" is semantically incorrect for card transactions
- Official schema used "Account" generically, but your data is specific

**✅ FIX**: Rename to match domain reality
```cypher
(:Card {                           // Label matches data semantics
  cardNumber: card_number,
  cardType: card_type,
  cardBrand: card_brand,
  creditLimit: credit_limit,
  expires: expires,
  cvv: cvv
})

// Keep relationship pattern from official model
(:Card)-[:PERFORMED]->(:Transaction)  // Was: Account PERFORMS Transaction
```

**Rule**: If property names contradict label → WRONG LABEL. Fix immediately.

---

### Mistake #2: Burying Entities As Properties (Data Duplication)

**Symptom**: Related columns grouped together that represent a distinct concept

```cypher
// ❌ WRONG - Merchant data buried as properties, duplicated across 1000s of transactions
(:Transaction {
  transactionId: id,
  amount: amount,
  date: date,

  // These 4 fields are an entity, not properties!
  merchantId: merchant_id,         // Same merchant appears in 1000s of transactions
  merchantName: merchant_name,     // "Joe's Coffee" repeated 10,000 times
  merchantCity: merchant_city,     // "Seattle" repeated 10,000 times
  merchantState: merchant_state    // "WA" repeated 10,000 times
})
```

**Why this is wrong**:
- Data duplication: "Joe's Coffee, Seattle, WA" stored 10,000 times
- Can't analyze merchants: "Which merchants have highest fraud rates?"
- Can't traverse: "Show me Customer→Card→Transaction→Merchant path"
- Wastes storage and creates update anomalies

**✅ FIX**: Extract to separate entity
```cypher
(:Transaction {
  transactionId: id,
  amount: amount,
  date: date
})

(:Merchant {                       // NEW entity - normalized data
  merchantId: merchant_id,
  name: merchant_name,
  city: merchant_city,
  state: merchant_state
})

// Connect via relationship
(:Transaction)-[:AT_MERCHANT]->(:Merchant)
```

**Rule**: If 3+ related columns appear together AND represent a distinct concept → Extract to entity

---

### Mistake #3: Ignoring Reference/Lookup Data

**Symptom**: Code/description pairs buried in properties

```cypher
// ❌ WRONG - MCC lookup data duplicated everywhere
(:Merchant {
  merchantId: merchant_id,
  name: merchant_name,
  mcc: "5812",                           // Code repeated across merchants
  mccDescription: "Eating Places"        // Description repeated across merchants
})

// Or even worse: buried in transactions
(:Transaction {
  transactionId: id,
  mcc: "5812",
  mccDescription: "Eating Places and Restaurants"  // Lookup data buried
})
```

**Why this is wrong**:
- MCC codes are industry-standard lookup tables (like country codes)
- Description "Eating Places and Restaurants" duplicated 100,000 times
- Can't analyze by category: "Show all restaurant transactions"
- Violates database normalization principles

**✅ FIX**: Create lookup entity
```cypher
(:MCC {                              // NEW entity - reference data
  code: "5812",
  description: "Eating Places and Restaurants",
  category: "Food & Dining"
})

(:Merchant {
  merchantId: merchant_id,
  name: merchant_name
})

// Connect via relationship
(:Merchant)-[:CLASSIFIED_AS]->(:MCC {code: "5812"})
(:Transaction)-[:AT_MERCHANT]->(:Merchant)-[:CLASSIFIED_AS]->(:MCC)
```

**Rule**: If it's a code/description pair used across many records → Create lookup entity

---

### How To Avoid These Mistakes

**Before presenting ANY mapping, ask yourself**:

1. **Semantic Check**: Do my labels match my property names?
   - Property: `card_number` but Label: `:Account` → ❌ WRONG
   - Property: `card_number` and Label: `:Card` → ✅ CORRECT

2. **Entity Check**: Am I grouping related columns that represent a concept?
   - `merchant_id, merchant_name, merchant_city` on Transaction → ❌ Extract to `:Merchant`
   - `merchant_id` on Transaction with `:AT_MERCHANT` relationship → ✅ CORRECT

3. **Duplication Check**: Will this data repeat across many nodes?
   - Same merchant info on 10,000 transactions → ❌ Normalize to `:Merchant` entity
   - Each transaction has unique amount/date → ✅ Keep as properties

**If in doubt → Extract to entity. Graph databases are designed for relationships.**

### Decision Tree: Official Schema + Your Data

```
Is this entity in the official model?
│
├─ YES → Adapt it
│   ├─ Does the official label make sense? (e.g., "Customer" for customers)
│   │   └─ YES → Use official label, add your properties
│   └─ Should it be renamed? (e.g., "Account" → "Card" for card data)
│       └─ YES → Rename label, keep relationship patterns
│
└─ NO → Is it fundamental to your dataset?
    ├─ YES → Add it as new entity type
    │   └─ Example: Merchant not in official schema but critical to transactions → add `:Merchant`
    └─ NO → Extended property on existing entity
        └─ Example: "favorite_color" on Customer → just an extra property
```

### Why This Matters

**If you use official patterns as foundations**:
- ✅ Benefit from battle-tested graph structures
- ✅ Model aligns with how your data actually works
- ✅ Schema is semantically correct and maintainable
- ✅ Follow Neo4j best practices while fitting your domain

**If you ignore official patterns entirely**:
- ❌ Reinvent graph structures already solved by experts
- ❌ May create inefficient traversal patterns
- ❌ Miss proven approaches to common problems
- ❌ Defeat the purpose of using the standardized catalog

---

## When and How to Adapt Official Models

**Core principle**: Official models give you the skeleton, your data provides the organs.

### Scenario 1: Entity Exists in Official Schema, Semantically Matches

**Official schema**: `(:Customer)` for customer data
**Your data**: CSV with customer demographics

**Action**: ✅ Use official label, extend with your properties

```cypher
// Official model provides:
(:Customer {
  customerId: string,
  firstName: string,
  lastName: string
})

// Your adaptation adds domain-specific properties:
(:Customer {
  customerId: id,                    // Source: customers.csv 'id'
  firstName: first_name,             // Source: customers.csv 'first_name'
  lastName: last_name,               // Source: customers.csv 'last_name'

  // Extended properties beyond official schema
  creditScore: credit_score,         // Your data: customers.csv 'credit_score'
  yearlyIncome: yearly_income,       // Your data: customers.csv 'yearly_income'
  preferredLanguage: language        // Your data: customers.csv 'language'
})
```

### Scenario 2: Entity Exists in Official Schema, But Wrong Semantics

**Official schema**: `(:Account)` for financial accounts
**Your data**: Card transaction data (cards, not bank accounts)

**Action**: ✅ Rename label to match domain, keep relationship patterns

```cypher
// Official model has:
(:Account {
  accountId: string,
  accountType: string
})
(:Account)-[:PERFORMS]->(:Transaction)

// Your adaptation renames to match data semantics:
(:Card {                             // Renamed: Account → Card
  cardNumber: card_number,           // Your data: cards.csv 'card_number'
  cardType: card_type,               // Your data: 'Credit' or 'Debit'
  cardBrand: card_brand,             // Your data: 'Visa', 'Mastercard'
  creditLimit: credit_limit          // Your data: cards.csv 'credit_limit'
})
(:Card)-[:PERFORMED]->(:Transaction) // Kept relationship pattern from official model
```

**Why rename?**: Calling a card an "account" creates semantic confusion. The official model's relationship pattern (entity PERFORMS transaction) still applies, but the entity name must match your domain.

### Scenario 3: Entity Missing from Official Schema, Fundamental to Data

**Official schema**: Transaction Graph (has Account, Transaction, Customer)
**Your data**: Card transactions at merchants

**Action**: ✅ Add new entity type for fundamental data concept

```cypher
// Official model does NOT have Merchant
// Your data HAS merchant information in every transaction

// Add new entity:
(:Merchant {                         // NEW entity - not in official schema
  merchantId: merchant_id,           // Source: transactions.csv 'merchant_id'
  merchantName: merchant_name,       // Source: transactions.csv 'merchant_name'
  city: merchant_city,               // Source: transactions.csv 'merchant_city'
  state: merchant_state,             // Source: transactions.csv 'merchant_state'
  mcc: mcc                          // Source: transactions.csv 'mcc' code
})

// Add new relationship:
(:Transaction)-[:AT_MERCHANT]->(:Merchant)  // NEW relationship connecting transactions to merchants
```

**Why add?**: Merchant is fundamental to understanding transactions in your dataset. Burying merchant data as properties on Transaction nodes would:
- ❌ Create data duplication (same merchant info repeated for every transaction)
- ❌ Prevent merchant-level analysis (e.g., "which merchants have most fraud?")
- ❌ Lose graph benefits (can't traverse merchant networks)

### Scenario 4: Reference Data / Lookup Tables

**Official schema**: May not include industry-standard lookup tables
**Your data**: MCC codes, country codes, product categories

**Action**: ✅ Add lookup entities for better data normalization

```cypher
// Your data references MCC codes (Merchant Category Codes)
// Standard industry codes: 5812 = "Eating Places", 5411 = "Grocery Stores"

// Add lookup entity:
(:MCC {                              // NEW entity - industry standard codes
  code: mcc,                         // Source: mcc_codes.json 'code'
  description: description,          // Source: mcc_codes.json 'description'
  category: category                 // Source: mcc_codes.json 'category'
})

// Connect merchants to their MCC classification:
(:Merchant)-[:CLASSIFIED_AS]->(:MCC)
```

**Why add?**: Normalizes data, enables category-level analysis, follows graph best practices.

### Scenario 5: Compound Relationship Patterns

**Official schema**: Simple relationships
**Your data**: Relationships with rich temporal or contextual properties

**Action**: ✅ Extend relationship properties, consider intermediate nodes for complex cases

```cypher
// Official model might have:
(:Customer)-[:HAS_ACCOUNT]->(:Account)

// Your data has role-based, temporal account ownership:
(:Customer)-[:HAS_CARD {
  relationship: "primary" | "authorized_user",  // Extended property
  since: acct_open_date,                        // Extended property
  creditLimit: shared_limit,                    // Extended property
  lastUsed: last_transaction_date               // Extended property
}]->(:Card)
```

### Summary: Adaptation Guidelines

| Situation | In Official Schema? | Semantically Correct? | Action |
|-----------|-------------------|----------------------|---------|
| Standard entity (Customer, Transaction) | ✅ Yes | ✅ Yes | Use official label + extend properties |
| Entity with wrong name (Account vs Card) | ✅ Yes | ❌ No | Rename label + keep patterns |
| Fundamental entity missing (Merchant) | ❌ No | N/A | Add new entity + relationships |
| Lookup/reference data (MCC codes) | ❌ No | N/A | Add lookup entity + normalize |
| Complex relationships | ✅ Yes | Partial | Extend properties or intermediate nodes |

**Remember**: Official models are starting points. Your job is to **adapt proven patterns to your data reality**, not force your data into semantically incorrect labels.

---

## Data Models vs Use Cases

**Understanding the difference is critical:**

| Data Models | Use Cases |
|-------------|-----------|
| **Generic, reusable graph schemas** | **Industry-specific problem scenarios** |
| Example: "Transaction Graph" | Example: "Fraud Detection in Banking" |
| Abstract patterns | Concrete business problems |
| Can be applied across industries | Industry-specific implementations |
| Focus on structure (nodes, relationships) | Focus on outcomes (detect fraud, recommendations) |

**Relationship**: Use cases **reference** data models. A single data model (like "Transaction Graph") can be used in multiple use cases (fraud detection, AML, payment optimization).

**When to use which**:
- User says "I want to detect fraud" → Start with **use cases** (`list-usecases`)
- User says "I have transaction data" → Consider **data models** (`list-datamodels`)
- User says "Show me graph patterns for my domain" → Use **data models**

---

## How to Fetch Data Models

### List All Data Models

**CLI Command**:
```bash
python3 cli.py list-datamodels
```

**What It Returns**:
- Hierarchical tree of data models from neo4j.com/developer/industry-use-cases
- Categories and subcategories
- Individual data model names with URLs
- Total count of available data models

**Output Formats**:
```bash
# Default: Pretty tree view
python3 cli.py list-datamodels

# JSON format (for programmatic use)
python3 cli.py list-datamodels --json

# URLs only (for feeding to LLM)
python3 cli.py list-datamodels --urls-only

# Show URLs in tree view
python3 cli.py list-datamodels --verbose
```

### Get Specific Data Model

**CLI Command**:
```bash
python3 cli.py get-datamodel <URL>
```

**What It Does**:
- Fetches the data model page from neo4j.com
- Converts HTML to clean markdown format
- Extracts node labels, relationship types, properties
- Includes schema diagrams and explanations

**Usage Examples**:
```bash
# Print to stdout
python3 cli.py get-datamodel https://neo4j.com/developer/industry-use-cases/data-models/fraud-detection/

# Save to file
python3 cli.py get-datamodel <URL> -o datamodel.md
```

**When to use**:
- After finding relevant data model with `list-datamodels`
- Before generating ingestion code
- To understand schema requirements
- To map user's data to canonical model

---

## Matching User Requests

### User Provides Domain/Industry

Users often describe their domain rather than specific patterns:

| User Says | Explore Data Models For |
|-----------|------------------------|
| "customer transaction data" | Transaction Graph, Customer 360 |
| "supply chain" | Supply Chain Network |
| "healthcare records" | Healthcare Data Models |
| "financial services" | Transaction, Fraud, Risk models |
| "social network" | Social Graph patterns |
| "product catalog" | Product/Catalog models |

### Matching Strategy

**Look for domain alignment**:
- Keywords: "transaction", "customer", "supply chain", "healthcare", "social"
- Data types: What entities does user have? (customers, products, transactions, etc.)
- Relationships: What connections exist in their data?

**Don't require exact naming**:
- "payments" → "Transaction Graph" ✅
- "customer network" → "Customer 360" or "Social Graph" ✅
- "medical records" → "Healthcare" models ✅

---

## When Match Is Clear

**User**: "I have transaction data and want to model it as a graph"

**You discover**:
```bash
python3 cli.py list-datamodels
# Returns: "Transaction Graph" data model
```

**Your response**:
```
✅ Matched data model: Transaction Graph

This model represents financial transactions, accounts, and entities with temporal relationships.

Typical structure:
- Account nodes
- Transaction nodes
- SENT/RECEIVED relationships
- Temporal properties (timestamp, amount)

Let me fetch the full documentation...
```

Then use `get-datamodel` to retrieve complete schema.

---

## When Match Is Ambiguous

**User**: "I have customer data"

**Too vague**. Multiple data models may apply.

**Your response**:
```
I found several data models that could work with customer data:

1. **Customer 360** - Complete customer view with all touchpoints
2. **Transaction Graph** - Customer transactions and payments
3. **Social Graph** - Customer networks and relationships
4. **Fraud Detection** - Customer behavior and risk patterns

What are you trying to accomplish with the customer data?
```

Present options, let user clarify intent.

---

## When No Match Exists

**User**: "I need a data model for quantum computing workflows"

**No Neo4j data model for this domain** (hypothetical example).

**Your response**:
```
I couldn't find a quantum computing data model in Neo4j's catalog.

Available data models include:
- Transaction Graph (financial services)
- Customer 360 (customer data)
- Supply Chain Network
- Healthcare models
- Fraud Detection
- Social Graph patterns

Would any of these work for your use case, or would you like to explore custom graph modeling?
```

**Don't invent a quantum computing data model**. Present what exists.

---

## Workflow: From Discovery to Implementation

### Typical Flow

1. **User describes their data domain**
   ```
   User: "I have transaction data to load into Neo4j"
   ```

2. **You list relevant data models**
   ```bash
   python3 cli.py list-datamodels
   # Identify: Transaction Graph
   ```

3. **Fetch the data model documentation**
   ```bash
   python3 cli.py get-datamodel <transaction-graph-url>
   ```

4. **Analyze the schema**
   - What node labels are defined?
   - What relationships are used?
   - What properties are required?

5. **Map user's data to the model**
   - Compare user's CSV columns to required properties
   - Identify which columns map to nodes vs relationships
   - Flag missing required fields

6. **Generate ingestion code**
   - Use the official schema from the data model
   - Map user's data to canonical structure
   - Follow best practices from the documentation

---

## Communicating to User

### When Confirmed:
```
✅ Data model: {Name}

Fetching full schema documentation...
```
Brief, clear, move on.

### When Options Presented:
```
I found {N} data models that might work:
1. {Name} - {Brief description}
2. {Name} - {Brief description}
...

Which one matches your needs?
```
Concise list, let them choose.

### After Fetching Documentation:
```
✅ Retrieved: {Name} data model

Schema includes:
- {Node labels}
- {Key relationships}
- {Required properties}

Now analyzing your data to map to this schema...
```

Confirm what was fetched, explain structure, proceed.

---

## Presenting Schema and Mappings

**CRITICAL**: When presenting data model schemas or mapping decisions to users, ALWAYS use Cypher-style syntax. Neo4j users think in Cypher - show them the structure in the format they recognize.

### Format for Data Model Schemas

When you fetch a data model with `get-datamodel`, present the schema structure using Cypher syntax:

```cypher
// Official Schema: Transaction Graph

(:Account {
  accountId: string,           // Required: Unique account identifier
  accountType: string,         // Required: "INTERNAL" or "EXTERNAL"
  createdAt: datetime          // Required: Account creation timestamp
})

(:Transaction {
  transactionId: string,       // Required: Unique transaction ID
  amount: float,               // Required: Transaction amount
  currency: string,            // Required: Currency code (e.g., "USD")
  timestamp: datetime          // Required: Transaction timestamp
})

(:Account)-[:PERFORMS]->(:Transaction)
(:Transaction)-[:BENEFITS_TO]->(:Account)
```

### Format for User Data Mappings

When showing how user's data will map to the official schema:

```cypher
// Mapping: transactions.csv → Transaction nodes

(:Transaction {
  transactionId: id,                 // Source: transactions.csv 'id' column
  amount: amount,                    // Source: transactions.csv 'amount', clean $ prefix
  currency: "USD",                   // Constant: Inferred from context
  timestamp: date,                   // Source: transactions.csv 'date', parse to datetime

  // Extended properties (beyond official schema)
  merchantCity: merchant_city,       // Source: transactions.csv 'merchant_city'
  merchantState: merchant_state,     // Source: transactions.csv 'merchant_state'
  mcc: mcc                          // Source: transactions.csv 'mcc' code
})
```

### Why This Format

**Benefits**:
- **Familiar syntax**: Users immediately recognize Neo4j Cypher
- **Visual clarity**: Shows exactly how nodes will be created
- **Source tracing**: Comments link properties to data sources
- **Extension visibility**: Clearly marks fields beyond official schema
- **Professional standard**: How Neo4j community communicates schemas

**When to use**:
- After fetching a data model from the catalog
- When explaining schema structure to users
- When presenting mapping decisions before code generation
- In data validation reports showing schema compatibility
- Anywhere you describe node labels, properties, or relationships

---

## Example Conversation

**User**: "I want to model my transaction data in Neo4j"

**You do**:
1. `python3 cli.py list-datamodels`
2. Search for "transaction" or "payment" related models
3. Find: "Transaction Graph"
4. Fetch documentation: `python3 cli.py get-datamodel <url>`

**You respond**:
```
✅ Matched: Transaction Graph data model

This model represents financial transactions with:
- Account nodes (sender/receiver)
- Transaction nodes (amount, timestamp, type)
- SENT/RECEIVED relationships
- Support for fraud detection patterns

Let me check your data structure to map it to this schema...
```

Then proceed to analyze user's data files in `workspace/raw_data/`.

---

## Integration with Use Cases

**Data models support use cases**:

1. User wants to implement a use case (e.g., "Fraud Detection")
2. You fetch the use case documentation with `get-usecase`
3. Use case references specific data models (e.g., "Transaction Graph")
4. You fetch the data model with `get-datamodel`
5. Data model provides the schema
6. You generate code that follows both the use case patterns and data model schema

**Example**:
- Use case: "First-Party Fraud Detection"
- Data model: "Fraud Detection Graph" + "Transaction Graph"
- Result: Code that detects fraud using the canonical graph schema

---

## Key Takeaways

- **Data models come from Neo4j only** - never invent custom schemas without checking
- **Fetch fresh** from CLI each time to get latest models
- **Match by domain** - users won't know exact data model names
- **Present options** when ambiguous
- **Explain structure** briefly (nodes, relationships, properties)
- **Use with use cases** - data models provide schema, use cases provide business logic
- **Move efficiently** once matched - fetch documentation and proceed

---

See also:
- `../AGENT.md` - Overall guidance
- `match_business_to_usecases.md` - Use case discovery (complementary approach)
- `validate_neo4j_connection.md` - Connection validation
- `analyze_data_quality.md` - Data quality analysis & structure validation
- `generate_data_loader_code.md` - Code generation using data models
