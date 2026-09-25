"""
Multilingual & Adversarial Safety Engine for EduFeedia.
Provides deep protection against regional toxicity, Hinglish slang, transliteration,
code-switching, leetspeak obfuscation, and jailbreak bypasses across Indian languages.
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Any, Optional

# 1. Leetspeak & Obfuscation Normalization Map
LEET_CHAR_MAP = {
    '0': 'o', '1': 'i', '!': 'i', '|': 'i', '3': 'e', '4': 'a', '@': 'a',
    '5': 's', '$': 's', '7': 't', '+': 't', '8': 'b', '9': 'g', '2': 'z'
}

# Dangerous Emoji Sequences in Child Safety Contexts
RISK_EMOJI_PATTERNS = {
    "VIOLENCE": ["🔪", "💣", "🔫", "🗡️", "🩸"],
    "SELF_HARM": ["☠️", "💀", "💊", "💉", "🪢"],
    "NSFW": ["🔞", "🍆", "🍑"]
}

# 2. Comprehensive Multilingual & Transliterated Taxonomy
# Covers English, Hindi (Devanagari & Latin Hinglish), Marathi, Tamil, Telugu, Bengali
MULTILINGUAL_TAXONOMY: Dict[str, Dict[str, List[str]]] = {
    "VIOLENCE_AND_WEAPONS": {
        "hi_latin": [
            "maar daal", "chaku maar", "goli maar", "katl kar", "jaan se maar",
            "bomb banana", "hathiyar", "talwar", "danga karna", "pitai karna"
        ],
        "hi_devanagari": [
            "मार डाल", "गोली मार", "चाकू मार", "हत्या", "कत्ल", "बम बनाना", "बम",
            "हथियार", "दंगा", "खून खराबा", "विस्फोटक", "चाकू"
        ],
        "mr_latin": ["marun taak", "shastra", "rakhtapaat", "bhaandana"],
        "mr_devanagari": ["मारून टाक", "हत्या", "शस्त्र", "रक्तपात", "भांडण"],
        "ta_latin": ["kolai sei", "thakku", "aayudham", "kuthu"],
        "te_latin": ["champadam", "aayudham", "narakadam", "kottu"],
        "bn_latin": ["mere phel", "khun kor", "ostro", "boma banano"],
        "en": [
            "kill", "murder", "stab", "assault", "homemade explosive", "shoot up",
            "pipe bomb", "mass shooting", "torture", "decapitate"
        ]
    },
    "SELF_HARM": {
        "hi_latin": [
            "aatmhatya", "suicide kaise kare", "nas kaatna", "zehar khana", "mar jana chahta hu",
            "jaan dena", "khud ko chot"
        ],
        "hi_devanagari": [
            "आत्महत्या", "नसों को काटना", "जहर खाना", "मर जाना चाहता हूँ", "खुदकुशी", "आत्मघात"
        ],
        "mr_latin": ["aatmahatya", "vish ghene", "jeev dene"],
        "mr_devanagari": ["आत्महत्या", "विष घेणे", "जीव देणे"],
        "ta_latin": ["tharkolai", "vishayam kudi", "uyirai vidu"],
        "te_latin": ["aathmahathya", "vishamu thaagu", "praanam theesuko"],
        "bn_latin": ["aattohottya", "bish khawa", "jibon sesh"],
        "en": [
            "suicide", "how to commit suicide", "cut my wrists", "want to die", "hang myself",
            "painless suicide", "poison myself", "overdose pills", "kill myself", "end my life"
        ]
    },
    "DRUGS_AND_SUBSTANCES": {
        "hi_latin": [
            "nasha karna", "charas", "ganja khareedo", "drugs becho", "daru peena",
            "afeem", "chitta", "tambaku"
        ],
        "hi_devanagari": [
            "चरस", "गांजा", "नशा", "ड्रग्स खरीदना", "शराब पीना", "अफीम", "चिट्टा"
        ],
        "mr_latin": ["daru", "madhyapaan", "nasha"],
        "ta_latin": ["bodhai", "kallu", "marundhu"],
        "te_latin": ["mandhu", "kallu", "mathu padarthalu"],
        "bn_latin": ["nesha", "mod", "ganja"],
        "en": [
            "buy drugs", "smoke weed underage", "cook meth", "heroin injection",
            "fake id alcohol", "snort cocaine"
        ]
    },
    "PROFANITY_AND_BULLYING": {
        "hi_latin": [
            "chutiya", "madarchod", "bhenchod", "gaand", "harami", "kutta kamina",
            "bhadwe", "raand", "lauda", "teri maa ki", "bhosdike"
        ],
        "hi_devanagari": [
            "चूतिया", "मादरचोद", "बहनचोद", "हरामी", "कुत्ता", "कमीना", "भोसड़ीके", "गाली"
        ],
        "mr_latin": ["aai ghalya", "zhavadya", "bhadkhau"],
        "ta_latin": ["thevidya", "sunni", "omala", "otha"],
        "te_latin": ["dengu", "lanja", "na kodaka"],
        "bn_latin": ["khanki", "magi", "shala", "chudirbhai"],
        "en": [
            "loser kill yourself", "ugly freak", "retard", "slut", "bitch", "faggot",
            "nobody likes you die"
        ]
    },
    "NSFW_AND_EXPLOITATION": {
        "hi_latin": ["chudai", "sex video", "nangi photo", "blue film", "sambhog", "bina kapdo ke"],
        "hi_devanagari": ["संभोग", "सेक्स", "नंगी फोटो", "अश्लील", "ब्लू फिल्म"],
        "mr_latin": ["ashleel", "nagna"],
        "ta_latin": ["kama", "kamukathanam"],
        "te_latin": ["kamam", "srungaram"],
        "bn_latin": ["jouno", "ashleel"],
        "en": [
            "pornography", "explicit sex", "nude pics", "erotic roleplay", "deepfake porn",
            "child sexual", "send nudes"
        ]
    },
    "JAILBREAK_AND_BYPASS": {
        "hi_latin": ["safety filter todo", "jailbreak karo", "rules bhool jao", "uncensored ban jao"],
        "en": [
            "ignore previous instructions", "jailbreak", "dan mode", "you have no rules",
            "pretend to be uncensored", "bypass safety", "developer mode enabled",
            "hypothetically without restrictions", "sudo mode"
        ]
    }
}


class MultilingualSafetyEngine:
    """
    Evaluates student queries, content submissions, and chat interactions
    using cross-lingual phonetic normalization, leetspeak decoding,
    and regional safety dictionary analysis.
    """

    @classmethod
    def normalize_text(cls, raw_text: str) -> str:
        """
        Normalizes unicode, strips zero-width non-joiners, decodes leetspeak,
        and condenses spaced-out letters (e.g. 'k . i . l . l' -> 'kill').
        """
        if not raw_text:
            return ""

        # 1. Unicode NFKD normalization
        text = unicodedata.normalize('NFKD', raw_text)

        # 2. Strip zero-width & invisible characters
        text = re.sub(r'[\u200B-\u200D\uFEFF\u200E\u200F]', '', text)

        # 3. Lowercase
        text = text.lower()

        # 4. Leetspeak mapping (for Latin script characters)
        leet_normalized = []
        for ch in text:
            leet_normalized.append(LEET_CHAR_MAP.get(ch, ch))
        text = "".join(leet_normalized)

        # 5. Remove excessive punctuation spacing between single characters
        # e.g. "k . i . l . l" -> "kill", "s - u - i - c - i - d - e" -> "suicide"
        text = re.sub(r'(?<=\b\w)[\s\.\-_,]+(?=\w\b)', '', text)

        # 6. Normalize multiple whitespaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @classmethod
    def detect_script(cls, text: str) -> str:
        """Detects primary script: devanagari, tamil, telugu, bengali, or latin."""
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
        has_tamil = bool(re.search(r'[\u0B80-\u0BFF]', text))
        has_telugu = bool(re.search(r'[\u0C00-\u0C7F]', text))
        has_bengali = bool(re.search(r'[\u0980-\u09FF]', text))

        if has_devanagari:
            return "hi_devanagari"
        elif has_tamil:
            return "ta_script"
        elif has_telugu:
            return "te_script"
        elif has_bengali:
            return "bn_script"
        return "latin"

    @classmethod
    def evaluate(cls, raw_text: str) -> Dict[str, Any]:
        """
        Runs comprehensive multilingual and adversarial safety evaluation.
        Returns safety verdict, score, matched rules, and explanation.
        """
        if not raw_text or not raw_text.strip():
            return {
                "is_safe": True,
                "safety_score": 100.0,
                "risk_level": "none",
                "detected_language": "en",
                "flagged_categories": [],
                "matched_patterns": [],
                "explanation": "Content is empty or whitespace."
            }

        norm_text = cls.normalize_text(raw_text)
        script = cls.detect_script(raw_text)
        flagged_categories = []
        matched_patterns = []

        # 1. Check against Multilingual Taxonomy
        for category, lang_dict in MULTILINGUAL_TAXONOMY.items():
            for lang_key, patterns in lang_dict.items():
                for pat in patterns:
                    # Word boundary search for Latin, substring/boundary for Indic scripts
                    if " " in pat or script != "latin":
                        if pat in norm_text or pat in raw_text.lower():
                            flagged_categories.append(category)
                            matched_patterns.append(f"{lang_key}:{pat}")
                            break
                    else:
                        pattern_regex = rf'\b{re.escape(pat)}\b'
                        if re.search(pattern_regex, norm_text, re.IGNORECASE):
                            flagged_categories.append(category)
                            matched_patterns.append(f"{lang_key}:{pat}")
                            break

        # 2. Check risk emoji combinations with threat words
        for cat, emojis in RISK_EMOJI_PATTERNS.items():
            for em in emojis:
                if em in raw_text:
                    # If dangerous emoji accompanies threat context
                    threat_words = ["you", "die", "kill", "tera", "tujhe", "school", "friend", "teacher"]
                    if any(tw in norm_text for tw in threat_words):
                        flagged_categories.append(cat)
                        matched_patterns.append(f"emoji_threat:{em}")
                        break

        # 3. Determine Safety Verdict
        is_safe = len(flagged_categories) == 0
        categories_unique = list(set(flagged_categories))

        if is_safe:
            safety_score = 98.5
            risk_level = "safe"
            explanation = "Evaluated across English and Indic multilingual vocabularies. No safety violations detected."
        else:
            # Calibrate severity score
            if any(c in ["SELF_HARM", "VIOLENCE_AND_WEAPONS"] for c in categories_unique):
                safety_score = 10.0
                risk_level = "critical"
            elif any(c in ["NSFW_AND_EXPLOITATION", "DRUGS_AND_SUBSTANCES"] for c in categories_unique):
                safety_score = 25.0
                risk_level = "high"
            elif "JAILBREAK_AND_BYPASS" in categories_unique:
                safety_score = 40.0
                risk_level = "high"
            else:
                safety_score = 55.0
                risk_level = "medium"

            explanation = f"Flagged in categories: {', '.join(categories_unique)}. Matched patterns: {', '.join(matched_patterns[:3])}."

        return {
            "is_safe": is_safe,
            "safety_score": safety_score,
            "risk_level": risk_level,
            "detected_script": script,
            "flagged_categories": categories_unique,
            "matched_patterns": matched_patterns,
            "normalized_text": norm_text,
            "explanation": explanation
        }
