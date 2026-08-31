import re
from typing import List, Dict, Any, Tuple

# Comprehensive rule dictionaries categorized for under-18 student protection
SAFETY_RULES_TAXONOMY: Dict[str, List[str]] = {
    "VIOLENCE_AND_WEAPONS": [
        "how to make an explosive",
        "homemade bomb",
        "pipe bomb",
        "make explosives",
        "chemical explosives",
        "explosives",
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
        "how to hack wifi passwords",
        "synthesize toxic",
        "toxic chlorine gas",
        "bypass school firewalls",
        "web proxies to access",
        "access blocked adult content",
        "adult content",
        "rm -rf"
    ],
    "DRUGS_AND_SUBSTANCES": [
        "how to buy drugs",
        "synthesize methamphetamine",
        "cook meth",
        "heroin injection",
        "cocaine distribution",
        "vape tricks for kids",
        "buying alcohol underage",
        "buy alcohol underage",
        "alcohol underage",
        "underage drinking"
    ],
    "NSFW_AND_EXPLOITATION": [
        "explicit sex",
        "pornography",
        "porn",
        "nudity",
        "erotic roleplay",
        "dating adults",
        "meet strangers online",
        "adult content"
    ],
    "SELF_HARM": [
        "how to commit suicide",
        "suicide methods",
        "self harm tutorial",
        "self harm",
        "self-harm",
        "methods for self-harm",
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
        "cyberbullying",
        "target harassment"
    ],
    "PROMPT_INJECTION": [
        "ignore previous instructions",
        "ignore all previous instructions",
        "system override",
        "system prompt override",
        "disregard all prior safety",
        "override all safety filters",
        "reveal administrative api keys",
        "reveal root passwords",
        "jailbreak",
        "dan mode",
        "developer mode enabled",
        "disregard safety guidelines",
        "bypass school network firewall",
        "execute command"
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
