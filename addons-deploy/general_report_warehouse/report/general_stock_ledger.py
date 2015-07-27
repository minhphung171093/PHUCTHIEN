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

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.start_date = False
        self.end_date = False
        self.company_name = False
        self.company_address = False
        self.warehouse = False
        self.warehouse_id = False
        self.product_id = False
        self.product = False
        self.product_code = False
        
        self.vat = False
        self.get_company(cr, uid)
        self.localcontext.update({
            'get_vietname_date':self.get_vietname_date, 
            'get_line':self.get_line,
            'get_header':self.get_header,
            'get_start_date':self.get_start_date,
            'get_end_date':self.get_end_date,
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_company_vat':self.get_company_vat,
            'get_warehouse':self.get_warehouse,
            'get_current_time':self.get_current_time,
            'get_product':self.get_product,
            'get_product_code':self.get_product_code,
        })
    
    def get_company(self,cr,uid):
         user_obj = self.pool.get('res.users').browse(cr,uid,uid)
         self.company_name = user_obj and user_obj.company_id and user_obj.company_id.name or ''
         self.company_address = user_obj and user_obj.company_id and user_obj.company_id.street or ''
         self.vat = user_obj and user_obj.company_id and user_obj.company_id.vat or ''
         
    def get_company_name(self):
        return self.company_name
    
    def get_current_time(self):
        date = time.strftime(DATETIME_FORMAT)
        date = datetime.strptime(date, DATETIME_FORMAT)        
        return date.strftime('%d-%m-%Y %H:%M:%S')
    
    def get_company_address(self):
        return self.company_address     
    
    def get_company_vat(self):
        return self.vat    
        
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.start_date = wizard_data['date_start']
        self.end_date = wizard_data['date_end']
        self.warehouse = wizard_data['warehouse_id'][1] or ''
        self.warehouse_id  = wizard_data['warehouse_id'][0] or ''
        self.product_id = wizard_data['product_id'][0] or ''
        self.product = wizard_data['product_id'][1] or ''
        product_obj =  self.pool.get('product.product').browse(self.cr,self.uid,self.product_id)
        self.product_code = product_obj and product_obj.default_code or''
    
    def get_warehouse(self):
        return self.warehouse
    
    def get_product(self):
        return self.product
    
    def get_product_code(self):
        return self.product_code 
            
    def get_start_date(self):
        self.get_header()
        return self.get_vietname_date(self.start_date) 
    
    def get_end_date(self):
        return self.get_vietname_date(self.end_date) 
       
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
        
    def get_line(self):
        wizard_data = self.localcontext['data']['form']
        res =[]
        sql = '''
        SELECT * FROM fn_cash_book_report(%s,'%s','%s')
        ''' %(self.account_id,self.start_date,self.end_date)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            bal_amount = line['bal_amount'] and line['bal_amount'] or ''
            description = line['description'] and line['description'] or ''
            if lang=='e' and line['bold_flag'] == True:
                description = line['translate_des'] and line['translate_des'] or '',
                
            if line['bold_flag'] == True:
                bal_amount = line['bal_amount'] and line['bal_amount'] or 0
            
            pay_num =  line['pay_num'] or line['rec_num'] or ''
                
            res.append({
                 'gl_date':line['gl_date'] and self.get_vietname_date(line['gl_date']) or '',
                 'document_date':line['document_date'] and self.get_vietname_date(line['document_date']) or '',
                 'rec_num':pay_num,
                 'description':description,
                 'pay_amount':line['pay_amount'] and line['pay_amount'] or '',
                 'rec_amount':line['rec_amount'] and line['rec_amount'] or '',
                 'bal_amount':bal_amount,
                 'bold_flag':line['bold_flag'] and line['bold_flag'] or False
                 })
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
