# Use Case Discovery & Matching

**Reference guide for selecting fraud detection use cases from Neo4j's official catalog.**

---

## Critical Rule: Never Invent Use Cases

### ❌ NEVER Do This:
- Make up use cases based on user's description
- Invent data models that sound reasonable
- Assume a use case exists without checking
- Create custom use cases not in Neo4j catalog

### ✅ ALWAYS Do This:
- Fetch use cases from `python cli.py list-usecases`
- Match user's request to **official Neo4j use cases only**
- If no match, present available options to user

---

## Why This Matters

**Neo4j's use cases are**:
- Battle-tested in production
- Come with proven data models
- Have documented minimum data requirements
- Include example queries and patterns

**If you invent a use case**:
- Data model may be suboptimal
- No proven patterns to reference
- User gets unvalidated approach
- Defeats the purpose of the toolkit

---

## How to Fetch Use Cases

### CLI Command
```bash
python cli.py list-usecases
```

### What It Returns
List of use case from the Neo4j Use Cases website

---

## Matching User Requests

### User Provides Informal Terms

Users rarely use exact Neo4j terminology. Examples:

| User Says | Maps To |
|-----------|---------|
| "1st party fraud" | First-Party Fraud Detection |
| "synthetic identity" | Synthetic Identity Fraud Detection |
| "transaction fraud" | Transaction Monitoring & AML |
| "account takeover" | Account Takeover Detection |
| "fraud rings" | Fraud Ring Detection |
| "mule accounts" | Money Mule Network Detection |

### Matching Strategy

**Look for semantic matches**:
- Keywords: "fraud", "synthetic", "transaction", "takeover", "ring", "mule"
- Intent: What pattern are they trying to detect?
- Domain: Financial services, identity verification, payments

**Don't require exact strings**:
- "1st party" → "First-Party" ✅
- "synthetic id" → "Synthetic Identity" ✅
- "fraud detection" → any fraud use case ✅

---

## When Match Is Clear

**User**: "I want to implement synthetic identity fraud"

**You discover**:
```bash
python cli.py list-usecases
# Returns: "Synthetic Identity Fraud Detection"
```

**Your response**:
```
✅ Matched use case: Synthetic Identity Fraud Detection

This use case detects shared PII across supposedly distinct customers.

Required data:
- Customer IDs
- PII identifiers (emails, phones, devices, addresses)

[Continue with checking .env and data files...]
```

Brief confirmation, then proceed.

---

## When Match Is Ambiguous

**User**: "help me with fraud"

**Too vague**. Multiple fraud use cases exist.

**Your response**:
```
I found several fraud detection use cases:

1. **Synthetic Identity Fraud** - Detect shared PII across customers
2. **Transaction Monitoring** - Flag suspicious transaction patterns
3. **Account Takeover** - Identify compromised accounts
4. **Fraud Rings** - Uncover coordinated fraud networks
5. **First-Party Fraud** - Detect customers committing fraud themselves

Which one matches your scenario?
```

Present options, let user choose.

---

## When No Match Exists

**User**: "help me with supply chain fraud"

**No Neo4j fraud use case for supply chain** (hypothetical example).

**Your response**:
```
I couldn't find a supply chain fraud use case in Neo4j's catalog.

Available fraud detection use cases:
- Synthetic Identity Fraud
- Transaction Monitoring
- Account Takeover
- Fraud Rings
- First-Party Fraud
- Money Mule Networks

Do any of these match what you're trying to solve? Or would you like to explore a different approach?
```

**Don't invent a supply chain fraud use case**. Present what exists.

## Communicating to User

### When Confirmed:
```
✅ Use case: {Name}
```
Brief, clear, move on.

### When Options Presented:
```
I found {N} fraud detection use cases:
1. {Name} - {Brief description}
2. {Name} - {Brief description}
...

Which one?
```
Concise list, let them choose.

### When Selected by User:
```
✅ Selected: {Name}

This will create {nodes} and {relationships}.
Required data: {minimum requirements}

[Continue with data analysis...]
```

Confirm, explain what it means, proceed.

---

## Example Conversation

**User**: "I want to detect 1st party fraud with my customer data"

**You do**:
1. `python cli.py list-usecases`
2. Search for "1st party" or "first party"
3. Find: "First-Party Fraud Detection"

**You respond**:
```
✅ Matched: First-Party Fraud Detection

This detects customers who commit fraud themselves (e.g., lying on applications, fake income, false identity claims).

Data model will include:
- Customer nodes (core entities)
- Application/Transaction events
- Risk indicators
- Behavioral patterns

Let me check your environment and data files...
```

Then proceed to check `.env` and `workspace/raw_data/`.

---

## Key Takeaways

- **Use cases come from Neo4j only** - never invent
- **Fetch fresh** from CLI or website each time
- **Match semantically** - users won't use exact terms
- **Present options** when ambiguous
- **Explain briefly** what the use case does
- **Extract data model** requirements for code generation
- **Move quickly** once matched - don't over-explain

---

See also:
- `../PROMPT.md` - Overall guidance
- `setup.md` - Connection validation (next step)
- `analyze_data.md` - Data analysis (after use case selected)
- `generate_mapper.md` - Code generation (final step)
