from google import genai
import json
import requests
import base64
import logging
import os
import tempfile

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None

_logger = logging.getLogger(__name__)

def _analyze_with_gemini(image_path, api_key, model_name):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        
        prompt = "Analyse cette carte de visite. Retourne UNIQUEMENT un JSON avec les clés: name, email, company, phone. Si une information est manquante, sa valeur doit être null."
        
        response = model.generate_content(
            [prompt, {'mime_type': 'image/jpeg', 'data': img_bytes}],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        _logger.error("Erreur lors de l'analyse avec Gemini: %s", e)
        return {"error": "IA Gemini indisponible ou erreur de configuration."}

def _analyze_with_ollama(image_path, ollama_url, ollama_model):
    try:
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

        prompt = "Analyse cette carte de visite. Retourne UNIQUEMENT un JSON avec les clés: name, email, company, phone. Si une information est manquante, sa valeur doit être null."

        payload = {
            "model": ollama_model,
            "format": "json",
            "prompt": prompt,
            "images": [img_base64],
            "stream": False
        }
        api_url = f"{ollama_url.rstrip('/')}/api/generate"
        response = requests.post(api_url, json=payload, timeout=60)
        response.raise_for_status()
        response_data = response.json()
        return json.loads(response_data.get('response', '{}'))
    except requests.exceptions.ConnectionError:
        _logger.error("Impossible de se connecter à l'API Ollama à l'adresse %s", ollama_url)
        return {"error": f"Connexion à Ollama impossible. Vérifiez que le service est démarré et que l'URL est correcte."}
    except Exception as e:
        _logger.error("Erreur lors de l'analyse avec Ollama: %s", e)
        return {"error": "IA Ollama indisponible ou erreur de configuration."}

def analyze_card(image_path, ai_provider, **kwargs):
    is_pdf = image_path.lower().endswith('.pdf')
    analysis_image_path = image_path
    temp_image_for_pdf = None

    if is_pdf:
        if not convert_from_path:
            _logger.error("Le module 'pdf2image' est requis pour analyser les PDF. Installez-le avec 'pip install pdf2image' et assurez-vous que Poppler est installé sur votre système.")
            return {"error": "Analyse PDF non supportée: pdf2image ou Poppler manquant."}
        try:
            images = convert_from_path(image_path, first_page=1, last_page=1)
            if images:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_image_file:
                    images[0].save(temp_image_file, 'JPEG')
                    analysis_image_path = temp_image_file.name
                    temp_image_for_pdf = analysis_image_path
            else:
                 return {"error": "Impossible de convertir le PDF en image."}
        except Exception as e:
            _logger.error("Erreur lors de la conversion du PDF en image : %s", e)
            return {"error": "Erreur de conversion PDF. Poppler est-il bien installé et dans le PATH ?"}

    try:
        if ai_provider == 'ollama':
            return _analyze_with_ollama(analysis_image_path, kwargs['ollama_url'], kwargs['ollama_model'])
        elif 'gemini' in ai_provider:
            return _analyze_with_gemini(analysis_image_path, kwargs['api_key'], ai_provider)
        else:
            _logger.warning("Le fournisseur d'IA '%s' n'est pas supporté.", ai_provider)
            return {"error": f"Fournisseur d'IA '{ai_provider}' non supporté."}
    finally:
        if temp_image_for_pdf:
            os.remove(temp_image_for_pdf)