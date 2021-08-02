# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class EquipmentProtocol(models.Model):
    _name = 'equipment.protocol'
    _inherit = ['equipment.mail.activity']
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
    equipment_test_type = fields.Selection(related='mail_activity_id.equipment_test_type_id.equipment_test_type', store=True, readonly=True)
    serial_no = fields.Char(string='Serial No')
    type = fields.Char(string='Type')
    sensor_type = fields.Char(string='Sensor Type')
    sensor_serial = fields.Char(string='Serial Number')
    gas_certificate_no = fields.Char(string='Certificate No')
    gas_bottle_no = fields.Char(string='Bottle No')
    remarks = fields.Char(string='Remarks')
    date = fields.Date(string='Due Date')
    #Anpassungen per 22.12.2020 
    category_id = fields.Char(string='Category')
    description = fields.Char(string='Beschreibung Anmerkungen')
    #Anpassung per 26.12.2020
    ref = fields.Char(string='Kunden-Nummer')

    def _get_report_filename(self):
        return self.order_date.strftime('%y_%m_%d')+'_'+self.serial_no+'_'+self.mail_activity_id.activity_type_id.name