from odoo import http, _
import json
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request, content_disposition
from odoo.exceptions import AccessError, MissingError
from odoo.osv.expression import OR
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from odoo import fields, _
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import io
import zipfile
import ast

class CustomerPortal(CustomerPortal):

    def prepare_portal_values(self, global_search=None):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner_object = request.env['res.partner'].sudo()
        partner_domain = []
        partner = partner_object.search([('user_ids', 'in', [request.uid])], limit=1)
        parents_partner = partner_object.search([('parent_id', '=', partner.id)])
        owners = parents_partner
        for parent in parents_partner:
            childs = partner_object.search([('parent_id', '=', parent.id)])
            while childs:
                owners += childs
                childs = partner_object.search([('parent_id', 'in', childs.ids)])
        if partner:
            partner_domain = ['|', '|', '|',
                              '|',
                              ('customer_id', '=', partner.id),
                              ('owner_user_id', '=', request.uid),
                              ('owner_user_id', 'in', owners.mapped('user_ids').ids),
                              ('manufacturer_id', '=', partner.id),
                              ('partner_id', '=', partner.id)]
        equipment_domain = OR([[('technician_user_id', '=', request.uid)], partner_domain])
        protocol_domain = []
        if global_search:
            customer_ids = partner_object.search(['|', ('name', 'ilike', global_search),
                                                  ('ref', 'ilike', global_search)])
            equipment_domain += ['|', '|',
                                 ('name', 'ilike', global_search),
                                 ('serial_no', 'ilike', global_search),
                                 ('customer_id', 'in', customer_ids.ids)]
            protocol_domain += ['|', '|',
                                ('equipment_id.name', 'ilike', global_search),
                                ('equipment_id.serial_no', 'ilike', global_search),
                                ('customer_id', 'in', customer_ids.ids)
                                ]
        equipments = request.env['maintenance.equipment'].search(equipment_domain)
        protocol_domain += [('equipment_id', 'in', equipments.ids)]
        values['equipment_count'] = request.env['maintenance.equipment'].search_count(equipment_domain)
        values['equipments'] = equipments
        values['protocol_count'] = request.env['equipment.protocol'].search_count(protocol_domain)
        return values

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        global_search = kw.get('search', False)
        values = self.prepare_portal_values(global_search)
        values['global_search'] = global_search
        return request.render("portal.portal_my_home", values)

    # ------------------------------------------------------------
    # My Equipment
    # ------------------------------------------------------------
    def _equipment_get_page_view_values(self, equipment, access_token, **kwargs):
        values = {
            'page_name': 'equipment',
            'equipment': equipment,
            'user': request.env.user
        }
        return self._get_page_view_values(equipment, access_token, values, 'my_equipments_history', False, **kwargs)

    @http.route(['/my/equipments', '/my/equipments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_equipments(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='equipment', groupby='none', global_search=False, **kw):
        values = self.prepare_portal_values(global_search)
        partner_object = request.env['res.partner'].sudo()
        partner_domain = []
        partner = partner_object.search([('user_ids', 'in', [request.uid])], limit=1)
        parents_partner = partner_object.search([('parent_id', '=', partner.id)])
        owners = parents_partner
        for parent in parents_partner:
            childs = partner_object.search([('parent_id', '=', parent.id)])
            while childs:
                owners += childs
                childs = partner_object.search([('parent_id', 'in', childs.ids)])
        if partner:
            partner_domain = ['|', '|', '|',
                              '|',
                              ('customer_id', '=', partner.id),
                              ('owner_user_id', '=', request.uid),
                              ('owner_user_id', 'in', owners.mapped('user_ids').ids),
                              ('manufacturer_id', '=', partner.id),
                              ('partner_id', '=', partner.id)]
        user_domain = OR([[('technician_user_id', '=', request.uid)], partner_domain])
        Equipment = request.env['maintenance.equipment']
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Equipment Name'), 'order': 'name'},
            'update': {'label': _('Last Update'), 'order': 'write_date desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': user_domain},
            'assigned': {'label': _('Assigned'), 'domain': user_domain + [('assign_date', '!=', False)]},
            'unassigned': {'label': _('Unassigned'), 'domain': user_domain + [('assign_date', '=', False)]},
        }
        searchbar_inputs = {
            'equipment': {'input': 'equipment', 'label': _('Search <span class="nolabel"> (in Equipment Name)</span>')},
            'category': {'input': 'category', 'label': _('Search in Category')},
            'customer_name': {'input': 'customer_name', 'label': _('Search in Customer Name')},
            'customer_ref': {'input': 'customer_ref', 'label': _('Search in Customer Ref')},
            'manufacturer': {'input': 'manufacturer', 'label': _('Search in Manufacturer')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'category': {'input': 'equipment', 'label': _('Category')},

        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain = searchbar_filters[filterby]['domain']
        if global_search:
            customer_ids = request.env['res.partner'].sudo().search(['|', ('name', 'ilike', global_search),
                                                                     ('ref', 'ilike', global_search)])
            domain += ['|', '|', ('name', 'ilike', global_search), ('serial_no', 'ilike', global_search), ('customer_id', 'in', customer_ids.ids)]
        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('maintenance.equipment', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('equipment', 'all'):
                search_domain = OR([search_domain, ['|', '|', ('name', 'ilike', search), ('note', 'ilike', search), ('serial_no', 'ilike', search)]])
            if search_in in ('category', 'all'):
                search_domain = OR([search_domain, [('category_id.name', 'ilike', search)]])
            domain += search_domain
        # equipments count
        equipment_count = Equipment.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/equipments",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=equipment_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        # equipments = Equipment.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        # request.session['my_equipments_history'] = equipments.ids[:100]
        # content according to pager and archive selected
        if groupby == 'category':
            order = "category_id, %s" % order  # force sort on project first to group by project in view
            equipments = Equipment.search(domain, order=order, limit=self._items_per_page, offset=(page - 1) * self._items_per_page)
            request.session['grouped_equipments'] = equipments.ids[:100]
            if groupby == 'category':
                grouped_equipments = [Equipment.concat(*g) for k, g in groupbyelem(equipments, itemgetter('category_id'))]
            else:
                grouped_equipments = [equipments]
        else:

            equipments = Equipment.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
            request.session['grouped_equipments'] = equipments.ids[:100]
            grouped_equipments = [equipments]
        values.update({
            'date': date_begin,
            'date_end': date_end,
            'equipments': equipments,
            'grouped_equipments': grouped_equipments,
            'page_name': 'equipment',
            'archive_groups': archive_groups,
            'searchbar_filters': searchbar_filters,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'filterby': filterby,
            'groupby': groupby,
            'default_url': '/my/equipments',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        return request.render("wepelo_equipment.portal_my_equipments", values)

    @http.route(['/my/equipment/<int:equipment_id>'], type='http', auth="public", website=True)
    def portal_my_equipment(self, equipment_id, access_token=None, **kw):
        try:
            equipment_sudo = self._document_check_access('maintenance.equipment', equipment_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        equipment_protocols = request.env['equipment.protocol'].search([('equipment_id', '=', equipment_id)])
        res_model_id = request.env['ir.model'].sudo().search([('model', '=', 'maintenance.equipment')], limit=1).id
        if equipment_sudo.equipment_service_id:
            domain = [('equipment_test_type_id', 'in', equipment_sudo.equipment_service_id.test_equipment_ids.ids)]
        else:
            domain = ['|', ('res_model_id', '=', False), ('res_model_id', '=', res_model_id)]
        activity_type_ids = request.env['mail.activity.type'].sudo().search(domain)
        user_ids = request.env['res.users'].sudo().search([('user_id', '=', request.uid)], limit=1)
        values = self._equipment_get_page_view_values(equipment_sudo, access_token, **kw)
        if equipment_protocols:
            values.update({'equipment_protocols': equipment_protocols})
        if activity_type_ids:
            values.update({'activity_type_ids': activity_type_ids})
        if user_ids:
            values.update({'user_id': request.uid,
                           'user_ids': user_ids})
        values.update({'user_ids': request.env['res.users'].sudo().search([])})
        name = equipment_sudo.serial_no + '_' + str(fields.Datetime.now().date().strftime('%d/%m/%y'))
        values.update({'equipment_ids': equipment_sudo,'date_today': str(fields.Datetime.now().date()), 'name': name})
        return request.render("wepelo_equipment.portal_my_equipment", values)

    # ------------------------------------------------------------
    # My Protocol
    # ------------------------------------------------------------

    def _protocol_get_page_view_values(self, protocol, access_token, **kwargs):
        values = {
            'page_name': 'protocol',
            'protocol': protocol,
            'user': request.env.user
        }
        return self._get_page_view_values(protocol, access_token, values, 'my_equipments_history', False, **kwargs)

    @http.route(['/my/protocols', '/my/protocols/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_protocols(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', groupby='none', global_search=False, **kw):
        values = self.prepare_portal_values(global_search)
        Protocol = request.env['equipment.protocol']
        protocol_domain = [('equipment_id', 'in', values['equipments'].ids)]
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Equipment Name'), 'order': 'name'},
            'update': {'label': _('Last Update'), 'order': 'write_date desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': protocol_domain},
            'with_guarantee': {'label': _('With guarantee'),
                               'domain': protocol_domain + [('x_garantie', '!=', False)]},
            'without_guarantee': {'label': _('Without guarantee'),
                                  'domain': protocol_domain + [('x_garantie', '=', False)]},
        }
        searchbar_inputs = {
            'serial_no': {'input': 'serial_no', 'label': _('Search in Serial Number')},
            'equipment': {'input': 'equipment', 'label': _('Search <span class="nolabel"> (in Equipment Name)</span>')},
            'customer_name': {'input': 'customer_name', 'label': _('Search in Customer Name')},
            'customer_ref': {'input': 'customer_ref', 'label': _('Search in Customer Ref')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'equipment': {'input': 'equipment', 'label': _('Equipment')},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain = searchbar_filters[filterby]['domain']
        if global_search:
            customer_ids = request.env['res.partner'].sudo().search(['|', ('name', 'ilike', global_search),
                                                                     ('ref', 'ilike', global_search)])
            domain += ['|', '|', ('equipment_id.name', 'ilike', global_search),
                       ('equipment_id.serial_no', 'ilike', global_search),
                       ('customer_id', 'in', customer_ids.ids)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('serial_no', 'all'):
                search_domain = OR([search_domain, [('serial_no', 'ilike', search)]])
            if search_in in ('equipment', 'all'):
                search_domain = OR([search_domain, [('equipment_id.name', 'ilike', search)]])
            if search_in in ('customer_name', 'customer_ref', 'all'):
                customer_ids = request.env['res.partner'].sudo().search(['|', ('name', 'ilike', search),
                                                                         ('ref', 'ilike', search)])
                search_domain = OR([search_domain, [('customer_id', 'in', customer_ids.ids)]])
            domain += search_domain

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('equipment.protocol', domain)
        # domain += [('technician_user_id', '=', request.uid)]
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # protocols count
        protocol_count = Protocol.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/protocols",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=protocol_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        if groupby == 'equipment':
            order = "equipment_id, %s" % order  # force sort on project first to group by project in view
            protocols = Protocol.search(domain, order=order, limit=self._items_per_page, offset=(page - 1) * self._items_per_page)
            request.session['grouped_protocols'] = protocols.ids[:100]
            if groupby == 'equipment':
                grouped_protocols = [Protocol.concat(*g) for k, g in groupbyelem(protocols, itemgetter('equipment_id'))]
            else:
                grouped_protocols = [protocols]
        else:
            protocols = Protocol.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
            request.session['grouped_protocols'] = protocols.ids[:100]
            grouped_protocols = [protocols]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'protocols': protocols,
            'page_name': 'protocol',
            'grouped_protocols': grouped_protocols,
            'archive_groups': archive_groups,
            'searchbar_filters': searchbar_filters,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'filterby': filterby,
            'groupby': groupby,
            'default_url': '/my/protocols',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        return request.render("wepelo_equipment.portal_my_protocols", values)

    @http.route(['/my/protocol/<int:protocol_id>'], type='http', auth="public", website=True)
    def portal_my_protocol(self, protocol_id, access_token=None, **kw):
        try:
            protocol_sudo = self._document_check_access('equipment.protocol', protocol_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._protocol_get_page_view_values(protocol_sudo, access_token, **kw)
        return request.render("wepelo_equipment.portal_my_protocol", values)

    @http.route(['/my/schedule_new_activity'], methods=['POST'], csrf=False, auth="user", website=True)
    def schedule_new_activity(self, **kw):
        values = kw.copy()
        try:
            for key, value in kw.items():
                if value in ('False', ''):
                    values[key] = False
                if key.startswith('csrf_token'):
                    values.pop(key)
            res_model_id = request.env['ir.model'].sudo().search([('model', '=', 'maintenance.equipment')], limit=1).id
            values.update({'res_model_id': res_model_id})
            request.env['mail.activity'].create(values)
        except (AccessError, MissingError):
            return json.dumps([{'error': 'There is a problem scheduling the activity'}])
        return json.dumps([{'success': 'The activity has been successfully scheduled'}])

    @http.route(['/my/schedule_dates'], methods=['GET'], csrf=False, auth="user", website=True)
    def schedule_dates(self, **kw):
        """Get list of schedule activities dates to display it in calendar."""
        values = []
        partner_object = request.env['res.partner'].sudo()
        partner_domain = []
        date_format = DEFAULT_SERVER_DATETIME_FORMAT
        partner = partner_object.search([('user_ids', 'in', [request.uid])], limit=1)
        parents_partner = partner_object.search([('parent_id', '=', partner.id)])
        owners = parents_partner
        for parent in parents_partner:
            childs = partner_object.search([('parent_id', '=', parent.id)])
            while childs:
                owners += childs
                childs = partner_object.search([('parent_id', 'in', childs.ids)])
        if partner:
            partner_domain = ['|', '|','|', '|', ('equipment_id.customer_id', '=', partner.id),
                              ('equipment_id.owner_user_id', '=', request.uid),
                              ('equipment_id.owner_user_id', 'in', owners.mapped('user_ids').ids),
                              ('equipment_id.manufacturer_id', '=', partner.id),
                              ('equipment_id.partner_id', '=', partner.id)]
        user_domain = OR([['|', ('equipment_id.technician_user_id', '=', request.uid), ('user_id', '=', request.uid)], partner_domain])
        maintenance_user_domain = OR([[('equipment_id.technician_user_id', '=', request.uid)], partner_domain])
        maintenances = request.env['maintenance.request'].sudo().search([('schedule_date', '!=', False)] + maintenance_user_domain)
        try:
            activity_ids = request.env['mail.activity'].search([('planning', '=', 'detail_plan'), ('schedule_date', '!=', False), ('active', '=', True)] + user_domain)
            activity_maintenance_ids = request.env['mail.activity'].search([('active', '=', True), ("res_model", "=", "maintenance.request"), ("res_id", "in", maintenances.ids)])
            all_activities = activity_ids + activity_maintenance_ids
            name = ""
            for activity_id in all_activities:
                activity_type = _("Activity type : ") + activity_id.activity_type_id.sudo().name if activity_id.activity_type_id else ""
                if activity_id.res_model != "maintenance.request":
                    equipment = _("Equipment : ") + str(activity_id.equipment_id.name)
                    created_on = _("Created on : ") + str(
                        activity_id.create_date.date()) if activity_id.create_date else ""
                    created_by = _("Created By : ") + activity_id.create_uid.sudo().name if activity_id.create_uid else ""
                    schedule_date = str(activity_id.schedule_date)
                else:
                    maintenance = request.env['maintenance.request'].sudo().browse(activity_id.res_id)
                    equipment = _("Equipment : ") + str(maintenance.equipment_id.name) if maintenance.equipment_id else ""
                    name = _("Maintenance Name : ") + maintenance.name if maintenance.name else ""
                    created_on = _("Created on : " )+ str(
                        maintenance.create_date.date()) if maintenance.create_date else ""
                    created_by = _("Created By : ") + maintenance.create_uid.sudo().name if maintenance.create_uid else ""
                    schedule_date = str(maintenance.schedule_date)
                customer = _("Customer : ") + str(activity_id.sudo().customer_id.name) if activity_id.customer_id else ""
                assigned_to = _("Assigned to : ") + activity_id.sudo().user_id.sudo().name if activity_id.user_id else ""
                due_on = _("Due on : ") + str(activity_id.date_deadline) if activity_id.date_deadline else ""
                summary = activity_type
                if name:
                    summary = summary + "<br/>" + name
                summary = summary + "<br/>" + equipment + "<br/>" + created_on + "<br/>" + created_by + "<br/>" + assigned_to + "<br/>" + due_on
                if customer:
                    summary = summary + "<br/>" + customer
                local = pytz.timezone(request._context.get("tz"))
                schedule_date = datetime.strptime(schedule_date, "%Y-%m-%d %H:%M:%S")
                schedule_date = schedule_date.astimezone(local)
                schedule_date = schedule_date.strftime(date_format)
                schedule_date = datetime.strptime(str(schedule_date), "%Y-%m-%d %H:%M:%S")
                values.append({'date_deadline': str(schedule_date), 'summary': summary})
        except (AccessError, MissingError):
            return json.dumps([{'error': 'There is a problem in get of scheduled dates'}])
        return json.dumps([{'success': values, 'months':  [_('January'), _('February'), _('March'), _('April'), _('May'), _('June'), _('July'), _('August'), _('September'), _('October'), _('November'), _('December')]}])

    @http.route('/protocol/report/<int:protocol_id>', csrf=False, type='http', auth="user", website=True)
    def print_protocol_report(self, protocol_id, **kw):
        """Get report of protocol by type."""
        if kw['type'] == 'maintenance':
            pdf = request.env.ref('wepelo_equipment.wepelo_equipment_protocol_maintenance').sudo().render_qweb_pdf([protocol_id])[0]
        elif kw['type'] == 'prot':
            pdf = request.env.ref('wepelo_equipment.wepelo_equipment_protocol_rep_prot').sudo().render_qweb_pdf([protocol_id])[0]
        elif kw['type'] == 'protocol':
            pdf = request.env.ref('wepelo_equipment.wepelo_equipment_protocol').sudo().render_qweb_pdf([protocol_id])[0]
        elif kw['type'] == 'calibration':
            pdf = request.env.ref('wepelo_equipment.wepelo_equipment_eichnachweis_protocol').sudo().render_qweb_pdf([protocol_id])[0]
        elif kw['type'] == 'uvv_hebebuhne':
            pdf = request.env.ref('wepelo_equipment.wepelo_equipment_hebebuhne_protocol').sudo().render_qweb_pdf([protocol_id])[0]
        elif kw['type'] == 'uvv_tore':
            pdf = request.env.ref('wepelo_equipment.wepelo_equipment_tore_protocol').sudo().render_qweb_pdf([protocol_id])[0]
        elif kw['type'] == 'routine_test':
            pdf = request.env.ref('wepelo_equipment.wepelo_equipment_bremsprufstand_protocol').sudo().render_qweb_pdf([protocol_id])[0]
        protocol = request.env['equipment.protocol'].browse(int(protocol_id))
        filename = ''
        if protocol:
            protocol.downloaded_user_ids = [(4, request._uid)]
            order_date = protocol.order_date.strftime('%y_%m_%d') if protocol.order_date else ''
            serial_no = protocol.equipment_id.serial_no if protocol.equipment_id else ''
            activity_type_name = protocol.equipment_id.activity_type_id.sudo().name if protocol.equipment_id.activity_type_id else ''
            filename = order_date+''+serial_no+''+activity_type_name+'.pdf'
        pdfhttpheaders = [('Content-Type', 'application/pdf'),
                          ('Content-Length', len(pdf)),
                          ('Content-Disposition', 'attachment;filename='+filename)]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/my/create_maintenance_request'], methods=['POST'], csrf=False, auth="user", website=True)
    def create_maintenance_request(self, **kw):
        values = kw.copy()
        try:
            for key, value in kw.items():
                if value in ('False', ''):
                    values[key] = False
                if key.startswith('equipment_id'):
                    values[key] = int(values[key])
                if key.startswith('category_id'):
                    values[key] = int(values[key])
                if key.startswith('user_id'):
                    values[key] = int(values[key])
                if key.startswith('x_garantie'):
                    if values[key] == 'on':
                        values[key] = True
                    else:
                        values[key] = False
                if key.startswith('csrf_token'):
                    values.pop(key)
            request.env['maintenance.request'].sudo().create(values)
        except (AccessError, MissingError):
            return json.dumps([{'error': 'There is a problem on create maintenance request'}])
        return json.dumps([{'success': 'The maintenance rqeuest has been successfully create'}])

    @http.route('/my/protocols/report', type='http', auth="user", website=True, csrf=False)
    def print_report_protocol(self, **kw):
        """Print protocol reports."""
        protocols = kw.get('protocols', False)
        if protocols:
            if ',' not in protocols:
                protocols = [int(protocols)]
            else:
                protocols = ast.literal_eval(protocols)
            protocols = request.env["equipment.protocol"].search([('id', 'in', protocols)])
            pdf = False
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as archive:
                for protocol in protocols:
                    if protocol.equipment_test_type == 'el_test' and protocol.mail_activity_id:
                        pdf = request.env.ref('wepelo_equipment.wepelo_equipment_protocol').sudo().render_qweb_pdf([protocol.id])[0]
                    elif protocol.maintenance_request_id:
                        pdf = request.env.ref('wepelo_equipment.wepelo_equipment_protocol_rep_prot').sudo().render_qweb_pdf([protocol.id])[0]
                    elif protocol.equipment_test_type == 'maintenance' and protocol.mail_activity_id:
                        pdf = request.env.ref('wepelo_equipment.wepelo_equipment_protocol_maintenance').sudo().render_qweb_pdf([protocol.id])[0]
                    elif protocol.equipment_test_type == 'calibration_ei' and protocol.mail_activity_id:
                        pdf = request.env.ref('wepelo_equipment.wepelo_equipment_eichnachweis_protocol').sudo().render_qweb_pdf([protocol.id])[0]
                    elif protocol.equipment_test_type == 'uvv' and protocol.category_id == request.env.ref("wepelo_equipment.equipment_hebebuhne"):
                        pdf = request.env.ref('wepelo_equipment.wepelo_equipment_hebebuhne_protocol').sudo().render_qweb_pdf([protocol.id])[0]
                    elif protocol.equipment_test_type == 'uvv' and protocol.category_id  == request.env.ref("wepelo_equipment.equipment_tore"):
                        pdf = request.env.ref('wepelo_equipment.wepelo_equipment_tore_protocol').sudo().render_qweb_pdf([protocol.id])[0]
                    elif protocol.equipment_test_type == 'routine_test' and protocol.category_id == request.env.ref("wepelo_equipment.equipment_bremsprufstand"):
                        pdf = request.env.ref('wepelo_equipment.wepelo_equipment_bremsprufstand_protocol').sudo().render_qweb_pdf([protocol.id])[0]
                    if pdf:
                        if protocol:
                            protocol.downloaded_user_ids = [(4, request._uid)]
                            name = protocol.order_date.strftime('%y_%m_%d') if protocol.order_date else ''
                            if protocol.equipment_id.serial_no:
                                serial_number = protocol.equipment_id.serial_no.replace('/', '\N{FULLWIDTH SOLIDUS}')
                                name += '_' + serial_number
                            if protocol.equipment_id.activity_type_id.sudo().name:
                                name += '_' + protocol.equipment_id.activity_type_id.sudo().name
                            filename = name + '.pdf'
                            archive.writestr(filename, pdf, compress_type=zipfile.ZIP_DEFLATED)
            content = stream.getvalue()
            name = 'protocols.zip'
            headers = [
                ('Content-Type', 'zip'),
                ('X-Content-Type-Options', 'nosniff'),
                ('Content-Length', len(content)),
                ('Content-Disposition', content_disposition(name))
            ]
            return request.make_response(content, headers)
        else:
            pass