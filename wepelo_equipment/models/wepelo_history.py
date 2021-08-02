# -*- coding: utf-8 -*-
# wepelo_history.py

from odoo import api, fields, models, _
import datetime

# Anlage der Felder 
class equipmentHistory(models.Model):
    _name = 'equipment.history'
    _inherit = 'maintenance.equipment'
    _description ='Historie des Inventars'
    #_rec_name = 'name'
    #name = fields.Char(string='Equipment Name')
    #date_hist = fields
    namehist = fields.Char(string='Name History')
    current_date = fields.Datetime(string='My date')
    topic = fields.Char(string='Topic')
    name = fields.Many2one('maintenance.equipment', string='Equipment')
    request_id = fields.Many2one('maintenance.request', string='Reparatur')