import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.ingestion.intelligence_pipeline import ContentIntelligencePipeline
from app.models.models import IngestedSource, ContentItem, CurriculumChunk

class TestContentIntelligencePipeline(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_sha256_canonical_deduplication(self):
        # 1. First submission of Khan Academy URL
        res1 = ContentIntelligencePipeline.process_and_stage_source(
            db=self.db,
            url="https://www.khanacademy.org/science/biology/cellular-respiration-and-fermentation",
            title="Cellular Respiration and Glycolysis",
            description="Detailed guide to aerobic respiration, Krebs cycle, and ATP synthesis in mitochondria.",
            raw_text="Cellular respiration converts glucose into ATP in the presence of oxygen."
        )
        self.assertTrue(res1["success"])
        self.assertFalse(res1["is_duplicate"])
        self.assertEqual(res1["subject"], "Science")
        self.assertIn("CBSE-G", res1["curriculum_code"])
        source_id = res1["source_id"]

        # 2. Duplicate submission should be detected
        res2 = ContentIntelligencePipeline.process_and_stage_source(
            db=self.db,
            url="https://www.khanacademy.org/science/biology/cellular-respiration-and-fermentation",
            title="Cellular Respiration and Glycolysis",
            description="Duplicate submission test."
        )
        self.assertTrue(res2["success"])
        self.assertTrue(res2["is_duplicate"])
        self.assertEqual(res2["source_id"], source_id)

    def test_source_approval_and_indexing(self):
        # Ingest PhET simulation URL
        res = ContentIntelligencePipeline.process_and_stage_source(
            db=self.db,
            url="https://phet.colorado.edu/sims/html/forces-and-motion-basics/latest/forces-and-motion-basics_all.html",
            title="Forces and Motion Interactive Physics Simulation",
            description="Explore Newton's Second Law of Motion: force equals mass times acceleration (F = ma)."
        )
        self.assertTrue(res["success"])
        source_id = res["source_id"]

        # Approve and index into catalog and RAG store
        approval = ContentIntelligencePipeline.approve_and_index_source(
            db=self.db,
            source_id=source_id,
            reviewer_id="teacher_user_01"
        )
        self.assertTrue(approval["success"])
        self.assertIn("content_item_id", approval)
        self.assertIn("chunk_id", approval)

        # Verify live database records
        item = self.db.query(ContentItem).filter(ContentItem.id == approval["content_item_id"]).first()
        self.assertIsNotNone(item)
        self.assertTrue(item.is_approved)
        self.assertEqual(len(item.embedding), 384)

        chunk = self.db.query(CurriculumChunk).filter(CurriculumChunk.id == approval["chunk_id"]).first()
        self.assertIsNotNone(chunk)
        self.assertEqual(len(chunk.embedding), 384)

if __name__ == "__main__":
    unittest.main()
