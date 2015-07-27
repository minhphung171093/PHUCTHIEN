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

import tools
from osv import fields,osv

class pos_order_report(osv.osv):
    _name = "report.pos.order"
    _description = "Point of Sale Orders Statistics"
    _auto = False
    _columns = {
        'date': fields.date('Date Order', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', readonly=True),
        'product_id':fields.many2one('product.product', 'Product', readonly=True),
        'state': fields.selection([('draft', 'New'), ('paid', 'Closed'), ('done', 'Synchronized'), ('invoiced', 'Invoiced'), ('cancel', 'Cancelled')],
                                  'State'),
        'user_id':fields.many2one('res.users', 'Salesman', readonly=True),
        'price_total':fields.float('Total Price', readonly=True),
        'total_discount':fields.float('Total Discount', readonly=True),
        'average_price': fields.float('Average Price', readonly=True,group_operator="avg"),
        'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True),
        'company_id':fields.many2one('res.company', 'Company', readonly=True),
        'nbr':fields.integer('# of Lines', readonly=True),
        'product_qty':fields.integer('# of Qty', readonly=True),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'delay_validation': fields.integer('Delay Validation'),
    }
    _order = 'date desc'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_pos_order')
        cr.execute("""
            create or replace view report_pos_order as (
                select   
                    row_number() over()  id ,
                    count(*) as bill,
                    to_date(to_char(po.date_order, 'dd-MM-YYYY'),'dd-MM-YYYY') as date_order,    
                    sum(po.amount_total)    amount_total,    
                    to_char(po.date_order, 'YYYY') as year,
                    to_char(po.date_order, 'MM') as month,
                    to_char(po.date_order, 'YYYY-MM-DD') as day,
                    po.partner_id,
                    po.state,
                    po.user_id,
                    po.shop_id,
                    po.company_id,
                    po.sale_journal
                from pos_order   po
                group by
                    to_char(po.date_order, 'dd-MM-YYYY'),to_char(po.date_order, 'YYYY'),to_char(po.date_order, 'MM'),
                    to_char(po.date_order, 'YYYY-MM-DD'), po.partner_id,po.state,
                    po.user_id,po.shop_id,po.company_id,po.sale_journal
                    """)

pos_order_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
