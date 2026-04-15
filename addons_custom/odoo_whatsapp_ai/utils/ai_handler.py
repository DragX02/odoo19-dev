import google.generativeai as genai
import json


def analyze_card(image_path,api_key,provider='gemini'):
    if provider == 'gemini':
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        with open(image_path, "rb") as f:
            img_data = f.read()

        prompt = "Analyse cette carte de visite. Réponds UNIQUEMENT en JSON: {name, email, phone, company, job}"

        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": img_data}
        ])

        text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(text)