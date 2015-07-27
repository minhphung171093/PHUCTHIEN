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
        self.warehouse_id =False
        self.warehouse_name =False
        self.category_id = False
        self.category_name = False
        
        self.product_id = False
        self.start_date = False
        self.date_end = False
        self.short_by = False
        self.blanket_id = False
        self.blanket_name = False
        self.company_name = False
        self.company_address = False
        self.total_td = 0
        self.total_rcv = 0
        self.total_iss = 0
        self.total_end = 0
        self.get_company(cr, uid)
        
        self.localcontext.update({
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_line_by_category_type':self.get_line_by_category_type, 
            'get_date_start':self.get_date_start,
            'get_date_end':self.get_date_end,
            'get_line_by_category':self.get_line_by_category,
            'get_total_td':self.get_total_td,
            'get_total_iss':self.get_total_iss,
            'get_total_rcv':self.get_total_rcv,
            'get_total_end':self.get_total_end,
            'get_line_by_warehouse_type':self.get_line_by_warehouse_type,
            'get_line_by_warehouse':self.get_line_by_warehouse,
            'get_line_by_product':self.get_line_by_product,
            
            'get_warehouse_name':self.get_warehouse_name,
            'get_category_name':self.get_category_name,
            'get_blanket_name':self.get_blanket_name,
            
            
        })
        
    def get_total_td(self):
        return self.total_td
    def get_total_iss(self):
        return self.total_rcv
    def get_total_rcv(self):
        return self.total_rcv
    def get_total_end(self):
        return self.total_end
    
    def get_company(self,cr,uid):
         user_obj = self.pool.get('res.users').browse(cr,uid,uid)
         self.company_name = user_obj and user_obj.company_id and user_obj.company_id.name or ''
         self.company_address = user_obj and user_obj.company_id and user_obj.company_id.street or ''
         self.vat = user_obj and user_obj.company_id and user_obj.company_id.vat or ''
         
    def get_company_name(self):
        return self.company_name
    def get_company_address(self):
        return self.company_address 
    
    def get_date_start(self):
        if not self.start_date:
            self.get_header()
        return self.get_vietname_date(self.start_date)
    
    def get_date_end(self):
        if not self.date_end:
            self.get_header()
        return self.get_vietname_date(self.date_end)
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_warehouse_name(self):
        if not self.warehouse_name:
            self.get_header()
        return self.warehouse_name 
    
    
    def get_category_name(self):
        return self.category_name 
    
    def get_blanket_name(self):
        return self.blanket_name
    
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        
        self.warehouse_id = wizard_data['warehouse_id'] and wizard_data['warehouse_id'][0] or 'null'
        self.warehouse_name = wizard_data['warehouse_id'] and wizard_data['warehouse_id'][1] or  'All Warehouse'
        
        self.category_id = wizard_data['categ_id'] and wizard_data['categ_id'][0] or 265
        self.category_name = wizard_data['categ_id'] and wizard_data['categ_id'][1] or 'All Category'
        
        self.product_id = wizard_data['product_id'] and wizard_data['product_id'][0] or 'null'
        
        self.blanket_id = wizard_data['blanket_id'] and wizard_data['blanket_id'][0] or 'null'
        self.blanket_name = wizard_data['blanket_id'] and wizard_data['blanket_id'][1] or 'All Blanket'
        
        self.short_by = wizard_data['short_by'] and wizard_data['short_by'] or False
        
        self.start_date = wizard_data['date_start']
        self.date_end = wizard_data['date_end']
        return True
    
    def get_line_by_product(self):
        self.get_total_value()
        sql ='''   
           select * from stock_balancesheet_report(%s,'%s', '%s', %s, %s, %s, %s)
        ''' %(self.short_by,self.start_date,self.date_end,self.warehouse_id,self.category_id,self.product_id,self.blanket_id)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_line_by_warehouse_type(self):
        self.get_total_value()
        sql ='''                
        SELECT warehouse_name || '-' || location_name  warehouse_name,  sum(sbal_value) td_vl,sum(rcv_value) rcv_vl ,sum(iss_value) iss_vl,
         sum(ebal_value) e_vl
            FROM stock_balancesheet_report(%s,'%s', '%s', %s, %s, %s, %s) 
            GROUP BY (warehouse_name || '-' || location_name)
            ORDER BY (warehouse_name || '-' || location_name)
        ''' %(self.short_by,self.start_date,self.date_end,self.warehouse_id,self.category_id,self.product_id,self.blanket_id)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    
    def get_line_by_warehouse(self,warehouse_name):
        sql ='''   
           select * from stock_balancesheet_report(%s,'%s', '%s', %s, %s, %s, %s) 
           WHERE (warehouse_name || '-' || location_name) = '%s'
        ''' %(self.short_by,self.start_date,self.date_end,self.warehouse_id,self.category_id,self.product_id,self.blanket_id,warehouse_name)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_line_by_category_type(self):
        sql = '''
        SELECT categ, sum(end_cost) bq_vl, sum(sbal_value) td_vl,sum(rcv_value) rcv_vl ,sum(iss_value) iss_vl, sum(ebal_value) e_vl
            FROM stock_balancesheet_report(%s,'%s', '%s', %s, %s, %s, %s) 
            GROUP BY categ
            ORDER BY categ
        ''' %(self.short_by,self.start_date,self.date_end,self.warehouse_id,self.category_id,self.product_id,self.blanket_id)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_line_by_category(self,categ):
        self.get_total_value()
        sql = '''
        select * from stock_balancesheet_report(%s,'%s', '%s', %s, %s, %s, %s) where categ = '%s'
        ''' %(self.short_by,self.start_date,self.date_end,self.warehouse_id,self.category_id,self.product_id,self.blanket_id,categ)
        self.cr.execute(sql)
        
        return self.cr.dictfetchall()
    
    
    def get_total_value(self):
        sql = '''
            SELECT sum(end_cost) bq_vl, sum(sbal_value) td_vl,sum(rcv_value) rcv_vl ,sum(iss_value) iss_vl, sum(ebal_value) e_vl
            FROM stock_balancesheet_report(%s,'%s', '%s', %s, %s, %s, %s) 
        ''' %(self.short_by,self.start_date,self.date_end,self.warehouse_id,self.category_id,self.product_id,self.blanket_id)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            self.total_td = line['td_vl']
            self.total_rcv = line['rcv_vl']
            self.total_iss = line['iss_vl']
            self.total_end = line['e_vl']
        return True
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
