# Data Mapper Code Generation

**Reference guide for generating data_mapper.py code that loads data into Neo4j.**

---

## Core Philosophy: Discovery-Based Generation

**NEVER hard-code knowledge about the toolkit API.** Instead, ALWAYS discover the latest patterns by reading the source code.

This ensures:
- Generated code uses current API (not outdated assumptions)
- Code follows working patterns from the toolkit
- Data model aligns exactly with official Neo4j use cases

---

## Critical Pre-Generation Steps

Before generating ANY code, you MUST complete these discovery steps:

### 1. Discover the Data Model

**Source**: Use case markdown from CLI (`python cli.py get-usecase <URL>`)

**Extract**:
- Node labels (e.g., `Customer`, `Email`, `Phone`)
- Required properties for each node (e.g., `customerId`, `address`, `phoneNumber`)
- Relationship types (e.g., `HAS_EMAIL`, `HAS_PHONE`)
- Relationship direction and cardinality

**Store this information** - it's the authoritative data model you MUST follow.

### 2. Discover the Query API

**Read these files**:
- `src/core/neo4j/query.py` - Query execution methods
- `src/core/neo4j/version.py` - Entry point for getting query runner
- `src/core/logger.py` - Logging patterns

**Learn**:
- How to get a query runner instance
- What methods are available (run, run_batched, run_transaction)
- Required parameters and patterns (especially UNWIND $batch)
- How to log progress

**Example discovery process**:
```python
# Read src/core/neo4j/version.py to discover:
from src.core.neo4j.version import get_query

# Read src/core/neo4j/query.py to discover:
query = get_query()
query.run_batched(cypher, data, batch_size=1000)  # Pattern: UNWIND $batch

# Read src/core/logger.py to discover:
from src.core.logger import log
log.info("Creating Customer nodes...")
```

### 3. Examine Working Examples

**Read**: `workspace/generated/data_mapper.py` (if it exists)

**Learn**:
- Path setup pattern (makes script runnable from any directory)
- Import order (path setup BEFORE src.* imports)
- Function structure (one per node type, one per relationship type)
- Error handling and cleanup patterns

### 4. Analyze the Data Source

**Check**: `workspace/raw_data/` directory

**Determine**:
- File format (CSV, JSON, Parquet, etc.)
- Column names / field structure
- Data types and encoding
- How to map source fields → use case properties

---

## Data Model Strict Alignment

**THE USE CASE DATA MODEL IS AUTHORITATIVE**

### ✅ You CAN:
- Add extra properties to nodes (if source data has them)
  - Example: Add `firstName`, `lastName` to Customer node
  - Use case requires: `customerId`
  - Source has: `customer_id`, `first_name`, `last_name`
  - Result: Map all three fields

### ❌ You CANNOT:
- Change node labels
  - Use case says: `Customer` → You must use `Customer`
  - Don't rename to: `Person`, `Client`, `Account`

- Change relationship types
  - Use case says: `HAS_EMAIL` → You must use `HAS_EMAIL`
  - Don't rename to: `OWNS_EMAIL`, `USES_EMAIL`, `EMAIL_OF`

- Modify required properties
  - Use case says: `customerId` → You must use `customerId`
  - Don't rename to: `customer_id`, `id`, `cust_id`

- Invent new node types or relationships
  - Use case defines: Customer, Email, Phone
  - Don't add: Address, Device, Transaction (unless in use case)

### Why This Matters

Neo4j use cases are battle-tested with:
- Proven data models optimized for fraud detection
- Pre-built query patterns that expect specific labels
- Graph Data Science algorithms that work on defined structures

**Changing the data model breaks these proven patterns.**

---

## Required Code Structure

### 1. Path Setup (REQUIRED)

**ALWAYS start with this pattern** (adapt from working example):

```python
# Setup Python path to find toolkit modules
import sys
from pathlib import Path

# Get project root (2 levels up from this script)
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent.parent
sys.path.insert(0, str(project_root))
```

**Why**:
- Makes script runnable from any directory
- Ensures `from src.*` imports work correctly
- Must come BEFORE any toolkit imports

**Where to learn this**:
- Read existing `workspace/generated/data_mapper.py`
- See working pattern in action

### 2. Import Order (REQUIRED)

```python
# FIRST: Path setup (above)

# SECOND: Standard library imports
import csv  # or json, parquet, etc.
from pathlib import Path

# THIRD: Toolkit imports (discovered from reading source)
from src.core.neo4j.version import get_query
from src.core.logger import log
```

### 3. Data Reading Function

Adapt to actual data format (CSV, JSON, etc.):

```python
def load_data():
    """
    Load data from source file.

    Returns:
        list: List of dictionaries, one per record
    """
    log.info("Loading data from workspace/raw_data/...")

    # Path is relative to this script
    data_path = Path(__file__).parent.parent / "raw_data" / "data.csv"

    # Adapt reading logic to format (CSV shown as example)
    records = []
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    log.info(f"Loaded {len(records)} records")
    return records
```

**Key points**:
- Use relative paths (not absolute)
- Use pathlib.Path for cross-platform compatibility
- Log progress for user visibility
- Return data in consistent format (list of dicts)

### 4. Node Creation Functions

One function per node type from use case:

```python
def create_<NodeType>_nodes(query, data):
    """
    Create <NodeType> nodes in Neo4j.

    Args:
        query: Neo4jQuery instance (from get_query())
        data: List of dictionaries with source data
    """
    log.info("Creating <NodeType> nodes...")

    # Transform source data to match use case properties
    node_data = [
        {
            'required_property': record['source_field'],
            'optional_property': record.get('other_field', 'default')
        }
        for record in data
    ]

    # Use discovered batching pattern with progress logging
    cypher = """
    UNWIND $batch AS row
    MERGE (n:<NodeType> {requiredProperty: row.required_property})
    SET n.optionalProperty = row.optional_property
    """

    # Process in batches with progress logging
    batch_size = 1000
    total_records = len(node_data)
    log_interval = max(50000, batch_size * 10)  # Log every 50k records or 10 batches, whichever is larger

    for i in range(0, total_records, batch_size):
        batch = node_data[i:i + batch_size]
        query.run(cypher, {'batch': batch})

        # Log progress periodically for large datasets
        records_processed = min(i + batch_size, total_records)
        if records_processed % log_interval == 0 or records_processed == total_records:
            progress_pct = (records_processed / total_records) * 100
            log.info(f"  Progress: {records_processed:,} / {total_records:,} records ({progress_pct:.1f}%)")

    log.info(f"✓ Created {len(node_data):,} <NodeType> nodes")
```

**Pattern requirements** (discovered from query.py):
- Must use `UNWIND $batch AS row`
- Use MERGE on unique identifier property
- Use SET for other properties
- Implement manual batching loop with `query.run()` for progress visibility
- Log progress every 50,000 records (or configurable interval) to show the load is progressing
- Use formatted numbers with commas (`:,`) for better readability

**Why Manual Batching Instead of run_batched()**:
The `query.run_batched()` method only logs at DEBUG level, which means users won't see progress for large datasets. For loads with hundreds of thousands or millions of records, implement your own batching loop with INFO-level progress logging to prevent the appearance of a frozen process.

### 5. Relationship Creation Functions

One function per relationship type from use case:

```python
def create_<RELATIONSHIP>_relationships(query, data):
    """
    Create <RELATIONSHIP> relationships between nodes.

    Args:
        query: Neo4jQuery instance
        data: List of dictionaries with relationship data
    """
    log.info("Creating <RELATIONSHIP> relationships...")

    # Extract relationship pairs
    rel_data = [
        {
            'source_id': record['source_key'],
            'target_id': record['target_key']
        }
        for record in data
    ]

    cypher = """
    UNWIND $batch AS row
    MATCH (source:<SourceNode> {id: row.source_id})
    MATCH (target:<TargetNode> {id: row.target_id})
    MERGE (source)-[:<RELATIONSHIP>]->(target)
    """

    # Process in batches with progress logging
    batch_size = 1000
    total_records = len(rel_data)
    log_interval = max(50000, batch_size * 10)  # Log every 50k records or 10 batches, whichever is larger

    for i in range(0, total_records, batch_size):
        batch = rel_data[i:i + batch_size]
        query.run(cypher, {'batch': batch})

        # Log progress periodically for large datasets
        records_processed = min(i + batch_size, total_records)
        if records_processed % log_interval == 0 or records_processed == total_records:
            progress_pct = (records_processed / total_records) * 100
            log.info(f"  Progress: {records_processed:,} / {total_records:,} relationships ({progress_pct:.1f}%)")

    log.info(f"✓ Created {len(rel_data):,} <RELATIONSHIP> relationships")
```

### 6. Main Execution Function

```python
def main():
    """
    Main execution function - orchestrates data loading.
    """
    log.info("Starting data load for <Use Case Name>...")

    # Load data
    data = load_data()

    # Get query runner (discovered from version.py)
    query = get_query()

    try:
        # Create nodes (one function call per node type)
        create_<NodeType>_nodes(query, data)
        # ... more node types

        # Create relationships (one function call per relationship type)
        create_<RELATIONSHIP>_relationships(query, data)
        # ... more relationships

        # Verify results
        verify_load(query)

        log.info("✅ Data load complete!")

    finally:
        # Always close connection
        query.close()


if __name__ == '__main__':
    main()
```

**Key patterns**:
- Use try/finally to ensure cleanup
- Call query.close() even if errors occur
- Log progress at each step
- Provide helpful completion message

---

## Cypher Query Patterns

### Discovered from query.py

**For batched operations** (bulk loading):
```cypher
UNWIND $batch AS row
MERGE (n:NodeType {uniqueKey: row.key})
SET n.property1 = row.value1,
    n.property2 = row.value2
```

**Pattern requirements**:
- MUST start with `UNWIND $batch AS row`
- Use `row.fieldName` to access batch data
- Toolkit passes batch as `{'batch': your_data_list}`

**For single operations**:
```cypher
MATCH (n:NodeType {id: $id})
RETURN n
```

**Pattern requirements**:
- Use `$paramName` for parameters
- Pass params as dict: `query.run(cypher, {'id': 'C001'})`

---

## Discovery Workflow Example

### User Request:
> "Load my customer data for synthetic identity fraud detection"

### Your Discovery Process:

**Step 1: Get Use Case Data Model**
```bash
# Run CLI to get use case details
python cli.py get-usecase https://neo4j.com/...synthetic-identity-fraud/

# Extract from markdown:
Nodes: Customer (customerId), Email (address), Phone (phoneNumber)
Relationships: HAS_EMAIL, HAS_PHONE
```

**Step 2: Discover Query API**
```python
# Read src/core/neo4j/version.py
# Learn: from src.core.neo4j.version import get_query

# Read src/core/neo4j/query.py
# Learn: query.run_batched(cypher, data, batch_size=1000)
# Learn: Must use UNWIND $batch AS row pattern

# Read src/core/logger.py
# Learn: from src.core.logger import log
# Learn: log.info("message")
```

**Step 3: Examine Data**
```bash
# Check what data files exist
ls workspace/raw_data/

# Read sample of data.csv
head workspace/raw_data/data.csv

# Determine: CSV with columns: customer_id, email, phone, first_name, last_name
```

**Step 4: Plan Mapping**
```
Use Case Model → Source Data:
- Customer.customerId ← customer_id
- Customer.firstName ← first_name (extra property, allowed)
- Customer.lastName ← last_name (extra property, allowed)
- Email.address ← email
- Phone.phoneNumber ← phone
```

**Step 5: Generate Code**
- Use path setup from working example
- Create load_data() for CSV reading
- Create create_customer_nodes() - maps to Customer label
- Create create_email_nodes() - maps to Email label
- Create create_phone_nodes() - maps to Phone label
- Create relationship functions using discovered API
- Use manual batching loop with progress logging (see section 4 for pattern)
- Include try/finally cleanup

**Result**: Working code that follows toolkit patterns and use case data model exactly.

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Hard-coding API
```python
# DON'T assume function names
from src.core.neo4j import Neo4jWriter  # May not exist!
writer.write_nodes(data)  # May not exist!
```

**✅ Instead**: Read src/core/neo4j/ files to discover actual API

### ❌ Mistake 2: Modifying Data Model
```python
# DON'T rename node labels
CREATE (n:Person {id: row.id})  # Use case says "Customer"!
```

**✅ Instead**: Use exact labels from use case

### ❌ Mistake 3: Missing Path Setup
```python
# DON'T start with toolkit imports
from src.core.neo4j.version import get_query  # Will fail!
```

**✅ Instead**: Add path setup FIRST (see working example)

### ❌ Mistake 4: Wrong Batch Pattern
```python
# DON'T use non-standard patterns
MERGE (n:Customer {id: $id})  # Missing UNWIND $batch!
```

**✅ Instead**: Use `UNWIND $batch AS row` pattern from query.py docs

### ❌ Mistake 5: No Progress Logging for Large Datasets
```python
# DON'T use run_batched() without progress logging
query.run_batched(cypher, node_data, batch_size=1000)  # User sees no progress for millions of records!
```

**✅ Instead**: Implement manual batching loop with periodic progress logging
```python
# Log progress every 50k records
for i in range(0, len(node_data), batch_size):
    batch = node_data[i:i + batch_size]
    query.run(cypher, {'batch': batch})

    records_processed = min(i + batch_size, len(node_data))
    if records_processed % 50000 == 0 or records_processed == len(node_data):
        progress_pct = (records_processed / len(node_data)) * 100
        log.info(f"  Progress: {records_processed:,} / {len(node_data):,} records ({progress_pct:.1f}%)")
```

**Why**: The `run_batched()` method logs only at DEBUG level. For datasets with hundreds of thousands or millions of records, users need to see progress to know the load isn't frozen.

---

## Testing & Verification

### Include Verification Function

```python
def verify_load(query):
    """
    Verify data was loaded correctly.

    Args:
        query: Neo4jQuery instance
    """
    log.info("Verifying data load...")

    # Count nodes by type
    result = query.run("MATCH (n:<NodeType>) RETURN count(n) as count")
    count = result[0]['count']
    log.info(f"Loaded {count} <NodeType> nodes")

    # Run use-case specific detection queries
    # (if applicable - e.g., fraud pattern detection)

    log.info("Verification complete")
```

**Purpose**:
- Confirms data loaded successfully
- Shows user immediate results
- Catches issues early

---

## Key Takeaways

### Always Do:
1. **Read toolkit source code** before generating
2. **Follow use case data model** exactly (labels, types, required properties)
3. **Include path setup** at top of generated script
4. **Use discovered API** (don't assume function names)
5. **Adapt data reading** to actual format (CSV, JSON, etc.)
6. **Log progress** at each step, especially during bulk data loading
7. **Implement progress logging** for large datasets (manual batching loop with periodic updates)
8. **Clean up resources** in finally block

### Never Do:
1. ❌ Hard-code toolkit API assumptions
2. ❌ Change use case node labels or relationship types
3. ❌ Invent custom data models
4. ❌ Skip path setup boilerplate
5. ❌ Forget to close connections
6. ❌ Use `run_batched()` without visible progress for large datasets

### Discovery Sources:
- Use case markdown → Data model (authoritative)
- `src/core/neo4j/` → Query API (latest)
- `workspace/generated/data_mapper.py` → Working patterns
- User's data files → Actual format and structure

---

## See Also

- `../PROMPT.md` - Overall toolkit guidance
- `discover_usecase.md` - How to fetch official use cases
- `setup.md` - Connection validation (if needed for Cypher version)
- Working example: `workspace/generated/data_mapper.py`
