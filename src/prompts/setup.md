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
python3 cli.py neo4j-info
```

### What It Returns
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

### What to Store
After running the command, keep this information for code generation:
- `version`: Full version string (e.g., "5.15.0")
- `cypher_version`: Cypher version (e.g., "23")
- Major version: Extract from version (e.g., "5")

---

## The .env File

### Required Before Any Connection

Users must create `.env` in the root directory:

### How to Check

```bash
ls .env
```

- **Exists**: Proceed to test connection
- **Missing**: Ask user to create it (provide template above)

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
  YES → Run: python3 cli.py neo4j-info
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

Please create .env in the root directory with your Neo4j credentials.
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

## Example Usage in Conversation

### User Request
> "Help me load data into Neo4j"

### Your Actions
1. Check .env: `ls .env`
2. If exists: `python3 cli.py neo4j-info`
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
- **CLI provides version info**: `python3 cli.py neo4j-info`
- **.env is required**: Check for it first
- **Pre-built infrastructure handles runtime**: You just need version for code generation
- **Communicate clearly**: Tell user what's wrong and how to fix it

---

See also:
- `../PROMPT.md` - Overall guidance
- `discover_usecase.md` - Next step: selecting use case
- `generate_mapper.md` - How to use version info when generating code
