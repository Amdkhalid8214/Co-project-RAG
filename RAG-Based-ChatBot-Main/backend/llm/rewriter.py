import re
import json
import asyncio
import logging
from typing import List, Dict
from backend.llm.client import ollama_client

logger = logging.getLogger(__name__)

PRONOUN_PATTERN = re.compile(
    r"\b(it|its|he|him|his|she|her|hers|they|them|their|theirs|this|that|these|those|former|latter|the same)\b",
    re.IGNORECASE
)

class QueryRewriter:
    def __init__(self):
        pass

    async def transform_query(
        self,
        question: str,
        chat_history: List[Dict[str, str]]
    ) -> List[str]:
        """
        Rewrites question using chat history to resolve pronouns and generates 2-3 alternative queries.
        Returns list of queries: [standalone_query, alt_1, alt_2].
        """
        clean_q = question.strip()

        # Handle compound questions joined by "and", "along with", "as well as", or comma
        if re.search(r"\b(and|as well as|along with)\b", clean_q, re.I):
            parts = re.split(r"\b(?:and|as well as|along with)\b", clean_q, flags=re.I)
            sub_queries = [p.strip() for p in parts if len(p.strip()) >= 10]
            if len(sub_queries) >= 2:
                # Clean leading phrases like 'explain', 'what are', 'tell me about'
                clean_subs = []
                for sq in sub_queries[:2]:
                    c_sub = re.sub(r'^(?:explain|describe|what are|what is|tell me about|list|detail)\s+(?:the\s+)?', '', sq, flags=re.I).strip()
                    clean_subs.append(c_sub if len(c_sub) >= 5 else sq)
                return [clean_q, clean_subs[0], clean_subs[1]]

        # Fast bypass: If no chat history or the question has no pronouns/anaphora,
        # it is already standalone. Skip the extra synchronous LLM call to save latency.
        if not chat_history or not PRONOUN_PATTERN.search(clean_q):
            return [
                clean_q,
                f"{clean_q} details",
                f"{clean_q} overview"
            ]

        # Format compact history (last 3 turns to keep prompt focused and latency low)
        recent_turns = chat_history[-3:]
        history_lines = []
        for msg in recent_turns:
            role = msg.get("role", "user")
            content = msg.get("content", "").replace("\n", " ")[:150]
            history_lines.append(f"{role}: {content}")
        history_str = "\n".join(history_lines)

        short_prompt = f"""Task: Resolve pronouns in Question using History into a standalone query, and generate 2 search variations.
History:
{history_str}
Question: {clean_q}
Format: JSON only: {{"standalone": "...", "alternatives": ["...", "..."]}}
JSON:"""

        try:
            raw_resp = await asyncio.wait_for(
                ollama_client.generate_complete(
                    prompt=short_prompt,
                    temperature=0.2,
                    max_tokens=60
                ),
                timeout=3.0
            )

            json_match = re.search(r"\{.*?\}", raw_resp, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                standalone = parsed.get("standalone", "").strip() or clean_q
                alts = parsed.get("alternatives", [])
                clean_alts = [str(a).strip() for a in alts if str(a).strip() and str(a).strip() != standalone]
                
                queries = [standalone] + clean_alts[:2]
                if len(queries) < 2:
                    queries.append(clean_q)
                return queries

        except Exception as e:
            logger.warning(f"Query rewriter error: {e}")

        # Fallback if JSON generation fails or times out
        return [clean_q, f"{clean_q} information"]

query_rewriter = QueryRewriter()
