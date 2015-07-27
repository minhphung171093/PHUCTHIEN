# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import tools
from openerp.tools.sql import drop_view_if_exists

class stock_report_prodlots(osv.osv):
    _inherit = "stock.report.prodlots"
    _auto = False
    _columns = {
                }
    def init(self, cr):
        drop_view_if_exists(cr, 'stock_report_prodlots')
        cr.execute("""
            create or replace view stock_report_prodlots as (
                select max(id) as id,
                    location_id,
                    product_id,
                    prodlot_id,
                    sum(qty) as qty
                from (
                    select -max(sm.id) as id,
                        sm.location_id,
                        sm.product_id,
                        sm.prodlot_id,
                        -sum(sm.primary_qty) as qty
                    from stock_move as sm
                    left join stock_location sl
                        on (sl.id = sm.location_id)
                    where state = 'done'
                    group by sm.location_id, sm.product_id, sm.product_uom, sm.prodlot_id
                    union all
                    select max(sm.id) as id,
                        sm.location_dest_id as location_id,
                        sm.product_id,
                        sm.prodlot_id,
                        sum(sm.primary_qty) as qty
                    from stock_move as sm
                    left join stock_location sl
                        on (sl.id = sm.location_dest_id)
                    where sm.state = 'done'
                    group by sm.location_dest_id, sm.product_id, sm.product_uom, sm.prodlot_id
                ) as report
                group by location_id, product_id, prodlot_id
            )""")


stock_report_prodlots()

class stock_report_tracklots(osv.osv):
    _inherit = "stock.report.tracklots"
    _auto = False
    _columns = {
    }

    def init(self, cr):
        drop_view_if_exists(cr, 'stock_report_tracklots')
        cr.execute("""
           create or replace view stock_report_tracklots as (

            select max(id) as id,
                    location_id,
                    product_id,
                    tracking_id,
                    sum(qty) as name
                from (
                    select -max(sm.id) as id,
                        sm.location_id,
                        sm.product_id,
                        sm.tracking_id,
                        -sum(sm.primary_qty) as qty
                    from stock_move as sm
                    left join stock_location sl
                        on (sl.id = sm.location_id)
                    where state = 'done'
                    group by sm.location_id, sm.product_id, sm.product_uom, sm.tracking_id
                    union all
                    select max(sm.id) as id,
                        sm.location_dest_id as location_id,
                        sm.product_id,
                        sm.tracking_id,
                        sum(sm.primary_qty) as qty
                    from stock_move as sm
                    left join stock_location sl
                        on (sl.id = sm.location_dest_id)
                    where sm.state = 'done'
                    group by sm.location_dest_id, sm.product_id, sm.product_uom, sm.tracking_id
                ) as report
                group by location_id, product_id, tracking_id
            )""")


stock_report_tracklots()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
