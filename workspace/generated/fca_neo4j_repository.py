"""
FCA Handbook Neo4j Repository

Handles all Neo4j database operations with optimized queries and batch processing.
"""

import sys
import os
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.neo4j.query import Neo4jQuery
from src.core.logger import log
from workspace.generated.fca_models import (
    Handbook, Chapter, Section, Provision, GlossaryTerm, CrossReference,
    HierarchyRelationship, EntityType, ReferenceTargetType, LoaderConfig
)
from workspace.generated.fca_exceptions import Neo4jOperationError, TemporalVersionError


class FCANeo4jRepository:
    """
    Repository for FCA Handbook data in Neo4j

    Responsibilities:
    - Schema management (constraints, indexes)
    - Batch loading of entities and relationships
    - Temporal version chain management
    - Query execution with error handling
    """

    def __init__(self, config: LoaderConfig):
        """
        Initialize repository

        Args:
            config: Loader configuration object
        """
        self.config = config
        self.query = Neo4jQuery()
        # Schema setup removed - database runs without constraints/indexes

    def save_handbook(self, handbook: Handbook):
        """
        Save a handbook to Neo4j

        Args:
            handbook: Handbook domain model
        """
        cypher = """
        MERGE (h:Handbook {handbookCode: $handbookCode})
        SET h.handbookName = $handbookName
        """

        try:
            self.query.run(cypher, handbook.to_neo4j_params())
        except Exception as e:
            raise Neo4jOperationError(f"Failed to save handbook {handbook.handbook_code}: {e}", query=cypher)

    def create_handbook_chapter_relationship(self, handbook_code: str, chapter_id: str):
        """
        Create CONTAINS relationship between handbook and chapter

        Args:
            handbook_code: Handbook code (e.g., "prin")
            chapter_id: Chapter ID (e.g., "prin1")
        """
        cypher = """
        MATCH (h:Handbook {handbookCode: $handbookCode})
        MATCH (c:Chapter {chapterId: $chapterId})
        MERGE (h)-[:CONTAINS]->(c)
        """

        try:
            self.query.run(cypher, {'handbookCode': handbook_code, 'chapterId': chapter_id})
        except Exception:
            # Handbook or chapter doesn't exist yet - skip relationship
            pass

    def chapter_version_exists(self, chapter_id: str, version_date: str) -> bool:
        """
        Check if a specific version of a chapter already exists

        Args:
            chapter_id: Chapter identifier
            version_date: Version date in ISO format (YYYY-MM-DD)

        Returns:
            True if version exists, False otherwise
        """
        cypher = """
        MATCH (c:Chapter {chapterId: $chapterId, versionDate: date($versionDate)})
        RETURN c.chapterId as id
        """
        result = self.query.run(cypher, {
            'chapterId': chapter_id,
            'versionDate': version_date
        })
        return len(result) > 0

    def save_chapter(self, chapter: Chapter):
        """
        Save a chapter to Neo4j

        Args:
            chapter: Chapter domain model
        """
        cypher = """
        CREATE (c:Chapter {
            chapterId: $chapterId,
            versionDate: date($versionDate),
            validFrom: date($validFrom),
            validTo: CASE WHEN $validTo IS NULL THEN NULL ELSE date($validTo) END,
            isCurrent: $isCurrent,
            chapterName: $chapterName,
            lastModifiedDate: $lastModifiedDate,
            nextChapterId: $nextChapterId,
            previousChapterId: $previousChapterId,
            isChapterDeleted: $isChapterDeleted,
            isSectionDeleted: $isSectionDeleted,
            isHeaderDeleted: $isHeaderDeleted,
            chapterDeletionMessage: $chapterDeletionMessage,
            sectionDeletionMessage: $sectionDeletionMessage,
            isChapterFutureVersion: $isChapterFutureVersion,
            isSectionFutureVersion: $isSectionFutureVersion,
            chapterFutureVersionMessage: $chapterFutureVersionMessage,
            futureVersionDate: $futureVersionDate,
            breadcrumbsJson: $breadcrumbsJson
        })
        """

        try:
            self.query.run(cypher, chapter.to_neo4j_params())
        except Exception as e:
            raise Neo4jOperationError(f"Failed to save chapter {chapter.chapter_id}: {e}", query=cypher)

    def create_chapter_navigation_relationships(self, chapter_id: str, next_chapter_id: Optional[str]):
        """
        Create NEXT relationship between chapters (one-way navigation)

        Only creates relationships if both chapters already exist in the database.

        Args:
            chapter_id: Source chapter ID
            next_chapter_id: Target next chapter ID (optional)
        """
        if next_chapter_id:
            cypher = """
            MATCH (c1:Chapter {chapterId: $chapterId})
            MATCH (c2:Chapter {chapterId: $nextChapterId})
            MERGE (c1)-[:NEXT]->(c2)
            """
            try:
                self.query.run(cypher, {'chapterId': chapter_id, 'nextChapterId': next_chapter_id})
            except Exception:
                # Target chapter doesn't exist yet - skip relationship
                pass

    def save_sections_batch(self, sections: List[Section]):
        """
        Save sections in batch

        Args:
            sections: List of Section domain models
        """
        if not sections:
            return

        log.info(f"Loading {len(sections)} sections in batch...")

        cypher = """
        UNWIND $batch AS row
        MERGE (s:Section {sectionId: row.sectionId, versionDate: date(row.versionDate)})
        SET s.validFrom = date(row.validFrom),
            s.validTo = CASE WHEN row.validTo IS NULL THEN NULL ELSE date(row.validTo) END,
            s.isCurrent = row.isCurrent,
            s.sectionName = row.sectionName,
            s.sectionNumber = row.sectionNumber,
            s.level = row.level,
            s.chapterId = row.chapterId,
            s.sectionHeader = row.sectionHeader,
            s.sectionFooter = row.sectionFooter
        """

        section_params = [s.to_neo4j_params() for s in sections]

        try:
            self.query.run_batched(cypher, section_params, batch_size=self.config.batch_size)
        except Exception as e:
            raise Neo4jOperationError(f"Failed to save sections batch: {e}", query=cypher)

    def save_provisions_batch(self, provisions: List[Provision]):
        """
        Save provisions in batch

        Args:
            provisions: List of Provision domain models
        """
        if not provisions:
            return

        log.info(f"Loading {len(provisions)} provisions in batch...")

        cypher = """
        UNWIND $batch AS row
        MERGE (p:Provision {provisionId: row.provisionId, versionDate: date(row.versionDate)})
        SET p.validFrom = date(row.validFrom),
            p.validTo = CASE WHEN row.validTo IS NULL THEN NULL ELSE date(row.validTo) END,
            p.isCurrent = row.isCurrent,
            p.entityId = row.entityId,
            p.provisionName = row.provisionName,
            p.provisionNumber = row.provisionNumber,
            p.provisionType = row.provisionType,
            p.provisionTypeId = row.provisionTypeId,
            p.provisionTagId = row.provisionTagId,
            p.contentText = row.contentText,
            p.timeline = row.timeline,
            p.isDeleted = row.isDeleted,
            p.sectionId = row.sectionId,
            p.sectionName = row.sectionName,
            p.subSectionName = row.subSectionName
        """

        provision_params = [p.to_neo4j_params() for p in provisions]

        try:
            self.query.run_batched(cypher, provision_params, batch_size=self.config.batch_size)
        except Exception as e:
            raise Neo4jOperationError(f"Failed to save provisions batch: {e}", query=cypher)

    def save_glossary_terms_batch(self, terms: List[GlossaryTerm]):
        """
        Save glossary terms in batch

        Args:
            terms: List of GlossaryTerm domain models
        """
        if not terms:
            return

        log.info(f"Loading {len(terms)} glossary terms in batch...")

        cypher = """
        UNWIND $batch AS row
        MERGE (t:GlossaryTerm {termId: row.termId})
        SET t.name = row.name,
            t.link = row.link
        """

        term_params = [t.to_neo4j_params() for t in terms]

        try:
            self.query.run_batched(cypher, term_params, batch_size=self.config.batch_size)
        except Exception as e:
            raise Neo4jOperationError(f"Failed to save glossary terms: {e}", query=cypher)

    def create_hierarchy_relationships_batch(self, relationships: List[HierarchyRelationship]):
        """
        Create hierarchy relationships (Chapter->Section, Section->Section, Section->Provision) in batch

        Args:
            relationships: List of HierarchyRelationship domain models
        """
        if not relationships:
            return

        log.info(f"Creating {len(relationships)} hierarchy relationships...")

        # Group by parent/child type combinations
        chapter_to_section = []
        section_to_section = []
        section_to_provision = []

        for rel in relationships:
            if rel.parent_type == EntityType.CHAPTER and rel.child_type == EntityType.SECTION:
                chapter_to_section.append(rel)
            elif rel.parent_type == EntityType.SECTION and rel.child_type == EntityType.SECTION:
                section_to_section.append(rel)
            elif rel.parent_type == EntityType.SECTION and rel.child_type == EntityType.PROVISION:
                section_to_provision.append(rel)

        # Chapter -> Section
        if chapter_to_section:
            cypher = """
            UNWIND $batch AS row
            MATCH (c:Chapter {chapterId: row.parent_id})
            MATCH (s:Section {sectionId: row.child_id})
            MERGE (c)-[:CONTAINS]->(s)
            """
            params = [rel.to_neo4j_params() for rel in chapter_to_section]
            self.query.run_batched(cypher, params, batch_size=self.config.batch_size)

        # Section -> Section
        if section_to_section:
            cypher = """
            UNWIND $batch AS row
            MATCH (parent:Section {sectionId: row.parent_id})
            MATCH (child:Section {sectionId: row.child_id})
            MERGE (parent)-[:CONTAINS]->(child)
            """
            params = [rel.to_neo4j_params() for rel in section_to_section]
            self.query.run_batched(cypher, params, batch_size=self.config.batch_size)

        # Section -> Provision
        if section_to_provision:
            cypher = """
            UNWIND $batch AS row
            MATCH (s:Section {sectionId: row.parent_id})
            MATCH (p:Provision {provisionId: toInteger(row.child_id)})
            MERGE (s)-[:CONTAINS]->(p)
            """
            params = [rel.to_neo4j_params() for rel in section_to_provision]
            self.query.run_batched(cypher, params, batch_size=self.config.batch_size)

    def create_provision_glossary_relationships_batch(self, relationships: List[tuple]):
        """
        Create DEFINES relationships between provisions and glossary terms

        Args:
            relationships: List of (provision_id, term_id) tuples
        """
        if not relationships:
            return

        log.info(f"Creating {len(relationships)} provision-glossary relationships...")

        cypher = """
        UNWIND $batch AS row
        MATCH (p:Provision {provisionId: row.provisionId})
        MATCH (t:GlossaryTerm {termId: row.termId})
        MERGE (p)-[:DEFINES]->(t)
        """

        params = [{'provisionId': pid, 'termId': tid} for pid, tid in relationships]

        try:
            self.query.run_batched(cypher, params, batch_size=self.config.batch_size)
        except Exception as e:
            raise Neo4jOperationError(f"Failed to create glossary relationships: {e}", query=cypher)

    def create_cross_references_batch(self, cross_refs: List[CrossReference]):
        """
        Create REFERENCES relationships for cross-references

        Args:
            cross_refs: List of CrossReference domain models
        """
        if not cross_refs:
            return

        log.info(f"Creating {len(cross_refs)} cross-references...")

        # Group by target type for efficient loading
        by_type = {
            ReferenceTargetType.CHAPTER: [],
            ReferenceTargetType.SECTION: [],
            ReferenceTargetType.PROVISION: []
        }

        for ref in cross_refs:
            by_type[ref.target_type].append(ref)

        # Chapter references - only create if target exists
        if by_type[ReferenceTargetType.CHAPTER]:
            log.info(f"  - {len(by_type[ReferenceTargetType.CHAPTER])} chapter references")
            cypher = """
            UNWIND $batch AS row
            MATCH (source:Provision {provisionId: row.sourceProvisionId})
            OPTIONAL MATCH (target:Chapter {chapterId: row.targetChapterId})
            WITH source, target, row
            WHERE target IS NOT NULL
            MERGE (source)-[:REFERENCES {
                linkText: row.linkText,
                targetType: row.targetType,
                href: row.href
            }]->(target)
            """
            params = [ref.to_neo4j_params() for ref in by_type[ReferenceTargetType.CHAPTER]]
            self.query.run_batched(cypher, params, batch_size=self.config.batch_size)

        # Section references - only create if target exists
        if by_type[ReferenceTargetType.SECTION]:
            log.info(f"  - {len(by_type[ReferenceTargetType.SECTION])} section references")
            cypher = """
            UNWIND $batch AS row
            MATCH (source:Provision {provisionId: row.sourceProvisionId})
            OPTIONAL MATCH (target:Section {sectionId: row.targetSectionId})
            WITH source, target, row
            WHERE target IS NOT NULL
            MERGE (source)-[:REFERENCES {
                linkText: row.linkText,
                targetType: row.targetType,
                href: row.href
            }]->(target)
            """
            params = [ref.to_neo4j_params() for ref in by_type[ReferenceTargetType.SECTION]]
            self.query.run_batched(cypher, params, batch_size=self.config.batch_size)

        # Provision references (with valid provision IDs only) - only create if target exists
        valid_prov_refs = [ref for ref in by_type[ReferenceTargetType.PROVISION] if ref.target_provision_id]
        if valid_prov_refs:
            log.info(f"  - {len(valid_prov_refs)} provision references")
            cypher = """
            UNWIND $batch AS row
            MATCH (source:Provision {provisionId: row.sourceProvisionId})
            OPTIONAL MATCH (target:Provision {provisionId: row.targetProvisionId})
            WITH source, target, row
            WHERE target IS NOT NULL
            MERGE (source)-[:REFERENCES {
                linkText: row.linkText,
                targetType: row.targetType,
                href: row.href
            }]->(target)
            """
            params = [ref.to_neo4j_params() for ref in valid_prov_refs]
            self.query.run_batched(cypher, params, batch_size=self.config.batch_size)

    def recalculate_version_chains_bulk(self, entity_label: str, id_field: str, entity_ids: List[str]):
        """
        Recalculate temporal properties and version relationships for multiple entities in bulk

        This is an optimized version that processes multiple entities efficiently.

        Args:
            entity_label: Node label (Chapter, Section, Provision)
            id_field: ID property name (chapterId, sectionId, provisionId)
            entity_ids: List of entity IDs to process
        """
        if not entity_ids:
            return

        log.info(f"Recalculating version chains for {len(entity_ids)} {entity_label} entities...")

        # Step 1: Update temporal properties for all entities at once
        update_temporal_cypher = f"""
        MATCH (n:{entity_label})
        WHERE n.{id_field} IN $entityIds AND n.versionDate IS NOT NULL
        WITH n.{id_field} as entityId, n
        ORDER BY n.versionDate ASC
        WITH entityId, collect(n) as versions
        UNWIND range(0, size(versions)-1) as idx
        WITH versions[idx] as node, idx, size(versions) as total,
             CASE WHEN idx < size(versions)-1 THEN versions[idx+1].versionDate ELSE null END as nextVersionDate
        SET node.validFrom = date(node.versionDate),
            node.validTo = CASE WHEN nextVersionDate IS NULL THEN NULL ELSE date(nextVersionDate) END,
            node.isCurrent = CASE WHEN idx = total-1 THEN true ELSE false END
        """

        try:
            self.query.run(update_temporal_cypher, {'entityIds': entity_ids})
        except Exception as e:
            raise TemporalVersionError(f"Failed to update temporal properties for {entity_label}: {e}", entity_type=entity_label)

        # Step 2: Delete old version chain relationships
        delete_rels_cypher = f"""
        MATCH (n:{entity_label})-[r:NEXT_VERSION]-()
        WHERE n.{id_field} IN $entityIds
        DELETE r
        """

        try:
            self.query.run(delete_rels_cypher, {'entityIds': entity_ids})
        except Exception as e:
            log.warning(f"Could not delete old version relationships: {e}")

        # Step 3: Create new version chain relationships (one-way only)
        create_rels_cypher = f"""
        MATCH (n:{entity_label})
        WHERE n.{id_field} IN $entityIds AND n.versionDate IS NOT NULL
        WITH n.{id_field} as entityId, n
        ORDER BY n.versionDate ASC
        WITH entityId, collect(n) as versions
        UNWIND range(0, size(versions)-2) as idx
        WITH versions[idx] as prev, versions[idx+1] as next
        CREATE (prev)-[:NEXT_VERSION]->(next)
        """

        try:
            self.query.run(create_rels_cypher, {'entityIds': entity_ids})
        except Exception as e:
            raise TemporalVersionError(f"Failed to create version relationships for {entity_label}: {e}", entity_type=entity_label)

        log.info(f"Version chains recalculated for {len(entity_ids)} {entity_label} entities")

    def close(self):
        """Close Neo4j connection"""
        if self.query:
            self.query.close()
