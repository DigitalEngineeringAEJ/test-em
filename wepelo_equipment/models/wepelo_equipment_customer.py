# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo import exceptions

class ResPartner(models.Model):
    _inherit = 'res.partner'

    name = fields.Char(string='Name')
    contact_person = fields.Char(string='Contact Person')
    additive = fields.Char(string='Additive')
    type = fields.Selection(selection_add=[('manufacturer', 'Manufacturer'), ('calibration_service', 'Calibration Service'),('vendor', 'Vendor')])
    equipment_ids = fields.One2many('maintenance.equipment', 'customer_id', string='Equipments', copy=False)
    equipment_protocol_ids = fields.One2many('equipment.protocol', 'customer_id', string ='Protocols', copy=False)
    equipment_count = fields.Integer(string="Equipment", compute='_compute_equipment_count')
    protocol_count = fields.Integer(string="Protocol", compute='_compute_protocol_count')

    def _compute_equipment_count(self):
        for customer in self:
            customer.equipment_count = len(customer.equipment_ids)
    
    def _compute_protocol_count(self):
        for customer in self:
            customer.protocol_count = len(customer.equipment_protocol_ids)

    @api.constrains('ref')
    def _check_ref_no(self):
        if self.company_type == 'company':
            if not self.ref:
                raise exceptions.ValidationError(_("Leider wurde keine Kundennummer angegeben"))

    @api.model
    def create(self, vals):
        """Add sequence."""
        vals.update({"ref": self.env["ir.sequence"].next_by_code("res.partner.ref.seq")})
        return super(ResPartner, self).create(vals)
            
class EquipmentTypes(models.Model):
    _name = 'equipment.types'
    _description = 'Equipment Types'

    name = fields.Char(string='Name')
