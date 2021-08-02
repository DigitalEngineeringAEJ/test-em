from odoo import models, api
from lxml import etree


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    _order = "create_date asc"

    @api.model
    def fields_view_get(
            self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """fields_view_get to remove create from list of attachment."""
        res = super(IrAttachment, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if self.env.context.get("no_display_create"):
            doc = etree.XML(res["arch"])
            for node in doc.xpath("//kanban"):
                node.set("create", "0")
                node.set("edit", "0")
                node.set("delete", "0")
            for node in doc.xpath("//tree"):
                node.set("create", "0")
                node.set("edit", "0")
                node.set("delete", "0")
            for node in doc.xpath("//form"):
                node.set("create", "0")
                node.set("edit", "0")
                node.set("delete", "0")
            res["arch"] = etree.tostring(doc, encoding="unicode")
        return res
