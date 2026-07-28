"""
RAGTUNE Intent Router & Query Planning Engine - Intent Classifier
Analyzes natural language queries and context to determine intent categories and confidence scores.
"""

import re
from typing import Tuple
from router.domain import IntentCategory

SQL_KEYWORDS = [r"\bselect\b", r"\bsales\b", r"\brevenue\b", r"\btotal\b", r"\bcount\b", r"\bavg\b", r"\bmax\b", r"\bmin\b", r"\btable\b", r"\bdatabase\b", r"\bquarter\b"]
RAG_KEYWORDS = [r"\bpolicy\b", r"\bclause\b", r"\bdocument\b", r"\bcontract\b", r"\bagreement\b", r"\bterms\b", r"\bper\s+diem\b", r"\bsla\b", r"\buptime\b"]
SUMMARIZE_KEYWORDS = [r"\bsummarize\b", r"\bsummary\b", r"\boverview\b", r"\bkey\s+takeaways\b"]
POLICY_KEYWORDS = [r"\bcompliance\b", r"\bsecurity\s+policy\b", r"\bguidelines\b", r"\brule\b"]


class IntentClassifier:
    def __init__(self):
        self.sql_regexes = [re.compile(p, re.IGNORECASE) for p in SQL_KEYWORDS]
        self.rag_regexes = [re.compile(p, re.IGNORECASE) for p in RAG_KEYWORDS]
        self.summarize_regexes = [re.compile(p, re.IGNORECASE) for p in SUMMARIZE_KEYWORDS]
        self.policy_regexes = [re.compile(p, re.IGNORECASE) for p in POLICY_KEYWORDS]

    def classify(self, query_text: str) -> Tuple[IntentCategory, float]:
        """
        Classifies query into IntentCategory and returns (category, confidence_score).
        """
        if not query_text or not query_text.strip():
            return IntentCategory.UNKNOWN, 0.0

        q_clean = query_text.strip()

        sql_hits = sum(1 for r in self.sql_regexes if r.search(q_clean))
        rag_hits = sum(1 for r in self.rag_regexes if r.search(q_clean))
        sum_hits = sum(1 for r in self.summarize_regexes if r.search(q_clean))
        pol_hits = sum(1 for r in self.policy_regexes if r.search(q_clean))

        # Check hybrid condition (both SQL and RAG keywords present)
        if sql_hits > 0 and rag_hits > 0:
            return IntentCategory.HYBRID_ANALYTICS, 0.92

        if sum_hits > 0:
            return IntentCategory.SUMMARIZATION, 0.90

        if pol_hits > 0:
            return IntentCategory.POLICY_LOOKUP, 0.88

        if sql_hits > rag_hits and sql_hits > 0:
            confidence = min(0.70 + (sql_hits * 0.1), 0.95)
            return IntentCategory.STRUCTURED_SQL, confidence

        if rag_hits > sql_hits and rag_hits > 0:
            confidence = min(0.70 + (rag_hits * 0.1), 0.95)
            return IntentCategory.UNSTRUCTURED_RAG, confidence

        # Default fallback to UNSTRUCTURED_RAG for general questions
        return IntentCategory.UNSTRUCTURED_RAG, 0.75
