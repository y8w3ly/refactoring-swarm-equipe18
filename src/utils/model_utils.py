import json
import time
import os
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)

MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"


def get_model(api_key: str):
    if MOCK_MODE:
        return MockModel()

    import google.generativeai as genai

    genai.configure(api_key=api_key)

    # ✅ FIX: Using the model confirmed in your list
    return genai.GenerativeModel("gemini-3-flash-preview")


class MockModel:
    def generate_content(self, content):
        class MockResponse:
            text = '{"verdict": "PASS", "feedback": "Mock mode - code looks good"}'

        return MockResponse()


def call_with_retry(model, prompt: str, max_retries: int = 5) -> str:
    if MOCK_MODE:
        return model.generate_content([]).text

    # Start with a 20-second wait to be safe
    base_wait = 20

    for attempt in range(max_retries):
        try:
            response = model.generate_content([{"role": "user", "parts": [prompt]}])
            return response.text

        except Exception as e:
            error_str = str(e)

            # Handle Rate Limits (429) or Quota errors
            if (
                "429" in error_str
                or "quota" in error_str.lower()
                or "resource" in error_str.lower()
            ):
                wait_time = base_wait * (
                    2**attempt
                )  # Exponential backoff: 20s, 40s, 80s...
                print(
                    f"   ⏳ Rate limit hit. Cooling down for {wait_time}s (Attempt {attempt+1}/{max_retries})..."
                )
                time.sleep(wait_time)
            else:
                # If the model is 404 again (unlikely now), print it clearly
                print(f"❌ API Error: {error_str}")
                raise e

    raise Exception("❌ Max retries exceeded. API is too busy.")
