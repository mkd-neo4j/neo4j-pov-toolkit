# Neo4j PoV Toolkit - Technical Solution

## Overview

The Neo4j PoV Toolkit is an LLM-powered code generation system that transforms raw data into a working Neo4j database with minimal user effort. The user provides their data, selects a use case, and the system generates a single, readable ingestion file that maps their data to proven Neo4j data models.

**Core Principle**: The LLM generates only the essential translation logic. Everything else database writing, logging, connection management, version handling is pre-built, tested, and optimized.

## Architecture Philosophy

### What the LLM Generates
- **One file**: `workspace/generated/data_mapper.py`
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
neo4j-pov-toolkit/
├── workspace/                          # USER WORKSPACE - Everything you need is here
│   ├── raw_data/                      # Drop your data files here
│   │   ├── customers.csv
│   │   ├── accounts.csv
│   │   └── transactions.csv
│   │
│   ├── generated/                     # LLM-generated code goes here
│   │   └── data_mapper.py            # ONLY LLM-generated file
│   │                                  # Easy to find, easy to read
│   │
│   └── README.md                      # Quick start guide for users
│
├── src/                                # PRE-BUILT INFRASTRUCTURE (Don't touch)
│   ├── core/                          # Core functionality
│   │   ├── setup/
│   │   │   └── check_neo4j.py        # Validate connection + detect version
│   │   │
│   │   ├── neo4j/
│   │   │   ├── connection.py         # Connection management
│   │   │   ├── writer_v4.py          # Neo4j 4.x specific implementation
│   │   │   ├── writer_v5.py          # Neo4j 5.x specific implementation
│   │   │   └── validator.py          # Data validation utilities
│   │   │
│   │   ├── logger.py                 # Pre-configured logging
│   │   └── utils.py                  # Helper functions
│   │
│   └── cli/                           # CLI implementation
│       ├── main.py                    # CLI entry point
│       ├── commands/                  # Command implementations
│       └── utils/                     # CLI utilities
│
├── prompts/                            # Markdown prompts for LLM orchestration
│   ├── README.md                      # How the prompt system works
│   ├── 00_setup.md                    # Step 0: Connection & version detection
│   ├── 01_discover_usecase.md         # Step 1: Fetch use cases from website
│   ├── 02_analyze_data.md             # Step 2: Understand CSV structure
│   └── 03_load_data.md                # Step 3: Generate data_mapper.py
│
├── docs/
│   ├── WHY.md                         # Why this toolkit exists
│   └── SOLUTION.md                    # This document
│
├── cli.py                              # CLI entry point (run this)
├── .env                                # Your Neo4j credentials
├── .env.example                        # Template for configuration
└── requirements.txt                    # Python dependencies
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
**When**: Before generating `workspace/generated/data_mapper.py`
**Purpose**: Generate version-appropriate Cypher queries

With this information, the LLM knows:
- "I'm generating code for Neo4j 5.15"
- "I can use Cypher 23 features"
- "I should use `elementId()` not `id()`"
- "I can use `SET n += {props}` syntax"

#### Layer 2: Runtime Selection (Code Execution)
**When**: When `workspace/generated/data_mapper.py` runs
**Purpose**: Use the correct database driver and patterns

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

## The LLM-Generated File: `workspace/generated/data_mapper.py`

This is the **only** file the LLM creates. It's deliberately simple and readable. It lives in the `workspace/generated/` folder so users know exactly where to find it.

### Key Characteristics

1. **Readable**: Anyone can understand what it does
2. **Simple**: Just Data reading and field mapping
3. **Focused**: Only translation logic, no infrastructure code
4. **Logged**: Pre-built logging shows progress
5. **Versioned**: Generated for specific Neo4j version

The user can:
- Read it to understand the mapping
- Modify it if they want to adjust field names
- Regenerate it if they change their data structure

## Prompt-Driven Workflow

The prompts are **markdown files** that guide the LLM through a structured conversation. They don't contain hardcoded use cases instead, they instruct the LLM to fetch information dynamically from the Neo4j website.

### Why Markdown Prompts?

1. **Human-readable**: Easy to understand and modify
2. **Version-controllable**: Track changes over time
3. **Self-documenting**: The prompt explains what it does
4. **Dynamic**: Fetch use cases from website, don't hardcode them

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

## Benefits of This Architecture

1. **Minimal LLM-generated code** = Fewer errors, easier debugging
2. **Pre-built infrastructure** = Tested, optimized, reliable
3. **Version-aware generation** = Correct syntax for user's Neo4j
4. **Self-discovering use cases** = Always up-to-date with Neo4j website
5. **Single configuration file** = Minimal user effort
6. **Readable generated code** = Users can understand and modify
7. **No orchestrator complexity** = LLM conversation is the flow
8. **Regeneration-friendly** = Easy to iterate and refine
