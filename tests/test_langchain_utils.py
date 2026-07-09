import unittest

from backend.agents.langchain_utils import build_embeddings, build_llm, normalize_groq_model_name


def _response_to_str(response) -> str:
    """Normalize an LLM response to a plain string.

    The fallback ``SimpleLangChainLLM.invoke`` returns a ``str`` directly.
    Real LangChain adapters (ChatOpenAI, ChatAIMLAPI) return message objects
    with a ``.content`` attribute.  This helper handles both.
    """
    if isinstance(response, str):
        return response
    content = getattr(response, "content", None)
    if content is not None:
        return str(content)
    return str(response)


class LangChainUtilsTests(unittest.TestCase):
    def test_groq_model_aliases(self):
        self.assertEqual(
            normalize_groq_model_name("Safety GPT OSS 20B"),
            "openai/gpt-oss-safeguard-20b",
        )
        self.assertEqual(
            normalize_groq_model_name("Qwen 3 32B"),
            "qwen/qwen3-32b",
        )
        self.assertEqual(
            normalize_groq_model_name("Llama 4 Scout"),
            "meta-llama/llama-4-scout-17b-16e-instruct",
        )

    def test_builders_expose_langchain_like_interfaces(self):
        llm = build_llm("gpt-4o-mini")
        embeddings = build_embeddings("sentence-transformers/all-MiniLM-L6-v2")

        self.assertTrue(hasattr(llm, "invoke"))
        self.assertTrue(hasattr(embeddings, "embed_query"))
        self.assertTrue(hasattr(embeddings, "embed_documents"))

        response = llm.invoke("Summarize this earnings call")
        # Normalize: real LangChain providers return message objects, the local
        # fallback returns a plain str — both are valid.
        response_str = _response_to_str(response)
        self.assertIsInstance(response_str, str)
        self.assertGreater(len(response_str), 0)

        vector = embeddings.embed_query("earnings call")
        self.assertGreater(len(vector), 0)

    def test_embedding_provider_ladder_accepts_cloud_options(self):
        aimlapi_embeddings = build_embeddings(
            "text-embedding-3-small",
            provider="aimlapi",
            api_key="test",
        )
        hf_cloud_embeddings = build_embeddings(
            "sentence-transformers/all-mpnet-base-v2",
            provider="hf_cloud",
            api_key="test",
        )

        self.assertTrue(hasattr(aimlapi_embeddings, "embed_query"))
        self.assertTrue(hasattr(hf_cloud_embeddings, "embed_query"))


if __name__ == "__main__":
    unittest.main()
