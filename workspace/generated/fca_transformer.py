"""
FCA Handbook Data Transformer

Transforms raw API data into domain models with validation.
"""

import sys
import os
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.logger import log
from workspace.generated.fca_models import (
    Handbook, Chapter, Section, Provision, GlossaryTerm, CrossReference,
    HierarchyRelationship, TemporalProperties, EntityType, ReferenceTargetType
)
from workspace.generated.fca_exceptions import DataValidationError


class FCADataTransformer:
    """
    Transforms FCA API data into domain models

    Responsibilities:
    - Parse API responses into typed models
    - Extract hierarchical structure from provision names
    - Parse HTML content for cross-references
    - Validate data integrity
    """

    @staticmethod
    def convert_fca_date_to_iso(fca_date: str) -> str:
        """
        Convert FCA date format (DD/MM/YYYY or DD-MM-YYYY) to ISO format (YYYY-MM-DD)

        Args:
            fca_date: Date in DD/MM/YYYY or DD-MM-YYYY format

        Returns:
            Date in YYYY-MM-DD format

        Raises:
            DataValidationError: If date format is invalid
        """
        # Handle both / and - separators
        fca_date = fca_date.replace('/', '-')

        try:
            dt = datetime.strptime(fca_date, '%d-%m-%Y')
            return dt.date().isoformat()
        except ValueError as e:
            raise DataValidationError(f"Invalid date format '{fca_date}': {e}")

    @staticmethod
    def parse_hierarchy(provision_name: str) -> List[str]:
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

    @staticmethod
    def parse_reference_target(href: str, link_text: str) -> Optional[Dict]:
        """
        Parse reference target from href to determine what it points to

        Args:
            href: Link href (e.g., "/handbook/prin2", "/handbook/gen2/gen2s2#p40456")
            link_text: Display text of the link

        Returns:
            Dictionary with targetType and target identifiers, or None if invalid
        """
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
                'targetType': ReferenceTargetType.PROVISION,
                'targetChapterId': chapter_id,
                'targetSectionId': section_id,
                'targetAnchor': anchor
            }
        elif section_id:
            # Section reference
            return {
                'targetType': ReferenceTargetType.SECTION,
                'targetChapterId': chapter_id,
                'targetSectionId': section_id
            }
        else:
            # Chapter reference
            return {
                'targetType': ReferenceTargetType.CHAPTER,
                'targetChapterId': chapter_id
            }

    @classmethod
    def extract_cross_references(cls, html_content: str, source_provision_id: int) -> List[CrossReference]:
        """
        Extract cross-references from HTML content

        Parses the contentType HTML field to find:
        - Cross-references to other provisions (in <span class="xref">)
        - Direct handbook links

        Args:
            html_content: HTML content from provision's contentType field
            source_provision_id: ID of the source provision

        Returns:
            List of CrossReference objects
        """
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
                target_info = cls.parse_reference_target(href, link_text)

                if target_info:
                    target_type = target_info.pop('targetType')
                    cross_ref = CrossReference(
                        source_provision_id=source_provision_id,
                        target_type=target_type,
                        link_text=link_text,
                        href=href,
                        target_chapter_id=target_info.get('targetChapterId'),
                        target_section_id=target_info.get('targetSectionId'),
                        target_anchor=target_info.get('targetAnchor')
                    )

                    # Extract provision ID from anchor if present
                    if target_type == ReferenceTargetType.PROVISION and target_info.get('targetAnchor'):
                        anchor = target_info['targetAnchor']
                        if anchor.startswith('p'):
                            try:
                                cross_ref.target_provision_id = int(anchor[1:])
                            except ValueError:
                                log.warning(f"Could not parse provision ID from anchor: {anchor}")

                    cross_refs.append(cross_ref)

        except Exception as e:
            log.warning(f"Error parsing cross-references for provision {source_provision_id}: {e}")

        return cross_refs

    @staticmethod
    def transform_handbook(handbook_code: str, handbook_name: str) -> Handbook:
        """
        Transform handbook data into Handbook model

        Args:
            handbook_code: Handbook code (e.g., "prin", "mifid")
            handbook_name: Full handbook name

        Returns:
            Handbook domain model
        """
        return Handbook(
            handbook_code=handbook_code.lower(),
            handbook_name=handbook_name
        )

    @classmethod
    def transform_chapter(cls, api_data: Dict, version_date: str) -> Chapter:
        """
        Transform API chapter data into Chapter model

        Args:
            api_data: Raw API data for chapter
            version_date: Version date in ISO format (YYYY-MM-DD)

        Returns:
            Chapter domain model

        Raises:
            DataValidationError: If required fields are missing
        """
        chapter_id = api_data.get('chapterId')
        if not chapter_id:
            raise DataValidationError("Missing required field: chapterId")

        temporal = TemporalProperties.from_iso_string(version_date)

        return Chapter(
            chapter_id=chapter_id,
            temporal=temporal,
            chapter_name=api_data.get('chapterName', ''),
            last_modified_date=api_data.get('lastModifiedDate'),
            next_chapter_id=api_data.get('nextChapterId'),
            previous_chapter_id=api_data.get('previousChapterId'),
            is_chapter_deleted=api_data.get('isChapterDeleted', False),
            is_section_deleted=api_data.get('isSectionDeleted', False),
            is_header_deleted=api_data.get('isHeaderDeleted', False),
            chapter_deletion_message=api_data.get('chapterDeletionMessage', ''),
            section_deletion_message=api_data.get('sectionDeletionMessage', ''),
            is_chapter_future_version=api_data.get('isChapterFutureVersion', False),
            is_section_future_version=api_data.get('isSectionFutureVersion', False),
            chapter_future_version_message=api_data.get('chapterFutureVersionMessage'),
            future_version_date=api_data.get('futureVersionDate'),
            breadcrumbs=api_data.get('breadCrumbs', [])
        )

    @classmethod
    def transform_provisions(
        cls,
        api_provisions: List[Dict],
        chapter_id: str,
        version_date: str
    ) -> Tuple[Dict[str, Section], List[Provision], List[HierarchyRelationship], List[CrossReference], List[Tuple[int, str]]]:
        """
        Transform API provisions into domain models and relationships

        Args:
            api_provisions: List of provision dictionaries from API
            chapter_id: Parent chapter ID
            version_date: Version date in ISO format

        Returns:
            Tuple of (sections_dict, provisions_list, hierarchy_relationships, cross_references, provision_glossary_links)
        """
        temporal = TemporalProperties.from_iso_string(version_date)

        sections = {}  # section_id -> Section
        provisions = []
        hierarchy_rels = []
        cross_refs = []
        provision_glossary = []  # (provision_id, term_id) tuples

        for prov_data in api_provisions:
            provision_name = prov_data.get('provisionName', '')
            provision_id = prov_data.get('provisionId')

            if not provision_id or not provision_name:
                log.warning(f"Skipping provision with missing ID or name: {prov_data}")
                continue

            # Parse hierarchy from provision name
            hierarchy = cls.parse_hierarchy(provision_name)
            handbook_code = hierarchy[0] if hierarchy else chapter_id.upper()

            # Create section nodes for each level in the hierarchy
            for i in range(1, len(hierarchy) - 1):  # Skip handbook code and final provision
                section_num = hierarchy[i]
                section_id = f"{handbook_code.lower()}{section_num}"

                if section_id not in sections:
                    section_name = f"{handbook_code} {section_num}"

                    sections[section_id] = Section(
                        section_id=section_id,
                        temporal=TemporalProperties.from_iso_string(version_date),
                        section_name=section_name,
                        section_number=section_num,
                        level=i,
                        chapter_id=chapter_id,
                        section_header=prov_data.get('sectionHeader', ''),
                        section_footer=prov_data.get('sectionFooter', '')
                    )

                # Create hierarchy relationship
                if i > 1:
                    # Parent is the previous level
                    parent_num = hierarchy[i-1]
                    parent_id = f"{handbook_code.lower()}{parent_num}"

                    hierarchy_rels.append(HierarchyRelationship(
                        parent_type=EntityType.SECTION,
                        parent_id=parent_id,
                        child_type=EntityType.SECTION,
                        child_id=section_id,
                        temporal=TemporalProperties.from_iso_string(version_date)
                    ))
                else:
                    # Top-level section connects to chapter
                    hierarchy_rels.append(HierarchyRelationship(
                        parent_type=EntityType.CHAPTER,
                        parent_id=chapter_id,
                        child_type=EntityType.SECTION,
                        child_id=section_id,
                        temporal=TemporalProperties.from_iso_string(version_date)
                    ))

            # Create provision
            if len(hierarchy) >= 2:
                parent_section_num = hierarchy[-2]
                parent_section_id = f"{handbook_code.lower()}{parent_section_num}"

                provision = Provision(
                    provision_id=provision_id,
                    temporal=TemporalProperties.from_iso_string(version_date),
                    entity_id=prov_data.get('entityId', ''),
                    provision_name=provision_name,
                    provision_number=hierarchy[-1] if hierarchy else '',
                    provision_type=prov_data.get('provisionType'),
                    provision_type_id=prov_data.get('provisionTypeId'),
                    provision_tag_id=prov_data.get('provisionTagId'),
                    content_text=prov_data.get('contentText', ''),
                    timeline=prov_data.get('timeline'),
                    is_deleted=prov_data.get('isDeleted', False),
                    section_id=prov_data.get('sectionId'),
                    section_name=prov_data.get('sectionName'),
                    sub_section_name=prov_data.get('subSectionName', '')
                )

                provisions.append(provision)

                # Add provision-to-section hierarchy
                hierarchy_rels.append(HierarchyRelationship(
                    parent_type=EntityType.SECTION,
                    parent_id=parent_section_id,
                    child_type=EntityType.PROVISION,
                    child_id=str(provision_id),
                    temporal=TemporalProperties.from_iso_string(version_date)
                ))

                # Extract cross-references
                html_content = prov_data.get('contentType', '')
                if html_content:
                    prov_cross_refs = cls.extract_cross_references(html_content, provision_id)
                    cross_refs.extend(prov_cross_refs)

                # Track glossary terms
                for term_data in prov_data.get('glossaryTerm', []):
                    term_id = term_data.get('termId')
                    if term_id:
                        provision_glossary.append((provision_id, term_id))

        return sections, provisions, hierarchy_rels, cross_refs, provision_glossary

    @staticmethod
    def transform_glossary_terms(provisions_data: List[Dict]) -> Dict[str, GlossaryTerm]:
        """
        Extract unique glossary terms from provisions data

        Args:
            provisions_data: List of provision dictionaries from API

        Returns:
            Dictionary of term_id -> GlossaryTerm
        """
        terms = {}

        for prov_data in provisions_data:
            for term_data in prov_data.get('glossaryTerm', []):
                term_id = term_data.get('termId')
                if term_id and term_id not in terms:
                    terms[term_id] = GlossaryTerm(
                        term_id=term_id,
                        name=term_data.get('name', ''),
                        link=term_data.get('link')
                    )

        return terms
