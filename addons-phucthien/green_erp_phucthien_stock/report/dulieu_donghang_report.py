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
            'get_loaithung':self.get_loaithung,
            
        })
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
            select spp.id , sp.name as so_phieuxuat, rp.name as ten_kh, ep.name_related as ten_nvdg, sp.ngay_gui, sp.ngay_nhan,
               sum(spp.sl_nhietke) as sl_nhietke, sum(spp.chi_phi_nhiet_ke) as chi_phi_nhiet_ke, sum(spp.chi_phi_gui_hang) as chi_phi_gui_hang, 
               sum(spp.sl_da) as sl_da, sum(spp.chi_phi_da) as chi_phi_da,sum(spp.chi_phi_thung) as chi_phi_thung
            from stock_picking_packaging spp
            left join stock_picking sp on sp.id = spp.picking_id
            left join loai_thung lt ON spp.loai_thung_id = lt.id
            left join res_partner rp ON sp.partner_id = rp.id
            left join hr_employee ep ON spp.employee_id = ep.id
            where sp.ngay_gui >= '%s' and (sp.ngay_nhan is null or sp.ngay_nhan <= '%s')
        ''' %(tu_ngay, den_ngay)
        if partner_id:
            sql+='''
                and rp.id = %s 
            '''%(partner_ids)
        if da_nhan:
            sql+='''
                and sp.ngay_nhan is not null
            '''
        if chua_nhan:
            sql+='''
                and sp.ngay_nhan is null
            '''    
        sql+='''
             group by spp.id, sp.name, rp.name, ep.name_related, sp.ngay_gui, sp.ngay_nhan
             order by sp.name
        '''
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            res.append({
                        'id': line['id'],
                        'so_phieuxuat': line['so_phieuxuat'],
                        'ten_kh':line['ten_kh'],
                        'ten_nvdg':line['ten_nvdg'],
                        'ngay_gui':self.get_vietname_date(line['ngay_gui']),
                        'ngay_nhan':self.get_vietname_date(line['ngay_nhan']),
                        'sl_nhietke':line['sl_nhietke'],
                        'chi_phi_nhiet_ke':line['chi_phi_nhiet_ke'],
                        'chi_phi_gui_hang': line['chi_phi_gui_hang'],
                        'sl_da': line['sl_da'],
                        'chi_phi_da':line['chi_phi_da'],
                        'chi_phi_thung':line['chi_phi_thung'],
                    })
        return res
    
    def get_loaithung(self,spp_id):
        result = []
        sql ='''
            SELECT  lt.name as loai_thung,spp.chi_phi_thung, spp.sl_thung,spp.sl_da, spp.chi_phi_da
            FROM stock_picking_packaging spp
            LEFT JOIN loai_thung lt ON spp.loai_thung_id = lt.id
            WHERE spp.id = %s
        ''' %(spp_id)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            result.append({
                        'loai_thung': line['loai_thung'],
                        'sl_thung': line['sl_thung'],
                        'chi_phi_thung': line['chi_phi_thung'],
                        'sl_da':line['sl_da'],
                        'chi_phi_da':line['chi_phi_da'],
                    })
        return result

