from google.generativeai import GenerativeModel, GenerationConfig
import google.generativeai as genai
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        try:
            # Gemini API settings
            GOOGLE_GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
            genai.configure(api_key=GOOGLE_GEMINI_API_KEY)
            # genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            raise

    def generate_personality_insights(self, top_genres, top_artists):
        if not top_genres or not top_artists:
            return "Not enough music preference data to generate insights."

        # Safety check for input lengths
        top_genres = top_genres[:5]  # Limit to top 5
        top_artists = top_artists[:5]  # Limit to top 5

        prompt = f"""
        Based on this user's top music preferences:
        Top Genres: {', '.join(top_genres)}
        Top Artists: {', '.join(top_artists)}

        Create a personalized, upbeat personality description that includes:
        1. Their likely fashion style and aesthetic preferences
        2. Probable interests and hobbies outside of music
        3. Their general vibe and energy in social situations
        4. How they might typically spend their free time
        5. What their ideal weekend might look like

        Style guide:
        - Keep the tone fun and positive, similar to Spotify Wrapped
        - Make specific references to their music preferences
        - Be creative but authentic
        - Format the response in clear paragraphs
        - Keep it around 150-200 words
        """

        try:
            generation_config = GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=1024,
            )

            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            if response.prompt_feedback:
                logger.info(f"Prompt feedback: {response.prompt_feedback}")

            # Check if we have a valid response
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            else:
                logger.error("Empty response from Gemini")
                return "Unable to generate personality insights at this time."

        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}", exc_info=True)
            return "Unable to generate personality insights at this time. Please try again later."