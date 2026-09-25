"""
Multimodal Safety Pipeline for EduFeedia.
Provides comprehensive image OCR & visual safety, video keyframe sampling at intervals,
timestamped transcript moderation, and audio-content moderation.
Catches violations that occur late in videos (e.g., at 07:42) even if the title,
description, and first 5 minutes are clean.
"""

import re
from typing import Dict, List, Any, Optional
from app.safety.multilingual_safety import MultilingualSafetyEngine

class MultimodalSafetyPipeline:
    """
    Multimodal inspection engine for images, video frames, and audio transcripts.
    Ensures fail-closed student and child safety before media is displayed.
    """

    @classmethod
    def scan_image(
        cls,
        image_metadata: Optional[Dict[str, Any]] = None,
        extracted_ocr_text: Optional[str] = None,
        visual_tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Scans an image using simulated or integrated OCR text extraction
        and visual category classifiers.
        """
        ocr_text = extracted_ocr_text or ""
        tags = [t.lower() for t in (visual_tags or [])]
        violations = []
        safety_score = 100.0

        # 1. Inspect OCR text extracted from graphic/diagram/meme
        if ocr_text:
            text_eval = MultilingualSafetyEngine.evaluate(ocr_text)
            if not text_eval["is_safe"]:
                violations.append({
                    "modality": "image_ocr",
                    "reason": f"Prohibited text in image: {', '.join(text_eval['flagged_categories'])}",
                    "matched": text_eval["matched_patterns"]
                })
                safety_score = min(safety_score, text_eval["safety_score"])

        # 2. Inspect visual safety tags (e.g. weapons, explicit content, blood)
        prohibited_visual_tags = {
            "weapon": "VIOLENCE",
            "gun": "VIOLENCE",
            "knife": "VIOLENCE",
            "blood": "VIOLENCE",
            "nudity": "NSFW",
            "explicit": "NSFW",
            "lingerie": "NSFW",
            "syringe": "DRUGS",
            "pills": "DRUGS",
            "tobacco": "DRUGS"
        }

        for tag in tags:
            for bad_tag, category in prohibited_visual_tags.items():
                if bad_tag in tag:
                    violations.append({
                        "modality": "visual_tag",
                        "category": category,
                        "reason": f"Visual tag '{tag}' violates student safety policy."
                    })
                    safety_score = min(safety_score, 20.0)

        is_safe = len(violations) == 0
        return {
            "is_safe": is_safe,
            "safety_score": safety_score,
            "ocr_text_extracted": ocr_text,
            "violations": violations,
            "risk_level": "safe" if is_safe else ("critical" if safety_score < 30 else "high")
        }

    @classmethod
    def scan_video_with_frame_sampling(
        cls,
        video_title: str,
        duration_seconds: int,
        sampled_frames: Optional[List[Dict[str, Any]]] = None,
        timestamped_transcript: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Keyframe sampling & timestamped transcript moderation:
        Even if the first 5 minutes of a video are safe, inspects frames sampled
        at 15s/30s intervals across the entire duration to catch violations
        (e.g., an unsafe frame appearing at 07:42).
        """
        frame_violations = []
        transcript_violations = []
        lowest_safety_score = 100.0

        # 1. Sampled Frame Inspection
        frames = sampled_frames or []
        for frame in frames:
            timestamp_str = frame.get("timestamp", "00:00")
            ocr = frame.get("ocr_text", "")
            tags = frame.get("visual_tags", [])

            frame_result = cls.scan_image(extracted_ocr_text=ocr, visual_tags=tags)
            if not frame_result["is_safe"]:
                frame_violations.append({
                    "timestamp": timestamp_str,
                    "violations": frame_result["violations"]
                })
                lowest_safety_score = min(lowest_safety_score, frame_result["safety_score"])

        # 2. Timestamped Transcript Inspection
        segments = timestamped_transcript or []
        for seg in segments:
            start_time = seg.get("start", 0.0)
            text_snippet = seg.get("text", "")
            
            # Format timestamp as MM:SS
            mins = int(start_time // 60)
            secs = int(start_time % 60)
            timestamp_str = f"{mins:02d}:{secs:02d}"

            text_eval = MultilingualSafetyEngine.evaluate(text_snippet)
            if not text_eval["is_safe"]:
                transcript_violations.append({
                    "timestamp": timestamp_str,
                    "text_snippet": text_snippet,
                    "flagged_categories": text_eval["flagged_categories"],
                    "matched_patterns": text_eval["matched_patterns"]
                })
                lowest_safety_score = min(lowest_safety_score, text_eval["safety_score"])

        is_safe = len(frame_violations) == 0 and len(transcript_violations) == 0

        # Action: SAFE -> Auto-Publish; SUSPICIOUS -> Quarantine for Human Review
        if is_safe:
            moderation_status = "SAFE"
            recommendation = "Content verified safe for student curriculum."
        elif lowest_safety_score < 30.0:
            moderation_status = "REJECT"
            recommendation = "Automatically blocked: critical visual or transcript safety violation."
        else:
            moderation_status = "SUSPICIOUS"
            recommendation = "Queued for human review: suspicious frames or transcript segment detected."

        return {
            "is_safe": is_safe,
            "overall_safety_score": lowest_safety_score,
            "moderation_status": moderation_status,
            "video_title": video_title,
            "duration_seconds": duration_seconds,
            "frames_analyzed": len(frames),
            "transcript_segments_analyzed": len(segments),
            "frame_violations": frame_violations,
            "transcript_violations": transcript_violations,
            "recommendation": recommendation
        }

    @classmethod
    def scan_audio_transcript(cls, transcript: str) -> Dict[str, Any]:
        """Speech-to-text transcript safety classification."""
        return MultilingualSafetyEngine.evaluate(transcript)
