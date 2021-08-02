# -*- coding: utf-8 -*-

import base64
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.exceptions import ValidationError
from collections import defaultdict
import calendar

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
    sensor_serial = fields.Char(related='equipment_id.test_equipment_device_id.sn', string='Serial No sensor', store=True, readonly=False)
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
    _inherit = ['mail.activity', 'equipment.mail.activity', 'mail.thread']
    _description = 'Mail Activity'

    category_id = fields.Many2one(related='equipment_id.category_id', string='Equipment Category', store=True, readonly=False)
    active = fields.Boolean(default=True)
    equipment_id = fields.Many2one('maintenance.equipment', compute='_get_equipment', string='Equipment', store=True)
    equipment_ids = fields.Many2many(comodel_name='maintenance.equipment', relation='mail_activity_maintenance_equipment_rel',
                                     column1='activity_id', column2='equipment_id', string='Equipments')
    equipment_service_id = fields.Many2one(related='equipment_id.equipment_service_id', string='Service strain"', store=True, readonly=False)
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
    month_more = fields.Boolean(compute='_compute_activity_months', string="> 3 Months Before Final Date")
    month_less = fields.Boolean(compute='_compute_activity_months', string='< 3 Months Before Final Date')
    month_late = fields.Boolean(compute='_compute_activity_months', string='< 1 Months Late')
    planning = fields.Selection([('basic_plan', 'Basic Planning'), ('detail_plan', 'Detail Planning')], string="Planning", default="basic_plan")
    schedule_date = fields.Datetime('Scheduled Date', help="Date the detail activity plans the equipment.")
    duration = fields.Float(help="Duration in hours.")
    serial_no = fields.Char('Serial Number')
    testing_device_name = fields.Char(related='equipment_id.equipment_type_id.name', string='testing_device_name', readonly=True)
    testing_device_sn = fields.Char(related='equipment_id.equipment_type_id.types_sn', string='testing_device_sn', readonly=True)
    
    zip2 = fields.Char(related='customer_id.zip2', string='Zip2', store=True, readonly=True)
    customer_street = fields.Char(related='customer_id.street', string='Street', store=True, readonly=True)
    customer_zip = fields.Char(related='customer_id.zip', string='ZIP', store=True, readonly=True)
    customer_city = fields.Char(related='customer_id.city', string='City', store=True, readonly=True)

    schedule_activity_type_ids = fields.One2many('schedule.activity.type', 'mail_activity_id', string="Activity Types")
    eichamt = fields.Char(string="Eichamt")
    test_specification_ids = fields.One2many('mail.activity.test', 'mail_activity_id', string="Tests Specification")
    is_exam_result_review = fields.Boolean(string="Weiterbetrieb bedenklich, Nachprüfung erforderlich")
    is_result_continuation_operation = fields.Boolean(string="Weiterbetrieb möglich, Mängel beheben")
    is_result_exam_no_defect = fields.Boolean(string="Keine Mängel, Weiterbetrieb bedenkenlos")
    is_exam_regular = fields.Boolean(string="Regelmäßige Prüfung")
    is_extraordinary = fields.Boolean(string="Außerordentliche Prüfung")
    is_exam_tore_review = fields.Boolean(string="Nachprüfung")
    result_exam_no_defects = fields.Boolean(string="Es wurden keine Mängel festgestellt")
    result_exam_defects = fields.Boolean(string="Es wurden folgende Mängel festgestellt:")
    note_tore = fields.Text(string="Note Tore")
    partial_exams = fields.Char(string="Ausstehende Teilprüfungen: ")
    operation_no_defects = fields.Boolean(string="Weiterbetrieb bedenkenlos, keine Mängel feststellbar")
    operation_review = fields.Boolean(string="Weiterbetrieb ist bedenklich, Nachprüfung erforderlich")
    operation_defects_remedied = fields.Boolean(string="Weiterbetrieb möglich, Mängel müssen behoben werden")
    calibration_device = fields.Char(string="Kalibriervorrichtung: ")
    ks = fields.Integer(string="KS: ")
    is_torque_measurement = fields.Boolean(string="Rollenbremsprüfstand auf der Basis der Drehmomentmessung")
    is_thermal_power = fields.Boolean(string="Rollenbremsprüfstand auf der Basis der Wirkleistungsmessung")
    is_plate = fields.Boolean(string="Plattenbremsprüfstand")
    small_measuring_range = fields.Float(string="Small measuring range")
    large_measuring_range = fields.Float(string="Large measuring range")
    measuring_ids = fields.One2many('mail.activity.measuring', 'mail_activity_id', string="Measuring")
    max_difference_ids = fields.One2many('mail.activity.max.difference', 'mail_activity_id', string="Max difference")
    is_test_speed = fields.Boolean(string="Prüfgeschwindigkeit bei Nenndrehzahl und max. Bremslast, für die der Bremsenprüfstand ausgelegt ist, wurde eingehalten")
    is_key_switch = fields.Boolean(string="Schlupfabschaltung bei max. 30 % tatsächlichem Schlupf wurde eingehalten")
    is_error_limit = fields.Boolean(string="Die Fehlergrenzen für die Anzeige von + - 2% für den gesamten Messbereich, auf den Skalenendwert, wurden eingehalten. Ab Rili 2011, bei nominaler maximaler Bremskraft von 8 kN im Messbereich 0-2000 N + -40 N und darüber + -2% vom momentanen Messwert, und bei einer nominalen maximalen Bremskraft über 8 kN im Messbereich von 0-5000 N + -100 N und darüber 2 % vom momentanen Messwert")
    is_permissible  = fields.Boolean(string="Die zulässige Abweichung zwischen der Anzeige der beiden Messgeräte li - re von 5 % des größeren Werts, jedoch höchstens 2 % des Skalenwerts, wurde eingehalten")
    is_less_nominal_diameter = fields.Boolean(string="Der gemessene Rollendurchmesser war an keiner Stelle geringer als 98 % vom Nenndurchmesser")
    is_surface_quality = fields.Boolean(string="Oberflächenbeschaffenheit der Rollen wurde eingehalten")
    is_no_concerns = fields.Boolean(string="Keine Bedenken")
    is_concerns = fields.Boolean(string="Bedenken. Die festgestellten Mängel sind umgehend zu beheben. Eine Wieder- holung der Stückprüfung ist innerhalb von 4 Wochen durchzuführen")
    is_next_routine_test = fields.Boolean(string="Nächste Stückprüfung:")
    month = fields.Char(string="Monat: ")
    year = fields.Char(string="Jahr: ")
    is_manufacturer = fields.Boolean(string="des Herstellers oder Importeurs")
    is_responsible_calibration_authority = fields.Boolean(string="der zuständigen Eichbehörde")
    is_state_side = fields.Boolean(string="von staatlicher Seite")
    is_technical_test = fields.Boolean(string="einer Technischen Prüfstelle")
    is_officially_organizations = fields.Boolean(string="der amtlich anerkannten Überwachungsorgnisationen")
    is_vehicle = fields.Boolean(string="der KFZ-Innung oder des KFZ-Landesverbandes")

    @api.onchange('operation_no_defects')
    def _onchange_operation_no_defects(self):
        if self.operation_no_defects:
            self.operation_review = False
            self.operation_defects_remedied = False

    @api.onchange('operation_review')
    def _onchange_review(self):
        if self.operation_review:
            self.operation_no_defects = False
            self.operation_defects_remedied = False

    @api.onchange('operation_defects_remedied')
    def _onchange_operation_defects_remedied(self):
        if self.operation_defects_remedied:
            self.operation_review = False
            self.operation_no_defects = False

    @api.onchange('is_exam_regular')
    def _onchange_is_exam_regular(self):
        if self.is_exam_regular:
            self.is_extraordinary = False
            self.is_exam_tore_review = False

    @api.onchange('is_extraordinary')
    def _onchange_is_exam_extraordinary(self):
        if self.is_extraordinary:
            self.is_exam_regular = False
            self.is_exam_tore_review = False

    @api.onchange('is_exam_tore_review')
    def _onchange_iis_exam_tore_review(self):
        if self.is_exam_tore_review:
            self.is_exam_regular = False
            self.is_extraordinary = False

    @api.onchange('is_exam_result_review')
    def _onchange_is_exam_result_review(self):
        if self.is_exam_result_review:
            self.is_result_continuation_operation = False
            self.is_result_exam_no_defect = False

    @api.onchange('is_result_continuation_operation')
    def _onchange_is_result_continuation_operation(self):
        if self.is_result_continuation_operation:
            self.is_exam_result_review = False
            self.is_result_exam_no_defect = False

    @api.onchange('is_result_exam_no_defect')
    def _onchange_iis_result_exam_no_defect(self):
        if self.is_result_exam_no_defect:
            self.is_exam_result_review = False
            self.is_result_continuation_operation = False

    @api.onchange('is_manufacturer')
    def _onchange_is_manufacturer(self):
        if self.is_manufacturer:
            self.is_responsible_calibration_authority = False
            self.is_state_side = False
            self.is_technical_test = False
            self.is_officially_organizations = False
            self.is_vehicle = False

    @api.onchange('is_responsible_calibration_authority')
    def _onchange_is_responsible_calibration_authority(self):
        if self.is_responsible_calibration_authority:
            self.is_manufacturer = False
            self.is_state_side = False
            self.is_technical_test = False
            self.is_officially_organizations = False
            self.is_vehicle = False

    @api.onchange('is_state_side')
    def _onchange_is_state_side(self):
        if self.is_state_side:
            self.is_responsible_calibration_authority = False
            self.is_manufacturer = False
            self.is_technical_test = False
            self.is_officially_organizations = False
            self.is_vehicle = False

    @api.onchange('is_technical_test')
    def _onchange_is_technical_test(self):
        if self.is_technical_test:
            self.is_responsible_calibration_authority = False
            self.is_manufacturer = False
            self.is_state_side = False
            self.is_officially_organizations = False
            self.is_vehicle = False

    @api.onchange('is_officially_organizations')
    def _onchange_is_officially_organizations(self):
        if self.is_officially_organizations:
            self.is_responsible_calibration_authority = False
            self.is_manufacturer = False
            self.is_state_side = False
            self.is_technical_test = False
            self.is_vehicle = False

    @api.onchange('is_vehicle')
    def _onchange_is_vehicle(self):
        if self.is_vehicle:
            self.is_responsible_calibration_authority = False
            self.is_manufacturer = False
            self.is_state_side = False
            self.is_officially_organizations = False
            self.is_technical_test = False

    @api.onchange('is_torque_measurement')
    def _onchange_is_torque_measurement(self):
        if self.is_torque_measurement:
            self.is_thermal_power = False
            self.is_plate = False

    @api.onchange('is_thermal_power')
    def _onchange_is_thermal_power(self):
        if self.is_thermal_power:
            self.is_torque_measurement = False
            self.is_plate = False

    @api.onchange('is_plate')
    def _onchange_is_plate(self):
        if self.is_plate:
            self.is_torque_measurement = False
            self.is_thermal_power = False

    @api.onchange('result_exam_no_defects')
    def _onchange_result_exam_no_defects(self):
        if self.result_exam_no_defects:
            self.result_exam_defects = False

    @api.onchange('result_exam_defects')
    def _onchange_result_exam_defects(self):
        if self.result_exam_defects:
            self.result_exam_no_defects = False
        else:
            self.note_tore = ""

    @api.depends('res_model', 'res_id')
    def _get_equipment(self):
        for activity in self:
            activity.equipment_id = False
            if activity.res_model == 'maintenance.equipment':
                equipment = activity.res_model and self.env[activity.res_model].browse(activity.res_id)
                if equipment:
                    activity.equipment_id = equipment
                    activity.summary = equipment.name
                    activity.serial_no = equipment.serial_no

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
        if self.equipment_test_type and self.category_id and self.equipment_test_type == 'uvv' and self.category_id == self.env.ref("wepelo_equipment.equipment_hebebuhne"):
            self.test_specification_ids = False
            test_specification_data = []
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Typenschild")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Kurzanleitung Bedienung")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Warmkennzeichnung")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Ausführliche Bedienungsanleitung")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _('Kennzeichnung ,,Heben Senken"')}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Allgemeinzustand der Hebebühne")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Abschließbarer Hauptschalter")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Zustand Tragteller")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Sicherung der Bolzen")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Zustand/Funktion Fußabweiser")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Zustand Bolzen und Lagerstellen")}).id)
            test_specification_data.append(self.env["mail.activity.test"].new(
                {"test_specification": _("Tragkonstruktion (Verformung, Risse)")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Anzugsmoment Befestigungsdübel")}).id)
            test_specification_data.append(self.env["mail.activity.test"].new(
                {"test_specification": _("Fester Sitz aller tragenden Schrauben")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Zustand Polyflexriemen")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Zustand Tragarme")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Zustand Spindelzentrierung")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Zustand der Abdeckungen")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Zustand Hubspindel und Tragmutter")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Standsicherheit der Hebebühne")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Zustand Betonboden (Risse)")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Fester Sitz aller Schrauben")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Zustand Elektroleitungen")}).id)
            test_specification_data.append(self.env["mail.activity.test"].new(
                {"test_specification": _("Funktionstest Hebebühne mit Fahrzeug")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _("Funktion Tragarmarretierung")}).id)
            test_specification_data.append(
                self.env["mail.activity.test"].new({"test_specification": _('Funktionstest „Oben- und Unten-Aus"')}).id)
            test_specification_data.append(self.env["mail.activity.test"].new(
                {"test_specification": _(" Funktion elek. Gleichaufüberwachung")}).id)
            self.test_specification_ids = [(6, 0, test_specification_data)]
        if self.equipment_test_type == 'routine_test' and self.category_id == self.env.ref(
                "wepelo_equipment.equipment_bremsprufstand"):
            self.measuring_ids = False
            self.max_difference_ids = False
            measuring_data = []
            max_difference_data = []
            measuring_data.append(
                self.env["mail.activity.measuring"].new({"name": _("Nullpunkt:")}).id)
            measuring_data.append(
                self.env["mail.activity.measuring"].new({"name": _("Anzeige bei 30% Belastung:")}).id)
            measuring_data.append(
                self.env["mail.activity.measuring"].new({"name": _("Anzeige bei max Belastung:")}).id)
            self.measuring_ids = [(6, 0, measuring_data)]
            max_difference_data.append(
                self.env["mail.activity.max.difference"].new({"name": _("Anzeige bei 30% Belastung:")}).id)
            max_difference_data.append(
                self.env["mail.activity.max.difference"].new({"name": _("Anzeige bei max Belastung:")}).id)
            self.max_difference_ids = [(6, 0, max_difference_data)]
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
            months = activity.date_deadline.month - date.today().month
            days = abs((activity.date_deadline - date.today()).days)
            if activity.date_deadline.month == date.today().month:
                number_days_month = calendar.monthrange(date.today().year,date.today().month)[1]
            else:
                if activity.date_deadline.day > calendar.monthrange(date.today().year,date.today().month)[1]:
                    second_date = date(date.today().year, date.today().month, calendar.monthrange(date.today().year,date.today().month)[1])
                else:
                    second_date = date(date.today().year, date.today().month, activity.date_deadline.day)
                number_days_month = (activity.date_deadline - second_date).days
            activity.month_more = False
            activity.month_late = False
            activity.month_less = False
            if not activity.test_completed:
                if ((months == 1 and days > number_days_month) or months >1) and (months < 3 or (months == 3 and days <= number_days_month)) and activity.date_deadline > date.today():
                    activity.update({'month_less': True, 'month_more': False, 'month_late': False})
                elif ((months < 1 or months == 1) and days <= number_days_month and days <= 31) or activity.date_deadline <= date.today():
                    activity.update({'month_late': True, 'month_more': False, 'month_less': False})
                else:
                    activity.update({'month_late': False, 'month_more': True, 'month_less': False})

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
            'ref':self.ref,
            'eichamt':self.eichamt
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
            next_activity.write({'date_deadline': (next_activity.date_deadline + relativedelta(days=activity_after_days)), 'equipment_protocol_id': False, 'test_completed': False, 'schedule_date': False, 'duration': 0, 'planning': 'basic_plan'})
        if protocol:
            return {
                "type": "ir.actions.act_window",
                "res_model": "equipment.protocol",
                "view_mode": "form",
                "res_id": protocol.id,
        }

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
        res = super(MailActivity, self).create(vals)
        if res:
            res.signature = res.user_id.digital_signature
            if res.equipment_test_type == 'uvv' and res.category_id == self.env.ref("wepelo_equipment.equipment_hebebuhne"):
                test_specification_data = []
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Typenschild")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Kurzanleitung Bedienung")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Warmkennzeichnung")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Ausführliche Bedienungsanleitung")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _('Kennzeichnung ,,Heben Senken"')}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Allgemeinzustand der Hebebühne")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Abschließbarer Hauptschalter")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Zustand Tragteller")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Sicherung der Bolzen")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Zustand/Funktion Fußabweiser")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Zustand Bolzen und Lagerstellen")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Tragkonstruktion (Verformung, Risse)")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Anzugsmoment Befestigungsdübel")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Fester Sitz aller tragenden Schrauben")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Zustand Polyflexriemen")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Zustand Tragarme")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Zustand Spindelzentrierung")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Zustand der Abdeckungen")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Zustand Hubspindel und Tragmutter")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Standsicherheit der Hebebühne")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Zustand Betonboden (Risse)")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Fester Sitz aller Schrauben")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Zustand Elektroleitungen")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Funktionstest Hebebühne mit Fahrzeug")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Funktion Tragarmarretierung")}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _('Funktionstest „Oben- und Unten-Aus"')}).id)
                test_specification_data.append(self.env["mail.activity.test"].create({"test_specification": _("Funktion elek. Gleichaufüberwachung")}).id)
                res.test_specification_ids = [(6, 0, test_specification_data)]
            if res.equipment_test_type == 'routine_test' and res.category_id == self.env.ref("wepelo_equipment.equipment_bremsprufstand"):
                measuring_data = []
                max_difference_data = []
                measuring_data.append(
                    self.env["mail.activity.measuring"].create({"name": _("Nullpunkt:")}).id)
                measuring_data.append(
                    self.env["mail.activity.measuring"].create({"name": _("Anzeige bei 30% Belastung:")}).id)
                measuring_data.append(
                    self.env["mail.activity.measuring"].create({"name": _("Anzeige bei max Belastung:")}).id)
                res.measuring_ids = [(6, 0, measuring_data)]
                max_difference_data.append(
                    self.env["mail.activity.max.difference"].create({"name": _("Anzeige bei 30% Belastung:")}).id)
                max_difference_data.append(
                    self.env["mail.activity.max.difference"].create({"name": _("Anzeige bei max Belastung:")}).id)
                res.max_difference_ids = [(6, 0, max_difference_data)]

        return res

    def action_close_dialog(self):
        if not self.activity_type_id and self.schedule_activity_type_ids:
            # create activity for all schedule activity type
            for schedule_activity_type in self.schedule_activity_type_ids:
                self.env['mail.activity'].create({
            'activity_type_id': schedule_activity_type.activity_type_id.id,
            'summary': self.summary or schedule_activity_type.activity_type_id.summary,
            'automated': True,
            'note': self.note or schedule_activity_type.activity_type_id.default_description,
            'date_deadline': schedule_activity_type.date_deadline,
            'res_model_id': self.res_model_id.id,
            'res_model': self.res_model,
            'user_id': self.user_id.id or schedule_activity_type.activity_type_id.default_user_id.id or self.env.uid,
             'res_id': self.res_id
        })
        not_activity_types = self.env['mail.activity'].search([("activity_type_id", "=", False),("res_model_id", "=", self.res_model_id.id),("res_model", "=", self.res_model), ("res_id", "=", self.res_id)])
        for not_activity_type in not_activity_types:
            if not_activity_type.res_model == 'maintenance.equipment':
                not_activity_type.sudo().unlink()
            not_activity_type.sudo().unlink()
        return {'type': 'ir.actions.act_window_close'}

    @api.constrains("schedule_activity_type_ids", "activity_type_id")
    def _check_schedule_activity_type(self):
        for record in self:
            if not record.schedule_activity_type_ids and not record.activity_type_id:
                raise ValidationError(_("You should add Activity Type"))

    def _action_done(self, feedback=False, attachment_ids=None):
        messages = self.env['mail.message']
        next_activities_values = []

        # Search for all attachments linked to the activities we are about to unlink. This way, we
        # can link them to the message posted and prevent their deletion.
        attachments = self.env['ir.attachment'].search_read([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
        ], ['id', 'res_id'])

        activity_attachments = defaultdict(list)
        for attachment in attachments:
            activity_id = attachment['res_id']
            activity_attachments[activity_id].append(attachment['id'])
        for activity in self:
            # post message on activity, before deleting it
            # if the activity contain many activity types
            if activity.schedule_activity_type_ids and not activity.activity_type_id:
                for schedule_activity_type in activity.schedule_activity_type_ids:
                    # create activity for all schedule activity type
                    activity_done = self.create({
                        'activity_type_id': schedule_activity_type.activity_type_id.id,
                        'summary': activity.summary or schedule_activity_type.activity_type_id.summary,
                        'automated': True,
                        'note': activity.note or schedule_activity_type.activity_type_id.default_description,
                        'date_deadline': schedule_activity_type.date_deadline,
                        'res_model_id': activity.res_model_id.id,
                        'res_model': activity.res_model,
                        'user_id': activity.user_id.id or schedule_activity_type.activity_type_id.default_user_id.id or activity.env.uid,
                        'res_id': activity.res_id
                    })
                    # schedule the next activity type
                    if activity_done.activity_type_id:
                        if activity_done.force_next:
                            Activity = self.env['mail.activity'].with_context(
                                activity_previous_deadline=activity_done.date_deadline)  # context key is required in the onchange to set deadline
                            vals = Activity.default_get(Activity.fields_get())

                            vals.update({
                                'previous_activity_type_id': activity_done.activity_type_id.id,
                                'res_id': activity_done.res_id,
                                'res_model': activity_done.res_model,
                                'res_model_id': self.env['ir.model']._get(activity_done.res_model).id,
                            })
                            virtual_activity = Activity.new(vals)
                            virtual_activity._onchange_previous_activity_type_id()
                            virtual_activity._onchange_activity_type_id()
                            next_activities_values.append(virtual_activity._convert_to_write(virtual_activity._cache))
                            if self.res_model == 'maintenance.equipment':
                                self.unlink()
                        record = self.env[activity_done.res_model].browse(activity_done.res_id)
                        # archive all schedule activity type
                        record.message_post_with_view(
                            'mail.message_activity_done',
                            values={
                                'activity': activity_done,
                                'feedback': feedback,
                                'display_assignee': activity.user_id != self.env.user
                            },
                            subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_activities'),
                            mail_activity_type_id=activity_done.activity_type_id.id,
                            attachment_ids=[(4, attachment_id) for attachment_id in attachment_ids] if attachment_ids else [],
                        )
                        activity_message = record.message_ids[0]
                        message_attachments = self.env['ir.attachment'].browse(activity_attachments[activity_done.id])
                        if message_attachments:
                            message_attachments.write({
                                'res_id': activity_message.id,
                                'res_model': activity_message._name,
                            })
                            activity_message.attachment_ids = message_attachments
                        messages |= activity_message
                        activity_done.unlink()
                    not_activity_types = activity.search(
                        [("activity_type_id", "=", False), ("res_model_id", "=", activity.res_model_id.id),
                         ("res_model", "=", activity.res_model), ("res_id", "=", activity.res_id)])
                    for not_activity_type in not_activity_types:
                        if not_activity_type.res_model == 'maintenance.equipment':
                            not_activity_type.sudo().unlink()
            else:
                # if the activity contain one activity type
                if activity.force_next:
                    Activity = self.env['mail.activity'].with_context(
                        activity_previous_deadline=activity.date_deadline)  # context key is required in the onchange to set deadline
                    vals = Activity.default_get(Activity.fields_get())

                    vals.update({
                        'previous_activity_type_id': activity.activity_type_id.id,
                        'res_id': activity.res_id,
                        'res_model': activity.res_model,
                        'res_model_id': self.env['ir.model']._get(activity.res_model).id,
                    })
                    virtual_activity = Activity.new(vals)
                    virtual_activity._onchange_previous_activity_type_id()
                    virtual_activity._onchange_activity_type_id()
                    next_activities_values.append(virtual_activity._convert_to_write(virtual_activity._cache))
                record = self.env[activity.res_model].browse(activity.res_id)
                record.message_post_with_view(
                    'mail.message_activity_done',
                    values={
                        'activity': activity,
                        'feedback': feedback,
                        'display_assignee': activity.user_id != self.env.user
                    },
                    subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_activities'),
                    mail_activity_type_id=activity.activity_type_id.id,
                    attachment_ids=[(4, attachment_id) for attachment_id in attachment_ids] if attachment_ids else [],
                )

                # Moving the attachments in the message
                # directly, see route /web_editor/attachment/add
                activity_message = record.message_ids[0]
                message_attachments = self.env['ir.attachment'].browse(activity_attachments[activity.id])
                if message_attachments:
                    message_attachments.write({
                        'res_id': activity_message.id,
                        'res_model': activity_message._name,
                    })
                    activity_message.attachment_ids = message_attachments
                messages |= activity_message
        next_activities = self.env['mail.activity'].create(next_activities_values)
        self.unlink()  # will unlink activity, dont access `self` after that
        return messages, next_activities


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


class ScheduleActivityType(models.Model):
    _name = 'schedule.activity.type'
    _description = 'Schedule Activity Type'
    _order = 'activity_type_id'

    res_model_id = fields.Many2one(
        'ir.model', string='Document Model',
        index=True, related='mail_activity_id.res_model_id', compute_sudo=True, store=True, readonly=True)
    date_deadline = fields.Date('Due Date', index=True, required=True, default=fields.Date.context_today)
    activity_type_id = fields.Many2one('mail.activity.type', string='Activity Type', ondelete='restrict', required=1)
    mail_activity_id = fields.Many2one('mail.activity', string="Mail Activity")
    equipment_service_id = fields.Many2one(related='mail_activity_id.equipment_id.equipment_service_id', string='Service strain')
    mail_activity_type_ids = fields.Many2many('mail.activity.type', string="Mail Activity Types", compute="_compute_mail_activity_types")

    @api.depends("mail_activity_id.test_equipment_ids", "res_model_id")
    def _compute_mail_activity_types(self):
        for rec in self:
            domain = ['|', ('res_model_id', '=', False), ('res_model_id', '=', rec.res_model_id.id)]
            if rec.mail_activity_id.equipment_service_id:
                domain = [
                    ("equipment_test_type_id", "in", rec.mail_activity_id.test_equipment_ids.ids),

                ]
            activity_types = rec.env["mail.activity.type"].search(domain)
            rec.mail_activity_type_ids = activity_types.ids


class MailActivityTest(models.Model):
    _name = 'mail.activity.test'
    _description = 'Mail Activity Test'

    mail_activity_id = fields.Many2one('mail.activity', string='Mail Activity')
    test_specification = fields.Char(string="Prüfschrift")
    is_success = fields.Boolean(string="In Ordnung")
    is_failed = fields.Boolean(string="Mängel fehlt")
    is_after_examination = fields.Boolean(string="Nachprüfung")
    note = fields.Text(string="Bemerkung")


class MailActivityMeasuring(models.Model):
    _name = 'mail.activity.measuring'
    _description = 'Mail Activity Measuring'

    name = fields.Char(string="Messbereich: vorne/hinten oder")
    left_large = fields.Float(string="links groß")
    right_large = fields.Float(string="rechts groß")
    max_error_large = fields.Float(string="max.Fehler groß")
    left_small = fields.Float(string="links klein")
    right_small = fields.Float(string="rechts klein")
    max_error_small = fields.Float(string="max.Fehler klein")
    mail_activity_id = fields.Many2one('mail.activity', string='Mail Activity')


class MailActivityMaxDifference(models.Model):
    _name = 'mail.activity.max.difference'
    _description = 'Mail Activity Max Difference'

    name = fields.Char(string="Max Differenz der Anzeige links/rechts")
    kn = fields.Float(string="[kN]")
    percentage = fields.Float(string="[%]")
    mail_activity_id = fields.Many2one('mail.activity', string='Mail Activity')
