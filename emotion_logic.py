# emotion_logic.py (Corrected for proper InMemoryRunner usage)

import os 
from dotenv import load_dotenv
import uuid
import sys
import google.adk

print(f"--- Environment Check ---")
print(f"Python Executable: {sys.executable}")
print(f"ADK Version: {google.adk.__version__}")
print(f"--- Check Complete ---")

def run_adk_check():
    print(f"\n--- SERVER-SIDE ADK CHECK ---")
    print(f"Python Executable: {sys.executable}")
    print(f"ADK Version: {google.adk.__version__}")

    from google.adk.agents import Agent
    from google.adk.models.google_llm import Gemini
    try:
        test_agent = Agent(name="Test", model=Gemini(model="gemini-2.5-flash"))
        print(f"Agent object created successfully.")
        if hasattr(test_agent, 'run_async'):
             print(".run_async() attribute found on agent object.")
        else:
             print("!!! CRITICAL: .run_async() attribute is MISSING on agent object.")
    except Exception as e:
        print(f"Agent creation failed: {e}")
    print(f"--- CHECK END ---\n")

run_adk_check()

# Load Environment Variables
load_dotenv(dotenv_path='KEY.env') 

from google.adk.agents import Agent as ADKAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

print("✅ ADK components imported successfully.")

# --- Define System Instruction (keep this global - it's just text) ---
SYSTEM_INSTRUCTION = (
    "You are the Cat Emotion Analysis Agent. Your primary goal is to analyze "
    "the provided image of a cat. You must identify the cat's dominant emotion "
    "(e.g., Happy, Angry, Fearful, Curious, Relaxed),describe the cat's general emotion in the first sentence of response and provide a concise. "
    "Basing on the animal knowledge about cat's pupil size and body language, "
    "detailed explanation (2-3 sentences) based on observable visual cues such as "
    "ear position, eye dilation, whisker orientation, body posture, and tail position."
)

# --- Main analysis function using InMemoryRunner ---
async def analyze_emotion_with_adk(base64_image: str, mime_type: str, prompt: str) -> str:
    """
    Core async function using ADK InMemoryRunner.
    FIX: Initializes agent INSIDE the function to attach to current event loop.
    """
    
    try:
        # --- FIX: Initialize Agent INSIDE the function ---
        # This ensures the agent attaches to the CURRENT active event loop
        cat_emotion_agent = ADKAgent(
            name="CatEmotionAnalyzer",
            model=Gemini(
                model="gemini-2.5-flash",
                system_instruction=SYSTEM_INSTRUCTION,
            )
        )
        # -----------------------------------------------
        
        # Generate unique identifiers
        app_name = "CatEmotionApp"
        user_id = "emotion_user"
        session_id = str(uuid.uuid4())
        
        # Create the runner with app_name
        runner = InMemoryRunner(
            agent=cat_emotion_agent,
            app_name=app_name
        )
        
        # Get session service and create a session
        session_service = runner.session_service
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        # Construct the multimodal content
        content_parts = [
            types.Part(text=prompt),
            types.Part(
                inline_data=types.Blob(
                    mime_type=mime_type,
                    data=base64_image
                )
            )
        ]
        
        user_content = types.Content(parts=content_parts, role="user")
        
        # Use KEYWORD arguments for run_async()
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            # Extract text from the event
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
        
        return response_text if response_text else "No response generated"
            
    except Exception as e:
        error_msg = f"Error: ADK Agent failed to run. Details: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg