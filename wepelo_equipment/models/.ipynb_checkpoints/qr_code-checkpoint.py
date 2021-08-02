import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api
import urllib

class ProductQR(models.Model):
    _inherit = "maintenance.equipment"
    qr_code = fields.Binary("QR Code", attachment=True,  compute='_compute_generate_qr_code')
    
    def _compute_generate_qr_code(self):
        for record in self:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            base_url = record.env['ir.config_parameter'].get_param('web.base.url')
            base_url += '/my/equipment/%d' % (record.id) + "/?"
            qr.add_data(base_url)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            record.qr_code = qr_image 