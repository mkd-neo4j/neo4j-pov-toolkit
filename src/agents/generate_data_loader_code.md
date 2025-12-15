# Generating Data Loader Code

> **🛑 STOP**: Have you read [AGENT.md](../../AGENT.md)?
>
> If NO → Read it NOW before proceeding. It contains critical context about:
> - Your mission and core principles
> - When to read this file vs others
> - Essential tools and workflows
>
> This supporting agent assumes you've already read AGENT.md.

---

**Reference guide for generating the data_mapper.py code that will load your data into Neo4j.**

---

## 🔧 Persona: You Are The Engineer

**When using this file, you are in Engineer mode.**

**Your focus**:
- Production-quality code generation
- Implementing defensive error handling
- Writing data loading scripts based on validated mappings
- Following toolkit API patterns

**What you DO as Engineer**:
- Generate workspace/generated/data_mapper.py with production-ready code
- Implement defensive handling based on analysis findings from analyze_data_quality.md
- Use toolkit API correctly (discover by reading src/core/neo4j/)
- Follow data model mappings from Phase 1 (Architect work)
- Include progress logging, error handling, and cleanup
- Write code that handles nulls, type conversions, and invalid values

**What you DON'T do as Engineer (in this file)**:
- ❌ Schema mapping - that's Architect work (already done in Phase 1)
- ❌ Use case discovery - that's Architect work
- ❌ Skip data analysis - you MUST read analyze_data_quality.md first

**Prerequisites before using this file**:
1. **Phase 1 complete**: Architectural mapping done (fetch_neo4j_data_models.md)
2. **Data analyzed**: Quality checks complete (analyze_data_quality.md)
3. **Connection verified**: Neo4j accessible and version known (validate_neo4j_connection.md if needed)

**Your workflow**:
1. Read validation findings (nulls, types, transformations needed)
2. Read architectural mappings (which source fields → which graph properties)
3. Discover toolkit API by reading src/core/neo4j/
4. Generate production code with defensive handling for all identified issues

**Output**:
- workspace/generated/data_mapper.py file
- Code that handles all data quality issues identified in validation
- Progress logging for large datasets
- Error handling and connection cleanup
- Follows official data model from Phase 1

**Next steps after generation**:
"Code generated. User can run: `python3 workspace/generated/data_mapper.py`"

---

## Core Philosophy: Discovery-Based Generation

**NEVER hard-code knowledge about the toolkit API.** Instead, ALWAYS discover the latest patterns by reading the source code.

This ensures:
- Generated code uses current API (not outdated assumptions)
- Code follows working patterns from the toolkit
- Data model aligns exactly with official Neo4j use cases

---

## MANDATORY: Data Quality Validation First

> **⚠️ CRITICAL**: Before writing ANY code, you MUST validate data quality.
>
> **Why**: "You need to do some thinking yourself like what happens when I execute this and there's a column that's broken" - Pedro Leitao

**You cannot write defensive code if you don't know what you're defending against.**

### The Professional Practice

Data engineers and data scientists **always** validate data before production loads:

1. **Check for nulls** - Which required fields have missing values?
2. **Validate types** - Are integers actually integers? Dates parseable?
3. **Detect invalid values** - Malformed emails, negative amounts, impossible dates?
4. **Understand distributions** - Outliers? Suspicious patterns?

### Why This Matters

**"Customer is gonna give you is just a load of shite that you're gonna have to fix yourself"** - Pedro

- Raw customer data is rarely clean
- LLMs can't analyze 4GB files - need strategic sampling
- Broken data will crash ingestion code
- **"It's much, much harder to verify once it gets into Neo4j"** - Pedro
- Fix issues BEFORE Neo4j, not after

### What to Do

**Read and follow**: [analyze_data_quality.md](analyze_data_quality.md)

This guide covers:
- How to sample large files strategically
- Essential data quality checks (nulls, types, invalid values)
- Statistical analysis for numerical fields
- When to proceed vs block code generation
- How validation findings inform code generation

**After validation**, you'll know:
- Which fields need null handling
- What type conversions/parsing are required
- What cleaning/validation logic to include
- Expected warnings during load

**Then and only then** proceed to code generation below.

---

## Critical Pre-Generation Steps

After completing data quality validation, you MUST complete these discovery steps:

### 0. Review Neo4j Best Practices

**Read**: [neo4j/cypher_best_practices.md](neo4j/cypher_best_practices.md)

**Essential guidelines**:
- **Naming conventions**: CamelCase for nodes, UPPER_SNAKE_CASE for relationships, camelCase for properties
- **Query patterns**: Anchor on indexed properties, use UNWIND $batch for bulk operations
- **Data modeling**: Avoid supernodes, use specific relationship types, create constraints before loading
- **Performance**: Batch operations (1000-10000 records), profile queries, avoid gather-and-inspect patterns

**Why This Matters**:
- Ensures generated code follows Neo4j industry standards
- Prevents common performance pitfalls
- Creates maintainable, optimized Cypher queries
- Aligns with best practices from official Neo4j documentation

**Validation**: Before finalizing generated code, verify against the checklist in cypher_best_practices.md.

### 1. Discover the Data Model

**Source**: Use case markdown from CLI (`python3 cli.py get-usecase <URL>`)

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

## Performance Optimization for Large-Scale Data Loading

> **🚀 CRITICAL FOR PRODUCTION**: Follow these patterns when loading large datasets (>100K records).
>
> Based on real-world experience loading 5.6M+ Companies House records with addresses.

---

### Overview: The Performance Foundation

**The #1 performance killer in data loading**: Not creating constraints and indexes **before** loading data.

**Without constraints before loading**:
- Every `MERGE` operation scans all existing nodes (O(n) complexity)
- 5.6M companies = billions of comparisons
- Load time: hours or days

**With constraints created first**:
- `MERGE` uses index lookup (O(log n) complexity)
- 5.6M companies = fast indexed lookups
- Load time: minutes

---

### Principle 1: Native Cypher Only - No APOC

**CRITICAL**: Do not use APOC procedures in generated code.

❌ **Never use**:
```cypher
// APOC may not be installed
CALL apoc.periodic.iterate(...)
CALL apoc.load.csv(...)
CALL apoc.create.node(...)
```

✅ **Always use native Cypher**:
```cypher
// Works on any Neo4j instance
UNWIND $batch AS row
MERGE (n:Node {id: row.id})
SET n.property = row.value
```

**Why**:
- APOC is a plugin, not guaranteed to be installed
- Customer Neo4j instances may not have APOC enabled
- Generated code must work everywhere without dependencies
- Native Cypher is faster for bulk operations with proper indexing

---

### Principle 2: Constraints and Indexes BEFORE Data Loading

**The correct order**:
1. ✅ Create all constraints (for unique identifiers)
2. ✅ Create all indexes (for non-unique lookup properties)
3. ✅ Load all node types
4. ✅ Create all relationships

**Why constraints first**:
- Constraints automatically create indexes
- `MERGE` operations become O(log n) instead of O(n)
- Massive performance gain for large datasets

**Why indexes on non-unique properties**:
- Enables fast `MATCH` operations during relationship creation
- Example: Matching addresses by postcode for relationship creation

**Code template** (see Section 0 in Required Code Structure below):
```python
def create_constraints_and_indexes(query):
    """Create ALL constraints and indexes BEFORE loading data."""
    # Constraints on unique identifiers
    constraints = [
        "CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.companyId IS UNIQUE",
        "CREATE CONSTRAINT address_id_unique IF NOT EXISTS FOR (a:Address) REQUIRE a.addressId IS UNIQUE"
    ]

    # Indexes on non-unique lookup properties
    indexes = [
        "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)",
        "CREATE INDEX address_postcode IF NOT EXISTS FOR (a:Address) ON (a.postcode)"
    ]

    for constraint in constraints:
        query.run(constraint)

    for index in indexes:
        query.run(index)
```

**When to create indexes**:
- **BEFORE loading:** Unique constraints (used in MERGE)
- **BEFORE loading:** Indexes on properties used in relationship MATCH clauses
- **AFTER loading (optional):** Additional indexes for query optimization

---

### Principle 3: Multi-Pass Loading for Large Datasets

**For datasets with >1M records, use multi-pass loading strategy.**

**Single-pass approach** (❌ inefficient for large data):
```cypher
// Creates nodes and relationships in one query
// Problem: Nested MATCH operations during node creation are expensive
UNWIND $batch AS row
MERGE (c:Company {companyId: row.company_id})
MERGE (a:Address {addressId: row.address_id})
MERGE (c)-[:HAS_ADDRESS]->(a)
```

**Multi-pass approach** (✅ efficient for large data):
```python
# Pass 1: Load ALL Company nodes (5.6M records)
create_company_nodes(query, data)  # Uses constraint for fast MERGE

# Pass 2: Load ALL Address nodes
create_address_nodes(query, data)  # Uses constraint for fast MERGE

# Pass 3: Create ALL relationships
create_has_address_relationships(query, data)  # Uses both constraints for fast MATCH
```

**Why multi-pass is faster**:
1. Each pass focuses on one operation (node creation OR relationship creation)
2. Relationship creation uses indexed lookups (constraints created in step 0)
3. No nested MERGE operations (which are expensive)
4. Better memory usage and transaction management

**When to use multi-pass**:
- ✅ Datasets with >1M records
- ✅ Multiple node types (Companies, Addresses, etc.)
- ✅ Complex relationship patterns
- ✅ Production environments where performance matters

**When single-pass might be acceptable**:
- Small datasets (<10K records)
- Simple data model (one node type)
- Prototype/development environments

---

### Principle 4: Batch Size Optimization

**Batch size significantly impacts performance.**

**Recommended batch sizes by dataset scale**:

| Dataset Size | Node Batch Size | Relationship Batch Size | Rationale |
|--------------|----------------|------------------------|-----------|
| <10K records | 1,000 | 500 | Small transactions, frequent commits |
| 10K-100K | 5,000 | 2,500 | Balance transaction size and overhead |
| 100K-1M | 10,000 | 5,000 | Larger transactions for efficiency |
| 1M-10M | 10,000-15,000 | 5,000-7,500 | Tuned for large scale |
| >10M | 15,000-20,000 | 7,500-10,000 | Maximum efficiency, test and tune |

**Why different sizes for nodes vs relationships**:
- **Node creation**: Can handle larger batches (simpler operations)
- **Relationship creation**: Involves MATCH operations (more complex, smaller batches)

**How to determine optimal batch size**:
1. Start with recommended size based on dataset scale
2. Monitor memory usage during load
3. Use `PROFILE` on sample queries to check performance
4. Adjust batch size up/down based on results

**Example for 5.6M Companies House records**:
```python
# Nodes: 10,000 records per batch
create_company_nodes(query, data, batch_size=10000)

# Relationships: 5,000 per batch (more complex operations)
create_has_address_relationships(query, data, batch_size=5000)
```

---

### Principle 5: Query Consolidation vs Separation

**Understand when to combine operations vs separate them.**

#### ❌ Anti-Pattern: Nested Operations at Scale

```cypher
// Creating nodes and relationships in one query
// Problem: For each company, must search for address (expensive at scale)
UNWIND $batch AS row
MERGE (c:Company {companyId: row.company_id})
SET c.name = row.name
MERGE (a:Address {addressId: row.address_id})  // ❌ Expensive nested MERGE
SET a.street = row.street
MERGE (c)-[:HAS_ADDRESS]->(a)
```

**Why this is slow**:
- Each batch processes nodes AND relationships
- Nested MERGE operations multiply complexity
- Even with constraints, less efficient than separated operations

#### ✅ Optimal Pattern: Separated Multi-Pass

```cypher
// Pass 1: All Company nodes (fast, uses constraint)
UNWIND $batch AS row
MERGE (c:Company {companyId: row.company_id})
SET c.name = row.name,
    c.status = row.status

// Pass 2: All Address nodes (fast, uses constraint)
UNWIND $batch AS row
MERGE (a:Address {addressId: row.address_id})
SET a.street = row.street,
    a.postcode = row.postcode

// Pass 3: All relationships (fast, both sides use indexed lookups)
UNWIND $batch AS row
MATCH (c:Company {companyId: row.company_id})      // ✅ Index lookup
MATCH (a:Address {addressId: row.address_id})      // ✅ Index lookup
MERGE (c)-[:HAS_ADDRESS]->(a)
```

**Why this is fast**:
- Each query does one thing well
- All MATCH operations use indexed properties
- Constraints created first enable O(log n) lookups
- Better memory usage per transaction

---

### Principle 6: Progress Logging for Production

**Users need to see progress for large datasets.**

For datasets with millions of records, log progress periodically:

```python
batch_size = 10000
total_records = len(node_data)
log_interval = max(50000, batch_size * 10)  # Log every 50K or 10 batches

for i in range(0, total_records, batch_size):
    batch = node_data[i:i + batch_size]
    query.run(cypher, {'batch': batch})

    # Progress logging
    records_processed = min(i + batch_size, total_records)
    if records_processed % log_interval == 0 or records_processed == total_records:
        progress_pct = (records_processed / total_records) * 100
        log.info(f"  Progress: {records_processed:,} / {total_records:,} ({progress_pct:.1f}%)")
```

**Why this matters**:
- 5.6M records takes minutes to load
- Without logging, appears frozen
- Users need confirmation the process is working

---

### Complete Example: Companies House 5.6M Record Load

**Scenario**: Loading UK Companies House data with companies and addresses.

**Data model**:
- `Company` nodes: 5.6M records
- `Address` nodes: 4.2M unique addresses
- `HAS_ADDRESS` relationships: 5.6M connections

**Optimized loading strategy**:

```python
def main():
    """Load Companies House data with optimal performance."""
    log.info("Starting Companies House data load...")

    # Load source data
    data = load_data()

    # Get query runner
    query = get_query()

    try:
        # STEP 0: Create constraints and indexes FIRST
        # This is THE most important performance optimization
        create_constraints_and_indexes(query)

        # STEP 1: Load all Company nodes (5.6M records, batch_size=10000)
        create_company_nodes(query, data)

        # STEP 2: Load all Address nodes (4.2M records, batch_size=10000)
        create_address_nodes(query, data)

        # STEP 3: Create relationships (5.6M, batch_size=5000)
        # Fast because both Company and Address have constraints
        create_has_address_relationships(query, data)

        # Verify load
        verify_load(query)

        log.info("✅ Data load complete!")

    finally:
        query.close()


def create_constraints_and_indexes(query):
    """
    Create ALL constraints and indexes BEFORE loading data.
    Uses native Cypher only - no APOC required.
    """
    log.info("Creating constraints and indexes...")

    # Unique constraints (automatically create indexes)
    constraints = [
        "CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.companyId IS UNIQUE",
        "CREATE CONSTRAINT address_id_unique IF NOT EXISTS FOR (a:Address) REQUIRE a.addressId IS UNIQUE"
    ]

    # Additional indexes for non-unique lookup properties
    indexes = [
        "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)",
        "CREATE INDEX address_postcode IF NOT EXISTS FOR (a:Address) ON (a.postcode)"
    ]

    for constraint in constraints:
        query.run(constraint)
        log.info(f"  ✓ Created constraint")

    for index in indexes:
        query.run(index)
        log.info(f"  ✓ Created index")

    log.info("✓ All constraints and indexes created")


def create_company_nodes(query, data):
    """
    Load all Company nodes.
    Batch size: 10,000 for large dataset (5.6M records).
    """
    log.info("Creating Company nodes...")

    # Transform data
    company_data = [
        {
            'companyId': record['company_number'],
            'name': record['company_name'],
            'status': record['company_status'],
            'incorporationDate': record['incorporation_date']
        }
        for record in data
    ]

    # Cypher query (uses constraint for fast MERGE)
    cypher = """
    UNWIND $batch AS row
    MERGE (c:Company {companyId: row.companyId})
    SET c.name = row.name,
        c.status = row.status,
        c.incorporationDate = row.incorporationDate
    """

    # Load in batches with progress logging
    batch_size = 10000  # Optimal for large dataset
    total_records = len(company_data)
    log_interval = 50000  # Log every 50K records

    for i in range(0, total_records, batch_size):
        batch = company_data[i:i + batch_size]
        query.run(cypher, {'batch': batch})

        # Progress logging
        records_processed = min(i + batch_size, total_records)
        if records_processed % log_interval == 0 or records_processed == total_records:
            progress_pct = (records_processed / total_records) * 100
            log.info(f"  Progress: {records_processed:,} / {total_records:,} ({progress_pct:.1f}%)")

    log.info(f"✓ Created {len(company_data):,} Company nodes")


def create_address_nodes(query, data):
    """
    Load all Address nodes.
    Batch size: 10,000 for large dataset.
    """
    log.info("Creating Address nodes...")

    # Extract unique addresses
    address_data = []
    seen_addresses = set()

    for record in data:
        address_id = record['registered_office_address_hash']  # Unique identifier
        if address_id not in seen_addresses:
            address_data.append({
                'addressId': address_id,
                'street': record['address_line_1'],
                'locality': record['locality'],
                'postcode': record['postcode']
            })
            seen_addresses.add(address_id)

    # Cypher query (uses constraint for fast MERGE)
    cypher = """
    UNWIND $batch AS row
    MERGE (a:Address {addressId: row.addressId})
    SET a.street = row.street,
        a.locality = row.locality,
        a.postcode = row.postcode
    """

    # Load in batches
    batch_size = 10000
    total_records = len(address_data)
    log_interval = 50000

    for i in range(0, total_records, batch_size):
        batch = address_data[i:i + batch_size]
        query.run(cypher, {'batch': batch})

        records_processed = min(i + batch_size, total_records)
        if records_processed % log_interval == 0 or records_processed == total_records:
            progress_pct = (records_processed / total_records) * 100
            log.info(f"  Progress: {records_processed:,} / {total_records:,} ({progress_pct:.1f}%)")

    log.info(f"✓ Created {len(address_data):,} Address nodes")


def create_has_address_relationships(query, data):
    """
    Create HAS_ADDRESS relationships.
    Batch size: 5,000 (smaller because of MATCH operations).
    """
    log.info("Creating HAS_ADDRESS relationships...")

    # Extract relationships
    rel_data = [
        {
            'companyId': record['company_number'],
            'addressId': record['registered_office_address_hash']
        }
        for record in data
    ]

    # Cypher query (both MATCH clauses use indexed lookups)
    cypher = """
    UNWIND $batch AS row
    MATCH (c:Company {companyId: row.companyId})
    MATCH (a:Address {addressId: row.addressId})
    MERGE (c)-[:HAS_ADDRESS]->(a)
    """

    # Load in batches (smaller batch size for relationships)
    batch_size = 5000  # Smaller for MATCH operations
    total_records = len(rel_data)
    log_interval = 50000

    for i in range(0, total_records, batch_size):
        batch = rel_data[i:i + batch_size]
        query.run(cypher, {'batch': batch})

        records_processed = min(i + batch_size, total_records)
        if records_processed % log_interval == 0 or records_processed == total_records:
            progress_pct = (records_processed / total_records) * 100
            log.info(f"  Progress: {records_processed:,} / {total_records:,} ({progress_pct:.1f}%)")

    log.info(f"✓ Created {len(rel_data):,} HAS_ADDRESS relationships")
```

**Performance results**:
- **Without constraints first**: Hours or failure
- **With constraints first + multi-pass + optimal batching**: Minutes
- **Key factors**: Constraints, multi-pass strategy, large batch sizes

---

### Key Takeaways: Performance Optimization

**Always Do**:
1. ✅ **Create constraints and indexes FIRST** (before any data loading)
2. ✅ **Use native Cypher only** (no APOC dependencies)
3. ✅ **Use multi-pass loading** for large datasets (nodes first, then relationships)
4. ✅ **Use large batch sizes** for scale (10K+ for millions of records)
5. ✅ **Create indexes on lookup properties** (not just unique constraints)
6. ✅ **Log progress** for datasets with >100K records
7. ✅ **Test and tune batch sizes** based on memory and performance

**Never Do**:
1. ❌ Load data without creating constraints first
2. ❌ Use APOC procedures (may not be installed)
3. ❌ Create indexes after loading millions of records (very slow)
4. ❌ Use small batch sizes (1000) for large datasets (>1M records)
5. ❌ Combine node and relationship creation for large datasets
6. ❌ Skip progress logging for long-running operations

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

### 0. Create Constraints and Indexes (FIRST - BEFORE Data Loading)

**CRITICAL**: This function must be called BEFORE any data loading operations.

**Why this is Section 0**: It must execute before all other operations for optimal performance.

```python
def create_constraints_and_indexes(query):
    """
    Create ALL constraints and indexes BEFORE loading any data.

    CRITICAL IMPORTANCE:
    - Constraints enable O(log n) MERGE operations instead of O(n)
    - For 5.6M records: Minutes vs hours/failure
    - Must be called FIRST in main() function

    Uses native Cypher only - no APOC required.
    """
    log.info("Creating constraints and indexes...")

    # STEP 1: Create unique constraints on identifier properties
    # Constraints automatically create indexes for fast lookups
    constraints = [
        "CREATE CONSTRAINT node_type_id_unique IF NOT EXISTS FOR (n:NodeType) REQUIRE n.nodeId IS UNIQUE",
        # Add constraint for each node type with unique identifier
        # Example:
        # "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.customerId IS UNIQUE",
        # "CREATE CONSTRAINT email_address_unique IF NOT EXISTS FOR (e:Email) REQUIRE e.address IS UNIQUE",
    ]

    for constraint in constraints:
        query.run(constraint)
        log.info(f"  ✓ Created constraint")

    # STEP 2: Create additional indexes on non-unique lookup properties
    # These enable fast MATCH operations during relationship creation
    indexes = [
        "CREATE INDEX node_type_property IF NOT EXISTS FOR (n:NodeType) ON (n.propertyName)",
        # Add indexes for properties used in MATCH clauses
        # Example:
        # "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)",
        # "CREATE INDEX address_postcode IF NOT EXISTS FOR (a:Address) ON (a.postcode)",
    ]

    for index in indexes:
        query.run(index)
        log.info(f"  ✓ Created index")

    log.info("✓ All constraints and indexes created")
```

**When to create what**:
- **Constraints**: Always on unique identifier properties (companyId, customerId, etc.)
- **Regular indexes**: On properties used for lookups during relationship creation
- **Composite indexes**: When multiple properties are frequently used together in WHERE clauses

**Example for real use case**:
```python
def create_constraints_and_indexes(query):
    """Create constraints and indexes for Companies House data."""
    log.info("Creating constraints and indexes...")

    constraints = [
        # Company unique identifier
        "CREATE CONSTRAINT company_id_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.companyId IS UNIQUE",
        # Address unique identifier
        "CREATE CONSTRAINT address_id_unique IF NOT EXISTS FOR (a:Address) REQUIRE a.addressId IS UNIQUE",
    ]

    indexes = [
        # For searching companies by name
        "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)",
        # For grouping addresses by postcode
        "CREATE INDEX address_postcode IF NOT EXISTS FOR (a:Address) ON (a.postcode)",
    ]

    for constraint in constraints:
        query.run(constraint)
        log.info(f"  ✓ Created constraint")

    for index in indexes:
        query.run(index)
        log.info(f"  ✓ Created index")

    log.info("✓ All constraints and indexes created")
```

**Performance impact**:
- **Without constraints**: MERGE scans all existing nodes (O(n) - very slow)
- **With constraints**: MERGE uses index lookup (O(log n) - fast)
- **For 5.6M records**: Difference between minutes and hours/failure

---

### 1. Path Setup (REQUIRED)

**ALWAYS start with this pattern**:

```python
# Setup Python path to find toolkit modules
import sys
from pathlib import Path

# Get project root (3 levels up from this script)
# workspace/generated/data_mapper.py -> workspace/generated/ -> workspace/ -> project_root/
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent.parent
sys.path.insert(0, str(project_root))
```

**Directory Structure Context**:
```
neo4j-demo-toolkit/              <- project root (where src/ lives)
├── src/                         <- toolkit source code
│   └── core/
│       └── neo4j/
├── workspace/
│   ├── raw_data/
│   │   └── data.csv
│   └── generated/
│       └── data_mapper.py       <- your script lives here
```

**Path Traversal from data_mapper.py**:
- `script_path.parent` = `workspace/generated/`
- `script_path.parent.parent` = `workspace/`
- `script_path.parent.parent.parent` = `neo4j-demo-toolkit/` (project root) ✅

**Why This Matters**:
- Makes script runnable from any directory
- Ensures `from src.*` imports work correctly
- Must come BEFORE any toolkit imports
- **CRITICAL**: Use exactly 3 `.parent` calls for project root

**Validation Tip**:
If you see `ModuleNotFoundError: No module named 'src'`, the path setup is wrong.
The correct pattern is always `.parent.parent.parent` (3 levels) for scripts in `workspace/generated/`.

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

    CRITICAL ORDER for large datasets:
    1. Create constraints and indexes FIRST
    2. Load all node types (multi-pass for >1M records)
    3. Create all relationships
    4. Verify results
    """
    log.info("Starting data load for <Use Case Name>...")

    # Load data
    data = load_data()

    # Get query runner (discovered from version.py)
    query = get_query()

    try:
        # STEP 0: Create constraints and indexes FIRST
        # CRITICAL: Must be called before any data loading
        # For large datasets (>1M), this is the difference between minutes and hours
        create_constraints_and_indexes(query)

        # STEP 1: Load all node types
        # For large datasets, use multi-pass strategy (all nodes of each type)
        create_<NodeType>_nodes(query, data)
        # ... more node types

        # STEP 2: Create all relationships
        # Fast because constraints enable indexed lookups in MATCH clauses
        create_<RELATIONSHIP>_relationships(query, data)
        # ... more relationships

        # STEP 3: Verify results
        verify_load(query)

        log.info("✅ Data load complete!")

    finally:
        # Always close connection
        query.close()


if __name__ == '__main__':
    main()
```

**Key patterns**:
- **STEP 0 is mandatory**: Create constraints and indexes before any data loading
- **Multi-pass for scale**: All nodes first, then all relationships (for >1M records)
- **Try/finally**: Ensure cleanup even if errors occur
- **Call query.close()**: Always clean up connection
- **Log progress**: At each major step
- **Helpful completion message**: User knows when load is done

---

## Cypher Query Patterns

### Neo4j Best Practices

**IMPORTANT**: All Cypher queries must follow Neo4j best practices. See [neo4j/cypher_best_practices.md](neo4j/cypher_best_practices.md) for complete guidelines.

**Quick reference**:
- **Node labels**: `CamelCase` (e.g., `Customer`, `EmailAddress`)
- **Relationship types**: `UPPER_SNAKE_CASE` (e.g., `HAS_EMAIL`, `PLACED_ORDER`)
- **Properties**: `camelCase` (e.g., `firstName`, `customerId`)
- **Constraints**: Create before loading data
- **Indexing**: Anchor queries on indexed properties
- **Batching**: 1000-10000 records per batch for optimal performance

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
python3 cli.py get-usecase https://neo4j.com/...synthetic-identity-fraud/

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

## Presenting Mappings to User

**CRITICAL**: When presenting mapping decisions to users, ALWAYS use Cypher-style syntax. Neo4j users need to see how their data will be structured as nodes and relationships in the graph.

### Format for Mapping Presentation

Before generating code, present the planned mappings using Cypher syntax with inline comments:

```cypher
// Mapping Plan: customer_data.csv → Synthetic Identity Fraud Detection Model

(:Customer {
  customerId: customer_id,           // Source: customer_data.csv 'customer_id' column

  // Extended properties (beyond base model)
  firstName: first_name,             // Source: customer_data.csv 'first_name'
  lastName: last_name,               // Source: customer_data.csv 'last_name'
  signupDate: signup_date            // Source: customer_data.csv 'signup_date', parse MM/DD/YYYY
})

(:Email {
  address: email                     // Source: customer_data.csv 'email', validate format
})

(:Phone {
  phoneNumber: phone                 // Source: customer_data.csv 'phone', clean format
})

// Relationships
(:Customer)-[:HAS_EMAIL]->(:Email)
(:Customer)-[:HAS_PHONE]->(:Phone)
```

### Annotate with Data Quality Notes

When you've analyzed the data (using analyze_data_quality.md), include data quality findings in comments:

```cypher
// Mapping with Data Quality Notes

(:Customer {
  customerId: customer_id,           // Source: customer_data.csv - ✓ 100% unique

  // Extended properties
  firstName: first_name,             // Source: customer_data.csv - ✓ no nulls
  lastName: last_name,               // Source: customer_data.csv - ✓ no nulls
  signupDate: signup_date            // Source: customer_data.csv - ⚠️ parse MM/DD/YYYY, 5 invalid dates
})

(:Email {
  address: email                     // Source: customer_data.csv - ⚠️ 15 invalid formats, will skip
})

(:Phone {
  phoneNumber: phone                 // Source: customer_data.csv - ⚠️ 120 null values (1.2%), will skip
})
```

### Show Transformations Clearly

When data requires transformation (cleaning, parsing, type conversion), make it explicit:

```cypher
// Mapping with Transformations

(:Transaction {
  transactionId: id,                 // Source: transactions.csv 'id'
  amount: amount,                    // Source: transactions.csv 'amount' - CLEAN: remove $ prefix
  date: date,                        // Source: transactions.csv 'date' - PARSE: YYYY-MM-DD → datetime
  type: use_chip,                    // Source: transactions.csv 'use_chip' - MAP: Swipe/Chip/Online → type

  // Extended properties
  merchantCity: merchant_city,       // Source: transactions.csv - ⚠️ 0.9% nulls
  merchantState: merchant_state,     // Source: transactions.csv - ✓ all valid US codes
  mcc: mcc                          // Source: transactions.csv - JOIN: mcc_codes.json for description
})
```

### Format for Extension Properties

Clearly separate base model properties from extended properties:

```cypher
// Base Model vs Extended Properties

(:Customer {
  // Base Model Properties (required by use case)
  customerId: id,                    // Required: unique identifier

  // Extended Properties (from user data, beyond base model)
  firstName: first_name,             // Additional context
  lastName: last_name,               // Additional context
  currentAge: current_age,           // Additional context
  gender: gender,                    // Additional context
  creditScore: credit_score,         // Additional context - useful for fraud detection
  yearlyIncome: yearly_income        // Additional context - CLEAN: remove $ prefix
})
```

### Why This Format Matters

**Benefits**:
- **Immediate recognition**: Users see familiar Cypher syntax
- **Visual verification**: Shows exactly what will be created in Neo4j
- **Source traceability**: Comments link each property to source data
- **Transformation clarity**: Shows what cleaning/parsing will occur
- **Quality visibility**: Data issues annotated inline
- **Decision review**: Users can approve/adjust before code generation

**When to use**:
- After planning mappings but before generating code
- In data validation reports showing schema compatibility
- When explaining mapping decisions to users
- As documentation in generated code comments
- Anywhere you describe how source data → graph nodes

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Loading Data Without Creating Constraints First

**THE #1 PERFORMANCE KILLER**

```python
# DON'T load data before creating constraints
def main():
    data = load_data()
    query = get_query()
    create_company_nodes(query, data)  # ❌ SLOW - no constraints yet!
    create_constraints_and_indexes(query)  # ❌ Too late!
```

**Why this is catastrophic**:
- Every MERGE scans all existing nodes (O(n) complexity)
- For 5.6M records: Hours or days instead of minutes
- May timeout or fail entirely

**✅ Instead**: Always create constraints FIRST
```python
def main():
    data = load_data()
    query = get_query()
    create_constraints_and_indexes(query)  # ✅ FIRST!
    create_company_nodes(query, data)  # ✅ Fast - uses constraints
```

---

### ❌ Mistake 2: Using APOC Procedures

```cypher
# DON'T use APOC (may not be installed)
CALL apoc.periodic.iterate(
  "MATCH (n) RETURN n",
  "SET n.processed = true",
  {batchSize: 1000}
)

CALL apoc.load.csv('file.csv') YIELD map
CREATE (n:Node {data: map})
```

**Why this fails**:
- APOC is a plugin, not guaranteed to be installed
- Customer Neo4j instances often don't have APOC enabled
- Generated code must work everywhere

**✅ Instead**: Use native Cypher only
```cypher
# Native Cypher works everywhere
UNWIND $batch AS row
MERGE (n:Node {id: row.id})
SET n.property = row.value
```

---

### ❌ Mistake 3: Small Batch Sizes for Large Datasets

```python
# DON'T use small batches for large datasets
batch_size = 1000  # ❌ Too small for 5.6M records!

for i in range(0, 5_600_000, batch_size):
    # This creates 5,600 transactions - inefficient!
```

**Why this is slow**:
- Transaction overhead adds up (5,600 transactions!)
- More network round trips
- Suboptimal resource utilization

**✅ Instead**: Scale batch size with data volume
```python
# For 5.6M records, use large batches
batch_size = 10000  # ✅ Only 560 transactions

for i in range(0, 5_600_000, batch_size):
    # Much more efficient!
```

**Recommended batch sizes**:
- <10K records: 1,000
- 100K-1M: 10,000
- >1M records: 10,000-15,000

---

### ❌ Mistake 4: Combining Node and Relationship Creation at Scale

```cypher
# DON'T combine operations for large datasets
UNWIND $batch AS row
MERGE (c:Company {companyId: row.company_id})
MERGE (a:Address {addressId: row.address_id})  # ❌ Nested MERGE expensive!
MERGE (c)-[:HAS_ADDRESS]->(a)
```

**Why this is slow**:
- Nested MERGE operations multiply complexity
- Even with constraints, less efficient than separated operations
- Poor memory usage pattern

**✅ Instead**: Use multi-pass loading
```cypher
// Pass 1: All Company nodes
UNWIND $batch AS row
MERGE (c:Company {companyId: row.company_id})
SET c.name = row.name

// Pass 2: All Address nodes
UNWIND $batch AS row
MERGE (a:Address {addressId: row.address_id})
SET a.street = row.street

// Pass 3: All relationships (fast - both sides indexed)
UNWIND $batch AS row
MATCH (c:Company {companyId: row.company_id})
MATCH (a:Address {addressId: row.address_id})
MERGE (c)-[:HAS_ADDRESS]->(a)
```

---

### ❌ Mistake 5: Creating Indexes After Loading Data

```python
# DON'T create indexes after loading millions of records
def main():
    data = load_data()
    query = get_query()
    create_company_nodes(query, data)  # Load 5.6M records
    create_address_nodes(query, data)  # Load 4.2M records
    create_constraints_and_indexes(query)  # ❌ VERY SLOW retroactive indexing!
```

**Why this is catastrophic**:
- Retroactive indexing on millions of records is VERY slow
- Locks the database during index creation
- May timeout

**✅ Instead**: Create indexes BEFORE data loading
```python
def main():
    data = load_data()
    query = get_query()
    create_constraints_and_indexes(query)  # ✅ FIRST - fast on empty database
    create_company_nodes(query, data)  # Uses indexes immediately
    create_address_nodes(query, data)  # Uses indexes immediately
```

---

### ❌ Mistake 6: Hard-coding Toolkit API

```python
# DON'T assume function names
from src.core.neo4j import Neo4jWriter  # May not exist!
writer.write_nodes(data)  # May not exist!
```

**✅ Instead**: Read src/core/neo4j/ files to discover actual API

---

### ❌ Mistake 7: Modifying Data Model

```python
# DON'T rename node labels
CREATE (n:Person {id: row.id})  # Use case says "Customer"!
```

**✅ Instead**: Use exact labels from use case

---

### ❌ Mistake 8: Missing Path Setup

```python
# DON'T start with toolkit imports
from src.core.neo4j.version import get_query  # Will fail!
```

**✅ Instead**: Add path setup FIRST (see Section 1)

---

### ❌ Mistake 9: Wrong Batch Pattern

```python
# DON'T use non-standard patterns
MERGE (n:Customer {id: $id})  # Missing UNWIND $batch!
```

**✅ Instead**: Use `UNWIND $batch AS row` pattern

---

### ❌ Mistake 10: No Progress Logging for Large Datasets

```python
# DON'T use run_batched() without progress logging
query.run_batched(cypher, node_data, batch_size=1000)  # User sees no progress!
```

**✅ Instead**: Implement manual batching loop with progress logging
```python
# Log progress every 50k records
for i in range(0, len(node_data), batch_size):
    batch = node_data[i:i + batch_size]
    query.run(cypher, {'batch': batch})

    records_processed = min(i + batch_size, len(node_data))
    if records_processed % 50000 == 0 or records_processed == len(node_data):
        progress_pct = (records_processed / len(node_data)) * 100
        log.info(f"  Progress: {records_processed:,} / {len(node_data):,} ({progress_pct:.1f}%)")
```

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

### Always Do (CRITICAL for Production):

**Performance Optimization (Most Important)**:
1. ✅ **Create constraints and indexes FIRST** - before any data loading (difference between minutes and hours)
2. ✅ **Use native Cypher only** - no APOC dependencies (may not be installed)
3. ✅ **Use multi-pass loading** for large datasets (>1M: all nodes first, then relationships)
4. ✅ **Scale batch sizes** with data volume (10K+ for millions of records, 5K for relationships)
5. ✅ **Create indexes on lookup properties** - not just unique constraints (enables fast MATCH)
6. ✅ **Log progress** for datasets with >100K records (every 50K records)
7. ✅ **Test and tune batch sizes** based on memory and performance monitoring

**Code Generation Standards**:
8. ✅ **Review Neo4j best practices** (neo4j/cypher_best_practices.md) before generating
9. ✅ **Read toolkit source code** before generating (discover API)
10. ✅ **Follow use case data model** exactly (labels, types, required properties)
11. ✅ **Apply naming conventions**: CamelCase nodes, UPPER_SNAKE_CASE relationships, camelCase properties
12. ✅ **Include path setup** at top of generated script
13. ✅ **Use discovered API** (don't assume function names)
14. ✅ **Adapt data reading** to actual format (CSV, JSON, etc.)
15. ✅ **Clean up resources** in finally block
16. ✅ **Validate generated code** against best practices checklist

### Never Do (WILL CAUSE FAILURES):

**Performance Killers (CRITICAL)**:
1. ❌ **Load data without creating constraints first** - catastrophic for large datasets (hours vs minutes)
2. ❌ **Use APOC procedures** - may not be installed, code won't be portable
3. ❌ **Create indexes after loading millions of records** - very slow retroactive indexing
4. ❌ **Use small batch sizes (1000) for large datasets (>1M)** - inefficient transaction overhead
5. ❌ **Combine node and relationship creation** for large datasets - nested operations are expensive
6. ❌ **Skip progress logging** for long-running operations - appears frozen to users

**Code Generation Errors**:
7. ❌ Hard-code toolkit API assumptions
8. ❌ Change use case node labels or relationship types
9. ❌ Invent custom data models
10. ❌ Skip path setup boilerplate
11. ❌ Forget to close connections

### Discovery Sources:
- `neo4j/cypher_best_practices.md` → Neo4j standards and optimization (mandatory)
- Use case markdown → Data model (authoritative)
- `src/core/neo4j/` → Query API (latest)
- `workspace/generated/data_mapper.py` → Working patterns
- User's data files → Actual format and structure

---

## See Also

- `neo4j/cypher_best_practices.md` - Neo4j standards and optimization (READ FIRST)
- `../AGENT.md` - Overall toolkit guidance
- `match_business_to_usecases.md` - How to fetch official use cases
- `analyze_data_quality.md` - Data validation before code generation
- `validate_neo4j_connection.md` - Connection validation (if needed for Cypher version)
- Working example: `workspace/generated/data_mapper.py`
