import os

folders = ['controllers', 'models', 'utils', 'security', 'views']
for folder in folders:
    os.makedirs(folder, exist_ok=True)

files = {
    "__manifest__.py": "{'name': 'WhatsApp AI CRM', 'version': '1.0', 'depends': ['base', 'contacts'], 'data': ['security/ir.model.access.csv'], 'installable': True, 'application': True}",
    "__init__.py": "from . import controllers\nfrom . import models",
    "models/__init__.py": "from . import res_partner",
    "controllers/__init__.py": "from . import main",
    "utils/__init__.py": "",
    "models/res_partner.py": "from odoo import models, fields\nclass ResPartner(models.Model):\n    _inherit = 'res.partner'\n    is_ai_generated = fields.Boolean(default=False)",
    "security/ir.model.access.csv": "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\naccess_res_partner_ai,res.partner.ai,model_res_partner,,1,1,1,1"
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("--- Structure Odoo creee avec succes (UTF-8) ---")