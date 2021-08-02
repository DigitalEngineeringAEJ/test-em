# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class EquipmentProtocol(models.Model):
    _name = 'equipment.protocol'
    _inherit = ['mail.thread', 'equipment.mail.activity']
    _description = 'Equipment Protocol'
    _rec_name = 'name'

    x_garantie = fields.Boolean(string='liegt eine Garantie vor')
    x_reparatur = fields.Text('Reparatur')
    x_durchPI = fields.Text('durch PI/Region')
    x_angegebener_fehler = fields.Text('angegebener Fehler')
    name = fields.Char(string="Name")
    order_date = fields.Date(string='Order Date')
    customer_id = fields.Many2one('res.partner', string='Customer')
    contractor_id = fields.Many2one('res.users', string='Contractor')
    testing_device = fields.Char(string='Testing Device')
    testing_device = fields.Char(string='Testing Device')
    testing_device_sn = fields.Char(string="S/N")
    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer')
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')
    equipment_service_id = fields.Many2one('equipment.service', string='Equipment System')
    exhaust_measuring_device = fields.Selection(related='equipment_service_id.exhaust_measuring_device', store=True, readonly=True)
    mail_activity_id = fields.Many2one('mail.activity', string='Mail Activity')
    equipment_test_type_id = fields.Many2one(related='mail_activity_id.equipment_test_type_id', store=True, readonly=True)
    equipment_test_type = fields.Selection([
        ('calibration_ei', _('Eichung')),
        ('el_test', _('DGUV V3')),
        ('routine_test', _('Stückprüfung')),
        ('calibration', _('Kalibrierung')),
        ('uvv', _('Betriebssicherheitsprüfung')),
        ('maintenance', _('Wartung')),
        ('repairs', _('Reparatur')),
    ], compute="_compute_equipment_test_type", string='Test strain')
    serial_no = fields.Char(string='Serial No')
    type = fields.Char(string='Type')
    sensor_type = fields.Char(string='Sensor Type')
    sensor_serial = fields.Char(string='Serial Number')
    gas_certificate_no = fields.Char(string='Certificate No')
    gas_bottle_no = fields.Char(string='Bottle No')
    remarks = fields.Char(string='Remarks')
    date = fields.Date(string='Due Date')
    #Anpassungen per 22.12.2020
    category_id = fields.Many2one(string='Category', related='equipment_id.category_id')
    description = fields.Char(string='Beschreibung Anmerkungen')
    #Anpassung per 26.12.2020
    ref = fields.Char(string='Kunden-Nummer')
    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance request')
    eichamt = fields.Char(string="Eichamt")
    is_downloaded = fields.Boolean(string="Downloaded", compute="_compute_downloaded_protocol")
    downloaded_user_ids = fields.Many2many('res.users', string="Downloaded users")

    @api.depends('downloaded_user_ids')
    def _compute_downloaded_protocol(self):
        for rec in self:
            rec.is_downloaded = False
            if rec._uid in rec.downloaded_user_ids.ids:
                rec.is_downloaded = True

    @api.depends('mail_activity_id.equipment_test_type_id', 'maintenance_request_id')
    def _compute_equipment_test_type(self):
        for rec in self:
            rec.equipment_test_type = False
            if rec.mail_activity_id.equipment_test_type_id:
                rec.equipment_test_type = rec.mail_activity_id.equipment_test_type_id.equipment_test_type
            if rec.maintenance_request_id:
                rec.equipment_test_type = 'repairs'

    @api.model
    def create(self, vals):
        res = super(EquipmentProtocol, self).create(vals)
        if res and res.equipment_id and res.order_date:
            res.equipment_id.letzte_eichung = res.order_date
        return res

    @api.onchange("order_date")
    def _onchange_order_date(self):
        last_protocol = False
        if self.equipment_id.protocols_ids:
            last_protocol = self.equipment_id.protocols_ids.sorted(key=lambda protocol: protocol.create_date)[-1]
        if self.order_date and self.equipment_id and last_protocol and self._origin.id == last_protocol.id:
            self.equipment_id.letzte_eichung = self.order_date

    def _get_report_filename(self):
        name =  self.order_date.strftime('%y_%m_%d')
        if self.serial_no:
            name +='_'+self.serial_no
        if self.mail_activity_id.activity_type_id.name:
            name += '_'+self.mail_activity_id.activity_type_id.name
        return name

    @api.onchange("contractor_id")
    def _onchange_contractor(self):
        """Change contractor."""
        if self.contractor_id and self.contractor_id.digital_signature:
            self.signature = self.contractor_id.digital_signature
