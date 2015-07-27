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
            'get_kho': self.get_kho,
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
        users_ids = wizard_data['users_ids']
        product_ids = wizard_data['product_ids']
        categ_ids = wizard_data['categ_ids']
        loc_ids = wizard_data['loc_ids']
        nsx_ids = wizard_data['nsx_ids']
        sql = '''
            select ail.id as id,ai.partner_id as partner_id,ai.date_invoice as ngay_hd,ai.reference_number as so_hd,rp.internal_code as ma_kh,rp.name as ten_kh,pp.default_code as ma_sp,
                pp.name_template as ten_sp,pu.name as dvt,spl.name as so_lo,spl.life_date as han_dung,ail.quantity as so_luong,ail.price_unit as gia_ban,
                ail.price_unit*ail.quantity as dt_truocthue,at.amount_tax as tien_thue,(ail.price_unit*ail.quantity)+at.amount_tax as dt_sauthue,pt.standard_price as gia_von,
                sl.name as loc_name,mp.name as nsx, rurp.name as nvbh
                from account_invoice_line ail
                    left join account_invoice ai on ail.invoice_id=ai.id
                    left join res_partner rp on ail.partner_id=rp.id
                    left join res_users ru on rp.user_id = ru.id
                    left join res_partner rurp on ru.partner_id=rurp.id
                    left join product_product pp on ail.product_id=pp.id
                    left join product_template pt on pp.product_tmpl_id=pt.id
                    left join product_category pc on pt.categ_id=pc.id
                    left join product_uom pu on ail.uos_id=pu.id
                    left join stock_production_lot spl on ail.prodlot_id = spl.id
                    left join (
                            select ail.id,sum(at.amount*ail.price_unit*ail.quantity) as amount_tax
                                from account_invoice_line ail
                                    left join account_invoice_line_tax ailt on ail.id=ailt.invoice_line_id
                                    left join account_tax at on ailt.tax_id=at.id
                                group by ail.id
                        ) as at on ail.id=at.id
                    left join stock_move sm on sm.id=ail.source_id
                    left join stock_location sl on sl.id=sm.location_id
                    left join manufacturer_product mp on pp.manufacturer_product_id = mp.id
                where ai.date_invoice between '%s' and '%s' and ai.state!='cancel' and ai.type='out_invoice' 
        '''%(date_from,date_to)
        if partner_ids:
            partner_ids = str(partner_ids).replace('[', '(')
            partner_ids = str(partner_ids).replace(']', ')')
            sql+='''
                and ai.partner_id in %s 
            '''%(partner_ids)
        if users_ids:
            users_ids = str(users_ids).replace('[', '(')
            users_ids = str(users_ids).replace(']', ')')
            sql+='''
                and rp.user_id in %s 
            '''%(users_ids)
        if product_ids:
            product_ids = str(product_ids).replace('[', '(')
            product_ids = str(product_ids).replace(']', ')')
            sql+='''
                and ail.product_id in %s 
            '''%(product_ids)
        if categ_ids:
            categ_ids = str(categ_ids).replace('[', '(')
            categ_ids = str(categ_ids).replace(']', ')')
            sql+='''
                and pc.id in %s 
            '''%(categ_ids)
        if loc_ids:
            loc_ids = str(loc_ids).replace('[', '(')
            loc_ids = str(loc_ids).replace(']', ')')
            sql+='''
                and sl.id in %s 
            '''%(loc_ids)
        if nsx_ids:
            nsx_ids = str(nsx_ids).replace('[', '(')
            nsx_ids = str(nsx_ids).replace(']', ')')
            sql+='''
                and mp.id in %s 
            '''%(nsx_ids)
        sql+='''
             order by ai.date_invoice
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
    
    def get_kho(self,invoice_line_id):
        sql = '''
            select sl.name 
                from stock_location sl
                    left join stock_move sm on sm.location_id = sl.id
                    left join account_invoice_line ail on sm.id=ail.source_id
                where ail.id=%s
        '''%(invoice_line_id)
        self.cr.execute(sql)
        name = self.cr.fetchone()
        return name and name[0] or ''
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

