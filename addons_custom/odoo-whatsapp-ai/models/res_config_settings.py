from odoo import fields,models


class ResConfig(models,TransientModel):
    _inherit = 'res.config.settings'

    meta_access_token = fields.Char(string="Meta Access Token", config_parameter='whatsapp_ai_crm.meta_access_token')
    meta_phone_id = fields.Char(string="Meta Phone ID", config_parameter='whatsapp_ai_crm.meta_phone_id')

    ai_provider = fields.Selection([
        ('gemini', 'Google Gemini'),
        ('azure', 'Microsoft Azure'),
        ('openai', 'OpenAI'),
        ('claude', 'Anthropic Claude'),
        ('gro')
    ], string="AI founiseur", default='gemini', config_parameter='whatsapp_ai_crm.ai_provider')

    ai-api_key = fields.Char(string="AI API Key", config_parameter='whatsapp_ai_crm.ai_api_key')