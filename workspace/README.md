# UK Companies House → Neo4j Pipeline

This workspace contains a complete pipeline for downloading UK Companies House data and loading it into Neo4j as a graph database.

## What's Included

| Component | Path | Purpose |
|-----------|------|---------|
| **Downloader** | `scripts/download_companies_house.py` | Downloads Companies House data |
| **Data Mapper** | `generated/data_mapper.py` | Loads CSV into Neo4j |
| **Raw Data** | `raw_data/` | Where the CSV file lives |

---

## Quick Start (5 minutes to graph)

### 1. Configure Neo4j Connection

Create a `.env` file in the project root with your Neo4j credentials:

```bash
# .env (in project root, not workspace/)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

### 2. Download the Data

```bash
python3 workspace/scripts/download_companies_house.py
```

This downloads ~470MB ZIP, extracts to ~2.6GB CSV, and renames it to `BasicCompanyData.csv`.

### 3. Load into Neo4j

```bash
python3 workspace/generated/data_mapper.py
```

This creates ~5.7M Company nodes, Addresses, SIC codes, and name history.

---

## The Data

### Source: Companies House Free Company Data Product

- **URL**: https://download.companieshouse.gov.uk/en_output.html
- **Updated**: Monthly (within 5 working days of month end)
- **Size**: ~470MB compressed, ~2.6GB uncompressed
- **Records**: ~5.7 million UK registered companies

### What's in the Data

| Field | Description |
|-------|-------------|
| CompanyNumber | Unique identifier (e.g., "12345678") |
| CompanyName | Legal name of the company |
| CompanyStatus | Active, Dissolved, Liquidation, etc. |
| CompanyCategory | Private Limited, PLC, LLP, etc. |
| IncorporationDate | When the company was registered |
| RegAddress.* | Registered office address fields |
| SICCode.* | Up to 4 industry classification codes |
| PreviousName_*.* | Up to 10 historical company names |

---

## The Graph Model

```
(:Company {companyNumber, name, status, category, ...})
    -[:HAS_ADDRESS]-> (:Address {addressLine1, postTown, postCode, ...})
    -[:CLASSIFIED_AS]-> (:SICCode {code, description})
    -[:PREVIOUSLY_NAMED]-> (:PreviousName {name, changeDate})

(:Address)-[:LOCATED_IN]->(:Country {name, code})
```

### Node Counts (approximate)

| Label | Count |
|-------|-------|
| Company | ~5.7M |
| Address | ~4.5M |
| SICCode | ~800 |
| Country | ~100 |
| PreviousName | ~2M |

---

## Download Script

### Basic Usage

```bash
# Download latest available file (auto-detects date)
python3 workspace/scripts/download_companies_house.py

# List available files (past 12 months)
python3 workspace/scripts/download_companies_house.py --list

# Download specific month
python3 workspace/scripts/download_companies_house.py --date 2025-12-01

# Keep the ZIP file after extraction
python3 workspace/scripts/download_companies_house.py --keep-zip
```

### How It Works

1. Constructs URL: `https://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-YYYY-MM-01.zip`
2. Downloads the ZIP file (~470MB, shows progress)
3. Extracts the CSV (~2.6GB)
4. Renames to `BasicCompanyData.csv` (generic name for the data mapper)
5. Cleans up the ZIP file

### Output

```
============================================================
COMPANIES HOUSE DATA DOWNLOADER
============================================================

Source: https://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-2025-12-01.zip
Output: /path/to/workspace/raw_data/BasicCompanyData.csv

Checking file availability...
✓ File available: 469.0 MB

Downloading BasicCompanyDataAsOneFile-2025-12-01.zip...
  Downloading: 469.0 MB / 469.0 MB (100.0%)
✓ Downloaded: 469.0 MB

Extracting...
  Extracting: BasicCompanyDataAsOneFile-2025-12-01.csv
✓ Extracted: BasicCompanyDataAsOneFile-2025-12-01.csv (2.6 GB)

Renaming to generic filename...
✓ Renamed: BasicCompanyDataAsOneFile-2025-12-01.csv → BasicCompanyData.csv

✅ DOWNLOAD COMPLETE
```

---

## Data Mapper Script

### Basic Usage

```bash
# Run all phases
python3 workspace/generated/data_mapper.py

# List available phases
python3 workspace/generated/data_mapper.py --list

# Run specific phase(s)
python3 workspace/generated/data_mapper.py --phase 6         # Name history only
python3 workspace/generated/data_mapper.py --phase 4 5 6     # Multiple phases

# Skip row counting (faster startup)
python3 workspace/generated/data_mapper.py --skip-row-count
```

### Phases

| Phase | Name | Description | Time |
|-------|------|-------------|------|
| 1 | Schema | Create constraints and indexes | ~5 sec |
| 2 | Lookup Tables | Country and SICCode nodes | ~3 min |
| 3 | Companies | Company nodes (5.7M) | ~15 min |
| 4 | Addresses | Address nodes + relationships | ~20 min |
| 5 | SIC Relationships | Company→SICCode links | ~15 min |
| 6 | Name History | PreviousName nodes + relationships | ~30 min |
| 7 | Verification | Count nodes and relationships | ~10 sec |

**Total estimated time: 60-90 minutes** (depends on hardware)

### Key Features

- **Streaming**: Never loads the entire 2.6GB file into memory
- **Batching**: Processes in batches of 2,000 records
- **Progress logging**: Updates every 50,000 records
- **Defensive**: Handles null values, missing fields, malformed data
- **Resumable**: Run individual phases if one fails

### Output

```
============================================================
COMPANIES HOUSE DATA LOADER
============================================================

Data file: BasicCompanyData.csv
File size: 2.56 GB
Phases to run: [1, 2, 3, 4, 5, 6, 7]
Total rows: 5,685,825

--- PHASE 1: Schema ---
Creating constraints and indexes...
✓ Constraints and indexes created

--- PHASE 3: Companies ---
Creating Company nodes...
  Company nodes: 50,000 / 5,685,825 (0.9%)
  Company nodes: 100,000 / 5,685,825 (1.8%)
  ...
✓ Created 5,685,825 Company nodes

--- VERIFICATION ---
==================================================
LOAD SUMMARY
==================================================
  Company              :    5,685,825
  Address              :    4,523,419
  Country              :          102
  SICCode              :          809
  PreviousName         :    2,134,567
  HAS_ADDRESS          :    4,523,419
  LOCATED_IN           :    4,102,876
  CLASSIFIED_AS        :    7,891,234
  PREVIOUSLY_NAMED     :    2,134,567
==================================================

✅ Data load complete!
```

---

## Troubleshooting

### "Data file not found"

Make sure you've run the download script first:

```bash
python3 workspace/scripts/download_companies_house.py
```

### "Cannot connect to Neo4j"

Check your `.env` file in the project root:

```bash
cat .env
# Should show NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
```

Test connection:

```bash
python3 cli.py neo4j-test
```

### Load is too slow

1. **Add indexes first**: Run phase 1 before other phases
   ```bash
   python3 workspace/generated/data_mapper.py --phase 1
   ```

2. **Increase Neo4j heap**: Edit `neo4j.conf`:
   ```
   server.memory.heap.initial_size=2g
   server.memory.heap.max_size=4g
   ```

3. **Skip row counting**: Faster startup
   ```bash
   python3 workspace/generated/data_mapper.py --skip-row-count
   ```

### Phase failed - how to resume

Just run the failed phase and later ones:

```bash
# If phase 5 failed, run 5, 6, 7
python3 workspace/generated/data_mapper.py --phase 5 6 7
```

---

## Folder Structure

```
workspace/
├── README.md                 # This file
├── raw_data/
│   └── BasicCompanyData.csv  # Downloaded data (2.6GB, gitignored)
├── scripts/
│   └── download_companies_house.py
└── generated/
    └── data_mapper.py
```

---

## Example Queries

Once loaded, try these Cypher queries in Neo4j Browser:

### Find a company

```cypher
MATCH (c:Company {companyNumber: '00000006'})
RETURN c
```

### Companies at same address

```cypher
MATCH (a:Address)<-[:HAS_ADDRESS]-(c:Company)
WHERE a.postCode = 'EC2M 4YF'
RETURN a, collect(c.name) as companies
LIMIT 10
```

### Industry classification

```cypher
MATCH (c:Company)-[:CLASSIFIED_AS]->(s:SICCode)
WHERE s.code = '62012'
RETURN s.description, count(c) as companies
```

### Name changes

```cypher
MATCH (c:Company)-[:PREVIOUSLY_NAMED]->(pn:PreviousName)
WHERE c.name CONTAINS 'GOOGLE'
RETURN c.name, collect(pn.name) as previousNames
```

---

## License & Attribution

- **Data Source**: [Companies House](https://download.companieshouse.gov.uk/en_output.html)
- **Data License**: Open Government Licence (OGL)
- **Attribution**: Contains public sector information licensed under the Open Government Licence v3.0
