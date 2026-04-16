# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class WhatsappMessage(models.Model):
    _name = 'whatsapp.message'
    _description = 'Historique des messages WhatsApp'
    _order = 'create_date DESC'

    partner_id = fields.Many2one('res.partner', string="Contact", required=False, ondelete='cascade', index=True)
    sender_jid = fields.Char(string="JID de l'expéditeur", required=True, index=True)
    body = fields.Text(string="Message")
    message_type = fields.Selection([
        ('incoming', 'Reçu'),
        ('outgoing', 'Envoyé'),
    ], string="Type", default='incoming')
    has_media = fields.Boolean(string="Contient un média", default=False)
    media_type = fields.Selection([
        ('image', 'Image'),
        ('pdf', 'PDF'),
        ('other', 'Autre'),
    ], string="Type de média")
    media_filename = fields.Char(string="Nom du fichier")
    ai_analysis = fields.Text(string="Analyse IA")
    create_date = fields.Datetime(string="Date", readonly=True)

    def _get_partner_conversation_history(self, partner_id, limit=50):
        """Retourne l'historique des messages pour un partenaire"""
        return self.search([
            ('partner_id', '=', partner_id)
        ], limit=limit, order='create_date DESC')
