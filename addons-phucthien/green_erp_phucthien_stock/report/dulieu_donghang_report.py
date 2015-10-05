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
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class Parser(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_data':self.get_data,
            'get_date_from':self.get_date_from,
            'get_date_to':self.get_date_to,
            
        })
        
    def get_date_from(self):
        wizard_data = self.localcontext['data']['form']
        date = datetime.strptime(wizard_data['tu_ngay'], DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_date_to(self):
        wizard_data = self.localcontext['data']['form']
        date = datetime.strptime(wizard_data['den_ngay'], DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_vietname_date(self, date):
        if not date:
            return ''
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
         
    def get_data(self):
        res = []
        wizard_data = self.localcontext['data']['form']
        partner_id = wizard_data['partner_id']
        da_nhan = wizard_data['da_nhan']
        chua_nhan = wizard_data['chua_nhan']
        tu_ngay = wizard_data['tu_ngay']
        den_ngay = wizard_data['den_ngay']
        sql ='''
            select sp.name as so_phieuxuat,sp.ngay_gui, rp.name as ten_kh,    
                sum(spp.sl_nhietke_conlai) as sl_nhietke_conlai,
                case when sp.ngay_nhan is not null then 'Da nhan' else 'Chua nhan' end as bb_giaonhan
            from stock_picking_packaging spp
            left join stock_picking sp on sp.id = spp.picking_id
            left join res_partner rp ON sp.partner_id = rp.id
            where sp.ngay_gui >= '%s' and (sp.ngay_nhan is null or sp.ngay_nhan <= '%s')
        ''' %(tu_ngay, den_ngay)
        if partner_id:
            sql+='''
                and rp.id = %s 
            '''%(partner_id[0])
        if da_nhan:
            sql+='''
                and sp.ngay_nhan is not null
            '''
        if chua_nhan:
            sql+='''
                and sp.ngay_nhan is null
            '''    
        sql+='''
             group by sp.name,sp.ngay_gui, rp.name,case when sp.ngay_nhan is not null then 'Da nhan' else 'Chua nhan' end
            order by sp.name
            '''
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            res.append({
                        'so_phieuxuat': line['so_phieuxuat'],
                        'ten_kh':line['ten_kh'],
                        'ngay_gui':self.get_vietname_date(line['ngay_gui']),
                        'sl_nhietke_conlai':line['sl_nhietke_conlai'],
                        'bb_giaonhan':line['bb_giaonhan'],
                    })
        return res
    
