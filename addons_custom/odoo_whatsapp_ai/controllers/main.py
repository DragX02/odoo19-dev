from odoo import http
from odoo.http import request
import requests
import tempfile
import os

class WhatsAppController(http.Controller):

    def _get_configs(self):
        ICP = request.env['ir.config_parameter'].sudo()
        return {
            'url': ICP.get_param('odoo_whatsapp_ai.evolution_api_url'),
            'key': ICP.get_param('odoo_whatsapp_ai.evolution_api_key'),
            'instance': ICP.get_param('odoo_whatsapp_ai.evolution_instance'),
            'ai_key': ICP.get_param('odoo_whatsapp_ai.key_ai_api'),
            'ai_model': ICP.get_param('odoo_whatsapp_ai.ai_model', default='gemini-1.5-flash'),
        }

    @http.route('/whatsapp/webhook', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def webhook(self):
        data = request.get_json_data()
        cfg = self._get_configs()
        
        if data.get('event') != 'messages.upsert':
            return {"status": "ignored"}

        msg_data = data.get('data', {})
        message = msg_data.get('message', {})
        sender = msg_data.get('key', {}).get('remoteJid')
        
        if 'imageMessage' in message:
            from ..utils.ai_handler import analyze_card
            temp_path = self._download_media(msg_data, cfg)
            if temp_path:
                try:
                    info = analyze_card(temp_path, cfg['ai_key'], cfg['ai_model'])
                    if info and "error" not in info:
                        text = (f"🔍 *Infos détectées*\n\n"
                                f"👤 Nom: {info.get('name')}\n"
                                f"📧 Email: {info.get('email')}\n"
                                f"🏢 Sté: {info.get('company')}\n\n"
                                f"1️⃣ Client\n2️⃣ Fournisseur\n3️⃣ Contact\n4️⃣ Ignorer")
                        self._send_text(sender, text, cfg)
                finally:
                    os.remove(temp_path) # Nettoyage du fichier temporaire
        
        elif 'conversation' in message or 'extendedTextMessage' in message:
            text = (message.get('conversation') or message.get('extendedTextMessage', {}).get('text') or "").strip().lower()
            if any(w in text for w in ['bonjour', 'hello', 'odoo']):
                self._send_text(sender, "Bonjour ! Le Bot Odoo est bien connecté.", cfg)
            elif text in ['1', '2', '3', '4']:
                self._process_choice(sender, text, cfg)
        return {"status": "ok"}

    def _download_media(self, msg_data, cfg):
        url = f"{cfg['url']}/media/download/{cfg['instance']}"
        try:
            res = requests.post(url, json={"message": msg_data}, headers={"apikey": cfg['key']}, timeout=30)
            res.raise_for_status()
            # Crée un fichier temporaire sécurisé
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(res.content)
                return temp_file.name
        except requests.exceptions.RequestException:
            # Idéalement, il faudrait logguer cette erreur pour le débogage
            pass
        return None

    def _send_text(self, to, txt, cfg):
        url = f"{cfg['url']}/message/sendText/{cfg['instance']}"
        payload = {
            "number": to,
            "text": txt
        }
        try:
            requests.post(url, json=payload, headers={"apikey": cfg['key']}, timeout=10)
        except requests.exceptions.RequestException:
            # Idéalement, il faudrait logguer cette erreur pour le débogage
            pass

    def _process_choice(self, sender, choice, cfg):
        actions = {'1': 'Client', '2': 'Fournisseur', '3': 'Contact', '4': 'Annulé'}
        self._send_text(sender, f"Action enregistrée : {actions.get(choice)}", cfg)