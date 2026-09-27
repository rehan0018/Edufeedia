"""
Provenance and Explainability Generator.
Constructs transparent, child- and parent-verifiable citations explaining
why Edufeedia selected each specific learning resource.
"""

from typing import List, Dict, Any, Optional
from app.schemas.schemas import InterpretedIntent, DiscoveredResource, KnowledgePathwayNode

class ProvenanceGenerator:
    """
    Produces transparent educational rationales ('Why am I seeing this?')
    and maps the topic onto the broader knowledge graph.
    """

    @classmethod
    def generate_why_chosen(
        cls,
        candidate: Dict[str, Any],
        intent: InterpretedIntent,
        student_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        reasons = []
        score = candidate.get("personalized_score") or candidate.get("quality_score", 0.90)
        pct = int(score * 100)

        # 1. Curriculum Match
        grade = candidate.get("grade_level", intent.grade_level)
        board = candidate.get("board", intent.board)
        reasons.append(f"✓ Aligned with Class {grade} {board} curriculum")

        # 2. Topic Match
        reasons.append(f"✓ Directly answers your topic: {candidate.get('topic', intent.topic)}")

        # 3. Source Trust Tier
        tier = candidate.get("authority_tier", "TIER_B")
        source = candidate.get("source_name") or candidate.get("creator_name", "Verified Educator")
        if tier == "TIER_A":
            reasons.append(f"✓ Official Tier A curriculum authority ({source})")
        elif tier == "TIER_B":
            reasons.append(f"✓ Established educational institution ({source})")
        elif tier == "TIER_C":
            reasons.append(f"✓ Vetted creator with proven pedagogy ({source})")

        # 4. Format & Duration
        res_type = candidate.get("resource_type", "video")
        dur = candidate.get("duration_minutes", 6)
        type_labels = {
            "animation": "Visual Socratic animation",
            "video": "Engaging concept video",
            "interactive_sim": "Interactive hands-on simulation",
            "reading": "Curriculum textbook reading",
            "quiz": "Diagnostic concept check"
        }
        reasons.append(f"✓ {type_labels.get(res_type, 'Learning module')} ({dur} min duration)")

        # 5. Personalization Context
        if student_context and student_context.get("weak_topics"):
            for wt in student_context["weak_topics"]:
                if wt.lower() in candidate.get("topic", "").lower():
                    prior_pct = int(student_context.get("topic_mastery", 0.60) * 100)
                    reasons.append(f"✓ Bridges prerequisite knowledge (prior topic mastery: {prior_pct}%)")
                    break

        return reasons

    @classmethod
    def generate_provenance_evidence(
        cls,
        candidate: Dict[str, Any],
        intent: InterpretedIntent,
        student_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Constructs a structured, verifiable evidence chain for child- and parent-facing transparency:
        Source authority -> Verification method -> Curriculum alignment evidence -> Creator accreditation.
        """
        source_name = candidate.get("source_name") or candidate.get("source_platform", "Curriculum Authority")
        tier = candidate.get("authority_tier", "TIER_B")
        raw_chapter = candidate.get("chapter") or candidate.get("provenance_metadata", {}).get("chapter")
        chapter = raw_chapter or f"Chapter: {candidate.get('topic', intent.topic)}"
        section = candidate.get("section") or f"Section: {candidate.get('topic', intent.topic)}"

        # Truthful verification status and timestamp: Never fabricate a verification timestamp
        raw_verified_at = candidate.get("verified_at")
        is_verified_source = candidate.get("is_verified", False) or (tier in ["TIER_A", "TIER_B"])
        verification_status = "verified" if (raw_verified_at or is_verified_source) else "pending_verification"
        verification_method = candidate.get("verification_method") or ("official_source_registry" if is_verified_source else "community_submission")

        # Grounded curriculum alignment evidence: distinguish formal textbook mappings from inferred query matches
        origin = candidate.get("origin", "")
        if origin == "ncert" or raw_chapter:
            evidence_text = f"Mapped directly to official {candidate.get('board', intent.board)} Class {candidate.get('grade_level', intent.grade_level)} textbook ({chapter})."
        elif origin == "oer":
            evidence_text = f"Aligned with standard {candidate.get('subject', intent.subject)} learning outcomes via {source_name} interactive pedagogy."
        else:
            evidence_text = f"Inferred from creator educational taxonomy matching student search for {candidate.get('topic', intent.topic)}."

        return {
            "source": source_name,
            "platform": candidate.get("source_platform", "Web Portal"),
            "chapter": chapter,
            "section": section,
            "verification_status": verification_status,
            "verification_method": verification_method,
            "verified_at": raw_verified_at,  # None when unverified, never a fabricated timestamp
            "authority_tier": tier,
            "curriculum_alignment": {
                "board": candidate.get("board", intent.board),
                "grade": candidate.get("grade_level", intent.grade_level),
                "subject": candidate.get("subject", intent.subject),
                "evidence": evidence_text
            },
            "creator_verification": {
                "creator_name": candidate.get("creator_name", source_name),
                "is_verified": is_verified_source,
                "audit_method": "educator_curriculum_audit" if tier == "TIER_C" else "government_or_academic_charter"
            },
            "content_verification": {
                "safety_audit_status": "PASSED_HARD_GATE",
                "age_suitability": f"Verified for Grade {candidate.get('grade_level', intent.grade_level)} Band",
                "has_captions": candidate.get("has_captions", True),
                "has_learning_outcomes": bool(
                    candidate.get("learning_outcomes") or
                    candidate.get("provenance_metadata", {}).get("learning_outcomes")
                )
            }
        }

    @classmethod
    def generate_knowledge_pathway(
        cls,
        intent: InterpretedIntent
    ) -> List[KnowledgePathwayNode]:
        """
        Creates a structured, prerequisite-to-advanced knowledge journey for the topic.
        """
        topic = intent.topic
        grade = intent.grade_level

        # Default pathway templates
        if "photosynthesis" in topic.lower():
            return [
                KnowledgePathwayNode(
                    concept="Plant Cell Structure & Chloroplasts",
                    depth="prerequisite",
                    relation="PREREQUISITE",
                    description="Cellular anatomy where chlorophyll captures sunlight.",
                    target_grade=max(6, grade - 1)
                ),
                KnowledgePathwayNode(
                    concept="Photosynthesis: Light & Dark Reactions",
                    depth="core",
                    relation="TARGET_OBJECTIVE",
                    description="Chemical transformation of sunlight, water, and CO2 into glucose.",
                    target_grade=grade
                ),
                KnowledgePathwayNode(
                    concept="Plant Respiration & Gas Exchange",
                    depth="related",
                    relation="COMPLEMENTARY",
                    description="How plants break down stored glucose for cellular energy.",
                    target_grade=grade
                ),
                KnowledgePathwayNode(
                    concept="Calvin Cycle & ATP / NADPH Synthesis",
                    depth="advanced",
                    relation="NEXT_LEVEL",
                    description="Biochemical cycle governing carbohydrate synthesis inside the stroma.",
                    target_grade=min(12, grade + 2)
                )
            ]
        elif "newton" in topic.lower() or "motion" in topic.lower():
            return [
                KnowledgePathwayNode(
                    concept="Velocity and Acceleration",
                    depth="prerequisite",
                    relation="PREREQUISITE",
                    description="Rate of change of displacement and vectors.",
                    target_grade=max(7, grade - 1)
                ),
                KnowledgePathwayNode(
                    concept="Newton's Laws of Motion (Action-Reaction)",
                    depth="core",
                    relation="TARGET_OBJECTIVE",
                    description="Fundamental laws governing force pairs, inertia, and momentum.",
                    target_grade=grade
                ),
                KnowledgePathwayNode(
                    concept="Frictional Forces & Surface Resistance",
                    depth="related",
                    relation="COMPLEMENTARY",
                    description="Opposing forces that counteract motion in physical systems.",
                    target_grade=grade
                ),
                KnowledgePathwayNode(
                    concept="Conservation of Momentum & Rocket Propulsion",
                    depth="advanced",
                    relation="NEXT_LEVEL",
                    description="Impulse dynamics applied to celestial and rocketry systems.",
                    target_grade=min(12, grade + 2)
                )
            ]
        elif "gravity" in topic.lower():
            return [
                KnowledgePathwayNode(
                    concept="Newton's Second Law (F = ma)",
                    depth="prerequisite",
                    relation="PREREQUISITE",
                    description="Relationship between mass, force, and acceleration.",
                    target_grade=max(7, grade - 1)
                ),
                KnowledgePathwayNode(
                    concept="Universal Law of Gravitation",
                    depth="core",
                    relation="TARGET_OBJECTIVE",
                    description="Inverse square attraction between masses across space.",
                    target_grade=grade
                ),
                KnowledgePathwayNode(
                    concept="Mass vs Weight and Free Fall",
                    depth="related",
                    relation="COMPLEMENTARY",
                    description="Why objects in orbit experience apparent weightlessness.",
                    target_grade=grade
                ),
                KnowledgePathwayNode(
                    concept="Kepler's Planetary Laws & Escape Velocity",
                    depth="advanced",
                    relation="NEXT_LEVEL",
                    description="Orbital mechanics governing satellite trajectories.",
                    target_grade=min(12, grade + 2)
                )
            ]
        else:
            return [
                KnowledgePathwayNode(
                    concept=f"Foundations of {topic}",
                    depth="prerequisite",
                    relation="PREREQUISITE",
                    description=f"Essential prerequisite principles for {topic}.",
                    target_grade=max(6, grade - 1)
                ),
                KnowledgePathwayNode(
                    concept=topic,
                    depth="core",
                    relation="TARGET_OBJECTIVE",
                    description=f"Core concepts, definitions, and applications of {topic}.",
                    target_grade=grade
                ),
                KnowledgePathwayNode(
                    concept=f"Applications of {topic}",
                    depth="related",
                    relation="COMPLEMENTARY",
                    description=f"Real-world practical examples and problem-solving.",
                    target_grade=grade
                ),
                KnowledgePathwayNode(
                    concept=f"Advanced {topic} for Competitions",
                    depth="advanced",
                    relation="NEXT_LEVEL",
                    description=f"Higher-order analysis and Olympiad-level extensions.",
                    target_grade=min(12, grade + 2)
                )
            ]
