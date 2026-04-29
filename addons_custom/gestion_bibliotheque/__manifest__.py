{
    'name': 'Gestion de Bibliothèque',
    'version': '1.0',
    'category': 'Education',
    'summary': 'Gérer les livres et les auteurs',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/livre_views.xml',
    ],
    'installable': True,
    'application': True,
}