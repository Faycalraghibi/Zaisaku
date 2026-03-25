"""Unit tests for zaisaku.generation.prompt — Prompt formatting."""

from zaisaku.generation.prompt import SYSTEM_PROMPT, build_rag_prompt


class TestPromptBuilder:
    def test_system_prompt_contains_json_instructions(self):
        assert "valid JSON object" in SYSTEM_PROMPT
        assert '"answer":' in SYSTEM_PROMPT
        assert '"confidence":' in SYSTEM_PROMPT
        assert '"sources_used":' in SYSTEM_PROMPT

    def test_build_rag_prompt_with_chunks(self):
        chunks = [
            {"text": "Apple revenue was 100B.", "metadata": {"source": "apple.pdf"}},
            {"text": "Microsoft revenue was 150B.", "metadata": {"source": "msft.txt"}},
        ]
        query = "What was the revenue?"
        
        prompt = build_rag_prompt(query, chunks)
        
        assert query in prompt
        assert "Apple revenue was 100B." in prompt
        assert "Source: apple.pdf" in prompt
        assert "Document 1" in prompt
        assert "Microsoft revenue was 150B." in prompt
        assert "Source: msft.txt" in prompt
        assert "Document 2" in prompt

    def test_build_rag_prompt_empty_chunks(self):
        query = "What is the meaning of life?"
        prompt = build_rag_prompt(query, [])
        
        assert query in prompt
        assert "No relevant documents found." in prompt

    def test_build_rag_prompt_missing_metadata(self):
        chunks = [{"text": "Just some text."}]  # No metadata key
        prompt = build_rag_prompt("Q", chunks)
        
        assert "Just some text." in prompt
        assert "Unknown Source" in prompt
