# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    # Configuration Evolution API
    evolution_api_url = fields.Char(
        string="URL Evolution API", 
        config_parameter='odoo_whatsapp_ai.evolution_api_url',
        default="http://localhost:8080"
    )
    evolution_api_key = fields.Char(
        string="Clé API (apikey)", 
        config_parameter='odoo_whatsapp_ai.evolution_api_key'
    )
    evolution_instance_name = fields.Char(
        string="Nom de l'Instance", 
        config_parameter='odoo_whatsapp_ai.evolution_instance'
    )

    # Configuration IA
    ai_api_key = fields.Char(
        string="AI API Key", 
        config_parameter='odoo_whatsapp_ai.ai_api_key'
    )
    ai_provider = fields.Selection([
        ('gemini', 'Google Gemini'),
        ('openai', 'OpenAI'),
    ], string="Fournisseur IA", default='gemini', config_parameter='odoo_whatsapp_ai.ai_provider')