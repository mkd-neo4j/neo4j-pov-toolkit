"""
FCA Handbook Domain Models

Data models representing FCA Handbook entities with validation and type safety.

Graph Model Hierarchy:
    (:Handbook) - Top-level handbook container (e.g., PRIN, MIFID, SYSC)
        -[:CONTAINS]-> (:Chapter) - Individual chapters with temporal versioning
            -[:NEXT]-> (:Chapter) - Sequential chapter navigation (one-way)
            -[:NEXT_VERSION]-> (:Chapter) - Temporal version chain (one-way)
            -[:CONTAINS]-> (:Section) - Sections with hierarchical nesting support
                -[:CONTAINS]-> (:Section) - Nested sections (e.g., 1.1 -> 1.1.1)
                -[:CONTAINS]-> (:Provision) - Individual provisions
                    -[:REFERENCES]-> (:Chapter|:Section|:Provision) - Cross-references
                    -[:DEFINES]-> (:GlossaryTerm) - Glossary term definitions
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any
from enum import Enum


class EntityType(Enum):
    """Entity types in the FCA Handbook graph"""
    HANDBOOK = "Handbook"
    CHAPTER = "Chapter"
    SECTION = "Section"
    PROVISION = "Provision"
    GLOSSARY_TERM = "GlossaryTerm"


class ProvisionType(Enum):
    """Types of provisions in the FCA Handbook"""
    RULES = "Rules"
    GUIDANCE = "Guidance"
    EVIDENTIAL = "Evidential"


class ReferenceTargetType(Enum):
    """Types of cross-reference targets"""
    CHAPTER = "chapter"
    SECTION = "section"
    PROVISION = "provision"


@dataclass
class TemporalProperties:
    """Temporal versioning properties shared across all entities"""
    version_date: date
    valid_from: date
    valid_to: Optional[date] = None
    is_current: bool = True

    @classmethod
    def from_iso_string(cls, version_date_str: str) -> 'TemporalProperties':
        """Create temporal properties from ISO date string"""
        version_dt = date.fromisoformat(version_date_str)
        return cls(
            version_date=version_dt,
            valid_from=version_dt,
            valid_to=None,
            is_current=True
        )


@dataclass
class Handbook:
    """FCA Handbook entity (top-level)"""
    handbook_code: str
    handbook_name: str

    def to_neo4j_params(self) -> Dict[str, Any]:
        """Convert to Neo4j parameter dictionary"""
        return {
            'handbookCode': self.handbook_code,
            'handbookName': self.handbook_name
        }


@dataclass
class Chapter:
    """FCA Handbook Chapter entity"""
    chapter_id: str
    temporal: TemporalProperties
    chapter_name: str
    last_modified_date: Optional[str] = None
    next_chapter_id: Optional[str] = None
    previous_chapter_id: Optional[str] = None
    is_chapter_deleted: bool = False
    is_section_deleted: bool = False
    is_header_deleted: bool = False
    chapter_deletion_message: str = ""
    section_deletion_message: str = ""
    is_chapter_future_version: bool = False
    is_section_future_version: bool = False
    chapter_future_version_message: Optional[str] = None
    future_version_date: Optional[str] = None
    breadcrumbs: List[Dict[str, Any]] = field(default_factory=list)

    def to_neo4j_params(self) -> Dict[str, Any]:
        """Convert to Neo4j parameter dictionary"""
        import json
        return {
            'chapterId': self.chapter_id,
            'versionDate': self.temporal.version_date.isoformat(),
            'validFrom': self.temporal.version_date.isoformat(),
            'validTo': self.temporal.valid_to.isoformat() if self.temporal.valid_to else None,
            'isCurrent': self.temporal.is_current,
            'chapterName': self.chapter_name,
            'lastModifiedDate': self.last_modified_date,
            'nextChapterId': self.next_chapter_id,
            'previousChapterId': self.previous_chapter_id,
            'isChapterDeleted': self.is_chapter_deleted,
            'isSectionDeleted': self.is_section_deleted,
            'isHeaderDeleted': self.is_header_deleted,
            'chapterDeletionMessage': self.chapter_deletion_message,
            'sectionDeletionMessage': self.section_deletion_message,
            'isChapterFutureVersion': self.is_chapter_future_version,
            'isSectionFutureVersion': self.is_section_future_version,
            'chapterFutureVersionMessage': self.chapter_future_version_message,
            'futureVersionDate': self.future_version_date,
            'breadcrumbsJson': json.dumps(self.breadcrumbs)
        }


@dataclass
class Section:
    """FCA Handbook Section entity"""
    section_id: str
    temporal: TemporalProperties
    section_name: str
    section_number: str
    level: int
    chapter_id: str
    section_header: str = ""
    section_footer: str = ""

    def to_neo4j_params(self) -> Dict[str, Any]:
        """Convert to Neo4j parameter dictionary"""
        return {
            'sectionId': self.section_id,
            'versionDate': self.temporal.version_date.isoformat(),
            'validFrom': self.temporal.version_date.isoformat(),
            'validTo': self.temporal.valid_to.isoformat() if self.temporal.valid_to else None,
            'isCurrent': self.temporal.is_current,
            'sectionName': self.section_name,
            'sectionNumber': self.section_number,
            'level': self.level,
            'chapterId': self.chapter_id,
            'sectionHeader': self.section_header,
            'sectionFooter': self.section_footer
        }


@dataclass
class Provision:
    """FCA Handbook Provision entity"""
    provision_id: int
    temporal: TemporalProperties
    entity_id: str
    provision_name: str
    provision_number: str
    provision_type: Optional[str]
    provision_type_id: Optional[int]
    provision_tag_id: Optional[int]
    content_text: str
    timeline: Optional[str]
    is_deleted: bool
    section_id: Optional[str]
    section_name: Optional[str]
    sub_section_name: str

    def to_neo4j_params(self) -> Dict[str, Any]:
        """Convert to Neo4j parameter dictionary"""
        return {
            'provisionId': self.provision_id,
            'versionDate': self.temporal.version_date.isoformat(),
            'validFrom': self.temporal.version_date.isoformat(),
            'validTo': self.temporal.valid_to.isoformat() if self.temporal.valid_to else None,
            'isCurrent': self.temporal.is_current,
            'entityId': self.entity_id,
            'provisionName': self.provision_name,
            'provisionNumber': self.provision_number,
            'provisionType': self.provision_type,
            'provisionTypeId': self.provision_type_id,
            'provisionTagId': self.provision_tag_id,
            'contentText': self.content_text,
            'timeline': self.timeline,
            'isDeleted': self.is_deleted,
            'sectionId': self.section_id,
            'sectionName': self.section_name,
            'subSectionName': self.sub_section_name
        }


@dataclass
class GlossaryTerm:
    """FCA Handbook Glossary Term entity"""
    term_id: str
    name: str
    link: Optional[str] = None

    def to_neo4j_params(self) -> Dict[str, Any]:
        """Convert to Neo4j parameter dictionary"""
        return {
            'termId': self.term_id,
            'name': self.name,
            'link': self.link
        }


@dataclass
class CrossReference:
    """Cross-reference between provisions and other entities"""
    source_provision_id: int
    target_type: ReferenceTargetType
    link_text: str
    href: str
    target_chapter_id: Optional[str] = None
    target_section_id: Optional[str] = None
    target_provision_id: Optional[int] = None
    target_anchor: Optional[str] = None

    def to_neo4j_params(self) -> Dict[str, Any]:
        """Convert to Neo4j parameter dictionary"""
        params = {
            'sourceProvisionId': self.source_provision_id,
            'linkText': self.link_text,
            'targetType': self.target_type.value,
            'href': self.href
        }

        if self.target_chapter_id:
            params['targetChapterId'] = self.target_chapter_id
        if self.target_section_id:
            params['targetSectionId'] = self.target_section_id
        if self.target_provision_id:
            params['targetProvisionId'] = self.target_provision_id
        if self.target_anchor:
            params['targetAnchor'] = self.target_anchor

        return params


@dataclass
class HierarchyRelationship:
    """Relationship in the Chapter → Section → Provision hierarchy"""
    parent_type: EntityType
    parent_id: str
    child_type: EntityType
    child_id: str
    temporal: Optional[TemporalProperties] = None

    def to_neo4j_params(self) -> Dict[str, Any]:
        """Convert to Neo4j parameter dictionary"""
        params = {
            'parent_id': self.parent_id,
            'child_id': self.child_id
        }

        if self.temporal:
            params['validFrom'] = self.temporal.valid_from.isoformat()
            params['validTo'] = self.temporal.valid_to.isoformat() if self.temporal.valid_to else None

        return params


@dataclass
class LoaderConfig:
    """Configuration for FCA Handbook loader"""
    batch_size: int = 1000
    validate_only: bool = False
    load_date: Optional[str] = None
    load_all_versions: bool = False
    max_retries: int = 3
    backoff_factor: float = 0.5
    retry_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    request_timeout: int = 30
    api_base_url: str = "https://api-handbook.fca.org.uk/Handbook"

    @property
    def chapter_endpoint(self) -> str:
        return "/GetAllHandBookProvisionsSortedOrderByChapter"

    @property
    def all_handbooks_endpoint(self) -> str:
        return "/GetAllHandbook"

    @property
    def timeline_endpoint(self) -> str:
        return "/GetHandbookTimelineEntries"
