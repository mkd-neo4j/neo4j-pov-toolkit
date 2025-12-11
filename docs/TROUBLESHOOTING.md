# Troubleshooting Guide

Common issues and solutions for the Neo4j PoV Toolkit.

---

## Connection Issues

### Unable to Connect to Neo4j

**Symptom**:
```
❌ Cannot connect to Neo4j
Error: ServiceUnavailable: Failed to establish connection
```

**Common Causes & Solutions**:

#### 1. Neo4j Not Running

**Check**:
```bash
# Neo4j Desktop: Check status in Desktop app
# Docker:
docker ps | grep neo4j
# System service:
neo4j status
```

**Solution**:
- Neo4j Desktop: Start database in Desktop app
- Docker: `docker start neo4j`
- System: `sudo systemctl start neo4j` or `neo4j start`

#### 2. Wrong Connection URI

**Check `.env` file**:
```env
NEO4J_URI=neo4j://localhost:7687
```

**Common mistakes**:
- ❌ `http://localhost:7474` (Browser port, not Bolt)
- ❌ `bolt://localhost:7474` (Wrong port)
- ❌ Missing protocol: `localhost:7687`
- ✅ `neo4j://localhost:7687` (Correct for local)
- ✅ `bolt://localhost:7687` (Alternative for local)
- ✅ `neo4j+s://xxxxx.databases.neo4j.io` (Correct for Aura)

**Test connection**:
```bash
# Try connecting with Neo4j Browser first
open http://localhost:7474

# Then test with CLI
python cli.py neo4j-test
```

#### 3. Incorrect Password

**Check**:
```bash
# Test with correct password in Neo4j Browser
# Then update .env
```

**Common issues**:
- Password was changed but .env not updated
- Copied password with extra spaces
- Using default password when it was changed

**Solution**:
1. Reset password if needed:
   - Neo4j Desktop: Database settings → Change password
   - Aura: Create new credentials in console
2. Update `.env` with exact password (no spaces)

#### 4. Firewall or Network Issues

**Check port accessibility**:
```bash
# Test if port 7687 is reachable
nc -zv localhost 7687
# or
telnet localhost 7687
```

**For Aura**:
- Ensure outbound HTTPS (443) is allowed
- Check corporate firewall settings
- Verify IP whitelist in Aura console (if enabled)

**Solution**:
- Allow port 7687 in firewall
- For Aura: Check network/firewall allows outbound connections
- Try from different network to isolate issue

---

## Python Environment Issues

### ModuleNotFoundError: No module named 'neo4j'

**Symptom**:
```
ModuleNotFoundError: No module named 'neo4j'
```

**Solution 1: Activate Virtual Environment**
```bash
# Check if venv is activated (should see (venv) in prompt)
# If not:
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

**Solution 2: Reinstall Dependencies**
```bash
pip install -r requirements.txt
```

**Solution 3: Verify Installation**
```bash
# Check neo4j package is installed
pip list | grep neo4j

# Should show:
# neo4j  5.x.x (or similar)
```

**Solution 4: Create New Virtual Environment**
```bash
# Remove old venv
rm -rf venv

# Create fresh venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ModuleNotFoundError: No module named 'src'

**Symptom** (when running data_mapper.py):
```
ModuleNotFoundError: No module named 'src'
```

**Cause**: Script doesn't have proper path setup

**Solution**: The generated `data_mapper.py` should include path setup at the top:

```python
# Setup Python path to find toolkit modules
import sys
from pathlib import Path

script_path = Path(__file__).resolve()
project_root = script_path.parent.parent.parent
sys.path.insert(0, str(project_root))
```

If missing, regenerate the code with the LLM or add this manually before imports.

---

## Data Mapper Execution Issues

### FileNotFoundError: workspace/raw_data/data.csv

**Symptom**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'workspace/raw_data/data.csv'
```

**Cause**: Data file doesn't exist or has different name

**Solution**:
```bash
# Check what files exist
ls workspace/raw_data/

# If file has different name, either:
# 1. Rename it:
mv workspace/raw_data/myfile.csv workspace/raw_data/data.csv

# 2. Update data_mapper.py to use correct filename
```

### Neo4j Driver Authentication Error

**Symptom**:
```
AuthError: The client is unauthorized due to authentication failure
```

**Solution**:
```bash
# 1. Verify credentials in .env
cat .env | grep NEO4J

# 2. Test credentials with CLI
python cli.py neo4j-test

# 3. Update .env with correct password
# 4. Try data mapper again
```

### Cypher Syntax Errors

**Symptom**:
```
CypherSyntaxError: Invalid input...
```

**Cause**: Generated code may have wrong Cypher syntax for your Neo4j version

**Solution**:
1. Check Neo4j version:
   ```bash
   python cli.py neo4j-info
   ```

2. Regenerate code with LLM, ensuring it detects correct version first

3. Neo4j 4.x vs 5.x/6.x have different syntax:
   - Neo4j 5.x/6.x: `SET n += properties`
   - Neo4j 4.x: `SET n.prop1 = value1, n.prop2 = value2`

---

## CLI Issues

### Permission Denied

**Symptom**:
```
bash: ./cli.py: Permission denied
```

**Solution**:
```bash
# Option 1: Make executable
chmod +x cli.py
./cli.py neo4j-test

# Option 2: Run with python
python cli.py neo4j-test
```

### Command Not Found: python

**Symptom**:
```
python: command not found
```

**Solution**:
```bash
# Try python3 instead
python3 cli.py neo4j-test

# Or create alias
alias python=python3

# Or use full path
/usr/bin/python3 cli.py neo4j-test
```

### CLI Hangs or Times Out

**Symptom**: CLI appears to hang when running commands

**Cause**: Usually network/connection issue

**Solution**:
1. Test basic connectivity:
   ```bash
   ping localhost
   nc -zv localhost 7687
   ```

2. Check Neo4j logs for errors:
   - Desktop: Click database → Logs
   - Docker: `docker logs neo4j`
   - System: `/var/log/neo4j/`

3. Try with timeout:
   ```bash
   timeout 10 python cli.py neo4j-test
   ```

---

## LLM Integration Issues

### LLM Can't Find CLI Commands

**Symptom**: LLM says "Command not found" or can't execute CLI

**Solution**:
1. Ensure LLM tool has access to project directory
2. Check working directory is project root
3. Try explicit path: `python /full/path/to/cli.py neo4j-test`

### LLM Generates Code with Wrong Imports

**Symptom**: Generated code has incorrect import statements

**Solution**: Remind LLM to read these files first:
```
"Before generating code, please read:
- src/core/neo4j/query.py
- src/core/neo4j/version.py
- src/core/logger.py"
```

### Generated Code Doesn't Match Data Model

**Symptom**: Wrong node labels or relationships

**Solution**: Ask LLM to fetch use case first:
```
"Please run: python cli.py get-usecase <URL>
And generate code that exactly matches that data model"
```

---

## Data Issues

### CSV Encoding Errors

**Symptom**:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```

**Solution**:
```python
# Update data_mapper.py to specify encoding
with open(csv_path, 'r', encoding='latin-1') as f:  # or 'iso-8859-1'
    reader = csv.DictReader(f)
```

### CSV Delimiter Issues

**Symptom**: Data appears as one column instead of multiple

**Solution**:
```python
# If using semicolon or tab-separated values
with open(csv_path, 'r') as f:
    reader = csv.DictReader(f, delimiter=';')  # or '\t'
```

### Missing Required Fields

**Symptom**:
```
KeyError: 'customer_id'
```

**Solution**:
1. Check CSV headers match code:
   ```bash
   head -1 workspace/raw_data/data.csv
   ```

2. Update data_mapper.py to use actual column names:
   ```python
   'customer_id': row['CustomerID'],  # If CSV uses 'CustomerID'
   ```

---

## Neo4j Database Issues

### Disk Space Full

**Symptom**:
```
Neo4jError: Could not write to log file
```

**Solution**:
```bash
# Check disk space
df -h

# Clean Neo4j logs if needed
# (Neo4j Desktop: Database settings → Clear logs)
```

### Database Locked

**Symptom**:
```
Database is locked by another process
```

**Solution**:
1. Close Neo4j Browser
2. Stop any other Neo4j connections
3. Restart Neo4j
4. Try again

### Constraint Violations

**Symptom**:
```
ConstraintValidationFailed: Node already exists with label
```

**Cause**: Duplicate nodes with same unique property

**Solution**:
1. Check for duplicates in source data
2. Use MERGE instead of CREATE in Cypher
3. Or clear database before reloading:
   ```cypher
   // In Neo4j Browser - CAUTION: Deletes all data
   MATCH (n) DETACH DELETE n
   ```

---

## Performance Issues

### Data Load Taking Too Long

**Symptom**: Data mapper runs very slowly

**Solution**:

1. **Check batch size** (in data_mapper.py):
   ```python
   # Increase batch size for faster loading
   query.run_batched(cypher, data, batch_size=5000)  # Default: 1000
   ```

2. **Create indexes first**:
   ```cypher
   // In Neo4j Browser, before loading
   CREATE INDEX customer_id IF NOT EXISTS FOR (c:Customer) ON (c.customerId);
   CREATE INDEX email_address IF NOT EXISTS FOR (e:Email) ON (e.address);
   ```

3. **Check database resources**:
   - Increase Neo4j memory (Desktop: Settings → Memory)
   - Close other applications

### Out of Memory Errors

**Symptom**:
```
MemoryError
```

**Solution**:

1. **Process data in chunks**:
   ```python
   # Instead of loading all at once
   chunk_size = 10000
   for i in range(0, len(data), chunk_size):
       chunk = data[i:i+chunk_size]
       create_nodes(query, chunk)
   ```

2. **Increase Python memory** (if very large dataset)

3. **Use streaming** instead of loading all into memory

---

## Getting More Help

If your issue isn't covered here:

### 1. Check Logs

**Neo4j Logs**:
- Desktop: Database → Logs tab
- Docker: `docker logs neo4j`
- System: `/var/log/neo4j/neo4j.log`

**Python Logs**:
```bash
# Run with debug output
python cli.py neo4j-test --verbose
```

### 2. Search Documentation

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Neo4j Python Driver Docs](https://neo4j.com/docs/python-manual/current/)
- [Toolkit README](../README.md)

### 3. Community Support

- [Neo4j Community Forum](https://community.neo4j.com)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/neo4j) (tag: neo4j)
- [GitHub Issues](https://github.com/neo4j/pov-toolkit/issues)

### 4. Gather Information

When seeking help, provide:
- Error message (full traceback)
- Neo4j version: `python cli.py neo4j-info`
- Python version: `python --version`
- Operating system
- Steps to reproduce

---

## Quick Checklist

When something goes wrong, try these in order:

- [ ] Neo4j is running
- [ ] `.env` file exists and has correct credentials
- [ ] Virtual environment is activated
- [ ] Dependencies are installed: `pip list | grep neo4j`
- [ ] Can connect via Neo4j Browser (http://localhost:7474)
- [ ] CLI test passes: `python cli.py neo4j-test`
- [ ] Data files exist in `workspace/raw_data/`
- [ ] Running from correct directory (project root)
- [ ] No typos in commands or file names

If all checked and still failing → check logs and seek help with specific error message.
