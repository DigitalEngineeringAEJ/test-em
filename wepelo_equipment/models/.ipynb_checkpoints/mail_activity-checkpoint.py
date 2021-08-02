# -*- coding: utf-8 -*-

import base64
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.exceptions import ValidationError


class EquipmentMailActivity(models.AbstractModel):
    _name = 'equipment.mail.activity'
    _description = 'Equipment Mail Activity'

    iea_ma = fields.Float(string='IEA [mA]')
    riso_m = fields.Float(string='RISO [MΩ]', default=19.99)
    rpe = fields.Float(string='RPE [Ω]')
    operator_rpe = fields.Selection([('equal', '='), ('greater_then', '>'), ('less_then', '<')], string='RPE Operator', default='equal')
    operator_riso = fields.Selection([('equal', '='), ('greater_then', '>'), ('less_then', '<')], string='RISO Operator', default='greater_then')
    operator_iea = fields.Selection([('equal', '='), ('greater_then', '>'), ('less_then', '<')], string='IEA Operator', default='equal')
    protection_class = fields.Char(string='Protection Class', default='I')
    visual_inspection = fields.Selection([('i.o', 'i.O'), ('n.i.o', 'n.i.O')], string='Visual Inspection', default='i.o')
    voltage_u_in_volts_v = fields.Float(string='Voltage U in volts [V]',  default=230)
    frequency_f_in_heart_hz = fields.Float(string='Frequency F in heart [Hz]', default=50)
    signature = fields.Binary(string='Signature')
    functional_test = fields.Selection([('i.o', 'i.O'), ('n.i.o', 'n.i.O')], string='Functional Test', default='i.o')
    tested_din_vde_0701_0702 = fields.Selection([('protective_line', 'Protective Line'), ('protective_insulation', 'Protective Insulation')],
                                                string='Tested according to DIN VDE 0701-0702 and Protected by', default='protective_line')
    evaluation = fields.Selection([('correspond_device', 'The device corresponds to the recognized rules of electrical engineering.'),
                                   ('not_correspond_device', 'The device does not corresponds to the recognized rules of electrical engineering.')],
                                   string='Evaluation', default='correspond_device')

    exhaust_hose_probe = fields.Boolean(string='Exhaust hose and exhaust probe removed and cleaned', default=True)
    measuring_optics = fields.Boolean(string='Measuring optics checked cleaned', default=True)
    measuring_cell = fields.Boolean(string='Measuring cell cleaned', default=True)
    cables_hose_connections = fields.Boolean(string='All cables and hose connections checked for tight fit', default=True)
    manual_calibration = fields.Boolean(string='Manual Calibration', default=True)
    functional_control = fields.Boolean(string='Function control of the device', default=True)
    test_filter = fields.Boolean(string='Testing the filters', default=True)
    test_calibration_filter = fields.Boolean(string='Testing of calibration filters (values see calibration certificate)', default=True)

    pre_filter = fields.Boolean(string='Prefilter removed and cleaned', default=True)
    coarse_filter = fields.Boolean(string='Coarse filter removed and cleaned', default=True)
    fine_filter = fields.Boolean(string='Fine filter replaced', default=True)
    leak_test_seal = fields.Boolean(string='Leak test seal checked for damage', default=True)
    leak_test_performed = fields.Boolean(string='Leak test performed', default=True)
    test_o2_sensor = fields.Boolean(string='O2 sensor tested', default=True)
    test_gas = fields.Boolean(string='Test Gas', default=True)
    type = fields.Char(string='Type')
    sensor_type = fields.Char(string='Sensor Type', default='Prüfung über ADU-Werte')
    sensor_serial = fields.Char(string='Serial No sensor')
    equipment_id = fields.Many2one('maintenance.equipment', compute='_get_equipment', string='Equipment', store=True)
    #gas_certificate_no = fields.Char(string='Certificate No')
    gas_certificate_no = fields.Char(related='equipment_id.test_equipment_device_id.x_zertnum' ,string='Certificate No', store=True, readonly=False)
    #gas_bottle_no = fields.Char(string='Bottle No')
    gas_bottle_no = fields.Char(related='equipment_id.test_equipment_device_id.x_flaschnum' ,string='Bottle No', store=True, readonly=False)
    #test_gas_concentration_co = fields.Float(string='Test gas concentration CO (vol %):')
    test_gas_concentration_co = fields.Float(related='equipment_id.test_equipment_device_id.x_gasco' ,string='Test gas concentration CO (vol %):', store=True, readonly=False)
    #test_gas_concentration_co2 = fields.Float(string='Test gas concentration CO2 (vol %):')
    test_gas_concentration_co2 = fields.Float(related='equipment_id.test_equipment_device_id.x_gasco2' ,string='Test gas concentration CO2 (vol %):', store=True, readonly=False)
    #test_gas_concentration_c3 = fields.Float(string='Test gas concentration C3 H8 (ppm):')
    test_gas_concentration_c3 = fields.Float(related='equipment_id.test_equipment_device_id.x_gasc3' ,string='Test gas concentration C3 H8 (ppm):', store=True, readonly=False)
    
    value_after_adjustment_co = fields.Float(string='Value displayed after adjustment CO (vol %):')
    value_after_adjustment_co2 = fields.Float(string='Value displayed after adjustment CO2 (vol %):')
    value_after_adjustment_c3 = fields.Float(string='Value displayed after adjustment C3 H8 (ppm):')
    date_action = fields.Datetime('Date current action', required=False, readonly=False, index=True, default=lambda self: fields.datetime.now())

class MailActivity(models.Model):
    _name = 'mail.activity'
    _inherit = ['mail.activity', 'equipment.mail.activity']
    _description = 'Mail Activity'

    category_id = fields.Many2one(related='equipment_id.category_id', string='Equipment Category', store=True, readonly=False)
    active = fields.Boolean(default=True)
    equipment_id = fields.Many2one('maintenance.equipment', compute='_get_equipment', string='Equipment', store=True)
    equipment_ids = fields.Many2many(comodel_name='maintenance.equipment', relation='mail_activity_maintenance_equipment_rel',
                                     column1='activity_id', column2='equipment_id', string='Equipments')
    equipment_service_id = fields.Many2one(related='equipment_id.equipment_service_id', string='Service strain', store=True, readonly=False)
    customer_id = fields.Many2one('res.partner', compute='_get_customer', string='Customer', ondelete='set null', store=True)
    customer_ids = fields.Many2many(comodel_name='res.partner', relation='mail_activity_res_partner_rel',
                                    column1='activity_id', column2='customer_id', string='Customers')
    customer = fields.Char(related='equipment_id.customer_id.name', string='Equipment Customer', readonly=True) #Kunde
    # Kundennummer einbauen --> 26.12.2020
    ref = fields.Char(related='equipment_id.customer_id.ref', string="Kundennummer")
    customer_base = fields.Char(related='customer_id.name', readonly=True) # Kundenstamm
    equipment_test_type_id = fields.Many2one(related='activity_type_id.equipment_test_type_id', store=True, readonly=False)
    equipment_test_type = fields.Selection(related='activity_type_id.equipment_test_type_id.equipment_test_type', store=True, readonly=True)
    exhaust_measuring_device = fields.Selection(related='equipment_id.equipment_service_id.exhaust_measuring_device', store=True)
    test_equipment_ids = fields.Many2many(related="equipment_id.equipment_service_id.test_equipment_ids", string='Test Equipments')
    equipment_protocol_id = fields.Many2one('equipment.protocol', string="Protocol", ondelete="set null")
    test_completed = fields.Boolean(string='Test Completed', default=False)
    test_fail = fields.Boolean(string='Test Fail', default=False)
    month_more = fields.Boolean(compute='_compute_activity_months', string="> 3 Months Before Final Date", default=False, store=True)
    month_less = fields.Boolean(compute='_compute_activity_months', string='< 3 Months Before Final Date', default=False, store=True)
    month_late = fields.Boolean(compute='_compute_activity_months', string='< 1 Months Late', default=False, store=True)
    planning = fields.Selection([('basic_plan', 'Basic Planning'), ('detail_plan', 'Detail Planning')], string="Planning", default="basic_plan")
    schedule_date = fields.Datetime('Scheduled Date', help="Date the detail activity plans the equipment.")
    duration = fields.Float(help="Duration in hours.")
    serial_no = fields.Many2one('maintenance.equipment', string="Serial No", ondelete="set null")
    testing_device_name = fields.Char(related='equipment_id.equipment_type_id.name', string='testing_device_name', readonly=True)
    testing_device_sn = fields.Char(related='equipment_id.equipment_type_id.types_sn', string='testing_device_sn', readonly=True)
    
    zip2 = fields.Char(related='customer_id.zip2', string='Zip2', store=True, readonly=True)
    customer_street = fields.Char(related='customer_id.street', string='Street', store=True, readonly=True)
    customer_zip = fields.Char(related='customer_id.zip', string='ZIP', store=True, readonly=True)
    customer_city = fields.Char(related='customer_id.city', string='City', store=True, readonly=True)

    @api.depends('res_model', 'res_id')
    def _get_equipment(self):
        for activity in self:
            activity.equipment_id = False
            if activity.res_model == 'maintenance.equipment':
                equipment = activity.res_model and self.env[activity.res_model].browse(activity.res_id)
                if equipment:
                    activity.equipment_id = equipment
                    activity.summary = equipment.name

    @api.depends('res_model', 'res_id', 'activity_type_id', 'customer_id', 'summary')
    def _compute_res_name(self):
        for activity in self:
            if activity.res_model == 'maintenance.equipment':
                if activity.activity_type_id and activity.customer_id and activity.summary:
                    activity.res_name = activity.activity_type_id.name +'/'+ activity.customer_id.name +'/'+activity.summary
                elif activity.activity_type_id and not activity.customer_id and not activity.summary:
                    activity.res_name = activity.activity_type_id.name
                elif activity.activity_type_id and activity.customer_id and not activity.summary:
                    activity.res_name = activity.activity_type_id.name +'/'+ activity.customer_id.name
                elif activity.activity_type_id and not activity.customer_id and activity.summary:
                    activity.res_name = activity.activity_type_id.name +'/'+ activity.summary
                elif not activity.activity_type_id and activity.customer_id and activity.summary:
                    activity.res_name = activity.customer_id.name +'/'+ activity.summary
            else:
                super(MailActivity, self)._compute_res_name()
                
    @api.onchange('activity_type_id')
    def action_generate_history_vals(self): 
        history_vals3 = {
        'name': self.equipment_id.id,
        'current_date': self.date_action.now(),
        'topic': self.activity_type_id.name
        }
        history3 = self.env['equipment.history'].create(history_vals3)

    @api.depends('equipment_id')
    def _get_customer(self):
        for activity in self:
            activity.customer_id = activity.equipment_id.customer_id

    @api.depends('date_deadline')
    def _compute_activity_months(self):
        for activity in self:
            remaining_months = (activity.date_deadline.year - date.today().year) * 12 + (activity.date_deadline.month - date.today().month)
            if remaining_months >= 3:
                activity.update({'month_more': True, 'month_late': False, 'month_less': False})
            elif remaining_months >=1 and remaining_months < 3:
                activity.update({'month_less': True, 'month_more': False, 'month_late': False})
            elif remaining_months < 1:
                activity.update({'month_late': True, 'month_more': False, 'month_less': False})

    @api.onchange('schedule_date')
    def onchange_schedule_date(self):
        if self.schedule_date:
            self.date_deadline = self.schedule_date.date()

    def unlink(self):
        maintenance = self.filtered(lambda rec: rec.res_model == 'maintenance.equipment' and rec.active)
        records = self
        if maintenance:
            maintenance.write({'active': False})
            records = self - maintenance
        return super(MailActivity, records).unlink()

    def action_activity_fail(self):
        self.update({'test_fail': True, 'month_late': False, 'month_more': False, 'month_less': False})
        self.action_done()

    def action_generate_protocol(self):
        protocol_vals = {
            'name': self.equipment_id.name,
            'date': self.date_deadline,
            'order_date': fields.Date.context_today(self),
            'customer_id': self.customer_id.id,
            'contractor_id': self.user_id.id,
            'manufacturer_id': self.equipment_id.manufacturer_id.id,
            'mail_activity_id': self.id,
            'equipment_test_type_id': self.activity_type_id.equipment_test_type_id.id,
            'equipment_test_type': self.equipment_test_type,
            'serial_no': self.equipment_id.serial_no,
            'equipment_service_id': self.equipment_id.equipment_service_id.id,
            'signature': self.signature or False,
            'visual_inspection': self.visual_inspection,
            'functional_test': self.functional_test,
            #Neue Felder per 26.12.2020 
            'equipment_id':self.equipment_id.id,
            'ref':self.ref
        }
        if self.equipment_test_type == 'el_test' and self.exhaust_measuring_device == 'petrol':
            el_test_vals = {
                'testing_device': self.testing_device_name,
                'testing_device_sn': self.testing_device_sn,
                'type': 'Infralyt Smart',
                'voltage_u_in_volts_v': self.voltage_u_in_volts_v,
                'frequency_f_in_heart_hz': self.frequency_f_in_heart_hz,
                'protection_class': self.protection_class,
                'tested_din_vde_0701_0702': self.tested_din_vde_0701_0702,
                'rpe': self.rpe,
                'operator_rpe': self.operator_rpe,
                'riso_m': self.riso_m,
                'operator_riso': self.operator_riso,
                'iea_ma': self.iea_ma,
                'operator_iea': self.operator_iea,
                'evaluation': self.evaluation,
            }
            protocol_vals.update(el_test_vals)
        if self.equipment_test_type == 'el_test' and self.exhaust_measuring_device == 'diesel':
            el_test_vals = {
                'testing_device': self.testing_device_name,
                'testing_device_sn': self.testing_device_sn,
                'type': 'Opacylit 1030',
                'voltage_u_in_volts_v': self.voltage_u_in_volts_v,
                'frequency_f_in_heart_hz': self.frequency_f_in_heart_hz,
                'protection_class': self.protection_class,
                'tested_din_vde_0701_0702': self.tested_din_vde_0701_0702,
                'rpe': self.rpe,
                'operator_rpe': self.operator_rpe,
                'riso_m': self.riso_m,
                'operator_riso': self.operator_riso,
                'iea_ma': self.iea_ma,
                'operator_iea': self.operator_iea,
                'evaluation': self.evaluation,
            }
            protocol_vals.update(el_test_vals)
        if self.equipment_test_type == 'maintenance' and self.exhaust_measuring_device == 'diesel':
            maintenance_diesel_vals = {
                'exhaust_hose_probe': self.exhaust_hose_probe,
                'measuring_optics': self.measuring_optics,
                'measuring_cell': self.measuring_cell,
                'cables_hose_connections': self.cables_hose_connections,
                'manual_calibration': self.manual_calibration,
                'functional_control': self.functional_control,
                'test_filter': self.test_filter,
                'test_calibration_filter': self.test_calibration_filter,
            }
            protocol_vals.update(maintenance_diesel_vals)

        if self.equipment_test_type == 'maintenance' and self.exhaust_measuring_device == 'petrol':
            maintenance_petrol_vals = {
                'exhaust_hose_probe': self.exhaust_hose_probe,
                'pre_filter': self.pre_filter,
                'coarse_filter': self.coarse_filter,
                'fine_filter': self.fine_filter,
                'leak_test_seal': self.leak_test_seal,
                'leak_test_performed': self.leak_test_performed,
                'test_o2_sensor': self.test_o2_sensor,
                'test_gas': self.test_gas,
                'sensor_type': self.sensor_type,
                'sensor_serial': self.sensor_serial,
                'gas_certificate_no': self.gas_certificate_no,
                'gas_bottle_no': self.gas_bottle_no,
                'test_gas_concentration_co': self.test_gas_concentration_co,
                'test_gas_concentration_co2': self.test_gas_concentration_co2,
                'test_gas_concentration_c3': self.test_gas_concentration_c3,
                'value_after_adjustment_co': self.value_after_adjustment_co,
                'value_after_adjustment_co2': self.value_after_adjustment_co2,
                'value_after_adjustment_c3': self.value_after_adjustment_c3
            }
            protocol_vals.update(maintenance_petrol_vals)

        protocol = self.env['equipment.protocol'].create(protocol_vals)
        self.write({'equipment_protocol_id': protocol.id,
                    'test_completed': True,
                    'month_late': False,
                    'month_more': False,
                    'month_less': False,
                })

        if self.equipment_test_type == 'el_test' or (self.equipment_test_type == 'maintenance' and self.exhaust_measuring_device in ['diesel', 'petrol']):
            if self.equipment_test_type == 'el_test':
                report = self.env.ref('wepelo_equipment.wepelo_equipment_protocol').render_qweb_pdf(protocol.ids[0])
            if self.equipment_test_type == 'maintenance' and self.exhaust_measuring_device in ['diesel', 'petrol']:
                report = self.env.ref('wepelo_equipment.wepelo_equipment_protocol_maintenance').render_qweb_pdf(protocol.ids[0])
            filename = protocol.order_date.strftime('%y_%m_%d')+'_'+self.equipment_id.serial_no+'_'+self.activity_type_id.name+'.pdf'
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(report[0]),
                'store_fname': filename,
                'res_model': 'maintenance.equipment',
                'res_id': self.equipment_id.id,
                'mimetype': 'application/x-pdf'
            })
            self.equipment_id.message_post(body=_('%s Completed (originally assigned to %s)') % (self.activity_type_id.name, self.user_id.name,), attachment_ids=[attachment.id])
        else:
            self.equipment_id.message_post(body=_('%s Completed (originally assigned to %s)') % (self.activity_type_id.name, self.user_id.name,))

        if self.equipment_test_type != 'repairs':
            next_activity = self.copy()
            activity_after_days = self.equipment_test_type_id.cycle_duration
            next_activity.write({'date_deadline': (next_activity.date_deadline + relativedelta(days=activity_after_days)), 'equipment_protocol_id': False, 'test_completed': False})

    @api.onchange('planning')
    def onchange_planning(self):
        if self.planning:
            self.schedule_date = False
            self.duration = 0

    def activity_edit(self):
        return {
            "name": _("Detail Planning"),
            "res_model": "mail.activity.edit.wizard",
            "view_mode": "form",
            "type": "ir.actions.act_window",
            "target": "new",
            'context': {
                'activity_ids': self.ids,
            }
        }

    @api.onchange("user_id")
    def _onchange_user(self):
        """Change user."""
        if self.user_id and self.user_id.digital_signature:
            self.signature = self.user_id.digital_signature

    @api.model
    def create(self, vals):
        """Add sequence."""
        res = super(MailActivity, self).create(vals)
        if res:
            res.signature = res.user_id.digital_signature
        return res

class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    new_signature = fields.Binary(string='New Signature')
    equipment_test_type_id = fields.Many2one('equipment.test', string="Equipment Test")

    @api.onchange('equipment_test_type_id')
    def onchange_equipment_test_type(self):
        if self.equipment_test_type_id:
            self.name = self.equipment_test_type_id.display_name
            
# Klasse für die Test-Geräte Bennin + S/N 
class EquipmentTypes(models.Model):
    _inherit = 'equipment.types'
    
    types_sn = fields.Char(string="S/N")

   