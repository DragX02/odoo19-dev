from odoo import models, fields, api
import requests

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_ai_generated = fields.Boolean(string="Généré par IA", default=False)

    def action_send_whatsapp_manual(self):
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        url = ICP.get_param('odoo_whatsapp_ai.evolution_api_url')
        key = ICP.get_param('odoo_whatsapp_ai.evolution_api_key')
        instance = ICP.get_param('odoo_whatsapp_ai.evolution_instance')
        
        phone = self.mobile or self.phone
        if not phone or not url: return

        payload = {
            "number": phone.replace('+', '').replace(' ', ''), 
            "text": f"Bonjour {self.name}, ce message provient d'Odoo."
        }
        requests.post(f"{url}/message/sendText/{instance}", json=payload, headers={"apikey": key})