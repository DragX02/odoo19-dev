from odoo import http
from odoo.http import request
import requests
import tempfile
import os
import logging

_logger = logging.getLogger(__name__)

class WhatsAppController(http.Controller):

    def _get_configs(self):
        ICP = request.env['ir.config_parameter'].sudo()
        return {
            'url': ICP.get_param('odoo_whatsapp_ai.evolution_api_url'),
            'key': ICP.get_param('odoo_whatsapp_ai.evolution_api_key'),
            'instance': ICP.get_param('odoo_whatsapp_ai.evolution_instance'),
            'ai_key': ICP.get_param('odoo_whatsapp_ai.key_ai_api'),
            'ai_model': ICP.get_param('odoo_whatsapp_ai.ai_model', default='gemini-1.5-flash'),
            'ollama_api_url': ICP.get_param('odoo_whatsapp_ai.ollama_api_url', default='http://localhost:11434'),
            'ollama_model': ICP.get_param('odoo_whatsapp_ai.ollama_model', default='llava'),
        }

    def _find_partner(self, sender_jid):
        """Finds a partner based on the WhatsApp JID."""
        Partner = request.env['res.partner'].sudo()
        phone_number = sender_jid.split('@')[0]
        if not phone_number:
            return Partner 
        
        partner = Partner.search([('x_phone_sanitized', '=', phone_number)], limit=1)
        if not partner:
            _logger.info("Webhook: Aucun partenaire trouvé pour le numéro %s (JID: %s). Vérifiez que le contact existe et que son numéro est correct.", phone_number, sender_jid)
        return partner

    @http.route(['/whatsapp/webhook', '/whatsapp/webhook/<string:path>'], type='json', auth='public', methods=['POST'], csrf=False)
    def webhook(self, path=None):
        data = request.jsonrequest if isinstance(request.jsonrequest, dict) else {}
        cfg = self._get_configs()

        if data.get('event') != 'messages.upsert':
            return {"status": "ignored"}

        msg_data = data.get('data', {})
        message = msg_data.get('message', {})
        sender = msg_data.get('key', {}).get('remoteJid')
        from_me = msg_data.get('key', {}).get('fromMe', False)

        # Si le message vient de vous (propriétaire du compte), enregistrez-le mais ne le traitez pas
        if from_me:
            # Extraire le destinataire du message envoyé
            recipient = sender
            partner = self._find_partner(recipient)

            # Enregistrer le message texte envoyé
            text = (message.get('conversation') or message.get('extendedTextMessage', {}).get('text') or "").strip()
            if text:
                request.env['whatsapp.message'].sudo().create({
                    'partner_id': partner.id if partner else None,
                    'sender_jid': recipient,
                    'body': text,
                    'message_type': 'outgoing',
                })
                _logger.info("Webhook: Message envoyé enregistré pour JID %s", recipient)

            # Enregistrer les médias envoyés
            is_image = 'imageMessage' in message
            is_pdf = 'documentMessage' in message and message['documentMessage'].get('mimetype') == 'application/pdf'
            if is_image or is_pdf:
                media_type = "image" if is_image else "pdf"
                media_filename = message.get('imageMessage', {}).get('caption') or message.get('documentMessage', {}).get('filename') or f"sent_media.{media_type}"
                request.env['whatsapp.message'].sudo().create({
                    'partner_id': partner.id if partner else None,
                    'sender_jid': recipient,
                    'body': f"Fichier {media_type} envoyé",
                    'message_type': 'outgoing',
                    'has_media': True,
                    'media_type': media_type,
                    'media_filename': media_filename,
                })
                _logger.info("Webhook: Média envoyé enregistré pour JID %s", recipient)

            return {"status": "ok"}

        partner = self._find_partner(sender)

        is_image = 'imageMessage' in message
        is_pdf = 'documentMessage' in message and message['documentMessage'].get('mimetype') == 'application/pdf'

        if is_image or is_pdf:
            from ..utils.ai_handler import analyze_card
            temp_path = self._download_media(msg_data, cfg)
            if temp_path:
                try:
                    analysis_kwargs = {
                        'api_key': cfg['ai_key'],
                        'ollama_url': cfg['ollama_api_url'],
                        'ollama_model': cfg['ollama_model'],
                    }
                    info = analyze_card(temp_path, cfg['ai_model'], **analysis_kwargs)

                    media_type = "image" if is_image else "pdf"
                    if partner:
                        display_type = "une image" if is_image else "un PDF"
                        partner.message_post(
                            body=f"Fichier reçu via WhatsApp ({display_type})... Analyse en cours.",
                            subject="Média WhatsApp Reçu", message_type='notification', subtype_xmlid='mail.mt_note'
                        )

                    # Enregistrer le message média
                    msg_vals = {
                        'partner_id': partner.id if partner else None,
                        'sender_jid': sender,
                        'body': f"Fichier {media_type} reçu",
                        'message_type': 'incoming',
                        'has_media': True,
                        'media_type': media_type,
                        'media_filename': os.path.basename(temp_path),
                    }
                    if info and "error" not in info:
                        msg_vals['ai_analysis'] = str(info)

                    request.env['whatsapp.message'].sudo().create(msg_vals)
                    if not partner:
                        _logger.info("Webhook: Message média enregistré pour JID %s (sans partenaire Odoo associé).", sender)

                    if info and "error" not in info:
                        PendingContact = request.env['whatsapp.pending.contact'].sudo()
                        pending_contact = PendingContact.search([('sender_jid', '=', sender)], limit=1)
                        contact_data = {
                            'sender_jid': sender,
                            'name': info.get('name'),
                            'email': info.get('email'),
                            'company_name': info.get('company'),
                            'phone': info.get('phone'),
                        }
                        if pending_contact:
                            pending_contact.write(contact_data)
                        else:
                            PendingContact.create(contact_data)
                        text = (f"🔍 *Infos détectées*\n\n"
                                f"👤 Nom: {info.get('name') or 'N/A'}\n"
                                f"📧 Email: {info.get('email') or 'N/A'}\n"
                                f"🏢 Sté: {info.get('company') or 'N/A'}\n\n"
                                f"1️⃣ Client\n2️⃣ Fournisseur\n3️⃣ Contact\n4️⃣ Ignorer")
                        self._send_text(sender, text, cfg, partner=partner)
                    else: # L'analyse IA a échoué ou aucun partenaire n'a été trouvé
                        error_msg = info.get("error", "Une erreur inconnue est survenue lors de l'analyse.")
                        _logger.error("Webhook: Échec de l'analyse IA pour JID %s: %s", sender, error_msg)
                        if partner:
                            partner.message_post(body=f"Échec de l'analyse IA : {error_msg}", subject="Erreur Analyse IA", message_type='notification', subtype_xmlid='mail.mt_note')
                        self._send_text(sender, f"Désolé, l'analyse de votre fichier a échoué : {error_msg}", cfg, partner=partner)

                except Exception as e: # Capturer toute autre erreur inattendue pendant l'analyse/le traitement
                    _logger.error("Webhook: Erreur inattendue lors du traitement du média pour JID %s: %s", sender, e)
                    error_msg = "Une erreur interne est survenue lors du traitement de votre fichier."
                    if partner:
                        partner.message_post(body=f"Erreur interne lors du traitement du média : {e}", subject="Erreur Traitement Média", message_type='notification', subtype_xmlid='mail.mt_note')
                    self._send_text(sender, error_msg, cfg, partner=partner)

                finally:
                    os.remove(temp_path) 
            else: # temp_path est None, ce qui signifie que le téléchargement a échoué
                error_msg = "Désolé, je n'ai pas pu télécharger votre fichier. Veuillez vérifier le format ou réessayer."
                _logger.error("Webhook: Échec du téléchargement du média pour JID %s. Message non traité.", sender)
                if partner:
                    partner.message_post(
                        body=f"Échec du téléchargement du média WhatsApp : {error_msg}",
                        subject="Erreur Média WhatsApp", message_type='notification', subtype_xmlid='mail.mt_note'
                    )
                self._send_text(sender, error_msg, cfg, partner=partner)
        
        elif 'conversation' in message or 'extendedTextMessage' in message:
            text = (message.get('conversation') or message.get('extendedTextMessage', {},).get('text') or "").strip()
            if not text:
                return {"status": "ok"}

            if partner:
                partner.message_post(body=text, subject="Message WhatsApp Reçu", message_type='comment', subtype_xmlid='mail.mt_comment')
                # Enregistrer le message dans l'historique
                request.env['whatsapp.message'].sudo().create({
                    'partner_id': partner.id,
                    'sender_jid': sender,
                    'body': text,
                    'message_type': 'incoming',
                })

            text_lower = text.lower()
            if any(w in text_lower for w in ['bonjour', 'hello', 'odoo']):
                self._send_text(sender, "Bonjour ! Le Bot Odoo est bien connecté.", cfg, partner=partner)
            elif text_lower in ['1', '2', '3', '4']:
                self._process_choice(sender, text_lower, cfg, partner=partner)
        return {"status": "ok"}

    def _download_media(self, msg_data, cfg):
        url = f"{cfg['url']}/media/download/{cfg['instance']}"
        try:
            res = requests.post(url, json={"message": msg_data}, headers={"apikey": cfg['key']}, timeout=30)
            res.raise_for_status()
            message = msg_data.get('message', {})
            mimetype = message.get('imageMessage', {}).get('mimetype') or \
                       message.get('documentMessage', {}).get('mimetype')
            
            suffix = '.bin' 
            if mimetype == 'image/jpeg':
                suffix = '.jpg'
            elif mimetype == 'image/png':
                suffix = '.png'
            elif mimetype == 'application/pdf':
                suffix = '.pdf'

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(res.content)
                return temp_file.name
        except requests.exceptions.RequestException as e:
            _logger.error("Erreur lors du téléchargement du média depuis Evolution API: %s", e)
        return None

    def _send_text(self, to, txt, cfg, partner=None):
        url = f"{cfg['url']}/message/sendText/{cfg['instance']}"
        payload = {
            "number": to,
            "text": txt
        }
        try:
            response = requests.post(url, json=payload, headers={"apikey": cfg['key']}, timeout=10)
            response.raise_for_status()
            if partner:
                partner.message_post(body=txt, subject="Réponse WhatsApp Envoyée", message_type='comment', subtype_xmlid='mail.mt_comment')
                # Enregistrer le message envoyé dans l'historique
                request.env['whatsapp.message'].sudo().create({
                    'partner_id': partner.id,
                    'sender_jid': to,
                    'body': txt,
                    'message_type': 'outgoing',
                })
        except requests.exceptions.RequestException as e:
            _logger.error("Erreur lors de l'envoi du message via Evolution API: %s", e)
            if partner:
                partner.message_post(body=f"⚠️ Échec de l'envoi de la réponse WhatsApp : {e}", subject="Erreur Envoi WhatsApp", message_type='notification', subtype_xmlid='mail.mt_note')


    @http.route('/whatsapp/send', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def send_whatsapp_message(self, partner_id, message):
        """Send a WhatsApp message from Odoo to a partner"""
        try:
            partner = request.env['res.partner'].sudo().browse(partner_id)
            if not partner.exists():
                return {"status": "error", "message": "Partner not found"}

            if not partner.phone:
                return {"status": "error", "message": "Partner has no phone number"}

            cfg = self._get_configs()
            if not cfg['url'] or not cfg['key'] or not cfg['instance']:
                return {"status": "error", "message": "WhatsApp API not configured"}

            # Get phone number in WhatsApp format
            import phonenumbers
            try:
                parsed_phone = phonenumbers.parse(partner.phone, "BE")
                cleaned_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164).lstrip('+')
                to = f"{cleaned_phone}@c.us"
            except Exception:
                return {"status": "error", "message": "Numéro de téléphone invalide ou impossible à analyser."}

            # Send the message
            self._send_text(to, message, cfg, partner=partner)
            return {"status": "ok", "message": "Message sent successfully"}
        except Exception as e:
            _logger.error("Error sending WhatsApp message: %s", e)
            return {"status": "error", "message": str(e)}

    @http.route('/whatsapp/import_history', type='json', auth='user', methods=['POST'], csrf=False)
    def import_message_history(self):
        """Importe l'historique des messages depuis Evolution API"""
        try:
            cfg = self._get_configs()
            if not cfg['url'] or not cfg['key'] or not cfg['instance']:
                return {"status": "error", "message": "WhatsApp API not configured"}

            # Récupérer tous les messages de l'instance
            url = f"{cfg['url']}/chat/messages/{cfg['instance']}"
            response = requests.get(url, headers={"apikey": cfg['key']}, timeout=30)
            response.raise_for_status()

            messages_data = response.json().get('data', [])
            Message = request.env['whatsapp.message'].sudo()
            imported_count = 0

            for msg_info in messages_data:
                # Vérifier si le message existe déjà
                existing = Message.search([
                    ('sender_jid', '=', msg_info.get('sender_jid')),
                    ('body', '=', msg_info.get('body')),
                    ('create_date', '=', msg_info.get('timestamp'))
                ], limit=1)

                if not existing:
                    sender_jid = msg_info.get('sender_jid', '')
                    partner = self._find_partner(sender_jid)

                    Message.create({
                        'partner_id': partner.id if partner else None,
                        'sender_jid': sender_jid,
                        'body': msg_info.get('body', ''),
                        'message_type': 'incoming' if not msg_info.get('fromMe') else 'outgoing',
                    })
                    imported_count += 1

            return {
                "status": "ok",
                "message": f"{imported_count} messages importés avec succès"
            }
        except Exception as e:
            _logger.error("Erreur lors de l'import de l'historique: %s", e)
            return {"status": "error", "message": str(e)}

    def _process_choice(self, sender, choice, cfg, partner=None):
        PendingContact = request.env['whatsapp.pending.contact'].sudo()
        pending_contact = PendingContact.search([('sender_jid', '=', sender)], limit=1)

        if not pending_contact:
            self._send_text(sender, "Je n'ai pas d'information en attente pour vous. Veuillez d'abord envoyer une carte de visite.", cfg, partner=partner)
            return

        if choice == '4':
            pending_contact.unlink()
            self._send_text(sender, "Opération annulée.", cfg, partner=partner)
            return

        if not pending_contact.name and not pending_contact.company_name:
            self._send_text(sender, "Impossible de créer le contact, le nom et la société sont manquants. Opération annulée.", cfg)
            pending_contact.unlink()
            return

        Partner = request.env['res.partner'].sudo()
        
        if not pending_contact.name and pending_contact.company_name:
            partner_vals = {
                'name': pending_contact.company_name,
                'company_type': 'company',
                'email': pending_contact.email,
                'phone': pending_contact.phone,
                'is_ai_generated': True,
            }
        else:  
            partner_vals = {
                'name': pending_contact.name,
                'company_type': 'person',
                'email': pending_contact.email,
                'phone': pending_contact.phone,
                'is_ai_generated': True,
            }
            if pending_contact.company_name:
                company = Partner.search([('name', '=ilike', pending_contact.company_name), ('is_company', '=', True)], limit=1)
                if not company:
                    company = Partner.create({'name': pending_contact.company_name, 'company_type': 'company'})
                partner_vals['parent_id'] = company.id

        if choice == '1':
            partner_vals['customer_rank'] = 1
        elif choice == '2':
            partner_vals['supplier_rank'] = 1

        new_partner = Partner.create(partner_vals)
        self._send_text(sender, f" Contact '{new_partner.name}' créé avec succès dans Odoo.", cfg, partner=new_partner)
        pending_contact.unlink()