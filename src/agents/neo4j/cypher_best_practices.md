# Neo4j Data Modeling and Cypher Best Practices

> **📚 Reference Guide**: This document contains Neo4j best practices for data modeling, Cypher query writing, and graph database optimization.
>
> **When to read this**: Before generating data loader code or Cypher queries to ensure adherence to Neo4j industry standards.

---

## Purpose

This agent provides authoritative Neo4j best practices aggregated from official Neo4j documentation. Use these guidelines when:
- Generating Cypher queries for data loading
- Designing graph data models
- Optimizing query performance
- Validating generated code against industry standards

**Source**: [Neo4j Data Model Best Practices](https://neo4j.com/developer/industry-use-cases/_attachments/neo4j_data_model_best_practices.txt)

---

## Core Modeling Principles

### Start with Use Cases
1. **Begin with specific business questions** the graph needs to answer
2. Follow iterative approach: **Conceptualize → Query Design → Testing**
3. Design for query efficiency, not just data storage
4. Ensure node uniqueness through constraints

### The Framework
```
Use Case → Data Model → Queries → Testing → Refinement
```

Each iteration should validate that the model answers all business questions efficiently.

---

## Naming Conventions

**CRITICAL**: Consistent naming is essential for code generation and query readability.

### Node Labels
- **Format**: `CamelCase` with uppercase first letter
- **Examples**: `Person`, `Customer`, `EmailAddress`, `PhoneNumber`
- **Don't**: `person`, `PERSON`, `email_address`, `phone-number`

```cypher
// ✅ Correct
CREATE (p:Person {name: "Alice"})
CREATE (e:EmailAddress {address: "alice@example.com"})

// ❌ Incorrect
CREATE (p:person {name: "Alice"})
CREATE (e:email_address {address: "alice@example.com"})
```

### Relationship Types
- **Format**: `ALL_CAPS_WITH_UNDERSCORES`
- **Examples**: `WORKS_AT`, `HAS_EMAIL`, `PURCHASED`, `FRIENDS_WITH`
- **Don't**: `worksAt`, `has-email`, `Purchased`

```cypher
// ✅ Correct
CREATE (p:Person)-[:WORKS_AT]->(c:Company)
CREATE (c:Customer)-[:HAS_EMAIL]->(e:Email)

// ❌ Incorrect
CREATE (p:Person)-[:worksAt]->(c:Company)
CREATE (c:Customer)-[:has_email]->(e:Email)
```

### Property Names
- **Format**: `camelCase` with lowercase first letter
- **Examples**: `firstName`, `emailAddress`, `createdAt`, `transactionAmount`
- **Don't**: `FirstName`, `email_address`, `created-at`, `transaction_amount`

```cypher
// ✅ Correct
CREATE (p:Person {
  firstName: "Alice",
  lastName: "Smith",
  emailAddress: "alice@example.com",
  createdAt: datetime()
})

// ❌ Incorrect
CREATE (p:Person {
  first_name: "Alice",
  LastName: "Smith",
  email_address: "alice@example.com",
  created_at: datetime()
})
```

---

## Node Design Guidelines

### Label Limits
- **Limit to 4 or fewer labels per node**
- Use properties instead of excessive labels
- Multiple labels should represent orthogonal categories

```cypher
// ✅ Good: Limited, meaningful labels
CREATE (p:Person:Employee)
CREATE (c:Customer:PremiumMember)

// ❌ Bad: Too many labels
CREATE (p:Person:Employee:Manager:FullTime:Remote:Senior)
```

**Why**: Excessive labels hurt query performance and make the model complex.

### Avoid Duplicate Data
- **Don't duplicate data across nodes**
- Use relationships to connect shared information
- Single source of truth for each piece of data

```cypher
// ❌ Bad: Duplicated company data
CREATE (p1:Person {name: "Alice", company: "Acme Corp", companyAddress: "123 Main St"})
CREATE (p2:Person {name: "Bob", company: "Acme Corp", companyAddress: "123 Main St"})

// ✅ Good: Company as separate node
CREATE (c:Company {name: "Acme Corp", address: "123 Main St"})
CREATE (p1:Person {name: "Alice"})-[:WORKS_AT]->(c)
CREATE (p2:Person {name: "Bob"})-[:WORKS_AT]->(c)
```

### List Properties vs. Connected Nodes
- **Model list properties as separate connected nodes**
- Enables relationship properties and graph traversal
- Better for querying and pattern matching

```cypher
// ❌ Avoid: List properties
CREATE (p:Person {
  name: "Alice",
  emails: ["alice@work.com", "alice@home.com", "alice@mobile.com"]
})

// ✅ Better: Separate nodes with relationships
CREATE (p:Person {name: "Alice"})
CREATE (e1:Email {address: "alice@work.com"})-[:BELONGS_TO {type: "work"}]->(p)
CREATE (e2:Email {address: "alice@home.com"})-[:BELONGS_TO {type: "home"}]->(p)
CREATE (e3:Email {address: "alice@mobile.com"})-[:BELONGS_TO {type: "mobile"}]->(p)
```

**When to use list properties**: Only for small, static lists that won't be queried independently.

### Prevent Supernodes
- **Supernode**: A node with an excessive number of relationships
- Carefully manage fanout (number of relationships per node)
- Use intermediate nodes to break up high-degree nodes

```cypher
// ❌ Risky: Supernode pattern
CREATE (year:Year {value: 2024})
// Millions of transactions all connect to same Year node
CREATE (t:Transaction)-[:IN_YEAR]->(year)

// ✅ Better: Timeline tree pattern
CREATE (year:Year {value: 2024})
CREATE (month:Month {value: "2024-01"})-[:IN_YEAR]->(year)
CREATE (day:Day {value: "2024-01-15"})-[:IN_MONTH]->(month)
CREATE (t:Transaction)-[:ON_DAY]->(day)
```

**Why**: Supernodes cause performance degradation and hotspot issues.

---

## Relationship Design

### Use Specific Relationship Types
- **Be specific** about relationship semantics
- Avoid generic types like `RELATED_TO` or `CONNECTED_TO`
- Types should describe the nature of the connection

```cypher
// ❌ Too generic
CREATE (p:Person)-[:RELATED_TO]->(c:Company)

// ✅ Specific and clear
CREATE (p:Person)-[:WORKS_AT]->(c:Company)
CREATE (p:Person)-[:FOUNDED]->(c:Company)
CREATE (p:Person)-[:INVESTED_IN]->(c:Company)
```

**Why**: Specific types enable better query targeting and model understanding.

### Avoid Symmetric Relationships
- **Don't create bidirectional relationships** when one direction suffices
- Choose direction based on query patterns
- Use undirected matching in queries when needed

```cypher
// ❌ Avoid: Symmetric relationships
CREATE (p1:Person)-[:FRIENDS_WITH]->(p2:Person)
CREATE (p2)-[:FRIENDS_WITH]->(p1)

// ✅ Better: Single direction, query both ways
CREATE (p1:Person)-[:FRIENDS_WITH]->(p2:Person)

// Query for friends in either direction
MATCH (p:Person {name: "Alice"})-[:FRIENDS_WITH]-(friend)
RETURN friend
```

### Respect Relationship Direction
- **Choose meaningful direction** based on domain semantics
- Direction should reflect the real-world relationship
- Document direction decisions in model

```cypher
// ✅ Natural direction
CREATE (customer:Customer)-[:PLACED]->(order:Order)
CREATE (order)-[:CONTAINS]->(product:Product)
CREATE (employee:Employee)-[:REPORTS_TO]->(manager:Employee)

// ❌ Unnatural direction
CREATE (order:Order)-[:PLACED_BY]->(customer:Customer)  // Backwards
```

### Intermediate Nodes for Complex Relationships
- **Use intermediate nodes** when relationships need many properties
- Better than heavily-propertied relationships
- Enables connecting relationships to other entities

```cypher
// ❌ Heavy relationship properties
CREATE (actor:Actor)-[:ACTED_IN {
  role: "Neo",
  screenTime: 120,
  salary: 10000000,
  contractDate: "2024-01-01"
}]->(movie:Movie)

// ✅ Better: Intermediate node
CREATE (actor:Actor)-[:PLAYED]->(role:Role {
  name: "Neo",
  screenTime: 120
})-[:IN_MOVIE]->(movie:Movie)
CREATE (role)-[:UNDER_CONTRACT]->(contract:Contract {
  salary: 10000000,
  date: "2024-01-01"
})
```

---

## Property Strategy

### Property Purposes
Properties should serve two purposes:
1. **Identification**: Unique identifiers for merging/matching
2. **Query answering**: Data needed to answer business questions

```cypher
// Good property design
CREATE (c:Customer {
  customerId: "C12345",           // Identification
  email: "alice@example.com",     // Identification (secondary)
  firstName: "Alice",             // Query answering
  lastName: "Smith",              // Query answering
  signupDate: date("2024-01-15"), // Query answering
  totalSpent: 1250.50             // Query answering
})
```

### Index Simple Properties
- **Create indexes** on properties used for anchoring queries
- Index properties used in `MATCH`, `MERGE`, `WHERE` clauses
- Composite indexes for frequently combined properties

```cypher
// Create unique constraint (automatically indexed)
CREATE CONSTRAINT customer_id_unique FOR (c:Customer) REQUIRE c.customerId IS UNIQUE

// Create regular index
CREATE INDEX customer_email FOR (c:Customer) ON (c.email)

// Composite index for range queries
CREATE INDEX transaction_date_amount FOR (t:Transaction) ON (t.date, t.amount)
```

### Data Accessibility Hierarchy
**Order of preference** for data access:
1. **Indexed properties** (fastest)
2. **Non-indexed properties**
3. **Relationship traversal**
4. **External lookups** (slowest)

Design queries to minimize lower-tier access.

---

## Cypher Query Patterns

### Anchor on Indexed Properties
- **Start queries** with indexed property lookups
- Avoids full graph scans
- Dramatically improves performance

```cypher
// ❌ Bad: No anchor, full scan
MATCH (c:Customer)
WHERE c.firstName = "Alice"
RETURN c

// ✅ Good: Anchor on indexed property
MATCH (c:Customer {customerId: "C12345"})
RETURN c

// ✅ Good: Anchor with index lookup
MATCH (c:Customer)
WHERE c.email = "alice@example.com"  // email is indexed
RETURN c
```

### Use Specific Relationship Types
- **Specify relationship types** in patterns
- Avoids checking all relationship types
- Enables relationship type indexes

```cypher
// ❌ Slower: Unspecified relationship type
MATCH (c:Customer)-[r]-(e:Email)
RETURN e

// ✅ Faster: Specific relationship type
MATCH (c:Customer)-[:HAS_EMAIL]->(e:Email)
RETURN e
```

### Minimize Gather-and-Inspect
- **Avoid patterns** that gather all nodes then filter
- Push filtering into the `MATCH` clause
- Use `WHERE` efficiently

```cypher
// ❌ Bad: Gather-and-inspect
MATCH (c:Customer)-[:PLACED]->(o:Order)
WITH collect(o) as orders
WHERE size(orders) > 10
RETURN c

// ✅ Better: Filter during traversal
MATCH (c:Customer)
WHERE size((c)-[:PLACED]->(:Order)) > 10
RETURN c

// ✅ Best: Aggregate efficiently
MATCH (c:Customer)-[:PLACED]->(o:Order)
WITH c, count(o) as orderCount
WHERE orderCount > 10
RETURN c
```

### Profile Queries
- **Always use `PROFILE`** for optimization
- Analyze query execution plans
- Look for expensive operations (eager, cartesian products, scans)

```cypher
// Profile a query
PROFILE
MATCH (c:Customer {customerId: "C12345"})-[:PLACED]->(o:Order)
RETURN c, o

// Explain without executing
EXPLAIN
MATCH (c:Customer)-[:PLACED]->(o:Order)
WHERE o.date > date("2024-01-01")
RETURN c, count(o) as orderCount
```

---

## Data Insertion Best Practices

### Create Unique Constraints First
- **Always create constraints** before loading data
- Ensures data integrity
- Automatically creates indexes for performance

```cypher
// Create constraints before loading
CREATE CONSTRAINT customer_id_unique FOR (c:Customer) REQUIRE c.customerId IS UNIQUE
CREATE CONSTRAINT email_address_unique FOR (e:Email) REQUIRE e.address IS UNIQUE
CREATE CONSTRAINT phone_number_unique FOR (p:Phone) REQUIRE p.phoneNumber IS UNIQUE
```

### Use MERGE for Unique Identifiers
- **`MERGE`** for nodes with unique identifiers
- Prevents duplicate nodes
- Combines match-or-create logic

```cypher
// ✅ Correct: MERGE on unique property
MERGE (c:Customer {customerId: "C12345"})
ON CREATE SET
  c.firstName = "Alice",
  c.lastName = "Smith",
  c.createdAt = datetime()
ON MATCH SET
  c.updatedAt = datetime()

// ❌ Wrong: CREATE can cause duplicates
CREATE (c:Customer {customerId: "C12345"})
```

### Batch Operations for Large Datasets
- **Use `UNWIND`** for batch processing
- Process 1000-10000 records per transaction
- Balance between transaction size and memory

```cypher
// Batch loading pattern
UNWIND $batch AS row
MERGE (c:Customer {customerId: row.customer_id})
SET c.firstName = row.first_name,
    c.lastName = row.last_name,
    c.email = row.email
```

**Recommended batch sizes**:
- Simple nodes: 5000-10000 per batch
- Complex relationships: 1000-5000 per batch
- Heavy properties: 500-1000 per batch

### Clean and Deduplicate Data
- **Validate data** before insertion
- Remove duplicates in preprocessing
- Handle nulls and invalid values

```python
# Preprocessing example (Python)
# Clean email addresses
data = [
    {
        'customerId': row['id'],
        'email': row['email'].strip().lower() if row['email'] else None,
        'firstName': row['first_name'].strip() if row['first_name'] else None
    }
    for row in raw_data
    if row['id']  # Skip rows without ID
]

# Deduplicate by customer ID
seen_ids = set()
unique_data = []
for record in data:
    if record['customerId'] not in seen_ids:
        unique_data.append(record)
        seen_ids.add(record['customerId'])
```

### Add Indexes for Frequent Queries
- **Create indexes** on properties used in lookups
- Balance between write performance and read performance
- Monitor query patterns and add indexes as needed

```cypher
// Indexes for common query patterns
CREATE INDEX customer_name FOR (c:Customer) ON (c.lastName, c.firstName)
CREATE INDEX order_date FOR (o:Order) ON (o.date)
CREATE INDEX transaction_amount FOR (t:Transaction) ON (t.amount)
```

### Convert Foreign Keys to Relationships
- **Replace foreign key references** with graph relationships
- More expressive and performant than joins
- Natural for graph traversal

```cypher
// ❌ Relational thinking
CREATE (o:Order {orderId: "O123", customerId: "C456"})

// ✅ Graph thinking
MERGE (c:Customer {customerId: "C456"})
MERGE (o:Order {orderId: "O123"})
MERGE (c)-[:PLACED]->(o)
```

---

## Common Structural Patterns

### Intermediate Nodes
**When to use**: Relationships need significant properties or connections to other entities.

```cypher
// Pattern: Actor → Role → Movie
CREATE (actor:Actor {name: "Keanu Reeves"})
CREATE (role:Role {
  name: "Neo",
  screenTime: 120
})
CREATE (movie:Movie {title: "The Matrix"})
CREATE (actor)-[:PLAYED]->(role)-[:IN_MOVIE]->(movie)
```

**Benefits**: Enables querying role-specific data independently.

### Linked Lists
**When to use**: Ordered sequences with natural progression.

```cypher
// Pattern: Sequential events
CREATE (e1:Event {name: "Registration", timestamp: datetime("2024-01-01T10:00:00")})
CREATE (e2:Event {name: "Login", timestamp: datetime("2024-01-01T10:05:00")})
CREATE (e3:Event {name: "Purchase", timestamp: datetime("2024-01-01T10:15:00")})
CREATE (e1)-[:NEXT]->(e2)-[:NEXT]->(e3)
```

**Benefits**: Enables sequential traversal and order-dependent queries.

### Timeline Trees
**When to use**: Time-based data with high cardinality (many events per time period).

```cypher
// Pattern: Year → Month → Day → Event
CREATE (year:Year {value: 2024})
CREATE (month:Month {value: "2024-01"})-[:IN_YEAR]->(year)
CREATE (day:Day {value: "2024-01-15"})-[:IN_MONTH]->(month)
CREATE (event:Event {type: "login"})-[:ON_DAY]->(day)
```

**Benefits**: Prevents supernodes, enables efficient time-range queries.

### Balanced Fanout
**When to use**: High-degree nodes that need distribution.

```cypher
// Pattern: Category → Subcategory → Item
CREATE (cat:Category {name: "Electronics"})
CREATE (subcat:Subcategory {name: "Phones"})-[:PART_OF]->(cat)
CREATE (item:Product {name: "iPhone 15"})-[:IN_CATEGORY]->(subcat)
```

**Benefits**: Distributes relationships, avoids single bottleneck nodes.

---

## Query Optimization Techniques

### 1. Profile and Analyze
```cypher
PROFILE
MATCH (c:Customer)-[:PLACED]->(o:Order)
WHERE o.date >= date("2024-01-01")
RETURN c.customerId, count(o) as orders
ORDER BY orders DESC
LIMIT 10
```

**Look for**:
- **Eager operations**: Materialize results early (costly)
- **Cartesian products**: Unintended cross-joins
- **Node by label scans**: Missing indexes
- **Large db hits**: Inefficient traversal

### 2. Consider Data Aggregation
- **Pre-aggregate** frequently computed values
- Store aggregates as properties
- Update on data changes

```cypher
// Store order count on customer
MATCH (c:Customer)<-[:PLACED_BY]-(o:Order)
WITH c, count(o) as orderCount
SET c.totalOrders = orderCount

// Query is now instant
MATCH (c:Customer)
WHERE c.totalOrders > 10
RETURN c
```

### 3. Use Query Hints (When Necessary)
```cypher
// Force index usage
MATCH (c:Customer)
USING INDEX c:Customer(email)
WHERE c.email STARTS WITH "alice"
RETURN c

// Force join
MATCH (c:Customer), (o:Order)
USING JOIN ON c
WHERE c.customerId = o.customerId
RETURN c, o
```

**Use sparingly**: Only when profiling shows the planner makes wrong choices.

### 4. Limit Result Sets Early
```cypher
// ✅ Good: Limit early
MATCH (c:Customer)
WHERE c.signupDate > date("2024-01-01")
WITH c
ORDER BY c.totalSpent DESC
LIMIT 100
MATCH (c)-[:PLACED]->(o:Order)
RETURN c, collect(o) as orders

// ❌ Bad: Limit late (processes all data first)
MATCH (c:Customer)-[:PLACED]->(o:Order)
WHERE c.signupDate > date("2024-01-01")
WITH c, collect(o) as orders
ORDER BY c.totalSpent DESC
LIMIT 100
RETURN c, orders
```

---

## Validation Checklist

Before finalizing any data model or generated code, verify:

### Model Completeness
- [ ] **All business questions** can be answered by the model
- [ ] **Unique node identification** is possible for all node types
- [ ] **Relationship types** are meaningful and specific
- [ ] **Critical queries** are optimized for indexed properties

### Naming Consistency
- [ ] **Node labels** use `CamelCase` (e.g., `Person`, `EmailAddress`)
- [ ] **Relationship types** use `ALL_CAPS_SNAKE_CASE` (e.g., `WORKS_AT`, `HAS_EMAIL`)
- [ ] **Properties** use `camelCase` (e.g., `firstName`, `createdAt`)
- [ ] **No symmetric relationships** (avoid bidirectional duplicates)

### Performance Optimization
- [ ] **Unique constraints** on identifier properties
- [ ] **Indexes** on frequently queried properties
- [ ] **Batch operations** use `UNWIND $batch` pattern
- [ ] **No supernodes** (high-degree nodes are distributed)
- [ ] **Queries anchor** on indexed properties

### Data Quality
- [ ] **Validation** before insertion (nulls, types, formats)
- [ ] **Deduplication** strategy defined
- [ ] **Null handling** for optional properties
- [ ] **Data cleaning** for format inconsistencies

### Testing
- [ ] **Representative data** used for testing
- [ ] **Query profiling** completed for critical paths
- [ ] **Edge cases** handled (nulls, duplicates, invalid data)
- [ ] **Performance benchmarks** meet requirements

---

## Integration with Code Generation

When generating `data_mapper.py` or other data loading scripts, apply these practices:

### 1. Naming Convention Enforcement
```python
# Validate naming in generated code
def validate_naming(node_label, rel_type, property_name):
    """Ensure naming follows Neo4j best practices."""
    assert node_label[0].isupper(), f"Node label must start with uppercase: {node_label}"
    assert "_" not in node_label, f"Node label must use CamelCase: {node_label}"

    assert rel_type.isupper(), f"Relationship type must be uppercase: {rel_type}"
    assert all(c.isalnum() or c == "_" for c in rel_type), f"Invalid relationship type: {rel_type}"

    assert property_name[0].islower(), f"Property must start with lowercase: {property_name}"
    assert "_" not in property_name, f"Property must use camelCase: {property_name}"
```

### 2. Constraint Creation First
```python
def create_constraints(query):
    """Create constraints before data loading."""
    constraints = [
        "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.customerId IS UNIQUE",
        "CREATE CONSTRAINT email_address_unique IF NOT EXISTS FOR (e:Email) REQUIRE e.address IS UNIQUE",
        "CREATE CONSTRAINT phone_number_unique IF NOT EXISTS FOR (p:Phone) REQUIRE p.phoneNumber IS UNIQUE"
    ]

    for constraint in constraints:
        query.run(constraint)
```

### 3. Batch Loading Pattern
```python
def load_nodes_in_batches(query, node_data, batch_size=1000):
    """Load nodes using UNWIND pattern with batching."""
    cypher = """
    UNWIND $batch AS row
    MERGE (c:Customer {customerId: row.customerId})
    SET c.firstName = row.firstName,
        c.lastName = row.lastName,
        c.email = row.email
    """

    for i in range(0, len(node_data), batch_size):
        batch = node_data[i:i + batch_size]
        query.run(cypher, {'batch': batch})
```

### 4. Data Validation
```python
def validate_customer_data(record):
    """Validate data before insertion."""
    if not record.get('customer_id'):
        return False, "Missing customer_id"

    email = record.get('email', '').strip()
    if email and '@' not in email:
        return False, f"Invalid email format: {email}"

    return True, None
```

---

## Key Takeaways

### Always Do
1. ✅ Use **CamelCase** for node labels
2. ✅ Use **UPPER_SNAKE_CASE** for relationship types
3. ✅ Use **camelCase** for properties
4. ✅ Create **unique constraints** before loading data
5. ✅ **Anchor queries** on indexed properties
6. ✅ Use **specific relationship types**
7. ✅ **Batch operations** with `UNWIND $batch`
8. ✅ **Profile queries** to identify bottlenecks
9. ✅ **Validate data** before insertion
10. ✅ **Prevent supernodes** with intermediate structures

### Never Do
1. ❌ Use inconsistent naming conventions
2. ❌ Create symmetric (bidirectional) relationships
3. ❌ Skip constraints on unique identifiers
4. ❌ Use generic relationship types (`RELATED_TO`)
5. ❌ Load data without batching (for large datasets)
6. ❌ Create nodes without validation
7. ❌ Allow supernode formation
8. ❌ Use foreign key properties instead of relationships
9. ❌ Skip query profiling for critical paths
10. ❌ Deploy without testing on representative data

---

## References

- **Source**: [Neo4j Data Model Best Practices](https://neo4j.com/developer/industry-use-cases/_attachments/neo4j_data_model_best_practices.txt)
- **Official Docs**: [Neo4j Data Modeling Guide](https://neo4j.com/docs/getting-started/data-modeling/)
- **Cypher Manual**: [Neo4j Cypher Documentation](https://neo4j.com/docs/cypher-manual/current/)

---

## See Also

- [generate_data_loader_code.md](../generate_data_loader_code.md) - Uses these best practices when generating code
- [analyze_data_quality.md](../analyze_data_quality.md) - Validates data before applying these patterns
- [AGENT.md](../../AGENT.md) - Overall toolkit guidance
