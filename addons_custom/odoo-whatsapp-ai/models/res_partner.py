from odoo import models, fields
class ResPartner(models.Model):
    _inherit = 'res.partner'
    is_ai_generated = fields.Boolean(default=False)