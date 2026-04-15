from odoo import fields, models

class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    evolution_api_url = fields.Char(string="URL Evolution API", config_parameter='odoo_whatsapp_ai.evolution_api_url', default="http://localhost:8080")
    evolution_api_key = fields.Char(string="Clé API Evolution", config_parameter='odoo_whatsapp_ai.evolution_api_key')
    evolution_instance = fields.Char(string="Nom Instance", config_parameter='odoo_whatsapp_ai.evolution_instance')
    key_ai_api = fields.Char(string="Clé API IA", config_parameter='odoo_whatsapp_ai.key_ai_api')
    ai_model = fields.Selection([
        ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
        ('gemini-1.5-pro', 'Gemini 1.5 Pro'),
        ('gpt-4o', 'GPT-4o'),
    ], string="Modèle IA", config_parameter='odoo_whatsapp_ai.ai_model', default='gemini-1.5-flash')