"""
Companies House Data Mapper - Neo4j Company Registry Graph

Purpose:
    Loads UK Companies House registry data into Neo4j. 
    Designed for the 2.6GB BasicCompanyData file with 5.7M company records.

Data Model:
    - Company (UK registered companies)
    - Address (registered office addresses)
    - Country (ISO country codes)
    - SICCode (Standard Industrial Classification codes)
    - PreviousName (company name history)

Performance Considerations:
    - Streams CSV file (never loads entire 2.6GB into memory)
    - Processes in configurable batch sizes
    - Creates constraints/indexes first for faster MERGE operations
    - Progress logging every 50,000 records
    - Estimated load time: 30-60 minutes depending on hardware

Usage:
    python3 workspace/generated/data_mapper.py

Requirements:
    - .env file with NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
    - Companies House CSV in workspace/raw_data/
"""

# =============================================================================
# PATH SETUP - Must come FIRST before any toolkit imports
# =============================================================================
import sys
from pathlib import Path

# Get project root (3 levels up from this script)
# workspace/generated/data_mapper.py -> workspace/generated/ -> workspace/ -> project_root/
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent.parent
sys.path.insert(0, str(project_root))

# =============================================================================
# IMPORTS
# =============================================================================
import csv
import re
from datetime import datetime

# Toolkit imports (after path setup)
from src.core.neo4j.version import get_query
from src.core.logger import log

# =============================================================================
# CONFIGURATION
# =============================================================================

# Batch sizes optimized for Companies House data
BATCH_SIZE = 2000  # Records per batch (tuned for this dataset)
LOG_INTERVAL = 50000  # Log progress every N records

# Data file path (relative to this script)
DATA_FILE = script_path.parent.parent / "raw_data" / "BasicCompanyDataAsOneFile-2025-12-01.csv"

# Country name to ISO code mapping
COUNTRY_CODES = {
    "united kingdom": "GB",
    "england": "GB",
    "wales": "GB",
    "scotland": "GB",
    "northern ireland": "GB",
    "great britain": "GB",
    "uk": "GB",
    "united states": "US",
    "usa": "US",
    "ireland": "IE",
    "france": "FR",
    "germany": "DE",
    "netherlands": "NL",
    "belgium": "BE",
    "spain": "ES",
    "italy": "IT",
    "portugal": "PT",
    "switzerland": "CH",
    "austria": "AT",
    "sweden": "SE",
    "norway": "NO",
    "denmark": "DK",
    "finland": "FI",
    "poland": "PL",
    "czech republic": "CZ",
    "hungary": "HU",
    "romania": "RO",
    "bulgaria": "BG",
    "greece": "GR",
    "cyprus": "CY",
    "malta": "MT",
    "luxembourg": "LU",
    "jersey": "JE",
    "guernsey": "GG",
    "isle of man": "IM",
    "gibraltar": "GI",
    "virgin islands, british": "VG",
    "cayman islands": "KY",
    "bermuda": "BM",
    "bahamas": "BS",
    "hong kong": "HK",
    "singapore": "SG",
    "australia": "AU",
    "new zealand": "NZ",
    "canada": "CA",
    "india": "IN",
    "china": "CN",
    "japan": "JP",
    "south africa": "ZA",
    "united arab emirates": "AE",
    "israel": "IL",
    "russia": "RU",
    "ukraine": "UA",
    "brazil": "BR",
    "mexico": "MX",
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def parse_date(date_str):
    """
    Parse UK date format (DD/MM/YYYY) to ISO format (YYYY-MM-DD).
    Returns None if date is empty or invalid.
    """
    if not date_str or not date_str.strip():
        return None
    try:
        dt = datetime.strptime(date_str.strip(), "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_sic_code(sic_text):
    """
    Parse SIC code text like "68209 - Other letting and operating..."
    Returns tuple of (code, description) or (None, None) if invalid.
    """
    if not sic_text or not sic_text.strip():
        return None, None

    sic_text = sic_text.strip()

    # Handle special cases
    if sic_text.lower() in ("none supplied", "none", ""):
        return None, None

    # Try to parse "CODE - Description" format
    match = re.match(r"^(\d+)\s*-\s*(.+)$", sic_text)
    if match:
        return match.group(1), match.group(2).strip()

    # Handle codes without description (just numbers)
    if sic_text.isdigit():
        return sic_text, None

    return None, None


def get_country_code(country_name):
    """
    Get ISO country code from country name.
    Returns the code or the original name if not found.
    """
    if not country_name:
        return None
    lookup = country_name.strip().lower()
    return COUNTRY_CODES.get(lookup, country_name.upper()[:2])


def clean_string(value):
    """Clean and normalize string values."""
    if not value:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def stream_csv(file_path, skip_header=True):
    """
    Generator that streams CSV rows one at a time.
    Never loads entire file into memory.
    
    IMPORTANT: Strips whitespace from column names to handle
    Companies House CSV quirk where some columns have leading spaces.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Strip whitespace from keys (Companies House has ' CompanyNumber' etc.)
            cleaned_row = {k.strip(): v for k, v in row.items()}
            yield cleaned_row


def count_rows(file_path):
    """Count total rows in file (for progress calculation)."""
    log.info(f"Counting rows in {file_path.name}...")
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        count = sum(1 for _ in f) - 1  # Subtract header
    log.info(f"Total rows: {count:,}")
    return count


def batch_generator(iterable, batch_size):
    """
    Yield batches of items from an iterable.
    Works with generators (doesn't load all into memory).
    """
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


# =============================================================================
# SCHEMA SETUP
# =============================================================================

def create_constraints_and_indexes(query):
    """
    Create constraints and indexes for efficient loading.
    Run ONCE before loading data.
    """
    log.info("Creating constraints and indexes...")

    constraints = [
        # Company - unique by company number
        """
        CREATE CONSTRAINT company_number IF NOT EXISTS
        FOR (c:Company) REQUIRE c.companyNumber IS UNIQUE
        """,
        # Address - composite key
        """
        CREATE CONSTRAINT address_composite IF NOT EXISTS
        FOR (a:Address) REQUIRE (a.addressLine1, a.postTown, a.postCode) IS NODE KEY
        """,
        # Country - unique by name (as it appears in the data)
        """
        CREATE CONSTRAINT country_name IF NOT EXISTS
        FOR (c:Country) REQUIRE c.name IS UNIQUE
        """,
        # SICCode - unique by code
        """
        CREATE CONSTRAINT sic_code IF NOT EXISTS
        FOR (s:SICCode) REQUIRE s.code IS UNIQUE
        """,
        # PreviousName - composite key (company + name + sequence is unique)
        """
        CREATE CONSTRAINT previous_name_composite IF NOT EXISTS
        FOR (pn:PreviousName) REQUIRE (pn.companyNumber, pn.name, pn.sequence) IS NODE KEY
        """,
    ]

    indexes = [
        # Company indexes for common queries
        "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name)",
        "CREATE INDEX company_status IF NOT EXISTS FOR (c:Company) ON (c.status)",
        "CREATE INDEX company_category IF NOT EXISTS FOR (c:Company) ON (c.category)",
        # Address indexes
        "CREATE INDEX address_postcode IF NOT EXISTS FOR (a:Address) ON (a.postCode)",
        "CREATE INDEX address_posttown IF NOT EXISTS FOR (a:Address) ON (a.postTown)",
    ]

    for constraint in constraints:
        try:
            query.run(constraint)
        except Exception as e:
            if "already exists" not in str(e).lower():
                log.warning(f"Constraint creation note: {e}")

    for index in indexes:
        try:
            query.run(index)
        except Exception as e:
            if "already exists" not in str(e).lower():
                log.warning(f"Index creation note: {e}")

    log.info("✓ Constraints and indexes created")


# =============================================================================
# LOOKUP TABLE LOADERS (Run first - small datasets)
# =============================================================================

def extract_and_create_country_nodes(query, total_rows):
    """
    Extract unique countries from data and create Country lookup nodes.
    Extracts from both CountryOfOrigin and RegAddress.Country fields.
    """
    log.info("Extracting unique countries from data...")

    countries = set()

    for i, row in enumerate(stream_csv(DATA_FILE)):
        # Extract from both country fields
        country_of_origin = clean_string(row.get("CountryOfOrigin", ""))
        address_country = clean_string(row.get("RegAddress.Country", ""))

        if country_of_origin:
            countries.add(country_of_origin)
        if address_country:
            countries.add(address_country)

        # Progress logging
        if (i + 1) % LOG_INTERVAL == 0:
            log.info(f"  Country scan: {i + 1:,} / {total_rows:,} ({(i + 1) / total_rows * 100:.1f}%)")

    log.info(f"Found {len(countries)} unique countries")

    # Create Country nodes with name and derived ISO code
    log.info("Creating Country nodes...")

    country_data = []
    for name in countries:
        code = get_country_code(name)
        country_data.append({"name": name, "code": code})

    cypher = """
    UNWIND $batch AS row
    MERGE (c:Country {name: row.name})
    SET c.code = row.code
    """

    query.run(cypher, {"batch": country_data})
    log.info(f"✓ Created {len(country_data)} Country nodes")


def extract_and_create_sic_codes(query, total_rows):
    """
    First pass: Extract unique SIC codes and create lookup nodes.
    Uses stream_csv which strips whitespace from column names.
    """
    log.info("Extracting unique SIC codes (first pass)...")

    sic_codes = {}  # code -> description

    for i, row in enumerate(stream_csv(DATA_FILE)):
        # Extract SIC codes from all 4 columns (column names already stripped by stream_csv)
        for sic_col in ["SICCode.SicText_1", "SICCode.SicText_2",
                        "SICCode.SicText_3", "SICCode.SicText_4"]:
            code, desc = parse_sic_code(row.get(sic_col, ""))
            if code and code not in sic_codes:
                sic_codes[code] = desc

        # Progress logging
        if (i + 1) % LOG_INTERVAL == 0:
            log.info(f"  SIC scan progress: {i + 1:,} / {total_rows:,} ({(i + 1) / total_rows * 100:.1f}%)")

    log.info(f"Found {len(sic_codes):,} unique SIC codes")

    # Create SICCode nodes
    log.info("Creating SICCode lookup nodes...")

    sic_data = [
        {"code": code, "description": desc}
        for code, desc in sic_codes.items()
    ]

    cypher = """
    UNWIND $batch AS row
    MERGE (s:SICCode {code: row.code})
    SET s.description = row.description
    """

    for batch in batch_generator(sic_data, BATCH_SIZE):
        query.run(cypher, {"batch": batch})

    log.info(f"✓ Created {len(sic_codes):,} SICCode nodes")
    return sic_codes


# =============================================================================
# MAIN DATA LOADERS (Large datasets - stream and batch)
# =============================================================================

def create_company_nodes(query, total_rows):
    """
    Create Company nodes from CSV.
    Streams data and processes in batches.
    
    Defensive handling: Skips rows with null/empty CompanyNumber.
    """
    log.info("Creating Company nodes...")

    cypher = """
    UNWIND $batch AS row
    MERGE (c:Company {companyNumber: row.companyNumber})
    SET c.name = row.name,
        c.category = row.category,
        c.status = row.status,
        c.countryOfOrigin = row.countryOfOrigin,
        c.incorporationDate = CASE WHEN row.incorporationDate IS NOT NULL
                              THEN date(row.incorporationDate) ELSE NULL END,
        c.dissolutionDate = CASE WHEN row.dissolutionDate IS NOT NULL
                            THEN date(row.dissolutionDate) ELSE NULL END,
        c.uri = row.uri,
        c.accountRefDay = row.accountRefDay,
        c.accountRefMonth = row.accountRefMonth,
        c.accountsCategory = row.accountsCategory,
        c.numMortCharges = toInteger(row.numMortCharges),
        c.numMortOutstanding = toInteger(row.numMortOutstanding),
        c.numMortSatisfied = toInteger(row.numMortSatisfied),
        c.numGenPartners = toInteger(row.numGenPartners),
        c.numLimPartners = toInteger(row.numLimPartners)
    """

    processed = 0
    skipped = 0
    
    for batch_rows in batch_generator(stream_csv(DATA_FILE), BATCH_SIZE):
        batch_data = []
        for row in batch_rows:
            # DEFENSIVE: Skip rows with null/empty CompanyNumber (required for MERGE)
            company_number = clean_string(row.get("CompanyNumber", ""))
            if not company_number:
                skipped += 1
                continue
                
            batch_data.append({
                "companyNumber": company_number,
                "name": clean_string(row.get("CompanyName", "")),
                "category": clean_string(row.get("CompanyCategory", "")),
                "status": clean_string(row.get("CompanyStatus", "")),
                "countryOfOrigin": clean_string(row.get("CountryOfOrigin", "")),
                "incorporationDate": parse_date(row.get("IncorporationDate", "")),
                "dissolutionDate": parse_date(row.get("DissolutionDate", "")),
                "uri": clean_string(row.get("URI", "")),
                "accountRefDay": clean_string(row.get("Accounts.AccountRefDay", "")),
                "accountRefMonth": clean_string(row.get("Accounts.AccountRefMonth", "")),
                "accountsCategory": clean_string(row.get("Accounts.AccountCategory", "")),
                "numMortCharges": row.get("Mortgages.NumMortCharges", "0") or "0",
                "numMortOutstanding": row.get("Mortgages.NumMortOutstanding", "0") or "0",
                "numMortSatisfied": row.get("Mortgages.NumMortSatisfied", "0") or "0",
                "numGenPartners": row.get("LimitedPartnerships.NumGenPartners", "0") or "0",
                "numLimPartners": row.get("LimitedPartnerships.NumLimPartners", "0") or "0",
            })

        if batch_data:
            query.run(cypher, {"batch": batch_data})

        processed += len(batch_data)
        if (processed + skipped) % LOG_INTERVAL == 0 or (processed + skipped) >= total_rows:
            log.info(f"  Company nodes: {processed:,} / {total_rows:,} ({processed / total_rows * 100:.1f}%)")

    if skipped > 0:
        log.warning(f"  Skipped {skipped:,} rows with null/empty CompanyNumber")
    log.info(f"✓ Created {processed:,} Company nodes")


def create_address_nodes_and_relationships(query, total_rows):
    """
    Create Address nodes and HAS_ADDRESS relationships.
    Uses composite key for address deduplication.
    
    Defensive handling: Skips rows with null address fields or null CompanyNumber.
    """
    log.info("Creating Address nodes and HAS_ADDRESS relationships...")

    # First create unique addresses, then create relationships
    cypher_address = """
    UNWIND $batch AS row
    MERGE (a:Address {
        addressLine1: row.addressLine1,
        postTown: row.postTown,
        postCode: row.postCode
    })
    SET a.addressLine2 = row.addressLine2,
        a.county = row.county,
        a.country = row.country,
        a.careOf = row.careOf,
        a.poBox = row.poBox
    """

    cypher_rel = """
    UNWIND $batch AS row
    MATCH (c:Company {companyNumber: row.companyNumber})
    MATCH (a:Address {
        addressLine1: row.addressLine1,
        postTown: row.postTown,
        postCode: row.postCode
    })
    MERGE (c)-[:HAS_ADDRESS {isCurrent: true}]->(a)
    """

    processed = 0
    skipped_address = 0
    skipped_company = 0
    
    for batch_rows in batch_generator(stream_csv(DATA_FILE), BATCH_SIZE):
        batch_data = []
        for row in batch_rows:
            # DEFENSIVE: Check CompanyNumber first
            company_number = clean_string(row.get("CompanyNumber", ""))
            if not company_number:
                skipped_company += 1
                continue
            
            addr_line1 = clean_string(row.get("RegAddress.AddressLine1", ""))
            post_town = clean_string(row.get("RegAddress.PostTown", ""))
            post_code = clean_string(row.get("RegAddress.PostCode", ""))

            # DEFENSIVE: Skip if missing required address fields
            if not addr_line1 or not post_town or not post_code:
                skipped_address += 1
                continue

            batch_data.append({
                "companyNumber": company_number,
                "addressLine1": addr_line1,
                "addressLine2": clean_string(row.get("RegAddress.AddressLine2", "")),
                "postTown": post_town,
                "county": clean_string(row.get("RegAddress.County", "")),
                "country": clean_string(row.get("RegAddress.Country", "")),
                "postCode": post_code,
                "careOf": clean_string(row.get("RegAddress.CareOf", "")),
                "poBox": clean_string(row.get("RegAddress.POBox", "")),
            })

        if batch_data:
            # Create address nodes
            query.run(cypher_address, {"batch": batch_data})
            # Create relationships
            query.run(cypher_rel, {"batch": batch_data})

        processed += len(batch_data)
        total_seen = processed + skipped_address + skipped_company
        if total_seen % LOG_INTERVAL == 0 or total_seen >= total_rows:
            log.info(f"  Address nodes: {processed:,} / {total_rows:,} ({total_seen / total_rows * 100:.1f}%)")

    if skipped_address > 0:
        log.warning(f"  Skipped {skipped_address:,} rows with incomplete address")
    if skipped_company > 0:
        log.warning(f"  Skipped {skipped_company:,} rows with null CompanyNumber")
    log.info(f"✓ Created {processed:,} Address nodes and HAS_ADDRESS relationships")


def create_address_country_relationships(query):
    """
    Create LOCATED_IN relationships from Address to Country.
    Matches on country name extracted from the data.
    """
    log.info("Creating Address->Country LOCATED_IN relationships...")

    cypher = """
    MATCH (a:Address)
    WHERE a.country IS NOT NULL AND a.country <> ''
    MATCH (c:Country {name: a.country})
    MERGE (a)-[:LOCATED_IN]->(c)
    """

    query.run(cypher)
    log.info("✓ Created Address->Country relationships")


def create_company_sic_relationships(query, total_rows):
    """
    Create CLASSIFIED_AS relationships between Company and SICCode.
    
    Defensive handling: Skips rows with null CompanyNumber.
    """
    log.info("Creating Company->SICCode CLASSIFIED_AS relationships...")

    cypher = """
    UNWIND $batch AS row
    MATCH (c:Company {companyNumber: row.companyNumber})
    MATCH (s:SICCode {code: row.sicCode})
    MERGE (c)-[:CLASSIFIED_AS {rank: row.rank}]->(s)
    """

    processed = 0
    skipped = 0
    
    for batch_rows in batch_generator(stream_csv(DATA_FILE), BATCH_SIZE):
        batch_data = []
        rows_processed_in_batch = 0
        for row in batch_rows:
            company_number = clean_string(row.get("CompanyNumber", ""))
            
            # DEFENSIVE: Skip rows with null CompanyNumber
            if not company_number:
                skipped += 1
                continue

            rows_processed_in_batch += 1
            # Check all 4 SIC code columns
            for rank, sic_col in enumerate([
                "SICCode.SicText_1", "SICCode.SicText_2",
                "SICCode.SicText_3", "SICCode.SicText_4"
            ], start=1):
                code, _ = parse_sic_code(row.get(sic_col, ""))
                if code:
                    batch_data.append({
                        "companyNumber": company_number,
                        "sicCode": code,
                        "rank": rank,
                    })

        if batch_data:
            query.run(cypher, {"batch": batch_data})

        processed += rows_processed_in_batch
        total_seen = processed + skipped
        if total_seen % LOG_INTERVAL == 0 or total_seen >= total_rows:
            log.info(f"  SIC relationships: {total_seen:,} / {total_rows:,} ({total_seen / total_rows * 100:.1f}%)")

    if skipped > 0:
        log.warning(f"  Skipped {skipped:,} rows with null CompanyNumber")
    log.info(f"✓ Created SIC relationships for {processed:,} companies")


def create_previous_name_nodes_and_relationships(query, total_rows):
    """
    Create PreviousName nodes and PREVIOUSLY_NAMED relationships.
    Handles up to 10 previous names per company.
    
    Defensive handling: Skips rows with null CompanyNumber or null previous name.
    """
    log.info("Creating PreviousName nodes and relationships...")

    cypher = """
    UNWIND $batch AS row
    MATCH (c:Company {companyNumber: row.companyNumber})
    MERGE (pn:PreviousName {
        companyNumber: row.companyNumber,
        name: row.previousName,
        sequence: row.sequence
    })
    SET pn.changeDate = CASE WHEN row.changeDate IS NOT NULL
                        THEN date(row.changeDate) ELSE NULL END
    MERGE (c)-[:PREVIOUSLY_NAMED {
        changeDate: CASE WHEN row.changeDate IS NOT NULL
                    THEN date(row.changeDate) ELSE NULL END,
        sequence: row.sequence
    }]->(pn)
    """

    processed = 0
    names_created = 0
    skipped = 0

    for batch_rows in batch_generator(stream_csv(DATA_FILE), BATCH_SIZE):
        batch_data = []
        rows_processed_in_batch = 0
        for row in batch_rows:
            company_number = clean_string(row.get("CompanyNumber", ""))
            
            # DEFENSIVE: Skip rows with null CompanyNumber
            if not company_number:
                skipped += 1
                continue

            rows_processed_in_batch += 1
            # Check all 10 previous name columns
            for seq in range(1, 11):
                name_col = f"PreviousName_{seq}.CompanyName"
                date_col = f"PreviousName_{seq}.CONDATE"

                prev_name = clean_string(row.get(name_col, ""))
                change_date = parse_date(row.get(date_col, ""))

                if prev_name:
                    batch_data.append({
                        "companyNumber": company_number,
                        "previousName": prev_name,
                        "changeDate": change_date,
                        "sequence": seq,
                    })
                    names_created += 1

        if batch_data:
            query.run(cypher, {"batch": batch_data})

        processed += rows_processed_in_batch
        total_seen = processed + skipped
        if total_seen % LOG_INTERVAL == 0 or total_seen >= total_rows:
            log.info(f"  Previous names: {total_seen:,} / {total_rows:,} ({total_seen / total_rows * 100:.1f}%)")

    if skipped > 0:
        log.warning(f"  Skipped {skipped:,} rows with null CompanyNumber")
    log.info(f"✓ Created {names_created:,} PreviousName nodes and relationships")


# =============================================================================
# VERIFICATION
# =============================================================================

def verify_load(query):
    """
    Verify data was loaded correctly by counting nodes and relationships.
    """
    log.info("Verifying data load...")

    counts = [
        ("Company", "MATCH (n:Company) RETURN count(n) as count"),
        ("Address", "MATCH (n:Address) RETURN count(n) as count"),
        ("Country", "MATCH (n:Country) RETURN count(n) as count"),
        ("SICCode", "MATCH (n:SICCode) RETURN count(n) as count"),
        ("PreviousName", "MATCH (n:PreviousName) RETURN count(n) as count"),
        ("HAS_ADDRESS", "MATCH ()-[r:HAS_ADDRESS]->() RETURN count(r) as count"),
        ("LOCATED_IN", "MATCH ()-[r:LOCATED_IN]->() RETURN count(r) as count"),
        ("CLASSIFIED_AS", "MATCH ()-[r:CLASSIFIED_AS]->() RETURN count(r) as count"),
        ("PREVIOUSLY_NAMED", "MATCH ()-[r:PREVIOUSLY_NAMED]->() RETURN count(r) as count"),
    ]

    log.info("\n" + "=" * 50)
    log.info("LOAD SUMMARY")
    log.info("=" * 50)

    for label, cypher in counts:
        result = query.run(cypher)
        count = result[0]["count"]
        log.info(f"  {label:20} : {count:>12,}")

    log.info("=" * 50 + "\n")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """
    Main execution function - orchestrates the entire data loading process.
    """
    log.info("=" * 60)
    log.info("COMPANIES HOUSE DATA LOADER")
    log.info("UK Company Registry Graph")
    log.info("=" * 60)

    # Verify data file exists
    if not DATA_FILE.exists():
        log.error(f"Data file not found: {DATA_FILE}")
        log.error("Please ensure BasicCompanyDataAsOneFile-*.csv is in workspace/raw_data/")
        return

    log.info(f"Data file: {DATA_FILE.name}")
    log.info(f"File size: {DATA_FILE.stat().st_size / (1024 ** 3):.2f} GB")

    # Count rows for progress tracking
    total_rows = count_rows(DATA_FILE)

    # Initialize query runner (set to None for safe cleanup in finally block)
    query = None

    try:
        # Get query runner
        query = get_query()

        # Phase 1: Schema setup
        log.info("\n--- PHASE 1: Schema Setup ---")
        create_constraints_and_indexes(query)

        # Phase 2: Lookup tables (small, run first)
        log.info("\n--- PHASE 2: Lookup Tables ---")
        extract_and_create_country_nodes(query, total_rows)
        extract_and_create_sic_codes(query, total_rows)

        # Phase 3: Main data (large, stream and batch)
        log.info("\n--- PHASE 3: Company Data ---")
        create_company_nodes(query, total_rows)

        # Phase 4: Address data
        log.info("\n--- PHASE 4: Address Data ---")
        create_address_nodes_and_relationships(query, total_rows)
        create_address_country_relationships(query)

        # Phase 5: Relationships
        log.info("\n--- PHASE 5: Industry Classification ---")
        create_company_sic_relationships(query, total_rows)

        # Phase 6: Name history
        log.info("\n--- PHASE 6: Name History ---")
        create_previous_name_nodes_and_relationships(query, total_rows)

        # Verification
        log.info("\n--- VERIFICATION ---")
        verify_load(query)

        log.info("✅ Data load complete!")

    except Exception as e:
        log.error(f"Load failed: {e}")
        raise

    finally:
        # Always close connection if it was established
        if query is not None:
            query.close()


if __name__ == "__main__":
    main()
