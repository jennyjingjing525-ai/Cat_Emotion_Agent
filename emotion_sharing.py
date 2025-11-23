# emotion_sharing.py
import os
import uuid 
from dotenv import load_dotenv
from google.adk.agents import Agent as ADKAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

# Load Environment Variables
load_dotenv(dotenv_path='KEY.env')

# Define System Instruction (Keep this global as it is just text)
SYSTEM_INSTRUCTION = (
    "You are a social media content generator. Your task is to take a detailed "
    "description of a cat's emotion and convert it into two distinct pieces of text: "
    "1. 'Instagram-worthy text': A concise, engaging, and creative caption suitable for Instagram. "
    "2. 'Image sharing text': A brief, direct message suitable for sharing with friends. "
    "Format your response as two separate paragraphs, clearly labeled as "
    "'**Instagram-worthy text:**' and '**Image sharing text:**'."
    "Key points to summarize interesting aspects of cat emotions, For example, a cat's crying expression might be because it wants to eat fish."
)

async def generate_sharing_text(emotion_description: str) -> str:
    """
    Uses the ADK InMemoryRunner to generate social media text from an emotion description.
    """
    try:
        # --- FIX: Initialize Agent INSIDE the function ---
        # This ensures the agent attaches to the CURRENT active event loop,
        # not a closed one from a previous request.
        emotion_sharing_agent = ADKAgent(
            name="CatEmotionSharer",
            model=Gemini(
                model="gemini-2.5-flash",
                system_instruction=SYSTEM_INSTRUCTION,
            )
        )
        # -------------------------------------------------

        # Generate IDs required by the ADK
        app_name = "CatEmotionShareApp"
        user_id = "sharing_user"      
        session_id = str(uuid.uuid4()) 
        
        runner = InMemoryRunner(
            agent=emotion_sharing_agent,
            app_name=app_name
        )
        
        session_service = runner.session_service
        
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        user_content = types.Content(parts=[types.Part(text=emotion_description)], role="user")
        
        response_text = ""
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
        
        return response_text if response_text else "No sharing text generated"
            
    except Exception as e:
        error_msg = f"Error: ADK Sharing Agent failed to run. Details: {e}"
        print(error_msg)
        return error_msg