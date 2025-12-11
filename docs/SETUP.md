# Setup Guide

Complete installation and configuration guide for the Neo4j PoV Toolkit.

---

## Prerequisites

Before you begin, ensure you have:

### 1. Python 3.8 or Higher

Check your Python version:

```bash
python --version
# or
python3 --version
```

If you need to install Python:
- **macOS**: `brew install python3`
- **Ubuntu/Debian**: `sudo apt-get install python3 python3-pip python3-venv`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

### 2. Neo4j Database

You need access to a Neo4j database. Choose one option:

#### Option A: Neo4j Desktop (Recommended for Local Development)
1. Download [Neo4j Desktop](https://neo4j.com/download/)
2. Create a new database
3. Start the database
4. Note the connection details (bolt://localhost:7687 by default)

#### Option B: Neo4j Aura (Cloud)
1. Create free account at [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura/)
2. Create a database instance
3. Download connection credentials
4. Note the connection URI and password

#### Option C: Docker
```bash
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your-password \
    neo4j:latest
```

**Supported Versions**: Neo4j 4.x, 5.x, and 6.x

### 3. LLM Tool (Claude Code or Cursor)

The toolkit is designed to work with AI coding assistants:
- **[Claude Code](https://claude.com/claude-code)** - Recommended
- **[Cursor](https://cursor.sh/)** - Alternative

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/neo4j/pov-toolkit.git
cd pov-toolkit
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
```

**Note**: The CLI automatically detects and activates the venv, but it's good practice to activate manually.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `neo4j` - Neo4j Python driver
- `python-dotenv` - Environment variable management
- `beautifulsoup4` - Web scraping for use cases
- `requests` - HTTP client
- `html2text` - HTML to markdown conversion

---

## Configuration

### Step 1: Create .env File

Copy the example configuration:

```bash
cp .env.example .env
```

### Step 2: Edit .env with Your Neo4j Credentials

Open `.env` in your text editor:

```bash
# macOS
open .env

# Linux
nano .env

# Windows
notepad .env
```

### Step 3: Configure Connection Details

Update with your Neo4j connection information:

```env
# Neo4j Connection Details
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
NEO4J_DATABASE=neo4j
```

**Configuration Options**:

- **NEO4J_URI**: Connection URI
  - Local: `neo4j://localhost:7687` or `bolt://localhost:7687`
  - Aura: `neo4j+s://xxxxx.databases.neo4j.io` (from Aura credentials)
  - Docker: `neo4j://localhost:7687` (default)

- **NEO4J_USER**: Database username
  - Default: `neo4j`
  - Aura: Usually `neo4j`

- **NEO4J_PASSWORD**: Database password
  - Set during Neo4j installation
  - Aura: Provided when creating database

- **NEO4J_DATABASE**: Target database name
  - Default: `neo4j`
  - Can be omitted (defaults to `neo4j`)

### Step 4: Secure Your .env File

The `.env` file contains credentials and should **never be committed** to version control:

```bash
# Verify .env is in .gitignore
cat .gitignore | grep .env
```

You should see `.env` listed in `.gitignore`.

---

## Verify Installation

### Test 1: Python and Dependencies

```bash
python --version
pip list | grep neo4j
```

Should show Python 3.8+ and the neo4j package.

### Test 2: Neo4j Connection

```bash
python cli.py neo4j-test
```

**Expected output**:
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

**If connection fails**, see [Troubleshooting](#troubleshooting) below.

### Test 3: Database Information

```bash
python cli.py neo4j-info
```

This shows:
- Neo4j version
- Cypher version
- Edition (Community/Enterprise)
- Connection details

### Test 4: CLI Help

```bash
python cli.py --help
```

Should display available commands:
- `neo4j-test` - Test connection
- `neo4j-info` - Show database info
- `list-usecases` - List Neo4j use cases
- `get-usecase` - Fetch use case details

---

## Workspace Setup

### Add Your Data

The toolkit expects data files in `workspace/raw_data/`:

```bash
# Copy your data files
cp ~/my-data/customers.csv workspace/raw_data/
cp ~/my-data/transactions.json workspace/raw_data/
```

**Supported formats**:
- CSV (comma-separated values)
- JSON (JavaScript Object Notation)
- Parquet (columnar storage)
- Any format Python can read

### Workspace Structure

```
workspace/
├── raw_data/         # Your data files go here
│   ├── customers.csv
│   └── transactions.json
│
└── generated/        # LLM-generated code appears here
    └── data_mapper.py
```

---

## Open in Your LLM Tool

### Using Claude Code

1. Open Claude Code
2. Select "Open Project"
3. Navigate to the `pov-toolkit` directory
4. Click "Open"

### Using Cursor

1. Open Cursor
2. File → Open Folder
3. Select the `pov-toolkit` directory
4. Click "Open"

---

## Start Your First Conversation

Once set up, start a conversation with your LLM tool:

> *"What fraud detection use cases are available?"*

or

> *"Help me load customer data for synthetic identity fraud detection"*

The LLM will guide you through:
1. Selecting a use case
2. Understanding minimum data requirements
3. Analyzing your data
4. Generating ingestion code
5. Running the data load

---

## Troubleshooting

### Connection Issues

**Error**: `Unable to connect to Neo4j`

**Solutions**:

1. **Verify Neo4j is running**:
   ```bash
   # Neo4j Desktop: Check status in Desktop app
   # Docker: docker ps | grep neo4j
   # System service: neo4j status
   ```

2. **Check credentials**:
   - Verify `NEO4J_URI` is correct
   - Confirm `NEO4J_PASSWORD` matches your database
   - Test with Neo4j Browser first (http://localhost:7474)

3. **Check network**:
   ```bash
   # Test if port is open
   nc -zv localhost 7687
   # or
   telnet localhost 7687
   ```

4. **Verify Aura connection**:
   - Ensure URI includes `neo4j+s://` (not `neo4j://`)
   - Check firewall/network allows outbound connections
   - Verify credentials from Aura console

### Virtual Environment Issues

**Error**: `ModuleNotFoundError: No module named 'neo4j'`

**Solutions**:

1. **Activate venv**:
   ```bash
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

2. **Reinstall dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   pip list | grep neo4j
   ```

**Note**: The CLI has auto-venv detection, but manual activation is recommended.

### Permission Issues

**Error**: `Permission denied` when running CLI

**Solution**:
```bash
# Make CLI executable
chmod +x cli.py

# Or run with python explicitly
python cli.py neo4j-test
```

### Python Version Issues

**Error**: `SyntaxError` or version-related errors

**Solution**:
```bash
# Check Python version
python --version

# Must be 3.8 or higher
# Use python3 if needed
python3 cli.py neo4j-test
```

---

## Advanced Configuration

### Custom Database Name

If using a non-default database:

```env
NEO4J_DATABASE=mydb
```

### Neo4j Enterprise Features

The toolkit automatically detects Enterprise vs Community edition. No special configuration needed.

### Multiple Environments

Create environment-specific .env files:

```bash
.env.dev
.env.staging
.env.prod
```

Load specific environment:

```bash
cp .env.dev .env
python cli.py neo4j-test
```

---

## Next Steps

Once setup is complete:

1. **Explore use cases**: `python cli.py list-usecases`
2. **Add your data**: Copy files to `workspace/raw_data/`
3. **Start conversation**: Open in Claude Code/Cursor
4. **Generate code**: Ask the LLM to help load your data
5. **Run ingestion**: `python workspace/generated/data_mapper.py`

See [README.md](../README.md) for the full workflow.

---

## Getting Help

- **Documentation**: [docs/](.)
- **Issues**: [GitHub Issues](https://github.com/neo4j/pov-toolkit/issues)
- **Neo4j Community**: [community.neo4j.com](https://community.neo4j.com)
