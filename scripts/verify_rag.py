import asyncio
import os
from backend import rag

# Mock environment variables if needed
os.environ["OPENAI_API_KEY"] = "sk-mock-key"

async def test_fetch():
    print("Testing fetch_multiple_papers...")
    # Use a dummy URL or a real one if possible, but let's try a fake one to see error handling
    urls = ["https://example.com/paper.pdf"]
    texts = await rag.fetch_multiple_papers(urls)
    print(f"Fetched {len(texts)} texts.")
    print(f"First text prefix: {texts[0][:100]}")

def test_answer():
    print("\nTesting answer_question with OpenAI...")
    # We expect this to fail with an API error because the key is fake, 
    # but it should NOT crash the script.
    response = rag.answer_question(
        context="This is a test context.",
        question="What is this?",
        model="openai",
        api_key="sk-test-key"
    )
    print(f"Response: {response}")

    print("\nTesting answer_question with Gemini...")
    response_gemini = rag.answer_question(
        context="This is a test context.",
        question="What is this?",
        model="gemini",
        api_key="fake-gemini-key"
    )
    print(f"Response Gemini: {response_gemini}")

if __name__ == "__main__":
    asyncio.run(test_fetch())
    test_answer()
