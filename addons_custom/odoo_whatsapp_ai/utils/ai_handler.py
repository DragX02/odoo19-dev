from google import genai
import json

def analyze_card(image_path, api_key, model_name="gemini-1.5-flash"):
    try:
        client = genai.Client(api_key=api_key)
        with open(image_path, "rb") as f:
            img_data = f.read()
        
        prompt = "Analyse cette carte de visite. Retourne UNIQUEMENT un JSON avec: name, email, company, phone. Sinon null."
        
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt, {"mime_type": "image/jpeg", "data": img_data}]
        )
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception:
        return {"error": "IA indisponible"}