# -*- coding: utf-8 -*-
# Name des Modells --> wepelo_repair

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta

# Anlage der Felder für das 
class XMaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    signature = fields.Binary(string='Unterschrift Bearbeiter')
    x_garantie = fields.Boolean(string='liegt eine Garantie vor')
    x_reparatur = fields.Text('Reparatur')
    x_durchPI = fields.Text('durch PI/Region')
    x_angegebener_fehler = fields.Text('angegebener Fehler')
    date_action = fields.Datetime('Date current action', required=False, readonly=False, index=True, default=lambda self: fields.datetime.now())
    
    #Anpassungen per 19.02.2021 ------ 
    
    last_calibration = fields.Date(string='Letzte Kalibrierung')
    receipt_date = fields.Date(string='Eingangsdatum', default=datetime.today())
    outgoing_date = fields.Date(string='Ausgangsdatum', compute='_compute_outgoing_date')
    lead_time_manufacturer = fields.Integer(string='Tage Hersteller')
    lead_time_contractor  = fields.Integer(string='Tage Auftragnehmer', default=1)
    sum_lead_time = fields.Integer(string='Summe Durchlaufzeit', compute='_compute_sum_lead_time')
    commment = fields.Text(string='Bemerkung')
    
    costs_manufacturer = fields.Float(string='Kosten Hersteller')
    costs_contractor = fields.Float(string='Eigene Kosten')
    costs_parcel_service = fields.Float(string='Kosten Paketdienstleister')
    sum_costs = fields.Float(string='Summe Kosten', compute='_compute_sum_costs')
    invoice_nr = fields.Char(string='Rechnungsnummer')
    
    
    @api.constrains('lead_time_contractor')
    def _compute_sum_lead_time(self):
        for record in self:
            self.sum_lead_time = self.lead_time_manufacturer + self.lead_time_contractor
    
    @api.constrains('sum_lead_time')
    def _compute_outgoing_date(self):
        if self.sum_lead_time:
            for record in self:
                self.outgoing_date = self.receipt_date + relativedelta(days=self.sum_lead_time)
        else: 
            self.outgoing_date = self.date_action.now()
            
    @api.constrains('costs_contractor')
    def _compute_sum_costs(self):
        for record in self:
            self.sum_costs = self.costs_manufacturer + self.costs_contractor + self.costs_parcel_service
            
    # --------
    
    #@api.onchange('kanban_state')
    #def action_generate_protocol_rep(self):
    @api.onchange('equipment_id', 'request_date')
    def onchange_equipmentid(self):
        if self.equipment_id.serial_no and self.request_date:
            self.name = self.equipment_id.serial_no + '_' + str(self.request_date.strftime('%d/%m/%y'))

    name = fields.Char(string='Name')
    
    def action_generate_protocol_rep(self):
        protocol_vals = {
            'name': self.equipment_id.name,
            'category_id':self.category_id.name,
            'description':self.description,
            'signature': self.signature,
            'x_garantie':self.x_garantie,
            'x_reparatur':self.x_reparatur,
            'x_durchPI':self.x_durchPI,
            'x_angegebener_fehler':self.x_angegebener_fehler,
            'order_date':self.request_date,
            'date':self.schedule_date,
            'serial_no':self.env['maintenance.equipment'].search([('id', '=', self.equipment_id.id)]).serial_no,
            'manufacturer_id':self.env['maintenance.equipment'].search([('id', '=', self.equipment_id.id)]).manufacturer_id.id,
            'customer_id':self.env['maintenance.equipment'].search([('id', '=', self.equipment_id.id)]).customer_id.id,
            'contractor_id':self.env['maintenance.equipment'].search([('id', '=', self.equipment_id.id)]).technician_user_id.id,
            'equipment_service_id':self.env['equipment.service'].search([('name','=',"Reparatur")]).id,
            'maintenance_request_id':self.id
            #'equipment_service_id':3 --> So wäre das richtig schlecht programmmiert --> Hardcode Pfui!!!!!
            }
        history_vals = { 
        'name': self.equipment_id.id,
        'current_date': self.date_action.now(),
        'topic': 'Reparatur Protokoll erstellt',
        'request_id': self.id,
            }
        
        protocol = self.env['equipment.protocol'].create(protocol_vals)
        history = self.env['equipment.history'].create(history_vals)
        
    @api.onchange('stage_id')
    def action_generate_history_vals(self): 
        history_vals2 = {
        'name': self.equipment_id.id,
        'current_date': self.date_action.now(),
        'topic': self.stage_id.name,
        'request_id':self.id,
          }
        history2 = self.env['equipment.history'].create(history_vals2)