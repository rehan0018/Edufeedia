import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ingestion.adapters.youtube import YouTubeAdapter
from app.ingestion.adapters.oer_adapter import OERContentAdapter
from app.ingestion.adapters.factory import ContentFetcherFactory

class TestSourceAdapters(unittest.TestCase):
    def setUp(self):
        self.yt_adapter = YouTubeAdapter()
        self.oer_adapter = OERContentAdapter()

    def test_youtube_adapter_video_handling(self):
        # Valid YouTube URL
        url = "https://www.youtube.com/watch?v=kKKM8Y-u7ds"
        self.assertTrue(self.yt_adapter.can_handle(url))

        data = self.yt_adapter.fetch_content_metadata(url)
        self.assertTrue(data["success"])
        self.assertEqual(data["platform"], "youtube")
        self.assertEqual(data["video_id"], "kKKM8Y-u7ds")
        self.assertIn("youtube-nocookie.com/embed/kKKM8Y-u7ds", data["embed_code"])
        self.assertTrue(data["is_child_safe_embed"])

    def test_oer_adapter_khan_academy(self):
        url = "https://www.khanacademy.org/science/physics/forces-newtons-laws"
        self.assertTrue(self.oer_adapter.can_handle(url))

        data = self.oer_adapter.fetch_content_metadata(url)
        self.assertTrue(data["success"])
        self.assertEqual(data["platform"], "khan_academy")
        self.assertEqual(data["title"], "Forces Newtons Laws")
        self.assertTrue(data["is_official_oer"])

    def test_oer_adapter_phet_simulation(self):
        url = "https://phet.colorado.edu/sims/html/circuit-construction-kit-dc/latest/circuit-construction-kit-dc_all.html"
        self.assertTrue(self.oer_adapter.can_handle(url))

        data = self.oer_adapter.fetch_content_metadata(url)
        self.assertTrue(data["success"])
        self.assertEqual(data["platform"], "phet")
        self.assertIn("<iframe", data["embed_code"])

    def test_content_fetcher_factory_dispatch(self):
        # Dispatch to YouTube
        yt_fetch = ContentFetcherFactory.fetch("https://youtu.be/dQw4w9WgXcQ")
        self.assertTrue(yt_fetch["success"])
        self.assertEqual(yt_fetch["platform"], "youtube")

        # Dispatch to Khan Academy
        oer_fetch = ContentFetcherFactory.fetch("https://www.khanacademy.org/math/algebra/quadratics")
        self.assertTrue(oer_fetch["success"])
        self.assertEqual(oer_fetch["platform"], "khan_academy")

        # Unsupported domain
        unsupported = ContentFetcherFactory.fetch("https://example-random-domain.com/page")
        self.assertFalse(unsupported["success"])
        self.assertEqual(unsupported["error"], "UNSUPPORTED_ADAPTER")

if __name__ == "__main__":
    unittest.main()
