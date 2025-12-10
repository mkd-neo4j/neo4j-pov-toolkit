# Workspace - Your Area

This is your workspace. Everything you need to interact with the Neo4j Demo Toolkit is here.

## Folders

### `raw_data/`
**Drop your data files here**
- CSV files
- JSON files
- Any data you want to load into Neo4j

Example:
```bash
cp ~/my-data/customers.csv workspace/raw_data/
cp ~/my-data/transactions.csv workspace/raw_data/
```

### `generated/`
**Review generated code here**
- The LLM generates ingestion code and places it here
- You can read, modify, or regenerate these files
- Main file: `data_mapper.py` - maps your data to Neo4j

## Quick Start

1. **Add your data**
   ```bash
   cp your-data.csv workspace/raw_data/
   ```

2. **Run a command**
   ```bash
   python cli.py neo4j-test    # Test connection
   python cli.py neo4j-info    # Show Neo4j details
   ```

3. **Start conversation with Claude Code or Cursor**
   - Ask to set up your use case
   - The LLM will analyze your data and generate code in `workspace/generated/`

4. **Run the generated code**
   ```bash
   python workspace/generated/data_mapper.py
   ```

## What NOT to do

**Don't go into the `src/` folder** - that's the toolkit's infrastructure. You don't need to look there or change anything there. Everything you need is in this workspace.

## Files you work with

- `workspace/raw_data/` - Your input data
- `workspace/generated/` - Generated ingestion code
- `.env` - Your Neo4j credentials (in project root)
- `cli.py` - Commands you run (in project root)

That's it! Stay in the workspace, and let the toolkit handle the rest.
