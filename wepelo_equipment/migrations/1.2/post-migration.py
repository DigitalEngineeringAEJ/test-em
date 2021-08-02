# -*- coding: utf-8 -*-
from odoo.api import Environment


def migrate(cr, version):
    """Update category equipment."""
    env = Environment(cr, 1, context={})
    category = env["maintenance.equipment.category"].search([("name", "=", "Tore"), ("id", "!=", env.ref("wepelo_equipment.equipment_tore").id)], limit=1)
    equipments = env["maintenance.equipment"].search([("category_id", "=", category.id)])
    for equipment in equipments:
        equipment.category_id = env.ref("wepelo_equipment.equipment_tore").id
    category.sudo().unlink()
