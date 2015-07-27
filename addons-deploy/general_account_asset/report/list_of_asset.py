# -*- coding: utf-8 -*-
##############################################################################
#
#    HLVSolution, Open Source Management Solution
#
##############################################################################

import time
from report import report_sxw
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import amount_to_text_vn
import amount_to_text_en

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.start_date = False
        self.end_date = False
        self.asset_type = False
        
        self.company_name = False
        self.company_address = False
        self.vat = False
        self.gross_value =  0.0
        self.value_of_month =  0.0
        
        self.localcontext.update({
            'get_vietname_date':self.get_vietname_date, 
            'get_header':self.get_header,
            'get_start_date':self.get_start_date,
            'get_end_date':self.get_end_date,
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_company_vat':self.get_company_vat,
            'get_line':self.get_line,
            'get_name_values':self.get_name_values,
            'get_gross_value':self.get_gross_value,
            'get_value_of_month':self.get_value_of_month,
            
        })
    
    def get_company(self, company_id):
        if company_id:
            company_obj = self.pool.get('res.company').browse(self.cr, self.uid, company_id)
            self.company_name = company_obj.name or ''
            self.company_address = company_obj.street or ''
            self.vat = company_obj.vat or ''
        return True
             
    def get_company_name(self):
        self.get_header()
        return self.company_name
    
    def get_company_address(self):
        return self.company_address     
    
    def get_company_vat(self):
        return self.vat
    
    def get_name_values(self):
        if self.asset_type == 'asset':
            return  u'DANH MỤC TÀI SẢN CỐ ĐỊNH'
        else:
            return u'DANH MỤC CÔNG CỤ DỤNG CỤ'
        
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        user_obj = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        self.get_company(user_obj.company_id.id or False)
        self.start_date = wizard_data['date_start']
        self.end_date = wizard_data['date_end']
        self.asset_type = wizard_data['asset_type']
    
    def get_start_date(self):
        return self.get_vietname_date(self.start_date) 
    
    def get_end_date(self):
        return self.get_vietname_date(self.end_date) 
    
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
        
    def get_line(self):
        res = self.pool.get('sql.list.of.asset').get_line(self.cr, self.start_date, self.end_date, self.asset_type)
        return res
    
    def get_gross_value(self):
        if not self.gross_value:
            self.get_sum_line()
        return self.gross_value
    
    def get_value_of_month(self):
        if not self.value_of_month:
            self.get_sum_line()
        return self.value_of_month
    
    def get_sum_line(self):
        res = self.pool.get('sql.list.of.asset').get_sum_line(self.cr, self.start_date, self.end_date, self.asset_type)
        for line in res:
            self.gross_value = line['gross_value'] or False
            self.value_of_month = line['value_of_month'] or False
    
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
