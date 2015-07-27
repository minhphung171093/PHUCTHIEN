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
from openerp.report import report_sxw
from openerp import pooler
from openerp.osv import osv
from openerp.tools.translate import _
import random
from datetime import date
from dateutil.rrule import rrule, DAILY

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.localcontext.update({
            'convert_date': self.convert_date,
            'get_date_from':self.get_date_from,
            'get_date_to':self.get_date_to,
            'get_lines': self.get_lines,
            'display_address': self.display_address,
        })
    def convert_date(self, date):
        if date:
            date = datetime.strptime(date, DATE_FORMAT)
            return date.strftime('%d/%m/%Y')
        
    def get_date_from(self):
        wizard_data = self.localcontext['data']['form']
        date = datetime.strptime(wizard_data['date_from'], DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_date_to(self):
        wizard_data = self.localcontext['data']['form']
        date = datetime.strptime(wizard_data['date_to'], DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_lines(self):
        wizard_data = self.localcontext['data']['form']
        date_from = wizard_data['date_from']
        date_to = wizard_data['date_to']
        partner_ids = wizard_data['partner_ids']
        product_ids = wizard_data['product_ids']
        categ_ids = wizard_data['categ_ids']
        nsx_ids = wizard_data['nsx_ids']
        sql = '''
            select dsct.partner_id as partner_id, rp.internal_code as ma_kh, rp.name as ten_kh,
                pp.default_code as ma_sp, pp.name_template as ten_sp, mp.name as nsx,pu.name as dvt,
                dsct.qty as so_luong, spct1.name as spct1, dsct.soluong_canhtranh1 as sl1,
                spct2.name as spct2, dsct.soluong_canhtranh2 as sl2,
                spct3.name as spct3, dsct.soluong_canhtranh3 as sl3
            from danhsach_canhtranh dsct
            left join res_partner rp on dsct.partner_id = rp.id
            left join product_product pp on dsct.product_id=pp.id
            left join product_template pt on pp.product_tmpl_id=pt.id
            left join product_category pc on pt.categ_id=pc.id
            left join product_uom pu on pt.uom_id=pu.id
            left join manufacturer_product mp on pp.manufacturer_product_id = mp.id
            left join sanpham_canhtranh spct1 on dsct.sanpham_canhtranh1_id = spct1.id
            left join sanpham_canhtranh spct2 on dsct.sanpham_canhtranh2_id = spct2.id
            left join sanpham_canhtranh spct3 on dsct.sanpham_canhtranh3_id = spct3.id
            where dsct.name between '%s' and '%s'
        '''%(date_from,date_to)
        if partner_ids:
            partner_ids = str(partner_ids).replace('[', '(')
            partner_ids = str(partner_ids).replace(']', ')')
            sql+='''
                and dsct.partner_id in %s 
            '''%(partner_ids)
        if product_ids:
            product_ids = str(product_ids).replace('[', '(')
            product_ids = str(product_ids).replace(']', ')')
            sql+='''
                and dsct.product_id in %s 
            '''%(product_ids)
        if categ_ids:
            categ_ids = str(categ_ids).replace('[', '(')
            categ_ids = str(categ_ids).replace(']', ')')
            sql+='''
                and pc.id in %s 
            '''%(categ_ids)
        if nsx_ids:
            nsx_ids = str(nsx_ids).replace('[', '(')
            nsx_ids = str(nsx_ids).replace(']', ')')
            sql+='''
                and mp.id in %s 
            '''%(nsx_ids)
        sql+='''
             order by dsct.name
        '''
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def display_address(self, partner_id):
        partner = self.pool.get('res.partner').browse(self.cr, self.uid, partner_id)
        address = partner.street and partner.street + ' , ' or ''
        address += partner.street2 and partner.street2 + ' , ' or ''
        address += partner.city and partner.city.name + ' , ' or ''
        if address:
            address = address[:-3]
        return address
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

