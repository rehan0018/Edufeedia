import re
from typing import List, Dict, Any, Tuple

# Comprehensive rule dictionaries categorized for under-18 student protection
SAFETY_RULES_TAXONOMY: Dict[str, List[str]] = {
    "VIOLENCE_AND_WEAPONS": [
        "how to make an explosive",
        "homemade bomb",
        "pipe bomb",
        "make explosives",
        "gun making",
        "mass shooting",
        "assault tutorial",
        "knife fight tactics",
        "torture",
        "beheading",
        "molotov cocktail"
    ],
    "DANGEROUS_ACTIVITIES": [
        "choking game challenge",
        "tide pod challenge",
        "drinking bleach",
        "stealing cars",
        "illegal street racing",
        "dangerous stunt at home",
        "bypass security system",
        "how to hack wifi passwords"
    ],
    "DRUGS_AND_SUBSTANCES": [
        "how to buy drugs",
        "synthesize methamphetamine",
        "cook meth",
        "heroin injection",
        "cocaine distribution",
        "vape tricks for kids",
        "buying alcohol underage"
    ],
    "NSFW_AND_EXPLOITATION": [
        "explicit sex",
        "pornography",
        "porn",
        "nudity",
        "erotic roleplay",
        "dating adults",
        "meet strangers online"
    ],
    "SELF_HARM": [
        "how to commit suicide",
        "suicide methods",
        "self harm tutorial",
        "cutting yourself",
        "pro-ana tips",
        "anorexia motivation"
    ],
    "HATE_AND_HARASSMENT": [
        "hate speech",
        "kill all",
        "racial slurs",
        "doxxing",
        "cyberbullying guide",
        "target harassment"
    ]
}

# Regex patterns for fast boundary-aware detection
COMPILED_PATTERNS: Dict[str, List[re.Pattern]] = {
    category: [re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE) for keyword in keywords]
    for category, keywords in SAFETY_RULES_TAXONOMY.items()
}

def evaluate_rules(text: str) -> Tuple[bool, List[str], List[str]]:
    """
    Evaluates text against hard safety rules.
    Returns: (is_blocked, matched_categories, matched_keywords)
    """
    if not text:
        return False, [], []

    matched_categories = []
    matched_keywords = []

    for category, patterns in COMPILED_PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                if category not in matched_categories:
                    matched_categories.append(category)
                matched_keywords.append(match.group(0))

    is_blocked = len(matched_categories) > 0
    return is_blocked, matched_categories, matched_keywords
