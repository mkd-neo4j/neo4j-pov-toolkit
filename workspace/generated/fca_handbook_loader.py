"""
FCA Handbook Data Loader (API-Based)

Purpose:
    Fetches UK Financial Conduct Authority (FCA) Handbook content via the FCA REST API
    and loads it into Neo4j as a hierarchical graph structure.

Architecture:
    This script operates in three phases:
    1. Fetch: Retrieves JSON data from FCA REST API
    2. Transform: Extracts provisions, sections, and relationships
    3. Load: Batches data and loads into Neo4j using MERGE operations

Graph Model:
    (:Chapter) nodes with properties:
        - chapterId: Unique identifier (e.g., "prin1")
        - chapterName: Chapter name (e.g., "PRIN 1 Application and Purpose")
        - lastModifiedDate: Last modification date
        - nextChapterId: Link to next chapter
        - previousChapterId: Link to previous chapter

    (:Section) nodes with properties:
        - sectionId: Unique identifier (e.g., "prin1s1")
        - sectionName: Section name (e.g., "PRIN 1.1 Application")
        - sectionHeader: Optional header content
        - sectionFooter: Optional footer content

    (:Provision) nodes with properties:
        - provisionId: Unique identifier (e.g., 99575)
        - entityId: Entity identifier (e.g., "prin2-prin2s1-p16")
        - provisionName: Provision name (e.g., "PRIN 2.1.1")
        - provisionType: Type (e.g., "Rules", "Guidance")
        - contentText: Plain text content
        - contentType: HTML content
        - timeline: Last modified date

    (:GlossaryTerm) nodes with properties:
        - termId: Unique identifier (e.g., "G430")
        - name: Term name (e.g., "firm")
        - link: Glossary link

    Relationships:
        - (:Chapter)-[:HAS_SECTION]->(:Section)
        - (:Section)-[:HAS_PROVISION]->(:Provision)
        - (:Provision)-[:DEFINES]->(:GlossaryTerm)
        - (:Chapter)-[:NEXT]->(:Chapter)
        - (:Chapter)-[:PREVIOUS]->(:Chapter)

Usage:
    # Load all chapters for a handbook (e.g., PRIN)
    python workspace/generated/fca_handbook_loader.py --handbook prin

    # Load specific chapters
    python workspace/generated/fca_handbook_loader.py --chapters prin1 prin2 prin3

    # Validate without loading
    python workspace/generated/fca_handbook_loader.py --handbook prin --validate-only

Requirements:
    - Neo4j connection configured in .env file
    - Dependencies: requests, neo4j
"""

import sys
import os
import argparse
import hashlib
from typing import Dict, List, Optional
import requests

# Add project root to path so we can import toolkit modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.neo4j.query import Neo4jQuery
from src.core.logger import log

# Constants
API_BASE_URL = "https://api-handbook.fca.org.uk/Handbook"
CHAPTER_ENDPOINT = "/GetAllHandBookProvisionsSortedOrderByChapter"
ALL_HANDBOOKS_ENDPOINT = "/GetAllHandbook"


class FCAHandbookAPILoader:
    """
    Fetches and loads FCA Handbook content from REST API into Neo4j

    This class handles the complete workflow of fetching JSON from the FCA API,
    transforming it, and loading into Neo4j.
    """

    def __init__(self, batch_size: int = 1000, validate_only: bool = False):
        """
        Initialize the loader

        Args:
            batch_size: Number of items to batch before loading to Neo4j
            validate_only: If True, validate data but don't load to Neo4j
        """
        self.batch_size = batch_size
        self.validate_only = validate_only

        # Initialize Neo4j connection unless in validate-only mode
        if not validate_only:
            self.query = Neo4jQuery()
            self._setup_constraints()

    def _setup_constraints(self):
        """Create Neo4j constraints for data integrity"""
        log.info("Setting up Neo4j constraints...")

        constraints = [
            "CREATE CONSTRAINT chapter_id_unique IF NOT EXISTS FOR (c:Chapter) REQUIRE c.chapterId IS UNIQUE",
            "CREATE CONSTRAINT section_id_unique IF NOT EXISTS FOR (s:Section) REQUIRE s.sectionId IS UNIQUE",
            "CREATE CONSTRAINT provision_id_unique IF NOT EXISTS FOR (p:Provision) REQUIRE p.provisionId IS UNIQUE",
            "CREATE CONSTRAINT term_id_unique IF NOT EXISTS FOR (t:GlossaryTerm) REQUIRE t.termId IS UNIQUE"
        ]

        for constraint in constraints:
            try:
                self.query.run(constraint)
            except Exception as e:
                log.warning(f"Constraint may already exist: {e}")

        log.info("Constraints configured")

    @staticmethod
    def get_all_handbooks() -> Dict[str, str]:
        """
        Fetch all available handbooks from the FCA API

        Returns:
            Dictionary mapping handbook codes (lowercase) to full names
        """
        try:
            url = f"{API_BASE_URL}{ALL_HANDBOOKS_ENDPOINT}"
            params = {'Date': '31-07-2023'}  # Use a stable date for consistency

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not data.get('Success'):
                log.error(f"Failed to fetch handbooks: {data.get('Error')}")
                return {}

            result = data.get('Result', {})
            headers = result.get('headers', [])

            handbooks = {}
            for header in headers:
                for part in header.get('parts', []):
                    code = part.get('contains')
                    name = part.get('name')
                    if code:
                        handbooks[code.lower()] = name

            log.info(f"Discovered {len(handbooks)} available handbooks from API")
            return handbooks

        except Exception as e:
            log.error(f"Failed to fetch handbooks list: {e}")
            return {}

    def fetch_chapter_data(self, chapter_id: str) -> Optional[Dict]:
        """
        Fetch chapter data from FCA API

        Args:
            chapter_id: Chapter identifier (e.g., "prin1", "prin2")

        Returns:
            Dictionary with chapter data, or None on error
        """
        try:
            url = f"{API_BASE_URL}{CHAPTER_ENDPOINT}/{chapter_id}?IsDeleted=false"
            log.debug(f"Fetching: {url}")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not data.get('Success'):
                log.error(f"API returned error for {chapter_id}: {data.get('Error')}")
                return None

            return data.get('Result')

        except requests.RequestException as e:
            log.error(f"Failed to fetch {chapter_id}: {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error fetching {chapter_id}: {e}")
            return None

    def discover_chapters(self, handbook_prefix: str) -> List[str]:
        """
        Discover all chapters for a handbook by following nextChapterId links

        Args:
            handbook_prefix: Handbook prefix (e.g., "prin")

        Returns:
            List of discovered chapter IDs
        """
        log.info(f"Discovering chapters for {handbook_prefix}...")

        chapters = []
        visited = set()

        # Start with chapter 1
        current_chapter_id = f"{handbook_prefix}1"
        max_iterations = 100  # Safety limit to prevent infinite loops

        for _ in range(max_iterations):
            # Avoid infinite loops
            if current_chapter_id in visited:
                log.warning(f"Circular reference detected at {current_chapter_id}, stopping")
                break

            # Try to fetch chapter
            data = self.fetch_chapter_data(current_chapter_id)

            if data is None:
                # No more chapters found
                break

            # Check if chapter has actual content (provisions)
            provisions = data.get('provisions', [])
            if not provisions or len(provisions) == 0:
                log.debug(f"Skipping empty chapter: {current_chapter_id}")

                # Still try to get next chapter
                next_chapter = data.get('nextChapterId')
                if next_chapter and next_chapter.startswith(handbook_prefix) and next_chapter not in visited:
                    current_chapter_id = next_chapter
                    continue
                else:
                    break

            # Add chapter to list
            chapters.append(current_chapter_id)
            visited.add(current_chapter_id)
            log.info(f"Found chapter: {current_chapter_id} - {data.get('chapterName', 'Unknown')} ({len(provisions)} provisions)")

            # Get next chapter from API response
            next_chapter = data.get('nextChapterId')

            if not next_chapter:
                # No more chapters
                break

            # Check if next chapter belongs to this handbook
            if not next_chapter.startswith(handbook_prefix):
                log.info(f"Reached end of {handbook_prefix} handbook (next: {next_chapter})")
                break

            current_chapter_id = next_chapter

        log.info(f"Discovered {len(chapters)} chapters with content")
        return chapters

    def load_chapter(self, chapter_id: str):
        """
        Load a single chapter and all its provisions into Neo4j

        Args:
            chapter_id: Chapter identifier (e.g., "prin1")
        """
        log.info(f"Loading chapter: {chapter_id}")

        # Fetch chapter data from API
        data = self.fetch_chapter_data(chapter_id)
        if data is None:
            log.warning(f"Skipping chapter {chapter_id} - no data")
            return

        if self.validate_only:
            log.info(f"[VALIDATE MODE] Would load chapter {chapter_id} with {len(data.get('provisions', []))} provisions")
            return

        # Load chapter node
        chapter_cypher = """
        MERGE (c:Chapter {chapterId: $chapterId})
        SET c.chapterName = $chapterName,
            c.lastModifiedDate = $lastModifiedDate,
            c.nextChapterId = $nextChapterId,
            c.previousChapterId = $previousChapterId,
            c.isDeleted = $isDeleted
        """

        self.query.run(chapter_cypher, {
            'chapterId': data.get('chapterId'),
            'chapterName': data.get('chapterName'),
            'lastModifiedDate': data.get('lastModifiedDate'),
            'nextChapterId': data.get('nextChapterId'),
            'previousChapterId': data.get('previousChapterId'),
            'isDeleted': data.get('isChapterDeleted', False)
        })

        # Create chapter navigation relationships
        if data.get('nextChapterId'):
            self.query.run("""
                MATCH (c1:Chapter {chapterId: $chapterId})
                MERGE (c2:Chapter {chapterId: $nextChapterId})
                MERGE (c1)-[:NEXT]->(c2)
            """, {'chapterId': data.get('chapterId'), 'nextChapterId': data.get('nextChapterId')})

        if data.get('previousChapterId'):
            self.query.run("""
                MATCH (c1:Chapter {chapterId: $chapterId})
                MERGE (c2:Chapter {chapterId: $previousChapterId})
                MERGE (c1)-[:PREVIOUS]->(c2)
            """, {'chapterId': data.get('chapterId'), 'previousChapterId': data.get('previousChapterId')})

        # Load provisions
        provisions = data.get('provisions', [])
        if provisions:
            self._load_provisions(data.get('chapterId'), provisions)

        log.info(f"Loaded chapter {chapter_id} with {len(provisions)} provisions")

    def _parse_hierarchy(self, provision_name: str) -> List[str]:
        """
        Parse provision name into hierarchical components

        Examples:
            "PRIN 3.1.1" -> ["PRIN", "3", "3.1", "3.1.1"]
            "COBS 2.1.1A" -> ["COBS", "2", "2.1", "2.1.1A"]

        Args:
            provision_name: Full provision name (e.g., "PRIN 3.1.1")

        Returns:
            List of hierarchical identifiers from broadest to most specific
        """
        parts = provision_name.split()
        if len(parts) < 2:
            return [provision_name]

        handbook_code = parts[0]  # e.g., "PRIN", "COBS"
        number_part = parts[1]     # e.g., "3.1.1", "2.1.1A"

        # Split on dots to get hierarchy levels
        levels = number_part.split('.')

        # Build hierarchy: PRIN, 3, 3.1, 3.1.1
        hierarchy = [handbook_code]
        current = ""

        for level in levels:
            if current:
                current += "." + level
            else:
                current = level
            hierarchy.append(current)

        return hierarchy

    def _extract_cross_references(self, html_content: str, source_provision_id: int) -> List[Dict]:
        """
        Extract cross-references from HTML content

        Parses the contentType HTML field to find:
        - Cross-references to other provisions (in <span class="xref">)
        - Direct handbook links

        Args:
            html_content: HTML content from provision's contentType field
            source_provision_id: ID of the source provision

        Returns:
            List of cross-reference dictionaries with source, target info, and link text
        """
        from bs4 import BeautifulSoup
        import re

        if not html_content:
            return []

        cross_refs = []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find all xref spans (primary cross-references)
            xrefs = soup.find_all('span', class_='xref')

            for xref in xrefs:
                link = xref.find('a')
                if not link:
                    continue

                href = link.get('href', '')
                link_text = link.get_text().strip()

                if not href or not link_text:
                    continue

                # Parse target from href
                # Examples:
                #   /handbook/prin2 -> chapter reference
                #   /handbook/gen2/gen2s2 -> section reference
                #   /handbook/gen2/gen2s2#p40456 -> provision reference

                # Extract target identifiers
                target_info = self._parse_reference_target(href, link_text)

                if target_info:
                    cross_refs.append({
                        'sourceProvisionId': source_provision_id,
                        'linkText': link_text,
                        'href': href,
                        **target_info
                    })

        except Exception as e:
            log.warning(f"Error parsing cross-references for provision {source_provision_id}: {e}")

        return cross_refs

    def _parse_reference_target(self, href: str, link_text: str) -> Optional[Dict]:
        """
        Parse reference target from href to determine what it points to

        Args:
            href: Link href (e.g., "/handbook/prin2", "/handbook/gen2/gen2s2#p40456")
            link_text: Display text of the link

        Returns:
            Dictionary with targetType and targetId, or None if invalid
        """
        import re

        # Remove leading/trailing slashes and whitespace
        href = href.strip().strip('/')

        # Pattern: handbook/CHAPTER or handbook/CHAPTER/SECTION or handbook/CHAPTER#anchor
        match = re.match(r'handbook/([a-z0-9]+)(?:/([a-z0-9s]+))?(?:#(.+))?', href.lower())

        if not match:
            return None

        chapter_id = match.group(1)
        section_id = match.group(2)
        anchor = match.group(3)

        if anchor:
            # Provision reference (has anchor like #p40456)
            return {
                'targetType': 'provision',
                'targetChapterId': chapter_id,
                'targetSectionId': section_id,
                'targetAnchor': anchor
            }
        elif section_id:
            # Section reference
            return {
                'targetType': 'section',
                'targetChapterId': chapter_id,
                'targetSectionId': section_id
            }
        else:
            # Chapter reference
            return {
                'targetType': 'chapter',
                'targetChapterId': chapter_id
            }

    def _load_provisions(self, chapter_id: str, provisions: List[Dict]):
        """
        Load provisions and build hierarchical structure in Neo4j

        Creates hierarchy: Chapter -> Section -> Subsection -> Provision
        Based on provision names like "PRIN 3.1.1":
          - PRIN 3 = Chapter
          - PRIN 3.1 = Section
          - PRIN 3.1.1 = Provision

        Args:
            chapter_id: Parent chapter ID
            provisions: List of provision dictionaries
        """
        # Track all nodes to create
        all_sections = {}  # section_id -> section_data
        provision_data = []
        glossary_data = []
        glossary_relationships = []
        hierarchy_relationships = []
        cross_references = []

        for prov in provisions:
            provision_name = prov.get('provisionName', '')
            provision_id = prov.get('provisionId')

            # Parse hierarchy from provision name (e.g., "PRIN 3.1.1" -> ["PRIN", "3", "3.1", "3.1.1"])
            hierarchy = self._parse_hierarchy(provision_name)

            # Create section nodes for each level in the hierarchy
            # e.g., for "PRIN 3.1.1": create sections for "3", "3.1"
            handbook_code = hierarchy[0] if hierarchy else chapter_id.upper()

            for i in range(1, len(hierarchy) - 1):  # Skip handbook code and final provision
                section_num = hierarchy[i]
                section_id = f"{handbook_code.lower()}{section_num}"

                if section_id not in all_sections:
                    # Determine section name based on level
                    if i == 1:
                        # Top level section (e.g., "3" in "PRIN 3.1.1")
                        section_name = f"{handbook_code} {section_num}"
                    else:
                        # Subsection (e.g., "3.1" in "PRIN 3.1.1")
                        section_name = f"{handbook_code} {section_num}"

                    all_sections[section_id] = {
                        'sectionId': section_id,
                        'sectionName': section_name,
                        'sectionNumber': section_num,
                        'level': i,
                        'chapterId': chapter_id
                    }

                # Create hierarchy relationship
                if i > 1:
                    # Parent is the previous level
                    parent_num = hierarchy[i-1]
                    parent_id = f"{handbook_code.lower()}{parent_num}"

                    hierarchy_relationships.append({
                        'parent_id': parent_id,
                        'child_id': section_id
                    })
                else:
                    # Top-level section connects to chapter
                    hierarchy_relationships.append({
                        'parent_type': 'Chapter',
                        'parent_id': chapter_id,
                        'child_type': 'Section',
                        'child_id': section_id
                    })

            # Add provision
            # Provision connects to its immediate parent section
            if len(hierarchy) >= 2:
                parent_section_num = hierarchy[-2]  # Second to last is parent
                parent_section_id = f"{handbook_code.lower()}{parent_section_num}"

                provision_data.append({
                    'provisionId': provision_id,
                    'entityId': prov.get('entityId'),
                    'provisionName': provision_name,
                    'provisionNumber': hierarchy[-1] if hierarchy else '',
                    'provisionType': prov.get('provisionType'),
                    'contentText': prov.get('contentText', ''),
                    'contentType': prov.get('contentType', ''),
                    'timeline': prov.get('timeline'),
                    'sectionName': prov.get('sectionName'),
                    'subSectionName': prov.get('subSectionName', ''),
                    'parentSectionId': parent_section_id
                })

            # Track glossary terms
            for term in prov.get('glossaryTerm', []):
                term_id = term.get('termId')
                if term_id:
                    if term_id not in [t['termId'] for t in glossary_data]:
                        glossary_data.append({
                            'termId': term_id,
                            'name': term.get('name'),
                            'link': term.get('link')
                        })

                    glossary_relationships.append({
                        'provisionId': provision_id,
                        'termId': term_id
                    })

            # Extract cross-references from HTML content
            html_content = prov.get('contentType', '')
            if html_content:
                provision_cross_refs = self._extract_cross_references(html_content, provision_id)
                cross_references.extend(provision_cross_refs)

        # Batch load sections
        section_list = list(all_sections.values())
        if section_list:
            log.info(f"Loading {len(section_list)} sections in hierarchy...")
            log.debug(f"Sample section data: {section_list[0] if section_list else 'none'}")

            section_cypher = """
            UNWIND $batch AS row
            MERGE (s:Section {sectionId: row.sectionId})
            SET s.sectionName = row.sectionName,
                s.sectionNumber = row.sectionNumber,
                s.level = row.level,
                s.chapterId = row.chapterId
            """
            self.query.run_batched(section_cypher, section_list, batch_size=self.batch_size)

        # Batch load provisions
        if provision_data:
            log.info(f"Loading {len(provision_data)} provisions...")
            log.debug(f"Sample provision data: {provision_data[0] if provision_data else 'none'}")

            provision_cypher = """
            UNWIND $batch AS row
            MERGE (p:Provision {provisionId: row.provisionId})
            SET p.entityId = row.entityId,
                p.provisionName = row.provisionName,
                p.provisionNumber = row.provisionNumber,
                p.provisionType = row.provisionType,
                p.contentText = row.contentText,
                p.contentType = row.contentType,
                p.timeline = row.timeline,
                p.sectionName = row.sectionName,
                p.subSectionName = row.subSectionName,
                p.parentSectionId = row.parentSectionId
            """
            self.query.run_batched(provision_cypher, provision_data, batch_size=self.batch_size)

        # Create hierarchy relationships (Chapter -> Section, Section -> Section, Section -> Provision)
        if hierarchy_relationships:
            log.info(f"Creating {len(hierarchy_relationships)} hierarchy relationships...")

            # Split into chapter-to-section and section-to-section relationships
            chapter_to_section = [r for r in hierarchy_relationships if 'parent_type' in r]
            section_to_section = [r for r in hierarchy_relationships if 'parent_type' not in r]

            # Chapter -> Section relationships
            if chapter_to_section:
                chapter_section_cypher = """
                UNWIND $batch AS row
                MATCH (c:Chapter {chapterId: row.parent_id})
                MATCH (s:Section {sectionId: row.child_id})
                MERGE (c)-[:CONTAINS]->(s)
                """
                self.query.run_batched(chapter_section_cypher, chapter_to_section, batch_size=self.batch_size)

            # Section -> Section relationships (hierarchy)
            if section_to_section:
                section_hierarchy_cypher = """
                UNWIND $batch AS row
                MATCH (parent:Section {sectionId: row.parent_id})
                MATCH (child:Section {sectionId: row.child_id})
                MERGE (parent)-[:CONTAINS]->(child)
                """
                self.query.run_batched(section_hierarchy_cypher, section_to_section, batch_size=self.batch_size)

        # Section -> Provision relationships
        if provision_data:
            log.info(f"Connecting provisions to sections...")
            provision_section_cypher = """
            UNWIND $batch AS row
            MATCH (s:Section {sectionId: row.parentSectionId})
            MATCH (p:Provision {provisionId: row.provisionId})
            MERGE (s)-[:CONTAINS]->(p)
            """
            self.query.run_batched(provision_section_cypher, provision_data, batch_size=self.batch_size)

        # Batch load glossary terms
        if glossary_data:
            log.info(f"Loading {len(glossary_data)} glossary terms...")
            glossary_cypher = """
            UNWIND $batch AS row
            MERGE (t:GlossaryTerm {termId: row.termId})
            SET t.name = row.name,
                t.link = row.link
            """
            self.query.run_batched(glossary_cypher, glossary_data, batch_size=self.batch_size)

        # Batch load glossary relationships
        if glossary_relationships:
            log.info(f"Loading {len(glossary_relationships)} glossary relationships...")
            glossary_rel_cypher = """
            UNWIND $batch AS row
            MATCH (p:Provision {provisionId: row.provisionId})
            MATCH (t:GlossaryTerm {termId: row.termId})
            MERGE (p)-[:DEFINES]->(t)
            """
            self.query.run_batched(glossary_rel_cypher, glossary_relationships, batch_size=self.batch_size)

        # Batch load cross-references
        if cross_references:
            log.info(f"Loading {len(cross_references)} cross-references...")

            # Group by target type for efficient loading
            chapter_refs = [r for r in cross_references if r['targetType'] == 'chapter']
            section_refs = [r for r in cross_references if r['targetType'] == 'section']
            provision_refs = [r for r in cross_references if r['targetType'] == 'provision']

            # Chapter references
            if chapter_refs:
                log.info(f"  - {len(chapter_refs)} chapter references")
                chapter_ref_cypher = """
                UNWIND $batch AS row
                MATCH (source:Provision {provisionId: row.sourceProvisionId})
                MERGE (target:Chapter {chapterId: row.targetChapterId})
                MERGE (source)-[:REFERENCES {
                    linkText: row.linkText,
                    targetType: row.targetType,
                    href: row.href
                }]->(target)
                """
                self.query.run_batched(chapter_ref_cypher, chapter_refs, batch_size=self.batch_size)

            # Section references
            if section_refs:
                log.info(f"  - {len(section_refs)} section references")
                section_ref_cypher = """
                UNWIND $batch AS row
                MATCH (source:Provision {provisionId: row.sourceProvisionId})
                MERGE (target:Section {sectionId: row.targetSectionId})
                MERGE (source)-[:REFERENCES {
                    linkText: row.linkText,
                    targetType: row.targetType,
                    href: row.href
                }]->(target)
                """
                self.query.run_batched(section_ref_cypher, section_refs, batch_size=self.batch_size)

            # Provision references (by anchor)
            if provision_refs:
                log.info(f"  - {len(provision_refs)} provision references (by anchor)")

                # Extract provisionId from anchors like #p22 or #p40456
                for ref in provision_refs:
                    anchor = ref.get('targetAnchor', '')
                    if anchor and anchor.startswith('p'):
                        try:
                            ref['targetProvisionId'] = int(anchor[1:])  # Remove 'p' prefix
                        except ValueError:
                            log.warning(f"Could not parse provision ID from anchor: {anchor}")

                # Filter to only those with valid provisionId
                valid_provision_refs = [r for r in provision_refs if 'targetProvisionId' in r]

                if valid_provision_refs:
                    provision_ref_cypher = """
                    UNWIND $batch AS row
                    MATCH (source:Provision {provisionId: row.sourceProvisionId})
                    MERGE (target:Provision {provisionId: row.targetProvisionId})
                    MERGE (source)-[:REFERENCES {
                        linkText: row.linkText,
                        targetType: row.targetType,
                        href: row.href
                    }]->(target)
                    """
                    self.query.run_batched(provision_ref_cypher, valid_provision_refs, batch_size=self.batch_size)
                    log.info(f"    Created {len(valid_provision_refs)} provision-to-provision references")

    def run(self, handbook: Optional[str] = None, chapters: Optional[List[str]] = None):
        """
        Execute the complete loading workflow

        Args:
            handbook: Handbook prefix to discover and load (e.g., "prin")
            chapters: Specific chapter IDs to load (e.g., ["prin1", "prin2"])
        """
        if handbook:
            log.info(f"Starting FCA Handbook ingestion for: {handbook.upper()}")
            chapters = self.discover_chapters(handbook.lower())
        elif chapters:
            log.info(f"Starting FCA Handbook ingestion for specific chapters: {chapters}")
        else:
            log.error("Must specify either --handbook or --chapters")
            return

        log.info(f"Mode: {'VALIDATE ONLY' if self.validate_only else 'LOAD TO NEO4J'}")
        log.info(f"Batch size: {self.batch_size}")
        log.info(f"Total chapters to process: {len(chapters)}")

        # Load each chapter
        for i, chapter_id in enumerate(chapters, 1):
            log.info(f"Processing chapter {i}/{len(chapters)}: {chapter_id}")
            self.load_chapter(chapter_id)

        log.info(f"Ingestion complete: {len(chapters)} chapters processed")

        # Close Neo4j connection
        if not self.validate_only:
            self.query.close()


def main():
    """Main entry point with argument parsing"""

    # Fetch available handbooks from API
    available_handbooks = FCAHandbookAPILoader.get_all_handbooks()

    parser = argparse.ArgumentParser(
        description='Load FCA Handbook content from REST API into Neo4j',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # List all available handbooks
  python workspace/generated/fca_handbook_loader.py --list-handbooks

  # Load all PRIN chapters
  python workspace/generated/fca_handbook_loader.py --handbook prin

  # Load specific chapters
  python workspace/generated/fca_handbook_loader.py --chapters prin1 prin2 prin3

  # Validate without loading
  python workspace/generated/fca_handbook_loader.py --handbook prin --validate-only

Total available handbooks: {len(available_handbooks)}
Common handbooks: prin, sysc, cobs, coll, conc, mcob, bcobs, fees
        """
    )

    parser.add_argument(
        '--list-handbooks',
        action='store_true',
        help='List all available handbooks and exit'
    )

    parser.add_argument(
        '--handbook',
        type=str,
        help='Handbook to load (discovers all chapters automatically). Use --list-handbooks to see all available.'
    )

    parser.add_argument(
        '--chapters',
        type=str,
        nargs='+',
        help='Specific chapter IDs to load (e.g., prin1 prin2)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Number of items per batch (default: 1000)'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Validate data without loading to Neo4j'
    )

    args = parser.parse_args()

    # Handle --list-handbooks
    if args.list_handbooks:
        print(f"\n{'='*80}")
        print(f"FCA Handbook - Available Handbooks ({len(available_handbooks)} total)")
        print(f"{'='*80}\n")

        for code, name in sorted(available_handbooks.items()):
            print(f"  {code:15} - {name}")

        print(f"\n{'='*80}")
        print(f"Usage: python workspace/generated/fca_handbook_loader.py --handbook <code>")
        print(f"{'='*80}\n")
        return

    # Validate arguments
    if not args.handbook and not args.chapters:
        parser.error("Must specify either --handbook or --chapters")

    # Validate handbook code
    if args.handbook and args.handbook.lower() not in available_handbooks:
        log.error(f"Unknown handbook: {args.handbook}")
        log.info(f"Use --list-handbooks to see all {len(available_handbooks)} available handbooks")
        return

    # Create and run loader
    try:
        loader = FCAHandbookAPILoader(
            batch_size=args.batch_size,
            validate_only=args.validate_only
        )

        loader.run(
            handbook=args.handbook,
            chapters=args.chapters
        )
    except KeyboardInterrupt:
        log.info("Interrupted by user")
    except Exception as e:
        log.error(f"Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()
