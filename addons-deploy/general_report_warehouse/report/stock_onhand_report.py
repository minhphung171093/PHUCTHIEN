# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

import time
from report import report_sxw
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.user_obj = pooler.get_pool(self.cr.dbname).get('res.users')
        self.cr = cr
        self.uid = uid
        self.company_name = False
        self.company_address = False
        self.warehouse_name = False
        self.categ_name = False
        
        self.group_by = False
        
        self.date_get  = False
        self.warehouse_id = 0.0
        
        self.categ_id = 0.0
        
        self.product_id = 0.0
        self.blanket_id = 0.0
        
        self.onhand_qty_from = False
        self.onhand_qty_to = False
        
        self.get_company(cr, uid)
        
        self.localcontext.update({
            'get_line':self.get_line,
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_warehouse':self.get_warehouse,
            'get_categ_name':self.get_categ_name,
            'get_group_by':self.get_group_by,
            'get_date_get':self.get_date_get,
            'get_current':self.get_current,
        })
    
    def get_warehouse(self):
        self.get_header()
        if self.warehouse_name:
            return self.warehouse_name
        else:
            return 'All Warehouse'
    
    def get_categ_name(self):
        self.get_header()
        if self.categ_name and self.categ_name != 'Null':
            return self.categ_name
        else:
            return 'All Category'
    
    def get_group_by(self):
        if self.group_by and self.group_by == 1:
            return 'Group By Warehouse'
        else:
            return 'Group All'
    
    def get_date_get(self):
        self.get_header()
        return self.get_vietname_date(self.date_get)
    
    def get_current(self):
        return self.get_vietname_date(False)
            
        
    def get_company(self,cr,uid):
         user_obj = self.pool.get('res.users').browse(cr,uid,uid)
         self.company_name = user_obj and user_obj.company_id and user_obj.company_id.name or ''
         self.company_address = user_obj and user_obj.company_id and user_obj.company_id.street or ''
         self.vat = user_obj and user_obj.company_id and user_obj.company_id.vat or ''
         
    def get_company_name(self):
        return self.company_name
    
    def get_company_address(self):
        return self.company_address     
    
    
    def get_header(self):
        res ={}
        
        wizard_data = self.localcontext['data']['form']
        
        if wizard_data['group_by'] == 2:
            self.group_by = 0
        else:
            self.group_by = wizard_data['group_by']
        self.date_get = wizard_data['date_get']
        
        self.warehouse_id = wizard_data['warehouse_id'] and wizard_data['warehouse_id'][0] or 'Null'
        self.warehouse_name = wizard_data['warehouse_id'] and wizard_data['warehouse_id'][1] or False
        
        self.categ_id = wizard_data['categ_id'] and wizard_data['categ_id'][0] or '265'
        self.categ_name = wizard_data['categ_id'] and wizard_data['categ_id'][1] or 'Null'
        
        self.product_id = wizard_data['product_id'] and wizard_data['product_id'][0] or 'Null'
        self.blanket_id = wizard_data['blanket_id'] and wizard_data['blanket_id'][0] or 'Null'
        
        self.onhand_qty_from = wizard_data['onhand_qty_from'] or 'Null'
        self.onhand_qty_to = wizard_data['onhand_qty_to'] or 'Null'
        
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        strng = date.strftime('%d %m %Y')
        return date.strftime('%d/%m/%Y')
        
                    
    def get_line(self):
        
        sql ='''
            SELECT *
            FROM stock_onhand_report(%s,'%s',%s,%s,%s,%s,%s,%s)
        ''' %(self.group_by,self.date_get,self.warehouse_id,self.categ_id,self.product_id,self.blanket_id,self.onhand_qty_from,self.onhand_qty_to)
        #stock_onhand_report(allgroup int, date_get date, warehouse int, categ int, product int, blanket int, from_qty numeric, to_qty numeric)
        self.cr.execute(sql)
        
        return self.cr.dictfetchall()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
