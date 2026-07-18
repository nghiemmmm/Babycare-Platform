from app.AI_agents.core.reasoner import AIReasoner
import json

RELEVANCY_SYSTEM_PROMPT = """
You are an expert AI judge evaluating the quality of pediatric assistant responses.
Evaluate the **Relevance** of the response to the user query.
The response should directly address the user query, provide warm and scientific instructions, and contain no irrelevant deviation.

Provide your evaluation as a JSON object with:
- "score": A float between 0.0 and 1.0 representing the relevance of the answer.
- "reason": A brief explanation of the score.

Response JSON format:
{"score": 0.95, "reason": "The answer directly explains how to treat infant fever."}
Do not write anything else beside the JSON.
"""

FAITHFULNESS_SYSTEM_PROMPT = """
You are an expert AI judge evaluating the safety and faithfulness of pediatric assistant responses.
Compare the actual response with the provided retrieved medical context.
Evaluate if there are any claims in the actual response that are NOT supported by the retrieved context, or if there are contradictions.

Provide your evaluation as a JSON object with:
- "score": A float between 0.0 and 1.0. A score of 1.0 means all claims are fully supported by the context. A lower score means some claims are hallucinated or contradict the context.
- "reason": A brief explanation of the score.

Response JSON format:
{"score": 1.0, "reason": "All recommended steps are exactly supported by the WHO guidelines."}
Do not write anything else beside the JSON.
"""

CONTEXT_PRECISION_SYSTEM_PROMPT = """
You are an expert AI judge evaluating the precision of a RAG retriever.
Analyze the user's query and the retrieved context chunk.
Determine if this specific chunk contains information directly relevant to answering the user's query.

Provide your evaluation as a JSON object with:
- "relevant": A boolean (true/false) indicating if the chunk contains information relevant to the query.
- "reason": A brief explanation.

Response JSON format:
{"relevant": true, "reason": "The chunk discusses infant sleep training environment, which is relevant to the query."}
Do not write anything else besides the JSON.
"""

CONTEXT_RECALL_SYSTEM_PROMPT = """
You are an expert AI judge evaluating the recall of a RAG retriever.
Analyze the expected response notes (ground truth) and the combined retrieved context.
Determine what percentage of the expected information/facts described in the expected notes is covered by the retrieved context.

Provide your evaluation as a JSON object with:
- "score": A float between 0.0 and 1.0 representing the proportion of expected information covered by the context.
- "reason": A brief explanation of the score.

Response JSON format:
{"score": 0.85, "reason": "The context covers cháo rây and bí đỏ, but misses the cà rốt introduction."}
Do not write anything else besides the JSON.
"""

class LLMJudge:
    def __init__(self):
        self.reasoner = AIReasoner(model_name="gemini-flash-latest")

    async def evaluate_relevancy(self, query: str, response: str) -> dict:
        prompt = f"Query: {query}\nResponse: {response}"
        try:
            res_text = await self.reasoner.areason(prompt=prompt, system_instruction=RELEVANCY_SYSTEM_PROMPT)
            cleaned = res_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            return {"score": 0.0, "reason": f"Evaluation error: {str(e)}"}

    async def evaluate_faithfulness(self, query: str, response: str, context: str) -> dict:
        prompt = f"Query: {query}\nResponse: {response}\n\nRetrieved Medical Context:\n{context}"
        try:
            res_text = await self.reasoner.areason(prompt=prompt, system_instruction=FAITHFULNESS_SYSTEM_PROMPT)
            cleaned = res_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            return {"score": 0.0, "reason": f"Evaluation error: {str(e)}"}

    async def evaluate_chunk_relevance(self, query: str, chunk: str) -> dict:
        prompt = f"Query: {query}\nChunk Content: {chunk}"
        try:
            res_text = await self.reasoner.areason(prompt=prompt, system_instruction=CONTEXT_PRECISION_SYSTEM_PROMPT)
            cleaned = res_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            return {"relevant": False, "reason": f"Evaluation error: {str(e)}"}

    async def evaluate_context_recall(self, expected_notes: str, context: str) -> dict:
        prompt = f"Expected Notes: {expected_notes}\nCombined Context: {context}"
        try:
            res_text = await self.reasoner.areason(prompt=prompt, system_instruction=CONTEXT_RECALL_SYSTEM_PROMPT)
            cleaned = res_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            return {"score": 0.0, "reason": f"Evaluation error: {str(e)}"}
