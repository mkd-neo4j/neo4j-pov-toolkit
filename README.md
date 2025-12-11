# Neo4j PoV Toolkit

> **From business problem to working Neo4j graph in minutes, not days**

An LLM-powered toolkit that transforms your raw data into a fully functional Neo4j database through natural conversation. No graph expertise required.

---

## The Problem

You have a business problem to solve. Maybe it's detecting fraudulent transactions, preventing account takeovers, or identifying synthetic identities. You know Neo4j could help, but there's a frustrating gap between:

> *"I have data in a CSV/Database"*

and

> *"I have a working Neo4j solution"*

That gap is filled with questions:
- How do I model this data as a graph?
- What should be nodes? What should be relationships?
- How do I write the ingestion code?
- Am I following best practices?
- **How long will this take?**

Currently, it takes too long. Days or weeks of learning, modeling, coding, and iteration just to see if Neo4j delivers value for your use case.

**This toolkit eliminates that gap.**

---

## The Solution: Have a Conversation

Instead of learning graph theory, you have a conversation. Here's how it works:

### Real Example: Fraud Detection

**You**: *"What fraud use cases are available for insurance?"*

**System**:
> I found 2 insurance fraud use cases:
> 1. **Claims Fraud** - Detect fraudulent insurance claims
> 2. **Quote Fraud** - Identify manipulated quote applications

**You**: *"Tell me about Claims Fraud - how does it work?"*

**System**:
> Claims Fraud detects fraudulent patterns by analyzing connections between claimants, medical professionals, and claims. It identifies:
> - Multiple claims from same claimant
> - Medical professionals with suspicious patterns
> - "Crash for cash" scams (same vehicle, multiple incidents)
>
> **Minimum data needed**:
> - Claimant IDs
> - Claim IDs
> - One identifier type: phone, email, or passport

**You**: *"Can you write code to load my customer data for synthetic identity fraud?"*

**System**:
> ✅ Matched use case: Synthetic Identity Fraud
>
> I found your data at `workspace/raw_data/data.csv` with:
> - customer_id
> - email
> - phone
> - first_name, last_name
>
> This is perfect! I'll generate a data mapper that:
> - Creates Customer, Email, and Phone nodes
> - Establishes HAS_EMAIL and HAS_PHONE relationships
> - Detects fraud rings automatically
>
> *[Generates workspace/generated/data_mapper.py]*

**You**: *"Run it"*

**System**:
```
Loading customer data...
✓ Created 100 Customer nodes
✓ Created 65 Email nodes
✓ Created 58 Phone nodes
✓ Created relationships
⚠️ Fraud Detection: Found 12 shared emails and 15 shared phones
```

**Minutes later, you have a working Neo4j database ready for fraud detection queries.**

---

## How It Works

### 1. Start a Conversation

Open the project in **Claude Code** or **Cursor** and say:

> *"Help me with fraud detection"*

or

> *"What use cases are available for financial services?"*

or

> *"Load my customer data into Neo4j"*

### 2. Explore Use Cases

The LLM guides you through available patterns:

- **Financial Services**: Synthetic Identity Fraud, Account Takeover, Transaction Monitoring, Fraud Rings
- **Insurance**: Claims Fraud, Quote Fraud
- **Manufacturing**: Supply Chain, BOM Management, Engineering Traceability
- **Cross-Industry**: Entity Resolution, IT Service Graphs

Each use case comes with:
- ✅ Battle-tested data model from Neo4j experts
- ✅ Minimum data requirements
- ✅ Example queries and detection patterns
- ✅ Graph Data Science algorithms

### 3. Provide Your Data

Just drop your files in `workspace/raw_data/`:

```bash
cp ~/my-data/customers.csv workspace/raw_data/
cp ~/my-data/transactions.json workspace/raw_data/
```

**Supported formats**: CSV, JSON, Parquet, or any format Python can read

**Minimum data**: Most use cases need surprisingly little:
- Synthetic Identity Fraud: Just `customer_id` + one PII field (email OR phone)
- Claims Fraud: Claimant + claim + one connection point
- Transaction Monitoring: Account + transaction + amounts

### 4. Get Working Code

The LLM:
1. Detects your Neo4j version (4.x, 5.x, 6.x)
2. Analyzes your data structure
3. Maps it to the proven data model
4. Generates `workspace/generated/data_mapper.py`
5. Creates batched, optimized ingestion code

### 5. Run and Explore

```bash
python workspace/generated/data_mapper.py
```

Your data is now in Neo4j, modeled correctly, ready to:
- Run fraud detection queries
- Apply Graph Data Science algorithms
- Visualize patterns in Neo4j Browser
- Build dashboards and applications

---

## What Makes This Different

### You Don't Need to Know:

❌ Graph modeling theory
❌ Cypher query language
❌ Neo4j best practices
❌ Data ingestion patterns
❌ Version-specific syntax differences

### You Just Need:

✅ A business problem
✅ Some data (CSV, JSON, etc.)
✅ 10 minutes

---

## The Value Proposition

### For Users

**Stop thinking. Start seeing value.**

You shouldn't need to become a graph expert to see if Neo4j solves your problem. This toolkit removes every barrier between your data and demonstrable value.

### For Neo4j Teams

**Democratize graph expertise.**

This toolkit captures the collective knowledge of Neo4j's engineering teams, solutions architects, consultants, and field engineers. Accelerate customer demos and POCs from days to minutes.

---

## Available Use Cases

The toolkit uses data models from the [Neo4j Industry Use Cases](https://neo4j.com/developer/industry-use-cases/) library:

### Fraud Detection (Financial Services)
- **Synthetic Identity Fraud** - Find shared PII across supposedly distinct customers
- **Account Takeover** - Identify compromised accounts through behavioral analysis
- **Transaction Monitoring** - Detect suspicious patterns in financial transactions
- **Transaction Fraud Ring** - Uncover networks of coordinated fraudulent activity
- **Entity Resolution** - Link customer records across systems
- **Deposit Analysis** - Analyze deposit patterns for suspicious behavior

### Insurance
- **Claims Fraud** - Detect fraudulent insurance claims and "crash for cash" scams
- **Quote Fraud** - Identify manipulated quote applications

### Manufacturing
- **Supply Chain Management** - E.V. route planning and logistics
- **Product Design** - Configurable BOMs, engineering traceability
- **Production Optimization** - Process monitoring and CPA

### Cross-Industry
- **Entity Resolution** - Connect fragmented data across systems
- **IT Service Graphs** - Infrastructure and service dependency mapping

*As Neo4j adds more use cases to the Industry Use Cases library, this toolkit automatically supports them.*

---

## Quick Start

### Prerequisites

- **Neo4j Database** (Desktop, Docker, or Aura)
- **Python 3.8+**
- **Claude Code or Cursor** (for LLM orchestration)

### Installation

```bash
# 1. Clone and setup
git clone https://github.com/neo4j/pov-toolkit.git
cd pov-toolkit
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure connection
cp .env.example .env
# Edit .env with your Neo4j credentials

# 3. Test connection
python cli.py neo4j-test
```

**Detailed setup**: See [docs/SETUP.md](docs/SETUP.md)

### Start Your First Conversation

Open the project in **Claude Code** or **Cursor** and say:

> *"What fraud detection use cases are available?"*

The LLM will guide you from there.

---

## Documentation

- **[Why This Exists](docs/WHY.md)** - The problem we're solving and our philosophy
- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[CLI Reference](docs/CLI.md)** - All available commands and options
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Technical Architecture](docs/SOLUTION.md)** - How it works under the hood

---

## Philosophy

This is not about building production-grade, enterprise-hardened systems. This is about:

- **Speed**: Minutes to value, not days
- **Simplicity**: Minimal data, minimal steps
- **Accessibility**: No graph expertise required
- **Demonstration**: Prove Neo4j's value quickly
- **Acceleration**: Remove friction from exploration and POCs

---

## Contributing

We welcome contributions! Here's how you can help:

1. **Report Issues** - Found a bug? [Open an issue](https://github.com/neo4j/pov-toolkit/issues)
2. **Suggest Features** - Have an idea? Let us know!
3. **Submit Pull Requests** - Code contributions welcome
4. **Improve Documentation** - Help make the docs better
5. **Share Use Cases** - Tell us your success stories

---

## Project Structure

```
neo4j-pov-toolkit/
├── workspace/           # YOUR WORKSPACE
│   ├── raw_data/       # Drop your data files here
│   └── generated/      # LLM-generated code appears here
│
├── src/                # Pre-built infrastructure
│   ├── core/          # Neo4j connection, logging, use case scraper
│   ├── cli/           # CLI commands
│   └── prompts/       # LLM guidance for code generation
│
├── docs/               # Documentation
│   ├── WHY.md         # Why this exists
│   ├── SETUP.md       # Installation guide
│   ├── CLI.md         # CLI reference
│   └── TROUBLESHOOTING.md
│
├── cli.py             # Main CLI entry point
└── .env               # Your Neo4j credentials (create from .env.example)
```

**You only need to interact with `workspace/`** - everything else is pre-built infrastructure.

---

## License

[License information here]

---

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/neo4j/pov-toolkit/issues)
- **Community**: [community.neo4j.com](https://community.neo4j.com)
- **Neo4j**: [neo4j.com](https://neo4j.com)

---

## The Goal

When you arrive with a business problem and raw data, you should be able to say:

> *"Here's my problem. Here's my data. Show me what Neo4j can do."*

**And within minutes, you should have your answer.**

That's why this toolkit exists.
