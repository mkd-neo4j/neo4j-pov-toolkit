# Neo4j Demo Toolkit - Technical Solution

## Overview

The Neo4j Demo Toolkit is an LLM-powered code generation system that transforms raw data into a working Neo4j database with minimal user effort. The user provides their data, selects a use case, and the system generates a single, readable ingestion file that maps their data to proven Neo4j data models.

**Core Principle**: The LLM generates only the essential translation logic. Everything else database writing, logging, connection management, version handling is pre-built, tested, and optimized.

## Architecture Philosophy

### What the LLM Generates
- **One file**: `src/data_mapper.py`
- **One purpose**: Translate raw CSV/JSON data into Neo4j-ready structures
- **Minimal complexity**: Simple, readable Python that maps fields and calls pre-built functions

### What's Pre-Built
- Neo4j connection and version detection
- Version-specific database writers (Neo4j 4.x and 5.x)
- Logging infrastructure
- Data validation utilities
- Error handling

### What the User Provides
- Raw data files (CSVs, JSON, etc.)
- A single `.env` configuration file with Neo4j credentials
- Answers to LLM questions about their use case

## Repository Structure

```
neo4j-demo-toolkit/
├── raw_data/                           # User drops their data here
│   ├── customers.csv
│   ├── accounts.csv
│   └── transactions.csv
│
├── src/
│   ├── data_mapper.py                 # ONLY LLM-generated file
│   │                                   # Easy to find, easy to read
│   │
│   └── core/                           # Pre-built infrastructure (hidden)
│       ├── setup/
│       │   └── check_neo4j.py         # Validate connection + detect version
│       │
│       ├── neo4j/
│       │   ├── connection.py          # Connection management
│       │   ├── writer_v4.py           # Neo4j 4.x specific implementation
│       │   ├── writer_v5.py           # Neo4j 5.x specific implementation
│       │   └── validator.py           # Data validation utilities
│       │
│       ├── logger.py                  # Pre-configured logging
│       └── utils.py                   # Helper functions
│
├── prompts/                            # Markdown prompts for LLM orchestration
│   ├── README.md                      # How the prompt system works
│   ├── 00_setup.md                    # Step 0: Connection & version detection
│   ├── 01_discover_usecase.md         # Step 1: Fetch use cases from website
│   ├── 02_analyze_data.md             # Step 2: Understand CSV structure
│   └── 03_generate_mapper.md          # Step 3: Generate data_mapper.py
│
├── config/
│   └── .env.example                   # Template for user configuration
│
└── docs/
    ├── WHY.md                          # Why this toolkit exists
    └── solution/
        └── SOLUTION.md                 # This document
```

## The Single Configuration File

Users configure exactly **one thing**: their Neo4j connection.

**`.env`** (user creates from `.env.example`):
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

That's it. No Python configuration files. No complex settings. Just connection details.

## Version Detection System

### Why Version Detection Matters

Neo4j has evolved significantly across versions:
- **Neo4j 4.x** uses older Cypher syntax and patterns
- **Neo4j 5.x** introduced new type systems, improved functions, and modern syntax

The LLM needs to know which version it's targeting so it can:
1. Generate appropriate Cypher syntax (different patterns, functions, keywords)
2. Use version-specific features (vector indexes in 5.x, legacy constraints in 4.x)
3. Ensure generated code runs without errors

### Two-Layer Version Handling

#### Layer 1: LLM Knowledge (Code Generation)
**When**: Before generating `data_mapper.py`
**Purpose**: Generate version-appropriate Cypher queries

The LLM runs `python src/core/setup/check_neo4j.py` which returns:
```json
{
  "connected": true,
  "neo4j_version": "5.15.0",
  "cypher_version": "23",
  "version_major": "5",
  "enterprise": true
}
```

With this information, the LLM knows:
- "I'm generating code for Neo4j 5.15"
- "I can use Cypher 23 features"
- "I should use `elementId()` not `id()`"
- "I can use `SET n += {props}` syntax"

#### Layer 2: Runtime Selection (Code Execution)
**When**: When `data_mapper.py` runs
**Purpose**: Use the correct database driver and patterns

The generated code calls:
```python
from src.core.neo4j.connection import get_writer

writer = get_writer()  # Automatically returns v4 or v5 writer
```

`get_writer()` internally:
1. Reads the Neo4j version
2. Returns `Neo4jWriterV4()` or `Neo4jWriterV5()`
3. Each writer uses version-specific driver patterns

### Version-Specific Code Examples

**Neo4j 4.x (Cypher 5) - Generated Code:**
```python
# LLM generates this when it knows version is 4.x
cypher = """
MERGE (c:Customer {customerId: $customerId})
ON CREATE SET
  c.createdAt = timestamp(),
  c.firstName = $firstName,
  c.lastName = $lastName
ON MATCH SET
  c.updatedAt = timestamp()
"""
```

**Neo4j 5.x (Cypher 23) - Generated Code:**
```python
# LLM generates this when it knows version is 5.x
cypher = """
MERGE (c:Customer {customerId: $customerId})
SET c += {
  firstName: $firstName,
  lastName: $lastName,
  createdAt: coalesce(c.createdAt, timestamp()),
  updatedAt: timestamp()
}
"""
```

Both accomplish the same goal, but use syntax appropriate to the version.

## The LLM-Generated File: `data_mapper.py`

This is the **only** file the LLM creates. It's deliberately simple and readable.

### Example Generated File

```python
"""
Data mapper for Synthetic Identity Fraud Detection
Generated for Neo4j 5.15.0 (Cypher 23)

This file maps raw CSV data to the Synthetic Identity data model:
- Nodes: Customer, Email, Phone, Device, Address
- Relationships: HAS_EMAIL, HAS_PHONE, USES_DEVICE, HAS_ADDRESS
"""

import csv
from pathlib import Path
from src.core.neo4j.connection import get_writer
from src.core.logger import log

def load_customers():
    """Load customer nodes from customers.csv"""
    writer = get_writer()

    customers = []
    with open('raw_data/customers.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            customers.append({
                'customerId': row['customer_id'],      # CSV -> Graph mapping
                'firstName': row['first_name'],         # Handles field translation
                'lastName': row['last_name'],
                'createdDate': row['created_date']
            })

    log.info(f"Loaded {len(customers)} customers from CSV")

    # Use pre-built function to write to Neo4j
    writer.write_nodes(
        label='Customer',
        data=customers,
        primary_key='customerId',
        batch_size=1000
    )

    log.info(f"- Created {len(customers)} Customer nodes")

def load_pii():
    """Load PII nodes (Email, Phone, Device) and relationships"""
    writer = get_writer()

    emails = []
    phones = []
    devices = []

    with open('raw_data/pii.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['pii_type'] == 'email':
                emails.append({
                    'emailAddress': row['pii_value'],
                    'customerId': row['customer_id']
                })
            elif row['pii_type'] == 'phone':
                phones.append({
                    'phoneNumber': row['pii_value'],
                    'customerId': row['customer_id']
                })
            elif row['pii_type'] == 'device':
                devices.append({
                    'deviceId': row['pii_value'],
                    'customerId': row['customer_id']
                })

    log.info(f"Loaded {len(emails)} emails, {len(phones)} phones, {len(devices)} devices")

    # Create Email nodes and relationships
    writer.write_nodes(label='Email', data=emails, primary_key='emailAddress')
    writer.write_relationships(
        rel_type='HAS_EMAIL',
        start_node_label='Customer',
        end_node_label='Email',
        start_key='customerId',
        end_key='emailAddress',
        data=emails
    )

    # Create Phone nodes and relationships
    writer.write_nodes(label='Phone', data=phones, primary_key='phoneNumber')
    writer.write_relationships(
        rel_type='HAS_PHONE',
        start_node_label='Customer',
        end_node_label='Phone',
        start_key='customerId',
        end_key='phoneNumber',
        data=phones
    )

    # Create Device nodes and relationships
    writer.write_nodes(label='Device', data=devices, primary_key='deviceId')
    writer.write_relationships(
        rel_type='USES_DEVICE',
        start_node_label='Customer',
        end_node_label='Device',
        start_key='customerId',
        end_key='deviceId',
        data=devices
    )

    log.info("Created all PII nodes and relationships")

def main():
    """Main ingestion pipeline"""
    log.info("Starting Synthetic Identity data ingestion...")

    load_customers()
    load_pii()

    log.info("- Ingestion complete!")
    log.info("You can now query your graph to detect shared PII patterns")

if __name__ == '__main__':
    main()
```

### Key Characteristics

1. **Readable**: Anyone can understand what it does
2. **Simple**: Just CSV reading and field mapping
3. **Focused**: Only translation logic, no infrastructure code
4. **Logged**: Pre-built logging shows progress
5. **Versioned**: Generated for specific Neo4j version

The user can:
- Read it to understand the mapping
- Modify it if they want to adjust field names
- Regenerate it if they change their data structure

## Pre-Built Infrastructure

These files are written once, tested thoroughly, and never change.

### `src/core/setup/check_neo4j.py`

```python
"""
Validates Neo4j connection and detects version information.
Run this FIRST before any code generation.

Usage:
    python src/core/setup/check_neo4j.py

Returns JSON:
    {
      "connected": true,
      "neo4j_version": "5.15.0",
      "cypher_version": "23",
      "version_major": "5",
      "enterprise": true
    }
"""

import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

def check_connection():
    load_dotenv()

    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER')
    password = os.getenv('NEO4J_PASSWORD')

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))

        # Get version information
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            component = result.single()

            version = component['versions'][0]
            edition = component['edition']
            major = version.split('.')[0]

            # Determine Cypher version based on Neo4j version
            cypher_version = "23" if major == "5" else "5"

            return {
                "connected": True,
                "neo4j_version": version,
                "cypher_version": cypher_version,
                "version_major": major,
                "enterprise": edition == "enterprise"
            }

    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }

    finally:
        driver.close()

if __name__ == '__main__':
    result = check_connection()
    print(json.dumps(result, indent=2))
```

### `src/core/neo4j/connection.py`

```python
"""
Manages Neo4j connections and version-specific writer selection.
"""

import os
from dotenv import load_dotenv
from .writer_v4 import Neo4jWriterV4
from .writer_v5 import Neo4jWriterV5

load_dotenv()

_cached_version = None

def get_neo4j_version():
    """
    Detects Neo4j version.
    Cached after first call for performance.
    """
    global _cached_version

    if _cached_version:
        return _cached_version

    from neo4j import GraphDatabase

    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER')
    password = os.getenv('NEO4J_PASSWORD')

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        result = session.run("CALL dbms.components() YIELD versions")
        version = result.single()['versions'][0]
        _cached_version = version

    driver.close()
    return version

def get_writer():
    """
    Returns the appropriate Neo4j writer for the detected version.

    Returns:
        Neo4jWriterV4 or Neo4jWriterV5
    """
    version = get_neo4j_version()
    major_version = int(version.split('.')[0])

    if major_version >= 5:
        return Neo4jWriterV5()
    else:
        return Neo4jWriterV4()
```

### `src/core/neo4j/writer_v5.py`

```python
"""
Neo4j 5.x writer implementation.
Uses modern Cypher syntax and driver patterns.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from ..logger import log

class Neo4jWriterV5:
    def __init__(self):
        load_dotenv()
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )

    def write_nodes(self, label, data, primary_key, batch_size=1000):
        """
        Write nodes to Neo4j using optimized batching.
        Uses Neo4j 5.x Cypher syntax.
        """
        cypher = f"""
        UNWIND $batch AS row
        MERGE (n:{label} {{{primary_key}: row.{primary_key}}})
        SET n += row
        """

        self._execute_batched(cypher, data, batch_size)

    def write_relationships(self, rel_type, start_node_label, end_node_label,
                          start_key, end_key, data, batch_size=1000):
        """
        Write relationships to Neo4j using optimized batching.
        Uses Neo4j 5.x Cypher syntax.
        """
        cypher = f"""
        UNWIND $batch AS row
        MATCH (start:{start_node_label} {{{start_key}: row.{start_key}}})
        MATCH (end:{end_node_label} {{{end_key}: row.{end_key}}})
        MERGE (start)-[r:{rel_type}]->(end)
        SET r += row
        """

        self._execute_batched(cypher, data, batch_size)

    def _execute_batched(self, cypher, data, batch_size):
        """Execute Cypher in batches for performance"""
        with self.driver.session(database=self.database) as session:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                session.run(cypher, batch=batch)
                log.debug(f"Processed batch {i//batch_size + 1}")

    def close(self):
        self.driver.close()
```

### `src/core/neo4j/writer_v4.py`

```python
"""
Neo4j 4.x writer implementation.
Uses legacy Cypher syntax for compatibility.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from ..logger import log

class Neo4jWriterV4:
    def __init__(self):
        load_dotenv()
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )

    def write_nodes(self, label, data, primary_key, batch_size=1000):
        """
        Write nodes to Neo4j using Neo4j 4.x compatible syntax.
        """
        # Build property setting manually for 4.x compatibility
        cypher = f"""
        UNWIND $batch AS row
        MERGE (n:{label} {{{primary_key}: row.{primary_key}}})
        ON CREATE SET n = row
        ON MATCH SET n = row
        """

        self._execute_batched(cypher, data, batch_size)

    def write_relationships(self, rel_type, start_node_label, end_node_label,
                          start_key, end_key, data, batch_size=1000):
        """
        Write relationships using Neo4j 4.x patterns.
        """
        cypher = f"""
        UNWIND $batch AS row
        MATCH (start:{start_node_label} {{{start_key}: row.{start_key}}})
        MATCH (end:{end_node_label} {{{end_key}: row.{end_key}}})
        MERGE (start)-[r:{rel_type}]->(end)
        ON CREATE SET r = row
        ON MATCH SET r = row
        """

        self._execute_batched(cypher, data, batch_size)

    def _execute_batched(self, cypher, data, batch_size):
        """Execute Cypher in batches"""
        with self.driver.session(database=self.database) as session:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                session.run(cypher, batch=batch)
                log.debug(f"Processed batch {i//batch_size + 1}")

    def close(self):
        self.driver.close()
```

### `src/core/logger.py`

```python
"""
Pre-configured logging for the toolkit.
Provides clean, colorized output for user feedback.
"""

import logging
import sys

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stdout
)

log = logging.getLogger('neo4j-demo-toolkit')

# Usage in generated code:
# from src.core.logger import log
# log.info("Message")
# log.debug("Debug info")
# log.error("Error message")
```

## Prompt-Driven Workflow

The prompts are **markdown files** that guide the LLM through a structured conversation. They don't contain hardcoded use cases instead, they instruct the LLM to fetch information dynamically from the Neo4j website.

### Why Markdown Prompts?

1. **Human-readable**: Easy to understand and modify
2. **Version-controllable**: Track changes over time
3. **Self-documenting**: The prompt explains what it does
4. **Dynamic**: Fetch use cases from website, don't hardcode them

### Prompt Flow

#### `prompts/00_setup.md`

```markdown
# Setup & Connection Validation

**Purpose**: Verify Neo4j connection and detect version before any code generation.

## Steps

1. **Check for .env file**
   - If missing, guide user to create it from .env.example
   - Required fields: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

2. **Run version detection**
   ```bash
   python src/core/setup/check_neo4j.py
   ```

3. **Parse the output JSON**
   Store this information for ALL subsequent prompts:
   - `neo4j_version`: Full version (e.g., "5.15.0")
   - `cypher_version`: Cypher version (e.g., "23")
   - `version_major`: Major version (e.g., "5")
   - `enterprise`: Boolean

4. **Communicate to user**
   "- Connected to Neo4j {version} (Cypher {cypher_version})"

## Critical Context

This version information MUST be available when generating Cypher in step 03.

Different Neo4j versions support different features:
- **Neo4j 4.x (Cypher 5)**: Legacy patterns, `ON CREATE/MATCH SET`, `id()`
- **Neo4j 5.x (Cypher 23)**: Modern syntax, `SET +=`, `elementId()`, vector indexes

## Error Handling

If connection fails:
- Show the error message
- Guide user to check .env credentials
- Suggest common issues (wrong URI, incorrect password, Neo4j not running)

## Next Step

Once connected and version detected proceed to `01_discover_usecase.md`
```

#### `prompts/01_discover_usecase.md`

```markdown
# Use Case Discovery

**Purpose**: Help user select a fraud detection use case by fetching options from the Neo4j website.

## Important: Self-Discovery

DO NOT use hardcoded use case lists. Always fetch fresh from the website.

## Steps

1. **Fetch use cases from Neo4j website**
   - URL: https://neo4j.com/developer/industry-use-cases/
   - Focus on fraud detection use cases
   - Extract: Use case names, descriptions, data model links

2. **Present to user**
   Show available use cases with brief descriptions:
   ```
   Available Fraud Detection Use Cases:

   1. Synthetic Identity Fraud
      Detect shared PII across supposedly distinct customers

   2. Transaction Monitoring
      Identify suspicious patterns in financial transactions

   3. Account Takeover
      Flag compromised accounts through behavioral analysis

   4. Fraud Rings
      Uncover networks of coordinated fraudulent activity

   Which use case would you like to implement?
   ```

3. **User selects use case**
   Store the selection for subsequent prompts.

4. **Fetch use case details**
   - Navigate to the specific use case page
   - Extract the data model definition
   - Identify minimum required data
   - Note any specific Cypher patterns or queries

## Context to Preserve

- Selected use case name
- Target data model (nodes, relationships, properties)
- Minimum data requirements
- Example queries (for documentation)

## Next Step

Once use case selected proceed to `02_analyze_data.md`
```

#### `prompts/02_analyze_data.md`

```markdown
# Data Analysis

**Purpose**: Understand the structure of the user's raw data and plan the mapping.

## Context Available

- Neo4j version: {from step 00}
- Selected use case: {from step 01}
- Target data model: {from step 01}

## Steps

1. **List files in raw_data/**
   ```bash
   ls raw_data/
   ```

2. **Inspect each file**
   For each CSV/JSON:
   - Read first 10 rows
   - Identify columns/fields
   - Understand data types
   - Note any data quality issues

3. **Map data to target model**
   Create a mapping plan:
   ```
   CSV: customers.csv
   Columns: customer_id, first_name, last_name, email, created_date

   > Will create Customer nodes
     customerId: customer_id
     firstName: first_name
     lastName: last_name
     email: email
     createdDate: created_date

   CSV: pii.csv
   Columns: customer_id, pii_type, pii_value

   > Will create Email, Phone, Device nodes based on pii_type
   > Will create HAS_EMAIL, HAS_PHONE, USES_DEVICE relationships
   ```

4. **Validate against minimum requirements**
   - Does the data contain required fields for this use case?
   - Are there any missing critical pieces?
   - Are there additional fields that could enrich the model?

5. **Present mapping plan to user**
   Show the proposed field mappings and ask for confirmation.

## User Feedback

User may:
- Approve the mapping > proceed to generation
- Request adjustments > refine the mapping
- Add additional data > re-analyze

## Next Step

Once mapping approved > proceed to `03_generate_mapper.md`
```

#### `prompts/03_generate_mapper.md`

```markdown
# Generate data_mapper.py

**Purpose**: Generate the single Python file that maps raw data to Neo4j.

## Context Available

- Neo4j version: {from step 00}
- Cypher version: {from step 00}
- Selected use case: {from step 01}
- Target data model: {from step 01}
- Data structure: {from step 02}
- Mapping plan: {from step 02}

## Version-Specific Cypher Syntax

### Neo4j 5.x (Cypher 23)
 Use: `SET n += {properties}`
 Use: `elementId()` for IDs
 Use: Modern type system
 Available: Vector operations (if needed)

### Neo4j 4.x (Cypher 5)
 Use: `ON CREATE SET ... ON MATCH SET ...`
 Use: `id()` for IDs
 Avoid: Vector operations (not supported)

## Code Generation Requirements

### Imports
```python
import csv
from pathlib import Path
from src.core.neo4j.connection import get_writer
from src.core.logger import log
```

### Structure
1. One function per entity type (e.g., `load_customers()`, `load_pii()`)
2. Each function:
   - Reads CSV data
   - Transforms to target schema
   - Calls `writer.write_nodes()` or `writer.write_relationships()`
   - Logs progress
3. A `main()` function that orchestrates all loads

### API Usage

**Writing nodes:**
```python
writer.write_nodes(
    label='Customer',
    data=customers,  # List of dicts
    primary_key='customerId',
    batch_size=1000
)
```

**Writing relationships:**
```python
writer.write_relationships(
    rel_type='HAS_EMAIL',
    start_node_label='Customer',
    end_node_label='Email',
    start_key='customerId',
    end_key='emailAddress',
    data=relationships,  # List of dicts with both keys
    batch_size=1000
)
```

### Logging
Use throughout:
```python
log.info(f"Loaded {len(data)} records from CSV")
log.info(f"Created {count} nodes")
```

### Error Handling
Include basic error handling for missing files:
```python
if not Path('raw_data/customers.csv').exists():
    log.error("Missing customers.csv in raw_data/")
    return
```

## Output File

Write to: `src/data_mapper.py`

Include a docstring at the top:
```python
"""
Data mapper for {Use Case Name}
Generated for Neo4j {version} (Cypher {cypher_version})

This file maps raw CSV data to the {Use Case} data model:
- Nodes: [list nodes]
- Relationships: [list relationships]
"""
```

## After Generation

Inform user:
1. "Generated src/data_mapper.py"
2. "Run it with: python src/data_mapper.py"
3. "This will load your data into Neo4j"
4. Suggest next steps (example queries, verification)

## Regeneration

If user wants to modify:
- They can edit data_mapper.py directly (it's readable)
- Or ask you to regenerate with different parameters
```

## User Workflow

From the user's perspective, here's the complete experience:

### Step 1: Initial Setup (One Time)

```bash
# Clone the repository
git clone https://github.com/neo4j/demo-toolkit.git
cd demo-toolkit

# Create .env file
cp .env.example .env
# Edit .env with Neo4j credentials
```

### Step 2: Add Data

```bash
# Drop CSVs into raw_data/
cp ~/my-data/customers.csv raw_data/
cp ~/my-data/transactions.csv raw_data/
```

### Step 3: Start Conversation with LLM

**User**: "Help me set up synthetic identity fraud detection"

**LLM**: *[Uses prompts/00_setup.md]*
- "Let me verify your Neo4j connection..."
- Runs `python src/core/setup/check_neo4j.py`
- "Connected to Neo4j 5.15 (Cypher 23)"

**LLM**: *[Uses prompts/01_discover_usecase.md]*
- Fetches use cases from neo4j.com
- "I found these fraud detection use cases..."
- User confirms: "Synthetic Identity"

**LLM**: *[Uses prompts/02_analyze_data.md]*
- Reads raw_data/ files
- "I see customers.csv with customer_id, email, phone..."
- "I'll map this to Customer, Email, Phone nodes..."
- User confirms mapping

**LLM**: *[Uses prompts/03_generate_mapper.md]*
- Generates `src/data_mapper.py` with Neo4j 5.x syntax
- "Generated src/data_mapper.py"
- "Run: python src/data_mapper.py"

### Step 4: Run Ingestion

```bash
python src/data_mapper.py
```

Output:
```
12:34:56 | INFO | Starting Synthetic Identity data ingestion...
12:34:57 | INFO | Loaded 10000 customers from CSV
12:34:58 | INFO | Created 10000 Customer nodes
12:34:59 | INFO | Loaded 8500 emails, 9200 phones, 7800 devices
12:35:01 | INFO | Created all PII nodes and relationships
12:35:01 | INFO | Ingestion complete!
12:35:01 | INFO | You can now query your graph to detect shared PII patterns
```

### Step 5: Query and Explore

The LLM can suggest queries:
```cypher
// Find customers sharing email addresses (synthetic identity pattern)
MATCH (c1:Customer)-[:HAS_EMAIL]->(e:Email)<-[:HAS_EMAIL]-(c2:Customer)
WHERE c1.customerId < c2.customerId
RETURN c1, e, c2
LIMIT 10
```

## Key Design Decisions

### 1. No Orchestrator Script
**Decision**: Let the LLM conversation be the orchestrator
**Rationale**: Simpler, more flexible, easier to understand

### 2. Single Generated File
**Decision**: LLM generates only `src/data_mapper.py`
**Rationale**: Easy to find, read, modify, regenerate

### 3. Markdown Prompts
**Decision**: Prompts are .md files, not Python code
**Rationale**: Readable, versionable, no code coupling

### 4. Self-Discovering Use Cases
**Decision**: Fetch use cases from website, don't hardcode
**Rationale**: No manual sync needed when website updates

### 5. Two-Layer Versioning
**Decision**: Version detection informs both LLM and runtime
**Rationale**: Correct Cypher syntax + correct driver usage

### 6. Pre-Built Infrastructure
**Decision**: Everything except data mapping is pre-built
**Rationale**: LLM focuses on simple logic, complex code is tested

### 7. Single .env Configuration
**Decision**: User only configures Neo4j connection
**Rationale**: Minimal friction, minimal decisions

## What Gets Built vs What Exists

### Pre-Built (In Repository)
- `src/core/neo4j/writer_v4.py`
- `src/core/neo4j/writer_v5.py`
- `src/core/neo4j/connection.py`
- `src/core/setup/check_neo4j.py`
- `src/core/logger.py`
- `prompts/00_setup.md`
- `prompts/01_discover_usecase.md`
- `prompts/02_analyze_data.md`
- `prompts/03_generate_mapper.md`
- `.env.example`

### User Provides
- `raw_data/*.csv` (their data)
- `.env` (their credentials)

### LLM Generates
- `src/data_mapper.py` (single file)

### User Runs
```bash
python src/data_mapper.py
```

## Benefits of This Architecture

1. **Minimal LLM-generated code** = Fewer errors, easier debugging
2. **Pre-built infrastructure** = Tested, optimized, reliable
3. **Version-aware generation** = Correct syntax for user's Neo4j
4. **Self-discovering use cases** = Always up-to-date with Neo4j website
5. **Single configuration file** = Minimal user effort
6. **Readable generated code** = Users can understand and modify
7. **No orchestrator complexity** = LLM conversation is the flow
8. **Regeneration-friendly** = Easy to iterate and refine

## Extension Points

### Adding New Neo4j Versions

Create `src/core/neo4j/writer_v6.py` with new patterns.
Update `connection.py` to detect and return new writer.
Update `prompts/03_generate_mapper.md` with v6 Cypher syntax.

### Adding New Use Cases

Nothing to do! Use cases are fetched from the Neo4j website.
When Neo4j adds new use cases, they automatically become available.

### Adding New Data Sources

Extend `data_mapper.py` generation to handle JSON, Parquet, databases.
Pre-build readers in `src/core/readers/`.

### Adding Validation

Pre-build validators in `src/core/validators/`.
Update prompt to call validation before ingestion.

## Success Metrics

This solution succeeds when:

1. **Time to value**: Minutes, not hours or days
2. **User effort**: Drop data, answer questions, run command
3. **Code quality**: Generated code is readable and correct
4. **Maintenance**: Minimal use cases self-discover, versions auto-detect
5. **Flexibility**: Users can modify generated code if needed
6. **Reliability**: Pre-built infrastructure is tested and stable

## Next Steps

To implement this solution:

1. Build pre-built infrastructure in `src/core/`
2. Write markdown prompts in `prompts/`
3. Create `.env.example` template
4. Test with multiple Neo4j versions (4.x and 5.x)
5. Test with multiple use cases from Neo4j website
6. Validate generated code quality
7. Document for users in README.md
