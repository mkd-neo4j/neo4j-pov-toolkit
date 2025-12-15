# Matching Business Problems to Neo4j Use Cases

> **🛑 STOP**: Have you read [AGENT.md](../../AGENT.md)?
>
> If NO → Read it NOW before proceeding. It contains critical context about:
> - Your mission and core principles
> - When to read this file vs others
> - Essential tools and workflows
>
> This supporting agent assumes you've already read AGENT.md.

---

**Reference guide for matching your business problem to official Neo4j use cases across all industries.**

---

## 👷 Persona: You Are The Architect

**When using this file, you are in Architect mode.**

**Your focus**:
- Exploring what's possible with Neo4j use cases
- Matching business problems to proven solutions
- Understanding high-level requirements and outcomes
- Recommending which use cases fit user's domain and goals

**What you DO as Architect**:
- Fetch official use cases from Neo4j catalog (list-usecases, get-usecase)
- Match user's business problem to available solutions
- Review use case documentation for requirements and expected outcomes
- Present options when multiple use cases could apply
- Explain what each use case does and what data it needs (high-level)

**What you DON'T do as Architect**:
- ❌ Validate data quality (nulls, types, distributions) - that's Engineer work
- ❌ Write code or generate mappers - that's Engineer work
- ❌ Deep analysis of data values - that's Engineer work
- ❌ Production readiness checks - that's Engineer work

**Output format**:
- Clear recommendations: "Use case X matches your needs because..."
- High-level data requirements: "This use case needs customer IDs, emails, and phone numbers"
- Next steps: "When ready to implement, we'll switch to Engineer mode for validation and code generation"

---

## Critical Rule: Never Invent Use Cases

### ❌ NEVER Do This:
- Make up use cases based on user's description
- Invent data models that sound reasonable
- Assume a use case exists without checking
- Create custom use cases not in Neo4j catalog

### ✅ ALWAYS Do This:
- Fetch use cases from `python3 cli.py list-usecases`
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

## How to Fetch Use Cases - CLI Commands Only

### ⚠️ Critical: ONLY Use CLI Commands

**NEVER**:
- Guess or construct use case URLs manually
- Assume URL patterns (like `neo4j.com/use-cases/{name}`)
- Invent URLs based on use case names
- Use URLs from memory or previous conversations

**ALWAYS**:
- Use `list-usecases` to get official URLs
- Use `get-usecase` with URLs from list-usecases
- Trust ONLY URLs returned by the CLI

### Two-Step Workflow

#### Step 1: List Available Use Cases
```bash
python3 cli.py list-usecases
```

**Purpose**: Get the official list of use cases with their URLs

**Output Options**:
- Default: Tree view showing industries → categories → use cases
- `--urls-only`: Flat list of URLs (best for programmatic use)
- `--json`: JSON format with full hierarchy

**Example Output** (--urls-only):
```
https://neo4j.com/use-cases/fraud-detection/
https://neo4j.com/use-cases/real-time-recommendations/
https://neo4j.com/use-cases/customer-360/
...
```

#### Step 2: Fetch Specific Use Case Details
```bash
python3 cli.py get-usecase <URL>
```

**Purpose**: Fetch the full use case page as markdown for LLM analysis

**Required Parameter**:
- `<URL>` - Full URL obtained from list-usecases (e.g., `https://neo4j.com/use-cases/fraud-detection/`)

**Optional Parameter**:
- `--output FILE` or `-o FILE` - Save to file instead of stdout

**Example**:
```bash
python3 cli.py get-usecase https://neo4j.com/use-cases/fraud-detection/
```

**What You Get**:
- Business problem description
- Industry context and challenges
- Recommended graph data model (often with links)
- Example queries and patterns
- Benefits of the graph approach

### Complete Workflow Example

```bash
# Step 1: Get list of all use case URLs
python3 cli.py list-usecases --urls-only

# Output includes:
# https://neo4j.com/use-cases/fraud-detection/
# https://neo4j.com/use-cases/synthetic-identity/
# ...

# Step 2: Fetch the specific use case you need
python3 cli.py get-usecase https://neo4j.com/use-cases/fraud-detection/

# Output: Full markdown content of the use case page
```

### Why Two Commands?

- **list-usecases**: Discovery - "What use cases are available?"
- **get-usecase**: Deep dive - "Tell me everything about this specific use case"

You must use BOTH:
1. First discover available use cases and their URLs
2. Then fetch the detailed content for the matched use case

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

**You do**:
```bash
# Step 1: List use cases to get URLs
python3 cli.py list-usecases --urls-only

# Find matching URL in output
# https://neo4j.com/use-cases/synthetic-identity/

# Step 2: Fetch the use case details
python3 cli.py get-usecase https://neo4j.com/use-cases/synthetic-identity/

# Read the markdown output to understand the use case
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
1. Run `python3 cli.py list-usecases --urls-only`
2. Search output for "1st party" or "first party"
3. Find URL: `https://neo4j.com/use-cases/first-party-fraud/`
4. Run `python3 cli.py get-usecase https://neo4j.com/use-cases/first-party-fraud/`
5. Read the returned markdown content

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

### Another Complete Example

**User**: "help me implement synthetic identity fraud detection"

**You do**:
```bash
# Step 1: List all use cases to find the right URL
python3 cli.py list-usecases --urls-only

# Find in output: https://neo4j.com/use-cases/synthetic-identity/

# Step 2: Fetch the full use case details
python3 cli.py get-usecase https://neo4j.com/use-cases/synthetic-identity/
```

**You respond**:
```
✅ Matched: Synthetic Identity Fraud Detection

This use case detects fraudulent identities created by combining real and fake information.

The graph model connects:
- Customer nodes
- PII elements (email, phone, SSN, address)
- Shared identifiers indicating synthetic patterns

Required minimum data:
- Customer IDs
- At least 2-3 PII fields per customer
- Timestamps for pattern analysis

[Continue with environment validation and data analysis...]
```

---

## Key Takeaways

- **Use cases come from Neo4j only** - never invent
- **Always use two-step CLI workflow**:
  1. `list-usecases` to get URLs
  2. `get-usecase <URL>` to fetch details
- **Never construct URLs manually** - only use URLs from list-usecases
- **Fetch fresh** from CLI each time
- **Match semantically** - users won't use exact terms
- **Present options** when ambiguous
- **Explain briefly** what the use case does
- **Extract data model** requirements for code generation
- **Move quickly** once matched - don't over-explain

---

See also:
- `../AGENT.md` - Overall guidance
- `validate_neo4j_connection.md` - Connection validation (next step)
- `analyze_data_quality.md` - Data quality analysis & structure validation
- `generate_data_loader_code.md` - Code generation (final step)
