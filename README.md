# Neo4j PoV Toolkit

> **From raw data to working Neo4j graph in minutes, not days**

An LLM-powered toolkit that transforms your raw data into a fully functional Neo4j database with minimal effort. Just provide your data, select a use case, and let the system generate ingestion code automatically.

## Overview

The Neo4j PoV Toolkit eliminates the friction between having data and seeing Neo4j's value. Instead of spending days learning graph modeling, Cypher syntax, and Neo4j best practices, you can now:

1. **Drop your CSV/JSON files** into a folder
2. **Select a use case** from Neo4j's proven catalog
3. **Run one command** and have a working graph database

The toolkit leverages **LLMs to generate ingestion code** that maps your data to battle-tested [Neo4j data models](https://neo4j.com/developer/industry-use-cases/), automatically handling version detection, query optimization, and best practices.

### Why This Exists

When you arrive with a business problem and raw data, you should be able to say:

> *"Here's my problem. Here's my data. Show me what Neo4j can do."*

**And within minutes, you should have your answer.** That's why this toolkit exists.

Read more: [Why the Neo4j PoV Toolkit Exists](docs/WHY.md)

## Key Features

- **LLM-Powered Code Generation** - Automatically generates optimized Neo4j ingestion code tailored to your data
- **Proven Data Models** - Uses battle-tested data models from the [Neo4j Industry Use Cases](https://neo4j.com/developer/industry-use-cases/) library
- **Version-Aware** - Automatically detects your Neo4j version (4.x, 5.x, 6.x) and generates appropriate Cypher syntax
- **Minimal Configuration** - Just a single `.env` file with Neo4j connection details
- **Zero Graph Expertise Required** - No need to understand graph modeling or Cypher
- **Fast Time-to-Value** - From data to working queries in minutes, not days
- **Multiple Use Cases** - Supports fraud detection, supply chain, entity resolution, and more

## Quick Start

### 1. Prerequisites

- **Python 3.8+**
- **Neo4j Database** (local, Docker, or Aura)
  - Supports Neo4j 4.x, 5.x, and 6.x
- **Claude Code or Cursor** (for LLM orchestration)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/neo4j/pov-toolkit.git
cd pov-toolkit

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create your `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your Neo4j credentials:

```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
NEO4J_DATABASE=neo4j
```

### 4. Test Connection

```bash
python cli.py neo4j-test
```

Expected output:
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

### 5. Add Your Data

Drop your data files into the workspace:

```bash
cp ~/my-data/customers.csv workspace/raw_data/
cp ~/my-data/transactions.csv workspace/raw_data/
```

### 6. Start Conversation with LLM

Open the project in **Claude Code** or **Cursor** and say:

> *"Help me set up synthetic identity fraud detection with my data"*

The LLM will:
1. Detect your Neo4j version
2. Show available use cases
3. Analyze your data structure
4. Generate `workspace/generated/data_mapper.py`
5. Guide you to run the ingestion

### 7. Run Generated Code

```bash
python workspace/generated/data_mapper.py
```

Your data is now in Neo4j, ready to query!

---

## CLI Commands

The toolkit provides several utility commands:

### Test Neo4j Connection

```bash
python cli.py neo4j-test
```

Quick validation that your Neo4j database is accessible.

### Show Database Information

```bash
python cli.py neo4j-info
```

Displays comprehensive connection details:
- Neo4j version
- Cypher version
- Edition (Community/Enterprise)
- Database name
- Connection URI

### List Available Use Cases

```bash
python cli.py list-usecases
```

Shows the hierarchical structure of all Neo4j use cases:

```
📁 Financial Services
  📂 Retail Banking
    📄 Synthetic Identity Fraud
    📄 Account Takeover Fraud
    📄 Transaction Monitoring
    📄 Transaction Fraud Ring
  📂 Investment Banking
    📄 Mutual Fund Dependency Analytics
📁 Insurance
  📄 Claims Fraud
  📄 Quote Fraud
📁 Manufacturing
  ...
```

### Get Use Case Details

```bash
python cli.py get-usecase <url>
```

Fetches and converts a specific use case page to markdown format.

---

## Project Structure

```
neo4j-pov-toolkit/
├── cli.py                    # Main CLI entry point
├── .env                      # Your Neo4j credentials (create from .env.example)
├── requirements.txt          # Python dependencies
│
├── workspace/                # YOUR WORKSPACE - Everything you need
│   ├── raw_data/            # Drop your CSV/JSON files here
│   ├── generated/           # LLM-generated ingestion code goes here
│   └── README.md            # Workspace quick start guide
│
├── src/                      # Pre-built infrastructure (don't touch)
│   ├── core/
│   │   ├── neo4j/          # Neo4j connection, query runner, version detection
│   │   ├── usecases/       # Use case scraper
│   │   ├── logger.py       # Pre-configured logging
│   │   └── web_utils.py    # Web scraping utilities
│   │
│   └── cli/                 # CLI implementation
│       ├── main.py         # CLI entry point
│       ├── commands/       # Command implementations
│       └── utils/          # CLI utilities
│
└── docs/                    # Documentation
    ├── WHY.md              # Why this toolkit exists
    └── SOLUTION.md         # Technical architecture details
```

### The Workspace Folder

Everything you interact with lives in `workspace/`:

- **`workspace/raw_data/`** - Drop your CSV, JSON, or other data files here
- **`workspace/generated/`** - LLM-generated code appears here (e.g., `data_mapper.py`)
- **`workspace/README.md`** - Quick reference guide

You never need to enter the `src/` folder—that's the pre-built infrastructure.

## Troubleshooting

### Connection Issues

**Error**: `Unable to connect to Neo4j`

**Solution**:
1. Verify Neo4j is running: `neo4j status`
2. Check `.env` credentials are correct
3. Test connection: `python cli.py neo4j-test --verbose`

### Virtual Environment Issues

**Error**: `ModuleNotFoundError: No module named 'neo4j'`

**Solution**:
```bash
# Ensure venv is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

The CLI automatically detects and activates the virtual environment, but you can also activate it manually.

## Contributing

We welcome contributions! Here's how you can help:

1. **Report Issues** - Found a bug? [Open an issue](https://github.com/neo4j/pov-toolkit/issues)
2. **Suggest Features** - Have an idea? Let us know!
3. **Submit Pull Requests** - Code contributions are welcome
4. **Improve Documentation** - Help make the docs better
5. **Share Use Cases** - Tell us about your success stories

### Contribution Guidelines

- Follow the existing code style (Black, Flake8)
- Add tests for new features
- Update documentation
- Keep commits atomic and descriptive