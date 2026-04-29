{
    'name': 'Portfolio Carousel 3D',
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Carousel 3D pour Portfolio',
    'author': 'DragX02',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'portfolio_carousel/static/src/scss/carou.scss',
            'portfolio_carousel/static/src/js/carou.js',
        ],
        'website.assets_editor': [
            'portfolio_carousel/static/src/js/website_snippet.js',
        ],
    },
    'installable': True,
    'application': False,
}