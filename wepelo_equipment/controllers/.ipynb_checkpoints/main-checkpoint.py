from odoo import http
from odoo.http import request
from odoo.addons.http_routing.controllers.main import WebClient, Routing

class Routing(Routing):

    @http.route('/website/translations/<string:unique>', type='http', auth="public", website=True)
    def get_website_translations(self, unique, lang, mods=None):
        IrHttp = request.env['ir.http'].sudo()
        modules = IrHttp.get_translation_frontend_modules()
        if mods:
            modules += mods
        return WebClient().translations(unique, mods=','.join(modules), lang=request.env.user.lang)