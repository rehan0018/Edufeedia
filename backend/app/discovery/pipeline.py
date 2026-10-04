"""
Discovery Engine Master Pipeline.
Orchestrates the authoritative sequence:
Candidate -> Identity / Provenance -> Safety Policy -> Age Gate ->
Source Authority -> Content Understanding -> Curriculum Alignment ->
Quality Score -> Personalized Reranking -> Diversity / Coverage -> Learning Navigator Payload.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.schemas.schemas import (
    InterpretedIntent, DiscoveredResource, DiscoverySearchResponse,
    ConceptCheckQuiz, ConceptCheckQuestion
)
from app.discovery.query_understanding import QueryUnderstandingEngine
from app.discovery.candidate_builder import CandidateBuilder
from app.discovery.resource_quality import ResourceQualityEngine, ScoringPolicy
from app.discovery.source_registry import SourceAuthorityRegistry
from app.discovery.personalized_reranker import PersonalizedReranker
from app.discovery.provenance import ProvenanceGenerator
from app.models.models import TopicMastery, User


class DiscoveryPipeline:
    """
    Unified intelligence pipeline delivering the full Edufeedia Learning Navigator payload.
    """

    @classmethod
    def execute_discovery(
        cls,
        db: Session,
        query: str,
        student_user: Optional[User] = None,
        custom_policy: Optional[ScoringPolicy] = None
    ) -> DiscoverySearchResponse:
        # 1. Fetch student contextual state if authenticated
        student_context = {}
        student_grade = None
        student_board = None
        weak_topics = []

        if student_user and student_user.role == "student":
            profile = getattr(student_user, "student_profile", None)
            if profile:
                student_grade = profile.grade_level
                student_board = profile.board
                student_context["grade"] = student_grade
                student_context["board"] = student_board
                student_context["preferred_format"] = (profile.learning_preference or [None])[0]

            # Query existing topic masteries
            masteries = db.query(TopicMastery).filter(
                TopicMastery.student_user_id == student_user.id
            ).all()
            for m in masteries:
                if float(m.mastery_score or 0) < 70.0:
                    weak_topics.append(m.topic)
            student_context["weak_topics"] = weak_topics

        # 2. Query Understanding & Intent Interpretation
        intent = QueryUnderstandingEngine.interpret_query(
            query=query,
            student_grade=student_grade,
            student_board=student_board
        )

        # Look up student's specific mastery on this target topic
        topic_mastery_val = 0.65
        if student_user:
            tm_record = db.query(TopicMastery).filter(
                TopicMastery.student_user_id == student_user.id,
                TopicMastery.topic.ilike(f"%{intent.topic}%")
            ).first()
            if tm_record:
                topic_mastery_val = float(tm_record.mastery_score) / 100.0
        student_context["topic_mastery"] = topic_mastery_val

        # 3. Build Federated Candidate Pool (30-50 candidates)
        raw_candidates = CandidateBuilder.build_candidate_pool(
            db=db,
            intent=intent,
            max_total_candidates=40
        )

        # Ensure authoritative sources are seeded in DB
        SourceAuthorityRegistry.ensure_default_sources_seeded(db)

        # 4. Filter through Identity -> Safety -> Age -> Authority -> Quality Scoring
        scored_candidates: List[Dict[str, Any]] = []
        for cand in raw_candidates:
            breakdown, composite_score = ResourceQualityEngine.score_candidate(
                candidate=cand,
                intent=intent,
                student_profile=student_context,
                policy=custom_policy,
                db=db
            )
            if breakdown and composite_score > 0:
                cand["quality_score"] = composite_score
                cand["score_breakdown"] = breakdown
                scored_candidates.append(cand)

        # 5. Personalized Reranking
        reranked_candidates = PersonalizedReranker.rerank_candidates(
            scored_candidates=scored_candidates,
            intent=intent,
            student_context=student_context
        )

        # 6. Transform into DiscoveredResource models with Provenance
        discovered_resources: List[DiscoveredResource] = []
        for c in reranked_candidates:
            why_chosen = ProvenanceGenerator.generate_why_chosen(c, intent, student_context)
            provenance_evidence = ProvenanceGenerator.generate_provenance_evidence(c, intent, student_context)
            res = DiscoveredResource(
                id=c["id"],
                title=c["title"],
                description=c.get("description"),
                resource_type=c.get("resource_type", "video"),
                source_name=c.get("source_name", "Edufeedia Verified"),
                source_platform=c.get("source_platform", "Web"),
                creator_name=c.get("creator_name"),
                authority_tier=c.get("authority_tier", "TIER_B"),
                authority_score=c.get("authority_score", 0.90),
                source_url=c["source_url"],
                embed_url=c.get("embed_url"),
                duration_minutes=c.get("duration_minutes", 6),
                grade_level=c.get("grade_level", intent.grade_level),
                board=c.get("board", intent.board),
                subject=c.get("subject", intent.subject),
                topic=c.get("topic", intent.topic),
                language=c.get("language", "en"),
                quality_score=c.get("personalized_score") or c.get("quality_score", 0.85),
                score_breakdown=c["score_breakdown"],
                why_chosen=why_chosen,
                provenance=provenance_evidence,
                is_verified=c.get("is_verified", True)
            )
            discovered_resources.append(res)

        # 7. Diversity & Categorical Segmentation
        categorized: Dict[str, List[DiscoveredResource]] = {
            "animation": [],
            "video": [],
            "read": [],
            "explore": [],
            "practice": []
        }

        for r in discovered_resources:
            if r.resource_type == "animation":
                categorized["animation"].append(r)
            elif r.resource_type == "video":
                categorized["video"].append(r)
            elif r.resource_type == "reading":
                categorized["read"].append(r)
            elif r.resource_type == "interactive_sim":
                categorized["explore"].append(r)

        # Pick Best Match (prefer top animation or highest scoring video)
        best_match = None
        if categorized["animation"]:
            best_match = categorized["animation"][0]
        elif discovered_resources:
            best_match = discovered_resources[0]

        # 8. Socratic "Understand It" Grade-Appropriate Synthesis
        understand_it = cls.synthesize_understand_it(intent)

        # 9. Interactive 5-Question Concept Check Quiz
        practice_quiz = cls.generate_concept_check(intent)

        # 10. Knowledge Pathway (Prerequisite -> Core -> Advanced)
        pathway = ProvenanceGenerator.generate_knowledge_pathway(intent)

        return DiscoverySearchResponse(
            query=query,
            interpreted_intent=intent,
            understand_it=understand_it,
            best_match=best_match,
            resources_by_category=categorized,
            all_ranked_resources=discovered_resources,
            practice_quiz=practice_quiz,
            knowledge_pathway=pathway,
            student_context={
                "topic_mastery": topic_mastery_val,
                "prior_mastery_pct": int(topic_mastery_val * 100),
                "weak_topics_count": len(weak_topics),
                "is_weak_topic": intent.topic.lower() in [w.lower() for w in weak_topics]
            },
            total_candidates_evaluated=len(raw_candidates),
            policy_version="v1.0"
        )

    @classmethod
    def synthesize_understand_it(cls, intent: InterpretedIntent) -> Dict[str, Any]:
        """
        Synthesizes a concise, pedagogically sound, grade-specific explanation
        answering the core learning objective without overwhelming the student.
        """
        topic = intent.topic.lower()
        grade = intent.grade_level

        if "photosynthesis" in topic:
            return {
                "headline": "How Plants Power the Planet Through Sunlight",
                "grade_adaptation": f"Customized for Class {grade} {intent.board} Science",
                "core_explanation": (
                    "Photosynthesis is the miraculous biological process through which green plants, algae, "
                    "and some bacteria convert light energy into chemical energy. Using chlorophyll inside "
                    "chloroplasts, plants absorb solar energy to combine water (drawn through the roots) and "
                    "carbon dioxide (absorbed from the air via stomata) to create glucose (sugar for energy) "
                    "and release pure oxygen into our atmosphere."
                ),
                "key_equation": "6 CO₂ (Carbon Dioxide) + 6 H₂O (Water) + Light Energy ➔ C₆H₁₂O₆ (Glucose) + 6 O₂ (Oxygen)",
                "key_takeaways": [
                    "Sunlight is absorbed by green chlorophyll pigments in chloroplast organelles.",
                    "Water is transported from roots through xylem vessels to the leaves.",
                    "Carbon dioxide enters through microscopic leaf pores called stomata.",
                    "Oxygen is released as a vital byproduct, supporting all terrestrial animal life."
                ],
                "vocabulary": [
                    {"term": "Chloroplast", "definition": "Cellular plant organelle where photosynthesis takes place."},
                    {"term": "Stomata", "definition": "Microscopic pores on leaf surfaces that open and close to exchange gases."},
                    {"term": "Autotroph", "definition": "An organism capable of producing its own organic nutrients from inorganic substances."}
                ]
            }
        elif "newton" in topic or "motion" in topic:
            return {
                "headline": "Forces in Nature Always Occur in Equal & Opposite Pairs",
                "grade_adaptation": f"Customized for Class {grade} {intent.board} Physics",
                "core_explanation": (
                    "Newton's Third Law of Motion states: 'To every action, there is always an equal and opposite reaction.' "
                    "Crucially, these paired forces act on two DIFFERENT objects at the exact same instant, which is why "
                    "they never cancel each other out. When you push against the ground, the ground pushes back on your foot "
                    "with equal force, propelling you forward."
                ),
                "key_equation": "F_A_on_B = - F_B_on_A (Action Force = - Reaction Force)",
                "key_takeaways": [
                    "Forces never exist in isolation; they are always mutual interactions between two bodies.",
                    "Action and reaction forces have identical magnitude but opposite direction.",
                    "Action and reaction forces act on different bodies simultaneously."
                ],
                "vocabulary": [
                    {"term": "Inertia", "definition": "The resistance of any physical object to a change in its velocity."},
                    {"term": "Momentum", "definition": "The product of an object's mass and its velocity (p = mv)."},
                    {"term": "Normal Force", "definition": "The support force exerted upon an object that is in contact with another stable object."}
                ]
            }
        elif "gravity" in topic:
            return {
                "headline": "The Universal Invisible Pull That Holds the Cosmos Together",
                "grade_adaptation": f"Customized for Class {grade} {intent.board} Physics",
                "core_explanation": (
                    "Gravity is an attractive force that exists between any two pieces of matter in the universe. "
                    "Sir Isaac Newton realized that the exact same force pulling an apple down from a tree also keeps "
                    "the Moon in orbit around the Earth. The strength of gravitational pull increases with greater mass "
                    "and decreases sharply as the distance between objects increases."
                ),
                "key_equation": "F = G × (m₁ × m₂) / r²",
                "key_takeaways": [
                    "Every object with mass exerts gravitational pull on every other object.",
                    "On Earth, acceleration due to gravity (g) is approximately 9.8 m/s².",
                    "Mass is constant everywhere; weight is the gravitational force acting on that mass."
                ],
                "vocabulary": [
                    {"term": "Free Fall", "definition": "Motion of an object where gravity is the only force acting upon it."},
                    {"term": "Gravitational Constant (G)", "definition": "Universal constant equal to 6.674 × 10⁻¹¹ N·m²/kg²."}
                ]
            }
        else:
            return {
                "headline": f"Core Learning Essentials: {intent.topic}",
                "grade_adaptation": f"Class {grade} {intent.board} Curriculum Reference",
                "core_explanation": f"Foundational Socratic principles and conceptual breakdown of {intent.topic} designed for Class {grade} students.",
                "key_equation": "Comprehensive curriculum synthesis",
                "key_takeaways": [
                    f"Understand the fundamental definition and real-world significance of {intent.topic}.",
                    "Analyze how this concept connects to prerequisite principles.",
                    "Apply theoretical principles to practical curriculum problem sets."
                ],
                "vocabulary": [
                    {"term": intent.topic, "definition": f"Core curriculum topic in Class {grade} {intent.subject}."}
                ]
            }

    @classmethod
    def generate_concept_check(cls, intent: InterpretedIntent) -> ConceptCheckQuiz:
        """
        Constructs an interactive 5-question concept check quiz testing
        conceptual comprehension of the discovered topic.
        """
        topic = intent.topic.lower()
        grade = intent.grade_level

        if "photosynthesis" in topic:
            questions = [
                ConceptCheckQuestion(
                    id="q1",
                    question_text="Which cellular organelle in green plant cells is responsible for capturing light energy?",
                    options=["Mitochondria", "Chloroplast", "Golgi Apparatus", "Vacuole"],
                    correct_option_index=1,
                    explanation="Chloroplasts contain green chlorophyll pigments that absorb photons and initiate photosynthesis."
                ),
                ConceptCheckQuestion(
                    id="q2",
                    question_text="What are the essential raw materials required for photosynthesis?",
                    options=["Oxygen and Glucose", "Carbon Dioxide and Water", "Nitrogen and Sunlight", "Hydrogen and Soil Minerals"],
                    correct_option_index=1,
                    explanation="Plants take in carbon dioxide (CO2) from the air and water (H2O) from the soil to produce glucose and oxygen."
                ),
                ConceptCheckQuestion(
                    id="q3",
                    question_text="Through which microscopic structures on leaves does carbon dioxide enter the plant?",
                    options=["Xylem", "Stomata", "Cuticle", "Phloem"],
                    correct_option_index=1,
                    explanation="Stomata are small pore openings guarded by guard cells on leaf surfaces that regulate gas exchange."
                ),
                ConceptCheckQuestion(
                    id="q4",
                    question_text="What vital gas is released into the atmosphere as a byproduct of photosynthesis?",
                    options=["Carbon Monoxide", "Nitrogen", "Oxygen", "Methane"],
                    correct_option_index=2,
                    explanation="Water molecules are split during light reactions (photolysis), releasing O2 oxygen gas into the air."
                ),
                ConceptCheckQuestion(
                    id="q5",
                    question_text="In what form do plants store excess synthesized carbohydrates?",
                    options=["Starch", "Cellulose", "Protein", "Glycogen"],
                    correct_option_index=0,
                    explanation="Plants convert produced glucose into insoluble starch granules for storage in leaves, stems, and tubers."
                )
            ]
        elif "newton" in topic or "motion" in topic:
            questions = [
                ConceptCheckQuestion(
                    id="q1",
                    question_text="According to Newton's Third Law, how do action and reaction forces compare?",
                    options=[
                        "Action force is always greater",
                        "Equal in magnitude, opposite in direction, acting on different bodies",
                        "Equal in magnitude, same direction, acting on the same body",
                        "Reaction force occurs only after a 1-second delay"
                    ],
                    correct_option_index=1,
                    explanation="Action-reaction pairs are strictly equal in magnitude, opposite in direction, and act on two distinct objects."
                ),
                ConceptCheckQuestion(
                    id="q2",
                    question_text="Why don't action and reaction forces cancel each other out?",
                    options=[
                        "Because one force is stronger than the other",
                        "Because they act on different bodies simultaneously",
                        "Because gravity overcomes them",
                        "Because friction cancels only the reaction force"
                    ],
                    correct_option_index=1,
                    explanation="Forces can only cancel out if they act on the SAME body. Action and reaction always act on different bodies."
                ),
                ConceptCheckQuestion(
                    id="q3",
                    question_text="When a swimmer pushes water backwards, what propels the swimmer forward?",
                    options=[
                        "The reaction force of the water pushing forward on the swimmer",
                        "The swimmer's buoyancy alone",
                        "Water gravity pulling the swimmer",
                        "Surface tension"
                    ],
                    correct_option_index=0,
                    explanation="The swimmer exerts force backwards on the water; by Newton's Third Law, the water pushes forward on the swimmer."
                ),
                ConceptCheckQuestion(
                    id="q4",
                    question_text="What is the SI unit of force in Newton's equations?",
                    options=["Joule (J)", "Pascal (Pa)", "Newton (N)", "Watt (W)"],
                    correct_option_index=2,
                    explanation="Force is measured in Newtons (N), where 1 N = 1 kg·m/s²."
                ),
                ConceptCheckQuestion(
                    id="q5",
                    question_text="Which law of motion explains why rockets can accelerate in the vacuum of space?",
                    options=[
                        "Newton's First Law (Inertia)",
                        "Newton's Second Law (F=ma) alone",
                        "Newton's Third Law (Conservation of Momentum via exhaust action-reaction)",
                        "Kepler's Law of Areas"
                    ],
                    correct_option_index=2,
                    explanation="Rockets expel hot gas exhaust backwards at high velocity; the exhaust pushes the rocket forward with equal force."
                )
            ]
        else:
            questions = [
                ConceptCheckQuestion(
                    id="q1",
                    question_text=f"What is the foundational definition of {intent.topic}?",
                    options=[
                        f"Core foundational scientific principle of {intent.topic}",
                        "An unrelated physical phenomenon",
                        "An obsolete mathematical theorem",
                        "A chemical element on the periodic table"
                    ],
                    correct_option_index=0,
                    explanation=f"Understanding {intent.topic} begins with mastering its core physical or biological definitions."
                ),
                ConceptCheckQuestion(
                    id="q2",
                    question_text=f"Which real-world application directly relies on {intent.topic}?",
                    options=[
                        f"Technological and ecological systems governed by {intent.topic}",
                        "Random atmospheric turbulence",
                        "Ancient hieroglyphics",
                        "Static non-interacting objects"
                    ],
                    correct_option_index=0,
                    explanation=f"Concepts in {intent.topic} directly inform modern scientific and technological advancements."
                ),
                ConceptCheckQuestion(
                    id="q3",
                    question_text=f"In Class {grade} {intent.subject}, which unit of measurement or standard formula is applied?",
                    options=[
                        "Standard SI and curriculum-aligned notation",
                        "Arbitrary uncalibrated scales",
                        "Imperial fathoms and furlongs",
                        "Fahrenheit only"
                    ],
                    correct_option_index=0,
                    explanation="Curriculum questions require standard SI units and certified equations."
                ),
                ConceptCheckQuestion(
                    id="q4",
                    question_text=f"What is a common misconception students encounter when studying {intent.topic}?",
                    options=[
                        "Confusing cause with effect or mixing up action-reaction bodies",
                        "Believing that numbers cannot be negative",
                        "Assuming planets are perfect cubes",
                        "None of the above"
                    ],
                    correct_option_index=0,
                    explanation="Careful conceptual analysis avoids confusing cause-effect and force pairs."
                ),
                ConceptCheckQuestion(
                    id="q5",
                    question_text=f"How does mastering {intent.topic} prepare you for higher-grade science?",
                    options=[
                        "It forms the essential prerequisite for advanced curriculum topics",
                        "It is never tested again after Class " + str(grade),
                        "It only applies to historical philosophy",
                        "It has no connection to future modules"
                    ],
                    correct_option_index=0,
                    explanation="Every core NCERT topic is a stepping stone for competitive and higher secondary examinations."
                )
            ]

        return ConceptCheckQuiz(
            quiz_id=f"quiz-check-{grade}-{intent.topic.lower().replace(' ', '-')}",
            topic=intent.topic,
            grade_level=grade,
            questions=questions,
            total_questions=5
        )
