# Prompt System Testing Tracker

This document tracks the development and testing of each prompt in the Neo4j PoV Toolkit prompt system.

## Prompt Design Philosophy

### Core Principle: Guidance Over Prescription

The prompts are **reference guides**, not **step-by-step procedures**. We provide:
- **Context**: What tools/resources are available and why they matter
- **Principles**: What makes a good outcome vs a bad outcome
- **Hints**: Suggestions for efficient information gathering
- **Examples**: Good vs bad conversation patterns

We do NOT provide:
- Rigid "Step 1, Step 2, Step 3" instructions
- Prescriptive decision trees
- Hardcoded conversation flows

### Why This Approach?

**Goal**: Let the LLM intelligently decide the best path based on the specific user situation.

**Benefits**:
- LLM can adapt to different user inputs
- More natural conversations
- LLM can discover optimal strategies
- Easier to maintain (less brittle than rigid scripts)

**Example**:
- ❌ Bad: "Step 1: Ask user for use case. Step 2: Check .env file."
- ✅ Good: "Consider checking for .env before asking user for credentials. Information gathering is cheap, user interruption is expensive."

### Information Gathering Strategy

**Principle**: Gather first, ask later.

The LLM should:
1. **Silently check** available resources (CLI commands, file system, etc.)
2. **Analyze** what's present vs what's missing
3. **Only ask user** when truly blocked or need clarification
4. **Batch questions** if multiple things are missing

**Why**: Users provide minimal input (e.g., "help me with 1st party fraud"). The LLM should discover available information before interrupting the user.

**Example Flow**:
```
User: "I want to implement 1st party fraud"

LLM thinks:
- Check `python cli.py list-usecases` → Find use cases
- Check `.env` exists → Present or missing?
- Check `workspace/raw_data/` → Any CSV files?
- Check Neo4j connection (if .env exists)

LLM responds:
"I found these things:
✅ Matched 'First-Party Fraud Detection' use case
✅ Found data.csv with customer info
❌ Missing .env file - need your Neo4j credentials

Please create .env with: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD"
```

## Overview

The prompt system consists of:
- **PROMPT.md** (root): High-level guidance and philosophy - single entry point
- **src/prompts/**: Supporting reference materials for specific tasks

## Testing Status

### ✅ Infrastructure
- [x] Created src/prompts/ folder
- [ ] PROMPT_TESTING.md (this file)
- [ ] PROMPT.md master orchestrator

### Step 0: Setup & Connection
**File**: `src/prompts/setup.md`
**Status**: Not Started
**Purpose**: Validate Neo4j connection and detect version

**Test Plan**:
- [ ] Check .env file existence validation
- [ ] Test Neo4j connection validation
- [ ] Test version detection (Neo4j 4.x)
- [ ] Test version detection (Neo4j 5.x)
- [ ] Verify error handling for connection failures

**Test Results**:
```
[Results will be recorded here after testing]
```

**Notes**:
```
[Testing notes and observations]
```

---

### Step 1: Use Case Discovery
**File**: `src/prompts/discover_usecase.md`
**Status**: Not Started
**Purpose**: Help user select fraud detection use case from Neo4j website

**Test Plan**:
- [ ] Test scraping Neo4j use cases website
- [ ] Verify use case list presentation
- [ ] Test use case selection flow
- [ ] Test data model extraction
- [ ] Verify minimum data requirements extraction

**Test Results**:
```
[Results will be recorded here after testing]
```

**Notes**:
```
[Testing notes and observations]
```

---

### Step 2: Data Analysis
**File**: `src/prompts/analyze_data.md`
**Status**: Not Started
**Purpose**: Analyze raw data and create mapping plan

**Test Plan**:
- [ ] Test workspace/raw_data/ file discovery
- [ ] Test CSV structure analysis (data.csv)
- [ ] Test field mapping to graph model
- [ ] Test mapping plan presentation
- [ ] Test user confirmation flow

**Test Results**:
```
[Results will be recorded here after testing]
```

**Notes**:
```
[Testing notes and observations]
```

---

### Step 3: Code Generation
**File**: `src/prompts/generate_mapper.md`
**Status**: Not Started
**Purpose**: Generate workspace/generated/data_mapper.py

**Test Plan**:
- [ ] Test code generation for Neo4j 5.x
- [ ] Test code generation for Neo4j 4.x
- [ ] Verify version-appropriate Cypher syntax
- [ ] Verify use of pre-built writer functions
- [ ] Test generated code readability
- [ ] Verify docstring and comments

**Test Results**:
```
[Results will be recorded here after testing]
```

**Notes**:
```
[Testing notes and observations]
```

---

### Integration Testing
**File**: `PROMPT.md`
**Status**: Not Started
**Purpose**: Full end-to-end flow through all steps

**Test Plan**:
- [ ] Test complete flow: connection → use case → data → generation
- [ ] Test state management between steps
- [ ] Test error recovery
- [ ] Test regeneration scenarios
- [ ] Test with different use cases

**Test Results**:
```
[Results will be recorded here after testing]
```

**Notes**:
```
[Testing notes and observations]
```

---

## Current Focus

**Working On**: Creating PROMPT_TESTING.md and PROMPT.md skeleton

**Next Step**: Write and test setup.md

---

## Issues & Blockers

None currently

---

## Key Decisions

1. **Location**: PROMPT.md at root for easy discovery
2. **Design**: Guidance-based, not prescriptive step-by-step
3. **Strategy**: Gather information first, ask user only when blocked
4. **Testing Approach**: Test LLM decision-making, not just instruction-following
5. **Tracking**: Use this file to document all test results

## Test Scenarios for LLM Intelligence

Beyond testing each prompt file, we need to validate that the LLM makes smart decisions:

### Scenario 1: Complete Information Available
**Input**: User says "implement 1st party fraud", `.env` exists, `data.csv` exists, Neo4j connected
**Expected**: LLM gathers everything silently, generates code immediately, minimal user interaction

### Scenario 2: Missing .env Only
**Input**: User request + data present, but no `.env`
**Expected**: LLM discovers use case + data, then asks ONLY for .env credentials

### Scenario 3: Ambiguous Use Case
**Input**: "help with fraud", `.env` exists, data exists
**Expected**: LLM checks connection + data first, then presents use case options (not asking blindly upfront)

### Scenario 4: No Data Files
**Input**: Valid use case + .env, but `workspace/raw_data/` empty
**Expected**: LLM validates connection first, then informs user about missing data with specific requirements

### Scenario 5: Multiple Blockers
**Input**: No .env, no data, vague use case
**Expected**: LLM discovers all issues, presents them in ONE message (batched), not asking one-by-one

### Scenario 6: Data Insufficient for Use Case
**Input**: Use case needs customer+transactions, but only customer.csv present
**Expected**: LLM analyzes data structure, identifies gap, explains what's missing and why

---

## Quick Reference

### How to Test a Prompt
1. Write the prompt file
2. Test with actual data/connections
3. Document results in this file
4. Get approval before proceeding
5. Move to next prompt

### Test Data
- **CSV File**: workspace/raw_data/data.csv (customer data with shared emails/phones)
- **Neo4j**: [Add connection details for testing]
- **Use Case**: Start with Synthetic Identity Fraud Detection

---

Last Updated: 2025-12-10
