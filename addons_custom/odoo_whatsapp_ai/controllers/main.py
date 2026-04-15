from odoo import http
from odoo.http import request
import requests
import json
from ..utils.ai_handler import analyze_card

class WhatsAppController(http.Controller):

    def _get_configs(self):
        ICP = request.env['ir.config_parameter'].sudo()
        return {
            'api_url': ICP.get_param('odoo_whatsapp_ai.evolution_api_url'),
            'api_key': ICP.get_param('odoo_whatsapp_ai.evolution_api_key'),
            'instance': ICP.get_param('odoo_whatsapp_ai.evolution_instance'),
            'ai_key': ICP.get_param('odoo_whatsapp_ai.key_ai_api'),
            'ai_model': ICP.get_param('odoo_whatsapp_ai.ai_model', default='gemini-1.5-flash'),
        }

    @http.route('/whatsapp/webhook', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def webhook(self):
        data = request.get_json_data()
        configs = self._get_configs()
        
        if data.get('event') != 'messages.upsert':
            return {"status": "ignored"}

        msg_data = data.get('data', {})
        message = msg_data.get('message', {})
        sender = msg_data.get('key', {}).get('remoteJid')
        
        if 'imageMessage' in message:
            image_path = self._save_evolution_media(msg_data, configs)
            if image_path:
                info = analyze_card(image_path, configs['ai_key'], configs['ai_model'])
                if info and "error" not in info:
                    self._send_evolution_confirmation(sender, info, configs)
        
        elif 'conversation' in message or 'extendedTextMessage' in message:
            text = (message.get('conversation') or message.get('extendedTextMessage', {}).get('text') or "").strip().lower()
            if any(w in text for w in ['bonjour', 'hello', 'odoo']):
                self._send_text(sender, "Bonjour ! Le Bot Odoo est bien connecté.", configs)
            elif text in ['1', '2', '3', '4']:
                self._handle_user_choice(sender, text, configs)
                
        return {"status": "ok"}

    def _save_evolution_media(self, msg_data, configs):
        url = f"{configs['api_url']}/media/download/{configs['instance']}"
        headers = {"apikey": configs['api_key']}
        payload = {"message": msg_data}
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                path = "O:/temp_card.jpg" 
                with open(path, "wb") as f:
                    f.write(response.content)
                return path
        except:
            return False

    def _send_text(self, to, text, configs):
        url = f"{configs['api_url']}/message/sendText/{configs['instance']}"
        payload = {"number": to, "text": text}
        headers = {"apikey": configs['api_key'], "Content-Type": "application/json"}
        requests.post(url, json=payload, headers=headers)

    def _send_evolution_confirmation(self, to, info, configs):
        text = (f"🔍 *Infos détectées*\n\n"
                f"👤 *Nom:* {info.get('name')}\n"
                f"📧 *Email:* {info.get('email')}\n"
                f"🏢 *Société:* {info.get('company')}\n\n"
                f"1️⃣ Client\n2️⃣ Fournisseur\n3️⃣ Contact\n4️⃣ Ignorer")
        self._send_text(to, text, configs)

    def _handle_user_choice(self, sender, choice, configs):
        pass