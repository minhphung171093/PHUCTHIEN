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
        self.get_company(cr, uid)
        self.lead_planned_revenue = 0.0
        self.opp_planned_revenue = 0.0
        self.total_order = 0.0
        self.localcontext.update({
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address, 
            'get_line':self.get_line,
            'get_vietname_date':self.get_vietname_date,
            'get_vietname_datetime':self.get_vietname_datetime,
        })
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)        
        return date.strftime('%d-%m-%Y')
    
    def get_vietname_datetime(self, date):
        if not date:
            date = time.strftime(DATETIME_FORMAT)
        date = datetime.strptime(date, DATETIME_FORMAT)        
        return date.strftime('%d-%m-%Y')
    
    def get_company(self,cr,uid):
         user_obj = self.pool.get('res.users').browse(cr,uid,uid)
         self.company_name = user_obj and user_obj.company_id and user_obj.company_id.name or ''
         self.company_address = user_obj and user_obj.company_id and user_obj.company_id.street or ''
         self.vat = user_obj and user_obj.company_id and user_obj.company_id.vat or ''
         
    def get_company_name(self):
        return self.company_name
    
    def get_company_address(self):
        return self.company_address    
                    
    def get_line(self,object):
        location_id = object.location_id.id
        inventory_id = object.id
        
        sql ='''
            SELECT pp.name_template product_name,pp.default_code,uom.name uom_name, ca.name category_name, sil.* 
            FROM stock_inventory_line sil 
            LEFT JOIN (product_template pt inner join product_product pp on pt.id = pp.product_tmpl_id inner join product_category ca on pt.categ_id = ca.id)
            ON  sil.product_id =  pp.id
            LEFT JOIN product_uom uom ON sil.product_uom = uom.id
            WHERE sil.inventory_id = %s
            Order By id
        ''' %(inventory_id)
        self.cr.execute(sql)
        res =[]
        for i in self.cr.dictfetchall():
#            sum_sys_value += i['sys_quantity'] * i['freeze_cost'],
#            sum_count_value += i['product_qty'] * i['freeze_cost']
            res.append(
                       {'product_name':i['product_name'],
                       'uom_name':i['uom_name'],
                       'product_ean':i['product_ean'],
                       'default_code':i['default_code'],
                       'category_name':i['category_name'],
                       })
        return res
        
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
