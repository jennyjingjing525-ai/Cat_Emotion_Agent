from flask import Flask, request, jsonify
from flask_cors import CORS 
import asyncio

# Import the emotion analysis functions
from emotion_logic import analyze_emotion_with_adk 
from emotion_sharing import generate_sharing_text

app = Flask(__name__)
CORS(app) 

# --- HELPER FUNCTION FOR EVENT LOOP ---
def run_async(coroutine):
    """
    Manually creates a new event loop for each request.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()
# --------------------------------------

@app.route('/analyze-emotion', methods=['POST'])
def analyze_emotion_endpoint():
    print("Received request from client...")
    try:
        data = request.get_json()
        if not data or 'image_data' not in data or 'mime_type' not in data or 'prompt' not in data:
            return jsonify({"error": "Missing data"}), 400

        image_data = data['image_data']
        mime_type = data['mime_type']
        prompt = data['prompt']
        
        # Run in its own isolated loop
        result_text = run_async(analyze_emotion_with_adk(
            base64_image=image_data,
            mime_type=mime_type,
            prompt=prompt
        ))
        
        if result_text.startswith("Error:"):
            return jsonify({"error": result_text}), 500

        return jsonify({"result": result_text}), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

@app.route('/share-emotion', methods=['POST'])
def share_emotion_endpoint():
    print("Received share request from client...")
    try:
        data = request.get_json()
        
        if not data or 'image_data' not in data or 'mime_type' not in data or 'prompt' not in data:
            return jsonify({"error": "Missing data"}), 400

        image_data = data['image_data']
        mime_type = data['mime_type']
        prompt = data['prompt']
        
        # --- STEP 1: ANALYZE (Loop A) ---
        # We run this, get the result, and let the loop CLOSE completely.
        emotion_description = run_async(analyze_emotion_with_adk(
            base64_image=image_data,
            mime_type=mime_type,
            prompt=prompt
        ))
        
        if emotion_description.startswith("Error"):
             return jsonify({"error": emotion_description}), 500

        # --- STEP 2: SHARE (Loop B) ---
        # We start a FRESH loop for the second agent. This prevents conflicts.
        final_result = run_async(generate_sharing_text(emotion_description))
        
        if final_result.startswith("Error:"):
            return jsonify({"error": final_result}), 500

        return jsonify({"result": final_result}), 200

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    print("--- Cat Emotion Server Starting (Decoupled Loops) ---")
    app.run(debug=True)