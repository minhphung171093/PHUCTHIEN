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
        partner_id = wizard_data['partner_id'] and 'and dh.partner_id = '+ str(wizard_data['partner_id'][0]) or ''
        saleperson_id = wizard_data['saleperson_id'] and 'and dh.saleperson_id = '+ str(wizard_data['saleperson_id'][0]) or ''
        da_nhan = wizard_data['da_nhan']  and 'and dh.ngay_nhan is not null' or ''
        chua_nhan = wizard_data['chua_nhan']  and 'and dh.ngay_nhan is null' or ''
        tu_ngay = wizard_data['tu_ngay'] and 'and dh.ngay_gui >= '+"'"+ wizard_data['tu_ngay']+"'" or ''
        den_ngay = wizard_data['den_ngay'] and 'and dh.ngay_gui <= ' +"'"+ wizard_data['den_ngay']+"'"  or ''
        sql ='''
            SELECT dh.id, dh.name as so_phieu, sp.name as so_phieuxuat, rp.name as ten_kh, uid.name as ten_nvkd, dh.ngay_gui, dh.ngay_nhan,
                   dh.sl_nhietke, dh.chi_phi_nhiet_ke, dh.chi_phi_gui_hang, SUM(dhl.sl_da) as sl_da, SUM(dhl.chi_phi_da) as chi_phi_da
            FROM dulieu_donghang_line dhl
            LEFT JOIN loai_thung lt ON dhl.loai_thung_id = lt.id
            LEFT JOIN dulieu_donghang dh ON dhl.dulieu_donghang_id = dh.id
            INNER JOIN stock_picking sp ON dh.picking_id = sp.id
            INNER JOIN res_partner rp ON dh.partner_id = rp.id
            INNER JOIN res_users ru ON dh.saleperson_id = ru.id
            INNER JOIN res_partner uid ON ru.partner_id = uid.id
            WHERE 1=1 %s %s %s %s %s %s
            GROUP BY dh.id, dh.name, sp.name, rp.name, uid.name, dh.ngay_gui, dh.ngay_nhan,
                   dh.sl_nhietke, dh.chi_phi_nhiet_ke, dh.chi_phi_gui_hang
            ORDER BY dh.name
        ''' %(partner_id,saleperson_id,da_nhan,chua_nhan, tu_ngay, den_ngay)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            res.append({
                        'id': line['id'],
                        'so_phieu': line['so_phieu'],
                        'so_phieuxuat': line['so_phieuxuat'],
                        'ten_kh':line['ten_kh'],
                        'ten_nvkd':line['ten_nvkd'],
                        'ngay_gui':self.get_vietname_date(line['ngay_gui']),
                        'ngay_nhan':self.get_vietname_date(line['ngay_nhan']),
                        'sl_nhietke':line['sl_nhietke'],
                        'chi_phi_nhiet_ke':line['chi_phi_nhiet_ke'],
                        'chi_phi_gui_hang': line['chi_phi_gui_hang'],
                        'sl_da': line['sl_da'],
                        'chi_phi_da':line['chi_phi_da'],
                    })
        return res
    
    def get_loaithung(self,dh_id):
        result = []
        sql ='''
            SELECT  lt.name as loai_thung, dhl.sl_thung,dhl.sl_da, dhl.chi_phi_da
            FROM dulieu_donghang_line dhl
            LEFT JOIN dulieu_donghang dh ON dhl.dulieu_donghang_id = dh.id
            LEFT JOIN loai_thung lt ON dhl.loai_thung_id = lt.id
            WHERE dh.id = %s
        ''' %(dh_id)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            result.append({
                        'loai_thung': line['loai_thung'],
                        'sl_thung': line['sl_thung'],
                        'sl_da':line['sl_da'],
                        'chi_phi_da':line['chi_phi_da'],
                    })
        return result

