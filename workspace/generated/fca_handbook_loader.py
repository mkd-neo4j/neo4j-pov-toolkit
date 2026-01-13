"""
FCA Handbook Data Loader (API-Based) - Refactored Enterprise Edition

Purpose:
    Fetches UK Financial Conduct Authority (FCA) Handbook content via the FCA REST API
    and loads it into Neo4j as a hierarchical graph structure.

Architecture:
    This script uses a clean separation of concerns:
    1. FCAAPIClient: Handles all HTTP communication with retry logic
    2. FCADataTransformer: Transforms raw API data into domain models
    3. FCANeo4jRepository: Manages all Neo4j operations with optimized batch processing

Graph Model (with Temporal Versioning):
    (:Handbook) nodes with properties:
        - handbookCode: Unique handbook identifier (e.g., "prin", "mifid", "sysc")
        - handbookName: Full handbook name

    (:Chapter) nodes with properties:
        - chapterId: Unique identifier (e.g., "prin1")
        - versionDate: Date this version became active (ISO format: YYYY-MM-DD)
        - validFrom: Date this version is valid from (Neo4j Date type)
        - validTo: Date this version is valid until (Neo4j Date type, null if current)
        - isCurrent: Boolean flag indicating if this is the current version
        - chapterName, nextChapterId, breadcrumbsJson, etc.

    (:Section) nodes with properties:
        - sectionId, versionDate, validFrom, validTo, isCurrent
        - sectionName, sectionNumber, level, chapterId

    (:Provision) nodes with properties:
        - provisionId, versionDate, validFrom, validTo, isCurrent
        - provisionName, provisionType, contentText, contentType, etc.

    (:GlossaryTerm) nodes with properties:
        - termId, name, link

    Relationships:
        - (:Handbook)-[:CONTAINS]->(:Chapter) [handbook contains chapters]
        - (:Chapter)-[:CONTAINS]->(:Section) [temporal validity]
        - (:Section)-[:CONTAINS]->(:Section) [nested sections, temporal]
        - (:Section)-[:CONTAINS]->(:Provision) [temporal validity]
        - (:Provision)-[:DEFINES]->(:GlossaryTerm)
        - (:Provision)-[:REFERENCES]->(:Chapter|:Section|:Provision) [temporal]
        - (:Chapter)-[:NEXT]->(:Chapter) [one-way chapter navigation]
        - (*)-[:NEXT_VERSION]->(*) [one-way temporal versioning]

Usage:
    # Load all chapters for a handbook (e.g., PRIN)
    python workspace/generated/fca_handbook_loader_v2.py --handbook prin

    # Load specific chapters
    python workspace/generated/fca_handbook_loader_v2.py --chapters prin1 prin2 prin3

    # Validate without loading
    python workspace/generated/fca_handbook_loader_v2.py --handbook prin --validate-only

    # Load historical version
    python workspace/generated/fca_handbook_loader_v2.py --handbook prin --date 01-01-2020

Requirements:
    - Neo4j connection configured in .env file
    - Dependencies: requests, neo4j, beautifulsoup4
"""

import sys
import os
import argparse
from typing import List, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.logger import log
from workspace.generated.fca_models import LoaderConfig, EntityType
from workspace.generated.fca_api_client import FCAAPIClient
from workspace.generated.fca_transformer import FCADataTransformer
from workspace.generated.fca_neo4j_repository import FCANeo4jRepository
from workspace.generated.fca_exceptions import (
    FCALoaderError, TransientAPIError, PermanentAPIError,
    DataValidationError, Neo4jOperationError
)


class FCAHandbookLoader:
    """
    Orchestrates the loading of FCA Handbook content into Neo4j

    This is the main coordinator class that uses:
    - FCAAPIClient for API communication
    - FCADataTransformer for data transformation
    - FCANeo4jRepository for database operations

    All business logic is delegated to specialized components.
    """

    def __init__(self, config: LoaderConfig):
        """
        Initialize the loader with configuration

        Args:
            config: Loader configuration object
        """
        self.config = config
        self.api_client = FCAAPIClient(config)
        self.transformer = FCADataTransformer()

        # Only initialize repository if not in validate-only mode
        self.repository = None if config.validate_only else FCANeo4jRepository(config)

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
            try:
                data = self.api_client.fetch_chapter_data(current_chapter_id)
            except PermanentAPIError as e:
                log.warning(f"Could not fetch {current_chapter_id}: {e}")
                break
            except TransientAPIError as e:
                log.error(f"Transient error fetching {current_chapter_id}: {e}")
                break

            if data is None:
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

    def load_chapter_versions(self, chapter_id: str, handbook_code: Optional[str] = None):
        """
        Load all historical versions of a chapter using Timeline API

        Args:
            chapter_id: Chapter identifier (e.g., "prin1")
            handbook_code: Handbook code (e.g., "prin") - extracted from chapter_id if not provided
        """
        log.info(f"Loading all versions for chapter: {chapter_id}")

        # Get timeline for this chapter
        try:
            timeline_dates = self.api_client.fetch_timeline_entries(chapter_id)
        except Exception as e:
            log.error(f"Could not fetch timeline for {chapter_id}: {e}")
            return

        if not timeline_dates:
            log.warning(f"No timeline entries found for {chapter_id}")
            return

        log.info(f"Found {len(timeline_dates)} versions to load for {chapter_id}")

        # Load each version (but skip individual version chain recalculation)
        for i, date in enumerate(timeline_dates):
            is_current = (i == 0)  # First date is newest/current
            log.info(f"Loading version {i+1}/{len(timeline_dates)}: {date} {'(current)' if is_current else ''}")

            try:
                self.load_chapter(chapter_id, handbook_code, version_date=date, skip_version_chain_recalc=True)
            except Exception as e:
                log.error(f"Failed to load version {date} of {chapter_id}: {e}")
                continue

        # Now recalculate version chains for ALL entities across all loaded versions
        log.info(f"Recalculating version chains across all {len(timeline_dates)} versions...")

        # Get all section IDs for this chapter
        section_ids_result = self.repository.query.run(
            "MATCH (s:Section {chapterId: $chapterId}) RETURN DISTINCT s.sectionId as sectionId",
            {'chapterId': chapter_id}
        )
        section_ids = [record['sectionId'] for record in section_ids_result]

        if section_ids:
            log.info(f"Recalculating version chains for {len(section_ids)} sections...")
            self.repository.recalculate_version_chains_bulk('Section', 'sectionId', section_ids)

        # Get all provision entity IDs for this chapter (across all versions)
        # We need to use entityId (not provisionId) as it's stable across versions
        provision_entity_ids_result = self.repository.query.run("""
            MATCH (c:Chapter {chapterId: $chapterId})-[:CONTAINS*]->(p:Provision)
            RETURN DISTINCT p.entityId as entityId
        """, {'chapterId': chapter_id})
        provision_entity_ids = [record['entityId'] for record in provision_entity_ids_result]

        if provision_entity_ids:
            log.info(f"Recalculating version chains for {len(provision_entity_ids)} provisions...")
            self.repository.recalculate_version_chains_bulk('Provision', 'entityId', provision_entity_ids)

        # Recalculate chapter version chain
        log.info(f"Recalculating version chain for chapter {chapter_id}...")
        self.repository.recalculate_version_chains_bulk('Chapter', 'chapterId', [chapter_id])

        log.info(f"✓ Loaded {len(timeline_dates)} versions of {chapter_id}")

    def load_chapter(self, chapter_id: str, handbook_code: Optional[str] = None, version_date: Optional[str] = None, skip_version_chain_recalc: bool = False):
        """
        Load a single chapter version into Neo4j with temporal versioning

        Args:
            chapter_id: Chapter identifier (e.g., "prin1")
            handbook_code: Handbook code (e.g., "prin") - extracted from chapter_id if not provided
            version_date: Specific version date to load (DD-MM-YYYY format). If None, uses config.load_date or current version
            skip_version_chain_recalc: If True, skip version chain recalculation (useful when loading multiple versions)
        """
        log.info(f"Loading chapter: {chapter_id}" + (f" (version: {version_date})" if version_date else ""))

        # Extract handbook code from chapter_id if not provided
        if not handbook_code:
            # Extract letters from the beginning of chapter_id (e.g., "prin1" -> "prin")
            import re
            match = re.match(r'^([a-z]+)', chapter_id.lower())
            handbook_code = match.group(1) if match else None

        try:
            # Fetch chapter data from API (with specific version date if provided)
            data = self.api_client.fetch_chapter_data(chapter_id, date=version_date)
            if data is None:
                log.warning(f"Skipping chapter {chapter_id} - no data")
                return

            # Determine version date
            # Priority: 1) Explicit version_date parameter, 2) config.load_date, 3) lastModifiedDate from API
            version_date_raw = version_date or self.config.load_date or data.get('lastModifiedDate')
            if not version_date_raw:
                raise DataValidationError(f"No version date available for {chapter_id}")

            version_date_iso = self.transformer.convert_fca_date_to_iso(version_date_raw)
            log.info(f"Loading {chapter_id} version: {version_date_iso}")

            if self.config.validate_only:
                log.info(f"[VALIDATE MODE] Would load chapter {chapter_id} with {len(data.get('provisions', []))} provisions")
                return

            # Check if this version already exists
            if self.repository.chapter_version_exists(chapter_id, version_date_iso):
                log.info(f"Version {version_date_iso} of {chapter_id} already exists, skipping")
                return

            # Transform chapter data
            chapter = self.transformer.transform_chapter(data, version_date_iso)

            # Save chapter
            self.repository.save_chapter(chapter)

            # Create handbook-chapter relationship if handbook_code is available
            if handbook_code:
                self.repository.create_handbook_chapter_relationship(handbook_code, chapter_id)

            # Create chapter navigation relationships (one-way)
            self.repository.create_chapter_navigation_relationships(
                chapter_id,
                data.get('nextChapterId')
            )

            # Transform provisions and relationships
            provisions_data = data.get('provisions', [])
            if provisions_data:
                sections_dict, provisions, hierarchy_rels, cross_refs, prov_glossary = \
                    self.transformer.transform_provisions(provisions_data, chapter_id, version_date_iso)

                # Save sections
                sections_list = list(sections_dict.values())
                if sections_list:
                    self.repository.save_sections_batch(sections_list)

                # Save provisions
                if provisions:
                    self.repository.save_provisions_batch(provisions)

                # Save glossary terms
                glossary_terms = self.transformer.transform_glossary_terms(provisions_data)
                if glossary_terms:
                    self.repository.save_glossary_terms_batch(list(glossary_terms.values()))

                # Create hierarchy relationships
                if hierarchy_rels:
                    self.repository.create_hierarchy_relationships_batch(hierarchy_rels)

                # Create provision-glossary relationships
                if prov_glossary:
                    self.repository.create_provision_glossary_relationships_batch(prov_glossary)

                # Create cross-references
                if cross_refs:
                    self.repository.create_cross_references_batch(cross_refs)

                # Recalculate version chains (bulk operation) - unless skipped
                if not skip_version_chain_recalc:
                    section_ids = list(sections_dict.keys())
                    provision_ids = [str(p.provision_id) for p in provisions]

                    if section_ids:
                        log.info(f"Recalculating version chains for {len(section_ids)} sections...")
                        self.repository.recalculate_version_chains_bulk('Section', 'sectionId', section_ids)

                    if provision_ids:
                        log.info(f"Recalculating version chains for {len(provision_ids)} provisions...")
                        self.repository.recalculate_version_chains_bulk('Provision', 'provisionId', provision_ids)

            # Recalculate chapter version chain - unless skipped
            if not skip_version_chain_recalc:
                log.info(f"Recalculating version chain for chapter {chapter_id}...")
                self.repository.recalculate_version_chains_bulk('Chapter', 'chapterId', [chapter_id])

            log.info(f"✓ Loaded chapter {chapter_id} version {version_date_iso} with {len(provisions_data)} provisions")

        except DataValidationError as e:
            log.error(f"Data validation error for {chapter_id}: {e}")
            raise
        except Neo4jOperationError as e:
            log.error(f"Neo4j operation error for {chapter_id}: {e}")
            raise
        except Exception as e:
            log.error(f"Unexpected error loading {chapter_id}: {e}")
            raise

    def run(self, handbook: Optional[str] = None, chapters: Optional[List[str]] = None):
        """
        Execute the complete loading workflow

        Args:
            handbook: Handbook prefix to discover and load (e.g., "prin")
            chapters: Specific chapter IDs to load (e.g., ["prin1", "prin2"])
        """
        handbook_code = None

        if handbook:
            log.info(f"Starting FCA Handbook ingestion for: {handbook.upper()}")
            handbook_code = handbook.lower()
            chapters = self.discover_chapters(handbook_code)

            # Create handbook node if not in validate-only mode
            if not self.config.validate_only and handbook_code:
                # Fetch handbook name from API
                try:
                    all_handbooks = self.api_client.get_all_handbooks()
                    handbook_name = all_handbooks.get(handbook_code, handbook_code.upper())

                    handbook_obj = self.transformer.transform_handbook(handbook_code, handbook_name)
                    self.repository.save_handbook(handbook_obj)
                    log.info(f"Created handbook node: {handbook_code} - {handbook_name}")
                except Exception as e:
                    log.warning(f"Could not create handbook node: {e}")

        elif chapters:
            log.info(f"Starting FCA Handbook ingestion for specific chapters: {chapters}")
            # Try to extract handbook code from first chapter
            if chapters:
                import re
                match = re.match(r'^([a-z]+)', chapters[0].lower())
                handbook_code = match.group(1) if match else None

                # Create handbook node if not in validate-only mode
                if not self.config.validate_only and handbook_code:
                    try:
                        all_handbooks = self.api_client.get_all_handbooks()
                        handbook_name = all_handbooks.get(handbook_code, handbook_code.upper())

                        handbook_obj = self.transformer.transform_handbook(handbook_code, handbook_name)
                        self.repository.save_handbook(handbook_obj)
                        log.info(f"Created handbook node: {handbook_code} - {handbook_name}")
                    except Exception as e:
                        log.warning(f"Could not create handbook node: {e}")
        else:
            log.error("Must specify either --handbook or --chapters")
            return

        log.info(f"Mode: {'VALIDATE ONLY' if self.config.validate_only else 'LOAD TO NEO4J'}")
        log.info(f"Batch size: {self.config.batch_size}")
        log.info(f"Total chapters to process: {len(chapters)}")

        # Load each chapter
        success_count = 0
        error_count = 0

        for i, chapter_id in enumerate(chapters, 1):
            log.info(f"\n{'='*80}")
            log.info(f"Processing chapter {i}/{len(chapters)}: {chapter_id}")
            log.info(f"{'='*80}")

            try:
                if self.config.load_all_versions:
                    # Load all historical versions using Timeline API
                    self.load_chapter_versions(chapter_id, handbook_code)
                else:
                    # Load single version (current or specified via --date)
                    self.load_chapter(chapter_id, handbook_code)
                success_count += 1
            except (DataValidationError, Neo4jOperationError) as e:
                log.error(f"Failed to load {chapter_id}: {e}")
                error_count += 1
            except Exception as e:
                log.error(f"Unexpected error loading {chapter_id}: {e}")
                error_count += 1

        log.info(f"\n{'='*80}")
        log.info(f"Ingestion complete:")
        log.info(f"  ✓ Successful: {success_count}/{len(chapters)}")
        if error_count > 0:
            log.info(f"  ✗ Failed: {error_count}/{len(chapters)}")
        log.info(f"{'='*80}\n")

    def close(self):
        """Clean up resources"""
        if self.api_client:
            self.api_client.close()
        if self.repository:
            self.repository.close()


def main():
    """Main entry point with argument parsing"""

    # Create temp loader just to fetch handbooks list
    temp_config = LoaderConfig(validate_only=True)
    temp_client = FCAAPIClient(temp_config)

    try:
        available_handbooks = temp_client.get_all_handbooks()
    except Exception as e:
        log.error(f"Could not fetch handbooks list: {e}")
        available_handbooks = {}
    finally:
        temp_client.close()

    parser = argparse.ArgumentParser(
        description='Load FCA Handbook content from REST API into Neo4j',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # List all available handbooks
  python workspace/generated/fca_handbook_loader_v2.py --list-handbooks

  # Load all PRIN chapters
  python workspace/generated/fca_handbook_loader_v2.py --handbook prin

  # Load specific chapters
  python workspace/generated/fca_handbook_loader_v2.py --chapters prin1 prin2 prin3

  # Validate without loading
  python workspace/generated/fca_handbook_loader_v2.py --handbook prin --validate-only

  # Load historical version
  python workspace/generated/fca_handbook_loader_v2.py --handbook prin --date 01-01-2020

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

    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Historical date to load (format: DD-MM-YYYY). If not specified, loads current version.'
    )

    parser.add_argument(
        '--load-all-versions',
        action='store_true',
        help='Load all historical versions using Timeline API (ignores --date)'
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
        print(f"Usage: python workspace/generated/fca_handbook_loader_v2.py --handbook <code>")
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

    # Create configuration
    config = LoaderConfig(
        batch_size=args.batch_size,
        validate_only=args.validate_only,
        load_date=args.date,
        load_all_versions=args.load_all_versions
    )

    # Create and run loader
    loader = None
    try:
        loader = FCAHandbookLoader(config)
        loader.run(
            handbook=args.handbook,
            chapters=args.chapters
        )
    except KeyboardInterrupt:
        log.info("\nInterrupted by user")
    except FCALoaderError as e:
        log.error(f"Loader error: {e}")
        raise
    except Exception as e:
        log.error(f"Fatal error: {e}")
        raise
    finally:
        if loader:
            loader.close()


if __name__ == '__main__':
    main()
