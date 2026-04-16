from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import re
try:
    import phonenumbers
except ImportError:
    phonenumbers = None
class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_ai_generated = fields.Boolean(string="Généré par IA", default=False)
    x_phone_sanitized = fields.Char(string="Numéro de téléphone nettoyé", compute='_compute_x_phone_sanitized', store=True, index=True)
    whatsapp_message_ids = fields.One2many('whatsapp.message', 'partner_id', string="Messages WhatsApp")

    @api.depends('phone', 'country_id')
    def _compute_x_phone_sanitized(self):
        if not phonenumbers:
            for partner in self:
                partner.x_phone_sanitized = False
            return

        for partner in self:
            number = partner.phone
            if not number:
                partner.x_phone_sanitized = False
                continue
            
            country_code = partner.country_id.code if partner.country_id else None
            try:
                parsed_phone = phonenumbers.parse(number, country_code)
                if phonenumbers.is_valid_number(parsed_phone):
                    partner.x_phone_sanitized = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164).lstrip('+')
                else:
                    partner.x_phone_sanitized = False
            except phonenumbers.phonenumberutil.NumberParseException:
                partner.x_phone_sanitized = False

    def action_send_whatsapp_manual(self):
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        url = ICP.get_param('odoo_whatsapp_ai.evolution_api_url')
        key = ICP.get_param('odoo_whatsapp_ai.evolution_api_key')
        instance = ICP.get_param('odoo_whatsapp_ai.evolution_instance')
        
        if not url or not key or not instance:
            raise UserError("Veuillez configurer l'URL, la clé API et l'instance d'Evolution API dans les paramètres.")
        
        phone = self.phone
        
        if not phone: 
            raise UserError("Ce contact n'a pas de numéro de téléphone (fixe ou mobile) renseigné.")

        if not phonenumbers:
            raise UserError("La librairie 'phonenumbers' n'est pas installée. Veuillez l'installer avec 'uv pip install phonenumbers'.")

        try:
            parsed_phone = phonenumbers.parse(phone, "BE")
            if not phonenumbers.is_valid_number(parsed_phone):
                raise UserError(f"Le numéro de téléphone '{phone}' n'est pas considéré comme valide.")
            
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
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            error_details = ""
            if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
                try:
                    api_error = e.response.json()
                    error_details = f" (Détail API : {api_error.get('message') or e.response.text})"
                except ValueError:
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