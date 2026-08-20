"""
Edufeedia Safety & Compliance Layer.
Provides unified Under-18 safety policy enforcement, age-appropriateness gating,
and multi-category content classification.
"""

from app.safety.policy_engine import policy_engine, PolicyEngine
from app.safety.age_policy import age_policy, AgePolicy
from app.safety.content_classifier import content_classifier, ContentClassifier

__all__ = ["policy_engine", "PolicyEngine", "age_policy", "AgePolicy", "content_classifier", "ContentClassifier"]
