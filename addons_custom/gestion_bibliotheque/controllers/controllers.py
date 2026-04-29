# from odoo import http


# class GestionBibliotheque(http.Controller):
#     @http.route('/gestion_bibliotheque/gestion_bibliotheque', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/gestion_bibliotheque/gestion_bibliotheque/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('gestion_bibliotheque.listing', {
#             'root': '/gestion_bibliotheque/gestion_bibliotheque',
#             'objects': http.request.env['gestion_bibliotheque.gestion_bibliotheque'].search([]),
#         })

#     @http.route('/gestion_bibliotheque/gestion_bibliotheque/objects/<model("gestion_bibliotheque.gestion_bibliotheque"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gestion_bibliotheque.object', {
#             'object': obj
#         })

