# Connection Setup & Version Detection

**Reference guide for validating Neo4j connections and detecting version information.**

---

## Why This Matters

### Version-Specific Cypher Syntax

Neo4j versions use different Cypher syntax. Generating code without knowing the version = broken code.

**Neo4j 5.x (Cypher 23+)**:
```cypher
// Modern syntax
MERGE (n:Customer {id: $id})
SET n += {firstName: $firstName, lastName: $lastName}
```

**Neo4j 4.x (Cypher 5)**:
```cypher
// Legacy syntax
MERGE (n:Customer {id: $id})
ON CREATE SET n.firstName = $firstName, n.lastName = $lastName
ON MATCH SET n.firstName = $firstName, n.lastName = $lastName
```

**Different syntax means**:
- `SET +=` (5.x) vs `ON CREATE/MATCH SET` (4.x)
- `elementId()` (5.x) vs `id()` (4.x)
- Vector indexes (5.x only)
- Different type systems

### Pre-Generation vs Runtime

**Two layers of version handling**:

1. **Pre-Generation** (what you need):
   - Know version BEFORE generating `data_mapper.py`
   - Choose correct Cypher syntax in generated code
   - Avoid using features that don't exist in user's version

2. **Runtime** (handled by pre-built code):
   - `get_writer()` auto-selects `Neo4jWriterV4` or `Neo4jWriterV5`
   - User doesn't need to think about this
   - Pre-built infrastructure handles it

---

## How to Check Connection & Version

### CLI Command
```bash
python cli.py neo4j info
```

### What It Returns
```json
{
  "status": "connected",
  "version": "5.15.0",
  "cypher_version": "23",
  "edition": "enterprise",
  "database": "neo4j"
}
```

### What to Store
After running the command, keep this information for code generation:
- `version`: Full version string (e.g., "5.15.0")
- `cypher_version`: Cypher version (e.g., "23")
- Major version: Extract from version (e.g., "5")

### If Connection Fails
```json
{
  "status": "error",
  "message": "Connection refused"
}
```

**Common causes**:
- .env file missing or incorrect
- Neo4j not running
- Wrong URI (e.g., `http://` instead of `bolt://`)
- Incorrect password
- Database name doesn't exist

---

## The .env File

### Required Before Any Connection

Users must create `.env` in the root directory:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

### How to Check

```bash
ls .env
```

- **Exists**: Proceed to test connection
- **Missing**: Ask user to create it (provide template above)

### Common Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| Wrong protocol | `http://localhost:7687` | Change to `bolt://` |
| Wrong port | `bolt://localhost:7474` | Change to `:7687` (bolt port) |
| Neo4j not running | Connection refused | Start Neo4j |
| Wrong database | Database not found | Check database name exists |

---

## When to Check Connection

### ✅ Check Early
- Before generating any code
- User may not have .env configured yet
- Better to catch early than fail during generation

### ❌ Don't Blindly Assume
- Don't assume .env exists
- Don't assume connection works
- Don't assume version is 5.x

### Decision Flow

```
User requests help
    ↓
Check: .env exists?
    ↓
  YES → Run: python cli.py neo4j info
    ↓
  SUCCESS → Store version info, proceed
    ↓
  FAILURE → Show error, ask user to fix
    ↓
  NO .env → Ask user to create it
```

---

## What to Communicate to User

### When Connected Successfully
```
✅ Connected to Neo4j 5.15.0 (Cypher 23)
```

Keep it brief. User doesn't need technical details unless they ask.

### When .env Missing
```
❌ Missing .env file

Please create .env in the root directory with your Neo4j credentials:

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

Provide the template, make it easy.

### When Connection Fails
```
❌ Cannot connect to Neo4j

Error: Connection refused

Please check:
- Is Neo4j running?
- Is NEO4J_URI correct in .env? (should be bolt://localhost:7687)
- Is NEO4J_PASSWORD correct?
```

Be helpful. Suggest common fixes.

---

## Version Information Usage

### During Code Generation

Use version to choose syntax:

**Neo4j 5.x**:
```python
cypher = """
MERGE (n:Customer {id: $id})
SET n += $properties
"""
```

**Neo4j 4.x**:
```python
cypher = """
MERGE (n:Customer {id: $id})
ON CREATE SET n = $properties
ON MATCH SET n = $properties
"""
```

### Inform User

When generating code, mention version:
```
Generating data_mapper.py for Neo4j 5.15 (using Cypher 23 syntax)...
```

This helps if they need to debug later.

---

## Pre-Built Infrastructure

### What's Already Implemented

**Connection Management**: `src/core/neo4j/connection.py`
- `get_writer()` - Auto-selects v4 or v5 writer based on detected version
- Caches version to avoid repeated checks

**Version-Specific Writers**:
- `src/core/neo4j/writer_v4.py` - Neo4j 4.x patterns
- `src/core/neo4j/writer_v5.py` - Neo4j 5.x patterns

**CLI Command**: `python cli.py neo4j info`
- Tests connection
- Returns version info as JSON
- Handles errors gracefully

### What You Generate

Your generated `data_mapper.py` just calls:
```python
from src.core.neo4j.connection import get_writer

writer = get_writer()  # Auto-selects correct writer
```

You don't write connection code. You don't handle version detection at runtime. That's all pre-built.

**You only need to**:
- Run `python cli.py neo4j info` before generating
- Use the version info to choose correct Cypher syntax
- Generate code that calls `writer.write_nodes()` and `writer.write_relationships()`

---

## Example Usage in Conversation

### User Request
> "Help me load data into Neo4j"

### Your Actions
1. Check .env: `ls .env`
2. If exists: `python cli.py neo4j info`
3. Store version: "5.15.0", Cypher "23"

### Your Response
```
✅ Connected to Neo4j 5.15.0

Ready to help load your data. What use case are you implementing?
```

---

## Key Takeaways

- **Always check connection before generating code**
- **Version determines Cypher syntax** (5.x vs 4.x are different)
- **CLI provides version info**: `python cli.py neo4j info`
- **.env is required**: Check for it first
- **Pre-built infrastructure handles runtime**: You just need version for code generation
- **Communicate clearly**: Tell user what's wrong and how to fix it

---

See also:
- `../PROMPT.md` - Overall guidance
- `discover_usecase.md` - Next step: selecting use case
- `generate_mapper.md` - How to use version info when generating code
