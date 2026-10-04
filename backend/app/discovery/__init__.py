"""
Edufeedia Intelligent Educational Discovery & Resource Intelligence Engine.
Discovers, verifies, ranks, explains, and connects students to trusted learning resources.
"""

from app.discovery.query_understanding import QueryUnderstandingEngine
from app.discovery.source_registry import SourceAuthorityRegistry
from app.discovery.resource_quality import ResourceQualityEngine, ScoringPolicy
from app.discovery.pipeline import DiscoveryPipeline
from app.discovery.learning_loop import LearningLoopManager

__all__ = [
    "QueryUnderstandingEngine",
    "SourceAuthorityRegistry",
    "ResourceQualityEngine",
    "ScoringPolicy",
    "DiscoveryPipeline",
    "LearningLoopManager"
]
