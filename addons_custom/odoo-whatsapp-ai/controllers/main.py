from odoo import http
from odoo.http import request
import requests
import os
from ..utils.ai_handler import analyze_card

class WhatsAppController(http.Controller):

    @http.route('/whatsapp/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def webhook(self, **post):
        data = request.jsonrequest
        
        # 1. Vérifier si on reçoit une image
        entry = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})
        if 'messages' in entry:
            message = entry['messages'][0]
            if message.get('type') == 'image':
                sender = message['from']
                image_id = message['image']['id']
                
                # 2. Télécharger l'image depuis Meta
                image_path = self._save_meta_image(image_id)
                
                # 3. Analyser avec Gemini
                info = analyze_card(image_path)
                
                # 4. Envoyer la demande de confirmation sur WhatsApp
                if "error" not in info:
                    self._send_whatsapp_confirmation(sender, info)
                
        return {"status": "ok"}

    def _save_meta_image(self, image_id):
        # Utilise ton Meta Token pour télécharger l'image
        token = os.getenv("META_ACCESS_TOKEN")
        url_info = f"https://graph.facebook.com/v19.0/{image_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        image_url = requests.get(url_info, headers=headers).json().get('url')
        img_data = requests.get(image_url, headers=headers).content
        
        path = "O:/temp_card.jpg" # Ajuste le chemin pour ton Windows
        with open(path, "wb") as f:
            f.write(img_data)
        return path

    def _send_whatsapp_confirmation(self, to, info):
        # Envoie un message avec des boutons (ou texte simple)
        # pour demander si c'est un Client ou Fournisseur
        token = os.getenv("META_ACCESS_TOKEN")
        phone_id = os.getenv("META_PHONE_ID")
        url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
        
        text = f"Carte détectée : {info['name']} chez {info['company']}.\n" \
               f"Ajouter comme :\n1. Client\n2. Fournisseur\n3. Annuler"
               
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }
        requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})