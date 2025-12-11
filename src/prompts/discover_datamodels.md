# Data Model Discovery & Exploration

> **🛑 STOP**: Have you read [PROMPT.md](../../PROMPT.md)?
>
> If NO → Read it NOW before proceeding. It contains critical context about:
> - Your mission and core principles
> - When to read this file vs others
> - Essential tools and workflows
>
> This supporting prompt assumes you've already read PROMPT.md.

---

**Reference guide for discovering and exploring Neo4j data models from the official catalog.**

---

## Critical Rule: Never Invent Data Models

### ❌ NEVER Do This:
- Make up data models based on user's description
- Invent graph schemas that sound reasonable
- Assume a data model exists without checking
- Create custom data models not in Neo4j catalog

### ✅ ALWAYS Do This:
- Fetch data models from `python3 cli.py list-datamodels`
- Use official Neo4j data models only
- If no match, present available options to user
- Use `get-datamodel` to retrieve full documentation

---

## Why This Matters

**Neo4j's data models are**:
- Battle-tested in production environments
- Designed by graph experts
- Reusable across different industries and use cases
- Come with documented node labels, relationships, and properties
- Include best practices for graph schema design

**If you invent a data model**:
- Schema may be suboptimal or inefficient
- No proven patterns to reference
- User gets unvalidated approach
- Defeats the purpose of using standardized models
- May not align with Neo4j best practices

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
- `../PROMPT.md` - Overall guidance
- `discover_usecase.md` - Use case discovery (complementary approach)
- `setup.md` - Connection validation
- `analyze_data.md` - Data quality validation & structure analysis
- `generate_mapper.md` - Code generation using data models
