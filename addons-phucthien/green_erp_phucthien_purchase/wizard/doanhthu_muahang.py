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
import time
from openerp.osv import osv,fields
from openerp.tools.translate import _


class doanhthu_muahang(osv.osv_memory):
    _name = 'doanhthu.muahang'
    
    _columns = {
        'partner_ids': fields.many2many('res.partner','doanhthumuahang_partner_ref','dtmh_id','partner_id', 'Nhà cung cấp'),
        'product_ids': fields.many2many('product.product','doanhthumuahang_product_ref','dtmh_id','product_id', 'Sản phẩm'),
        'categ_ids': fields.many2many('product.category','doanhthumuahang_categ_ref','dtmh_id','categ_id', 'Nhóm sản phẩm'),
        'loc_ids': fields.many2many('stock.location','doanhthumuahang_location_ref','dtmh_id','loc_id', 'Kho hàng'),
        'nsx_ids': fields.many2many('manufacturer.product','doanhthumuahang_manufacturer_product_ref','dtmh_id','nsx_id', 'Hãng sản xuất'),
        'account_ids': fields.many2many('account.account','doanhthumuahang_account_ref','dtmh_id','account_id', 'Tài khoản'),
        'date_from': fields.date('Từ ngày',required=True),
        'date_to': fields.date('Đến ngày',required=True),
        'amount_from': fields.float('Số tiền từ'),
        'amount_to': fields.float('Đến'),
        'hd_from': fields.char('Số hóa đơn từ'),
        'hd_to': fields.char('Đến'),
    }
    
    _defaults = {
        'date_from': time.strftime('%Y-%m-%d'),
        'date_to': time.strftime('%Y-%m-%d'),
    }
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'doanhthu.muahang'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['form'].update({'active_id':context.get('active_ids',False)})
        return {'type': 'ir.actions.report.xml', 'report_name': 'doanhthu_muahang_report', 'datas': datas}
    
doanhthu_muahang()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

