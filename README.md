# 🏢 Companies House → Neo4j

> **⚠️ BRANCH: `companies-house`**
>
> This is a **specific implementation branch** that loads UK Companies House data into Neo4j.
>
> Looking for the base toolkit? Switch to the [`main` branch](../../tree/main).

---

## What This Branch Does

This branch contains a complete, working pipeline to:

1. **Download** the UK Companies House Free Data Product (~2.6GB, 5.7M companies)
2. **Load** it into Neo4j as a fully connected graph
3. **Query** company relationships, addresses, industries, and name history

**Time to working graph: ~60-90 minutes** (mostly automated loading)

---

## Quick Start

### Prerequisites

- Neo4j 5.x+ running (Desktop, Docker, or Aura)
- Python 3.8+
- `.env` file with Neo4j credentials

### 1. Setup

```bash
# Clone and checkout this branch
git clone https://github.com/mkd-neo4j/neo4j-pov-toolkit.git
cd neo4j-pov-toolkit
git checkout companies-house

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure Neo4j connection
cp .env.example .env
# Edit .env with your credentials
```

### 2. Download the Data

```bash
python3 workspace/scripts/download_companies_house.py
```

Downloads ~470MB ZIP → extracts to ~2.6GB CSV.

### 3. Load into Neo4j

```bash
python3 workspace/generated/data_mapper.py
```

Creates 5.7M Company nodes, addresses, SIC codes, and name history.

### 4. Query!

```cypher
// Find companies at the same address
MATCH (a:Address)<-[:HAS_ADDRESS]-(c:Company)
WHERE a.postCode = 'EC2M 4YF'
RETURN a.postCode, collect(c.name) as companies
```

---

## The Graph Model

```
(:Company)─[:HAS_ADDRESS]──→(:Address)─[:LOCATED_IN]──→(:Country)
    │
    ├──[:CLASSIFIED_AS]──→(:SICCode)
    │
    └──[:PREVIOUSLY_NAMED]──→(:PreviousName)
```

| Node | Count | Description |
|------|-------|-------------|
| Company | ~5.7M | Every UK registered company |
| Address | ~4.5M | Registered office addresses |
| SICCode | ~800 | Industry classification codes |
| Country | ~100 | Countries of origin/address |
| PreviousName | ~2M | Historical company names |

---

## Detailed Documentation

📖 **[Full Documentation →](workspace/README.md)**

The workspace README covers:
- Download script options (`--list`, `--date`, `--keep-zip`)
- Data mapper phases (run specific phases, resume from failures)
- Troubleshooting common issues
- Example Cypher queries

---

## What's Different from `main` Branch

| Aspect | `main` branch | `companies-house` branch |
|--------|--------------|-------------------------|
| **Purpose** | Empty toolkit framework | Working Companies House implementation |
| **workspace/raw_data/** | Empty (placeholder) | Companies House CSV (after download) |
| **workspace/generated/** | Empty (placeholder) | `data_mapper.py` for Companies House |
| **workspace/scripts/** | Empty | `download_companies_house.py` |
| **Use Case** | Starting point for new projects | Reference implementation / UK company data |

---

## Data Source

- **Provider**: [Companies House](https://download.companieshouse.gov.uk/en_output.html)
- **License**: Open Government Licence (OGL) v3.0
- **Updates**: Monthly (within 5 working days of month end)
- **Contains**: All UK registered companies with addresses, SIC codes, status, and name history

---

## About the Toolkit

The underlying toolkit (`main` branch) is an LLM-powered framework that helps you:

1. Discover Neo4j use cases via CLI
2. Analyze your data for graph modeling
3. Generate data loading code automatically

This `companies-house` branch is a **complete example** of what the toolkit produces—you can use it as a reference or directly load UK company data into Neo4j.

---

## License

- **Toolkit**: [Your license here]
- **Data**: Contains public sector information licensed under the Open Government Licence v3.0
