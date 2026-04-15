from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import re
try:
    import phonenumbers
except ImportError:
    # Le module n'est pas installé, on peut éventuellement logguer un avertissement
    phonenumbers = None
class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_ai_generated = fields.Boolean(string="Généré par IA", default=False)

    def action_send_whatsapp_manual(self):
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        url = ICP.get_param('odoo_whatsapp_ai.evolution_api_url')
        key = ICP.get_param('odoo_whatsapp_ai.evolution_api_key')
        instance = ICP.get_param('odoo_whatsapp_ai.evolution_instance')
        
        if not url or not key or not instance:
            raise UserError("Veuillez configurer l'URL, la clé API et l'instance d'Evolution API dans les paramètres.")
        
        # Utilisation sécurisée des champs
        phone = getattr(self, 'mobile', False) or getattr(self, 'phone', False)
        
        if not phone: 
            raise UserError("Ce contact n'a pas de numéro de téléphone (fixe ou mobile) renseigné.")

        if not phonenumbers:
            raise UserError("La librairie 'phonenumbers' n'est pas installée. Veuillez l'installer avec 'uv pip install phonenumbers'.")

        try:
            # On suppose 'BE' (Belgique) comme région par défaut pour les numéros locaux.
            parsed_phone = phonenumbers.parse(phone, "BE")
            if not phonenumbers.is_valid_number(parsed_phone):
                raise UserError(f"Le numéro de téléphone '{phone}' n'est pas considéré comme valide.")
            
            # Formate au standard international E.164 et retire le '+'
            cleaned_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164).lstrip('+')
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise UserError(f"Impossible d'analyser le numéro de téléphone '{phone}'. Erreur : {e}")

        payload = {
            "number": f"{cleaned_phone}@c.us",
            "text": f"Bonjour {self.name}, ce message provient d'Odoo."
        }
        headers = {"apikey": key, "Content-Type": "application/json"}
        
        try:
            response = requests.post(f"{url.rstrip('/')}/message/sendText/{instance}", json=payload, headers=headers, timeout=10)
            response.raise_for_status() # Lève une erreur si le statut HTTP n'est pas 2xx
        except requests.exceptions.RequestException as e:
            # Essayer d'extraire un message d'erreur plus détaillé de la réponse de l'API
            error_details = ""
            if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
                try:
                    # La réponse de l'API Evolution est souvent en JSON
                    api_error = e.response.json()
                    error_details = f" (Détail API : {api_error.get('message') or e.response.text})"
                except ValueError:
                    # Si la réponse n'est pas du JSON, on utilise le texte brut
                    error_details = f" (Détail API : {e.response.text})"
            raise UserError(f"Erreur lors de la communication avec l'API WhatsApp : {str(e)}{error_details}")
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Succès',
                'message': 'Message WhatsApp envoyé avec succès.',
                'type': 'success',
                'sticky': False,
            }
        }