import unittest

from backend.agents.langchain_utils import build_embeddings, build_llm


class LangChainUtilsTests(unittest.TestCase):
    def test_builders_expose_langchain_like_interfaces(self):
        llm = build_llm("gpt-4o-mini")
        embeddings = build_embeddings("sentence-transformers/all-MiniLM-L6-v2")

        self.assertTrue(hasattr(llm, "invoke"))
        self.assertTrue(hasattr(embeddings, "embed_query"))
        self.assertTrue(hasattr(embeddings, "embed_documents"))

        response = llm.invoke("Summarize this earnings call")
        vector = embeddings.embed_query("earnings call")

        self.assertIsInstance(response, str)
        self.assertGreater(len(vector), 0)


if __name__ == "__main__":
    unittest.main()
