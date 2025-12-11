# CLI Reference

Complete command-line interface reference for the Neo4j PoV Toolkit.

---

## Overview

The toolkit provides a CLI for:
- Testing Neo4j connections
- Exploring available use cases
- Fetching use case details
- Inspecting database information

All commands follow the pattern:

```bash
python cli.py <command> [options]
```

---

## Global Options

### Help

Show help for any command:

```bash
python cli.py --help
python cli.py <command> --help
```

### Version

Display toolkit version:

```bash
python cli.py --version
```

---

## Commands

### neo4j-test

**Purpose**: Test Neo4j database connection

**Usage**:
```bash
python cli.py neo4j-test [options]
```

**Options**:
- `--json` - Output results in JSON format
- `--verbose` - Show detailed connection information

**Examples**:

Basic connection test:
```bash
python cli.py neo4j-test
```

Output:
```
╔═══════════════════════════════════════════════════════════════╗
║                     Neo4j Connection Test                     ║
╚═══════════════════════════════════════════════════════════════╝

Testing connection to Neo4j...

✓ Connection successful!

URI                 : neo4j://localhost:7687
Database            : neo4j
User                : neo4j

Connected to: Neo4j 2025.06.2 (Enterprise)
```

Verbose output with version details:
```bash
python cli.py neo4j-test --verbose
```

JSON output for scripting:
```bash
python cli.py neo4j-test --json
```

Output:
```json
{
  "connected": true,
  "uri": "neo4j://localhost:7687",
  "database": "neo4j",
  "user": "neo4j",
  "neo4j_version": "2025.06.2",
  "edition": "enterprise"
}
```

**Exit Codes**:
- `0` - Connection successful
- `1` - Connection failed

**Use Cases**:
- Verify setup before starting work
- Test credentials after configuration changes
- Health checks in scripts/CI

---

### neo4j-info

**Purpose**: Display comprehensive Neo4j database information

**Usage**:
```bash
python cli.py neo4j-info [options]
```

**Options**:
- `--json` - Output results in JSON format

**Examples**:

Show detailed database information:
```bash
python cli.py neo4j-info
```

Output:
```
╔═══════════════════════════════════════════════════════════════╗
║                 Neo4j Connection Information                  ║
╚═══════════════════════════════════════════════════════════════╝

✓ Connected

Neo4j Version       : 2025.06.2
Cypher Versions     : 5, 25
Edition             : Enterprise
URI                 : neo4j://localhost:7687
Database            : neo4j

Ready to generate ingestion code!
```

JSON output:
```bash
python cli.py neo4j-info --json
```

Output:
```json
{
  "connected": true,
  "neo4j_version": "2025.06.2",
  "cypher_version": ["5", "25"],
  "enterprise": true,
  "uri": "neo4j://localhost:7687",
  "database": "neo4j"
}
```

**Information Provided**:
- **Neo4j Version**: Full version string (e.g., 2025.06.2, 5.15.0, 4.4.9)
- **Cypher Versions**: Supported Cypher query language versions
- **Edition**: Enterprise or Community
- **URI**: Connection endpoint
- **Database**: Target database name

**Use Cases**:
- Check version before generating code (4.x vs 5.x syntax)
- Verify Enterprise features are available
- Confirm correct database target
- LLM uses this to generate version-appropriate Cypher

---

### list-usecases

**Purpose**: List all available Neo4j use cases

**Usage**:
```bash
python cli.py list-usecases [options]
```

**Options**:
- `--json` - Output results in JSON format
- `--urls-only` - Output only URLs (for LLM/scripting)
- `--verbose` - Show URLs in tree view

**Examples**:

Basic hierarchical view:
```bash
python cli.py list-usecases
```

Output:
```
╔═══════════════════════════════════════════════════════════════╗
║                        Neo4j Use Cases                        ║
╚═══════════════════════════════════════════════════════════════╝

Fetching use cases from neo4j.com...

📁 Financial Services
  📂 Retail Banking
    📄 Synthetic Identity Fraud
    📄 Account Takeover Fraud
    📄 Transaction Monitoring
    📄 Transaction Fraud Ring
    📄 Entity Resolution
    📄 Deposit Analysis
    📄 Automated Facial Recognition
  📂 Investment Banking
    📄 Mutual Fund Dependency Analytics
    📄 Regulatory Dependency Mapping

📁 Insurance
  📄 Claims Fraud
  📄 Quote Fraud

📁 Manufacturing
  📂 Supply Chain and Logistics Management
    📄 E.V. Route Planning
  📂 Product Design and Engineering
    📄 Configurable B.O.M.
    📄 Engineering Traceability
  📂 Production Planning and Optimization
    📄 Process Monitoring and CPA

📁 Industry Agnostic
  📄 Entity Resolution
  📄 IT Service Graph
```

JSON output (full hierarchy):
```bash
python cli.py list-usecases --json
```

URLs only (for LLM processing):
```bash
python cli.py list-usecases --urls-only
```

Output:
```
https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/synthetic-identity-fraud/
https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/account-takeover-fraud/
https://neo4j.com/developer/industry-use-cases/insurance/claims-fraud/
...
```

Verbose with URLs:
```bash
python cli.py list-usecases --verbose
```

**Use Cases**:
- Explore available patterns before starting
- Let LLM discover relevant use cases
- Find URLs for `get-usecase` command
- Understand industry coverage

---

### get-usecase

**Purpose**: Fetch and convert a specific Neo4j use case page to markdown

**Usage**:
```bash
python cli.py get-usecase <URL> [options]
```

**Arguments**:
- `URL` (required) - Full Neo4j use case page URL

**Options**:
- `--output FILE` or `-o FILE` - Save to file instead of stdout

**Examples**:

Fetch use case to terminal:
```bash
python cli.py get-usecase https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/synthetic-identity-fraud/
```

Output:
```markdown
# Synthetic Identity Fraud

## 1. Introduction

Synthetic identity theft is a type of fraud where a person combines real
and fake identity information...

## 2. Scenario

[Full use case content in markdown format]

## 3. Solution

## 4. Modelling

### 4.1. Data Model

Customer Node:
- customerId: Unique identifier

Email Node:
- address: Email address

[... complete use case details ...]
```

Save to file:
```bash
python cli.py get-usecase https://neo4j.com/developer/industry-use-cases/insurance/claims-fraud/ -o claims_fraud.md
```

**Content Retrieved**:
- Use case introduction and background
- Business scenario and problem statement
- Graph solution approach
- **Data model** (nodes, properties, relationships)
- **Minimum required fields**
- Demo data and Cypher examples
- Graph Data Science algorithms
- Query patterns

**Use Cases**:
- LLM reads this to understand data model requirements
- Save use case for reference
- Extract data model before code generation
- Understand minimum data requirements

**Finding URLs**:

Get URLs from `list-usecases`:
```bash
# List all URLs
python cli.py list-usecases --urls-only

# Find specific use case
python cli.py list-usecases --urls-only | grep fraud
```

---

## Output Formats

### JSON Output

Most commands support `--json` for programmatic use:

```bash
python cli.py neo4j-test --json | jq '.connected'
python cli.py neo4j-info --json | jq '.neo4j_version'
python cli.py list-usecases --json | jq '.children[].name'
```

### Plain Text Output

Default output is formatted for human readability:
- Box-drawing characters for visual structure
- Color-coded output (when terminal supports it)
- Clear status indicators (✓ ✗)

---

## Common Workflows

### Initial Setup Verification

```bash
# 1. Test connection
python cli.py neo4j-test

# 2. Get database info
python cli.py neo4j-info

# 3. Explore available use cases
python cli.py list-usecases
```

### Use Case Exploration

```bash
# 1. List all use cases
python cli.py list-usecases

# 2. Get URLs for fraud-related use cases
python cli.py list-usecases --urls-only | grep fraud

# 3. Fetch specific use case details
python cli.py get-usecase <URL>

# 4. Save for reference
python cli.py get-usecase <URL> -o usecase.md
```

### LLM Integration

The CLI is designed for LLM tools to use:

```bash
# LLM runs this to understand database version
python cli.py neo4j-info --json

# LLM runs this to find relevant use cases
python cli.py list-usecases --json

# LLM runs this to get data model requirements
python cli.py get-usecase <URL>
```

### Scripting and Automation

```bash
# Check if connected before proceeding
if python cli.py neo4j-test --json | jq -e '.connected'; then
  echo "Connected!"
  # Continue with workflow
else
  echo "Connection failed"
  exit 1
fi

# Get Neo4j version for conditional logic
VERSION=$(python cli.py neo4j-info --json | jq -r '.neo4j_version')
echo "Running on Neo4j $VERSION"

# Extract all use case URLs
python cli.py list-usecases --urls-only > usecases.txt
```

---

## Environment Variables

The CLI respects these environment variables from `.env`:

```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

See [SETUP.md](SETUP.md) for configuration details.

---

## Virtual Environment

The CLI automatically detects and activates virtual environments:

```bash
# CLI checks for these directories:
venv/
env/
.venv/

# If found and valid, automatically adds to Python path
# Manual activation still recommended but not required
```

---

## Exit Codes

Standard exit codes for scripting:

- `0` - Success
- `1` - General error
- `2` - Connection error
- `3` - Invalid arguments

Example:
```bash
python cli.py neo4j-test
if [ $? -eq 0 ]; then
  echo "Connection successful"
fi
```

---

## Troubleshooting

### Command Not Found

**Error**: `python: command not found`

**Solution**: Use `python3` instead:
```bash
python3 cli.py neo4j-test
```

### Permission Denied

**Error**: `Permission denied: ./cli.py`

**Solution**: Make executable or use python:
```bash
chmod +x cli.py
# OR
python cli.py neo4j-test
```

### Module Not Found

**Error**: `ModuleNotFoundError: No module named 'neo4j'`

**Solution**: Activate venv and install dependencies:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Connection Errors

See [SETUP.md](SETUP.md#troubleshooting) for Neo4j connection issues.

---

## Examples by Use Case

### Fraud Detection Investigation

```bash
# 1. See what fraud use cases exist
python cli.py list-usecases | grep -i fraud

# 2. Get synthetic identity fraud details
python cli.py get-usecase https://neo4j.com/developer/industry-use-cases/finserv/retail-banking/synthetic-identity-fraud/

# 3. Save for reference
python cli.py get-usecase <URL> -o synthetic_fraud.md
```

### Pre-Code Generation Check

```bash
# Before LLM generates code, verify:

# 1. Connection works
python cli.py neo4j-test

# 2. Get version for Cypher syntax
python cli.py neo4j-info --json | jq -r '.neo4j_version'

# 3. Data files exist
ls workspace/raw_data/

# 4. Use case data model known
python cli.py get-usecase <URL> | grep "Data Model" -A 20
```

---

## Advanced Usage

### Piping and Filtering

```bash
# Find all insurance use cases
python cli.py list-usecases --json | jq '.children[] | select(.name=="Insurance")'

# Count total use cases
python cli.py list-usecases --urls-only | wc -l

# Extract data model from use case
python cli.py get-usecase <URL> | sed -n '/Data Model/,/Demo Data/p'
```

### Integration with Other Tools

```bash
# Check Neo4j version and install specific client
VERSION=$(python cli.py neo4j-info --json | jq -r '.neo4j_version | split(".")[0]')
pip install neo4j-driver==$VERSION.*

# Generate list of all fraud URLs
python cli.py list-usecases --urls-only | grep fraud > fraud_usecases.txt
```

---

## Getting Help

For command-specific help:

```bash
python cli.py <command> --help
```

For general help:

```bash
python cli.py --help
```

For issues:
- [GitHub Issues](https://github.com/neo4j/pov-toolkit/issues)
- [Documentation](.)
