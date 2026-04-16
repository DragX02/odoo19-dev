{
    'name': 'WhatsApp AI CRM',
    'version': '1.0',
    'author': 'Odoo Dev',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/whatsapp_message_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_whatsapp_ai/static/src/css/whatsapp_chat.css',
            'odoo_whatsapp_ai/static/src/xml/whatsapp_chat.xml',
            'odoo_whatsapp_ai/static/src/js/whatsapp_chat.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}