{
    'name': 'WhatsApp AI CRM',
    'version': '1.0',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml', 
        'views/menus.xml',                    
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}