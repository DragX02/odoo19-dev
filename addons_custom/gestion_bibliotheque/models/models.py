from odoo import models, fields, api

class library_book(models.Model):
    _name = 'library.book'
    _description = 'Library Book'

    name = fields.Char(string='Title', required=True)
    author_id = fields.Many2one('library.author', string="Author")
    published_date = fields.Date(string='Published Date')
    isbn = fields.Char(string='ISBN')
    pages = fields.Integer(string='Number of Pages')