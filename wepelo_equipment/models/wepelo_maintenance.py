# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo import exceptions
from re import search
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta
import re

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.name))
        return result

    contact_person = fields.Char(related='customer_id.contact_person', string='Contact Person', readonly=True, store=True)
    activity_id = fields.Many2one('mail.activity', string='Activity', store=True, ondelete='set null')
    activity_ids = fields.One2many('mail.activity', 'equipment_id')
    pipeline_status = fields.Selection([('status1', 'Start Production'), ('status2', 'Data')], string='Pipeline Status Bar')
    house_no = fields.Char( compute='_compute_house_no', string='House Number')
    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer', ondelete='set null', domain="[('type', '=', 'manufacturer')]")
    inventory_number = fields.Char(string='Inventory Number')
    customer_id = fields.Many2one('res.partner', string='Customer', ondelete='set null', domain="[('type', 'not in', ('manufacturer', 'vendor')), ('is_company', '=', True), ('parent_id', '=', False)]")
    partner_id = fields.Many2one('res.partner', string='Vendor', ondelete='set null', domain="[('type', '=', 'vendor')]")
    email = fields.Char(related='customer_id.email', string='Email', readonly=True, store=True)
    mobile = fields.Char(related='customer_id.mobile', string='Mobile', readonly=True, store=True)
    zip = fields.Char(related='customer_id.zip', string='Zip', readonly=True, store=True)
    test_equipment_device_id = fields.Many2one('test.equipment.device', string='Testing Device', ondelete='set null')
    equipment_service_id = fields.Many2one('equipment.service', string='Service strain', ondelete='set null')
    city = fields.Char(related='customer_id.city', string='City', readonly=True, store=True)
    street = fields.Char(string='Street', compute="_compute_house_no")
    phone = fields.Char(related='customer_id.phone', string='Phone Number', readonly=True, store=True)
    test_device_name = fields.Many2one('test.equipment.device', string='Test Gas', store=True, ondelete='set null')
    protocol_number = fields.Integer(string="Protocol Number", compute='_compute_protocol_number')
    planing_count = fields.Integer(string="Planing", compute='_compute_planing_count')
    protocols_ids = fields.One2many('equipment.protocol', 'equipment_id')
    protocol_count = fields.Integer(string="Protocol", compute='_compute_protocol_count')
    equipment_type_id = fields.Many2one('equipment.types', string="Type")
    #Anpassungen per 09.02.2021
    rechnungsnr_eichung = fields.Char(string="Rechungsnummer")
    eichamt = fields.Text(string="Eichamt")
    letzte_eichung = fields.Date(string="letzte Eichung", default=datetime.today())
    gueltigkeit_eichung = fields.Integer(string="Gültigkeit in Jahren")
    naechste_eichung = fields.Date(string="Eichung bis", default=(datetime(datetime.today().year + 1, 12, 31)).date())
    show_user_tab_eichung = fields.Boolean(string='Show User Tab Eichung', related='category_id.show_user_tab_eichung')
    owner_user_ids = fields.Many2many('res.users', string='Owners', compute='_compute_owner_users')
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    attachment_count = fields.Integer(
        string="Attachments Number", compute="_compute_attachment_count"
    )

    def attachment_tree_view(self):
        """Get attachments for this object."""
        attachment_action = self.env.ref("base.action_attachment")
        action = attachment_action.read()[0]
        action["context"] = {
            "default_res_model": self._name,
            "default_res_id": self.ids[0],
            "no_display_create": True
        }
        action["domain"] = str(
            ["&", ("res_model", "=", self._name), ("res_id", "in", self.ids)]
        )
        return action

    @api.depends("attachment_ids")
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.env["ir.attachment"].search([("res_model", "=", self._name), ("res_id", "in", self.ids)]))

    @api.depends('customer_id', 'customer_id.street')
    def _compute_house_no(self):
        for rec in self:
            rec.house_no = ""
            rec.street = rec.customer_id.street
            if rec.customer_id and rec.customer_id.street:
                first_number = re.search('[0-9]+', rec.customer_id.street)
                if first_number:
                    first_number = re.search('[0-9]+', rec.customer_id.street).group()
                    if first_number:
                        street = rec.customer_id.street.rsplit(str(first_number), 1)[0]
                        if street:
                            rec.house_no = rec.customer_id.street.rsplit(str(street), 1)[-1]
                        rec.street = street

    @api.depends('customer_id')
    def _compute_owner_users(self):
        for rec in self:
            domain = [('type', 'not in', ['manufacturer', 'vendor'])]
            if rec.customer_id:
                owner_user_ids = rec.env['res.partner'].search([('parent_id', '=', rec.customer_id.id)])
                owners = owner_user_ids
                for owner in owner_user_ids:
                    childs = rec.env['res.partner'].search([('parent_id', '=', owner.id)])
                    while childs:
                        owners += childs
                        childs = rec.env['res.partner'].search([('parent_id', 'in', childs.ids)])
                owners += rec.customer_id
                domain = [('id', 'in', owners.mapped('user_ids').ids)]
            owners = rec.env['res.users'].search(domain)
            rec.owner_user_ids = owners.ids

    def _compute_planing_count(self):
        for equipment in self:
            equipment.planing_count = len(equipment.activity_ids)
            
    def _compute_protocol_count(self):
        for equipment in self:
            equipment.protocol_count = len(equipment.protocols_ids)
            
    def _compute_protocol_number(self):
        """Get number of protocol related to this equipment."""
        for record in self:
            record.protocol_number = self.env['equipment.protocol'].search_count([('equipment_id', '=', record.id)])

        
    @api.onchange('category_id', 'serial_no')
    def onchange_category_id(self):
        if self.category_id and not self.serial_no:
            self.name = self.category_id.name
        elif self.category_id and self.serial_no:
            self.name = self.category_id.name + '/' + self.serial_no
        elif not self.category_id and self.serial_no:
            self.name = self.serial_no
        else:
            self.name = ''

    @api.constrains('serial_no')
    def _check_dates(self):
        if not self.serial_no:
            raise exceptions.ValidationError(_("Leider wurde keine Seriennummer angegeben")) 
           
    @api.onchange('serial_no')
    def onchange_equipment_type_id(self):
        substring = str("AU")
        if self.serial_no and search(substring, self.category_id.name):
            self.equipment_type_id = self.env['equipment.types'].search([('name', '=',"Benning ST 710")]).id  
    
    @api.onchange('serial_no')
    def onchance_benzin_equipment_service_id(self): 
        substring = str("Benzin")
        if self.serial_no and search(substring, self.category_id.name):
            self.equipment_service_id = self.env['equipment.service'].search([('name','ilike',"Benzin")]).id           
    
    @api.onchange('serial_no')
    def onchance_diesel_equipment_service_id(self): 
        substring = str("Diesel")
        if self.serial_no and search(substring, self.category_id.name):
            self.equipment_service_id = self.env['equipment.service'].search([('name','ilike',"Diesel")]).id


class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    show_user_tab_eichung = fields.Boolean('Show User Tab Eichung')
