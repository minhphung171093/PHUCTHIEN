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
        self.group= False
        self.product_categ_name= False
        self.product_categ_id = False
        self.partner_id = False
        self.partner_name = False
        
        self.total_open_val = False
        self.total_bal_in_val = False
        self.total_bal_out_val = False
        self.total_close_val =False
        
        self.vat = False
        self.get_company(cr, uid)
        self.localcontext.update({
            'get_vietname_date':self.get_vietname_date, 
            'get_line_category':self.get_line_category,
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
            'get_group':self.get_group_type,
            'get_supplier':self.get_supplier,
            'get_product_category':self.get_product_category,
            'get_data_warehouse':self.get_data_warehouse,
            'get_total_bal_in_val':self.get_total_bal_in_val,
            'get_total_bal_out_val':self.get_total_bal_out_val,
            'get_total_close_val':self.get_total_close_val,
            'get_total_open_val':self.get_total_open_val,
            'get_data_category_code':self.get_data_category_code,
            'get_line_category_code':self.get_line_category_code,
            'get_line_skus':self.get_line_skus,
            'get_sum_val_skus':self.get_sum_val_skus,
            'get_line_warehouse_code':self.get_line_warehouse_code,
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
    
    def get_group_type(self):
        res ={
              '_by_category':'Category',
              '_by_warehouse':'Warehouse',
              '_by_skus':'Product'
              }
        return  res[self.group]
    
    def get_product_category(self):
        return self.product_categ_name
    
    def get_supplier(self):
        return self.partner_name
        
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.start_date = wizard_data['date_start']
        self.end_date = wizard_data['date_end']
        
        self.group = wizard_data['group'] 
        if 'product_categ' in wizard_data and wizard_data['product_categ']:
            self.product_categ_id = wizard_data['warehouse_id'][0] or ''
            self.product_categ_name = wizard_data['warehouse_id'][1] or ''
        else:
            self.product_categ_id = 'null'
            self.product_categ_name = 'All'
        
        if 'partner_id' in wizard_data and wizard_data['partner_id']:
            self.partner_id = wizard_data['partner_id'][0] or ''
            self.partner_name = wizard_data['partner_id'][1] or ''
        else:
            self.partner_id = 'null'
            self.partner_name = 'All'
        
        if 'warehouse_id' in wizard_data and wizard_data['warehouse_id']:
            self.warehouse = wizard_data['warehouse_id'][1] or ''
            self.warehouse_id  = wizard_data['warehouse_id'][0] or ''
        else:
            self.warehouse = 'All Warehouse'
            self.warehouse_id  = 'null'
        product_obj =  self.pool.get('product.product').browse(self.cr,self.uid,self.product_id)
        
    
    def get_warehouse(self):
        #self.get_header()
        return self.warehouse
    
    def get_total_open_val(self):
        return self.total_open_val
    
    def get_total_bal_in_val(self):
        return self.total_bal_in_val
    
    def get_total_bal_out_val(self):
        return self.total_bal_out_val
    
    def get_total_close_val(self):
        return self.total_close_val
    
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
    
    def get_line_category_code(self,category_code):
        sql = '''
        SELECT * FROM fn_stock_report(%s,%s,%s,'%s','%s')  where category_code = '%s' order by product_code
        ''' %(self.warehouse_id,self.product_categ_id,self.partner_id,self.start_date,self.end_date,category_code)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_data_category_code(self):
        res = []
        sub_open_amt = 0
        sub_bal_out_amt = 0
        sub_bal_in_amt = 0
        sub_close_amt = 0
        
        self.total_open_val = 0
        self.total_bal_in_val = 0
        self.total_bal_out_val = 0
        self.total_close_val = 0
        
        sql_data = '''
            SELECT  category_code,category_code ||' - '||category_name name_category
            FROM 
                    fn_stock_report(%s,%s,%s,'%s','%s') 
            GROUP BY category_code,category_name
            ORDER BY category_code
        '''%(self.warehouse_id,self.product_categ_id,self.partner_id,self.start_date,self.end_date)
        self.cr.execute(sql_data)
        
        for line in self.cr.dictfetchall():
            sql = '''
                SELECT sum(open_amt) sub_open_amt, sum(bal_out_amt) sub_bal_out_amt,sum(bal_in_amt) sub_bal_in_amt,sum(close_amt) sub_close_amt
                    FROM fn_stock_report(%s,%s,%s,'%s','%s')  
                    WHERE category_code = '%s'
            ''' %(self.warehouse_id,self.product_categ_id,self.partner_id,self.start_date,self.end_date,line['category_code'])
            self.cr.execute(sql)
            data = self.cr.dictfetchone()
            if data:
                sub_open_amt = data['sub_open_amt'] or 0
                sub_bal_in_amt = data['sub_bal_in_amt'] or 0
                sub_bal_out_amt = data['sub_bal_out_amt'] or 0
                sub_close_amt = data['sub_close_amt'] or 0
                
                self.total_open_val = self.total_open_val + sub_open_amt
                self.total_bal_in_val = self.total_bal_in_val + sub_bal_in_amt
                self.total_bal_out_val = self.total_bal_out_val + sub_bal_out_amt
                self.total_close_val = self.total_close_val + sub_close_amt
            
            res.append({
                        'category_code':line['category_code'],
                        'name_category':line['name_category'],
                        'sub_open_amt':sub_open_amt,
                        'sub_bal_in_amt':sub_bal_in_amt,
                        'sub_bal_out_amt':sub_bal_out_amt,
                        'sub_close_amt':sub_close_amt
                        })
        return res
    
    def get_line_warehouse_code(self,location_name):
        sql = '''
        SELECT * FROM fn_stock_report(%s,%s,%s,'%s','%s')  where location_name = '%s' order by product_code
        ''' %(self.warehouse_id,self.product_categ_id,self.partner_id,self.start_date,self.end_date,location_name)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_data_warehouse(self):
        res = []
        sub_open_amt = 0
        sub_bal_out_amt = 0
        sub_bal_in_amt = 0
        sub_close_amt = 0
        
        self.total_bal_in_val = 0
        self.total_bal_out_val = 0
        self.total_close_val = 0
        
        sql_data = '''
            SELECT 
                 location_name, warehouse_code ||' - ' ||location_name as warehouse
            FROM fn_stock_report(%s,%s,%s,'%s','%s') 
            GROUP BY warehouse_code,location_name
            ORDER BY warehouse_code,location_name 
        '''%(self.warehouse_id,self.product_categ_id,self.partner_id,self.start_date,self.end_date)
        self.cr.execute(sql_data)
        
        for line in self.cr.dictfetchall():
            sql = '''
                SELECT sum(open_amt) sub_open_amt, sum(bal_out_amt) sub_bal_out_amt,sum(bal_in_amt) sub_bal_in_amt,sum(close_amt) sub_close_amt
                    FROM fn_stock_report(%s,%s,%s,'%s','%s')  
                    WHERE location_name = '%s'
            ''' %(self.warehouse_id,self.product_categ_id,self.partner_id,self.start_date,self.end_date,line['location_name'])
            self.cr.execute(sql)
            
            data = self.cr.dictfetchone()
            if data:
                sub_open_amt = data['sub_open_amt'] or 0
                sub_bal_in_amt = data['sub_bal_in_amt'] or 0
                sub_bal_out_amt = data['sub_bal_out_amt'] or 0
                sub_close_amt = data['sub_close_amt'] or 0
                
                self.total_open_val = self.total_open_val + sub_open_amt
                self.total_bal_in_val = self.total_bal_in_val + sub_bal_in_amt
                self.total_bal_out_val = self.total_bal_out_val + sub_bal_out_amt
                self.total_close_val = self.total_close_val + sub_close_amt
             
            res.append({
                     'location_name': line['location_name'],
                     'warehouse':line['warehouse'],
                     'sub_open_amt':sub_open_amt,
                     'sub_bal_in_amt':sub_bal_in_amt,
                     'sub_bal_out_amt':sub_bal_out_amt,
                     'sub_close_amt':sub_close_amt
                    })
        return res
    
    def get_line_category(self, location_name):
        sql = '''
        SELECT * FROM fn_stock_report(%s,%s,%s,'%s','%s')  where location_name = '%s' order by product_code
        ''' %(self.warehouse_id,self.product_categ_id,self.partner_id,self.start_date,self.end_date,location_name)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
        
    def get_line_skus(self):
        sql = '''
            SELECT * FROM fn_stock_report(%s,%s,%s,'%s','%s') order by product_code
        ''' %(self.warehouse_id,self.product_categ_id,self.partner_id,self.start_date,self.end_date)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_sum_val_skus(self):
        sql = '''
                SELECT sum(open_amt) sub_open_amt, sum(bal_out_amt) sub_bal_out_amt,sum(bal_in_amt) sub_bal_in_amt,sum(close_amt) sub_close_amt
                    FROM fn_stock_report(%s,%s,%s,'%s','%s') 
            ''' %(self.warehouse_id,self.product_categ_id,self.partner_id,self.start_date,self.end_date)
        self.cr.execute(sql)
        return self.cr.dictfetchone()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
