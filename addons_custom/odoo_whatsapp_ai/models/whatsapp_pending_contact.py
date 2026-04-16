from odoo import models, fields

class WhatsappPendingContact(models.Model):
    _name = 'whatsapp.pending.contact'
    _description = 'Stockage temporaire des informations de contact WhatsApp'

    sender_jid = fields.Char(string="JID de l'expéditeur", required=True, index=True)
    name = fields.Char(string="Nom")
    email = fields.Char(string="Email")
    company_name = fields.Char(string="Nom de la société")
    phone = fields.Char(string="Téléphone")