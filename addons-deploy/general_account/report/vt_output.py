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
        self.company_address = False
        self.vat = False
        self.get_company(cr, uid)
        self.localcontext.update({
            'get_sum': self.get_sum,
            'get_vietname_date':self.get_vietname_date,
            'get_quantity':self.get_quantity,
            'get_tax_line':self.get_tax_line,
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_company_vat':self.get_company_vat,
        })
        
    def get_company(self,cr,uid):
         user_obj = self.pool.get('res.users').browse(cr,uid,uid)
         self.company_name = user_obj and user_obj.company_id and user_obj.company_id.name or ''
         self.company_address = user_obj and user_obj.company_id and user_obj.company_id.street or ''
         self.company_address = self.company_address +', '+ ( user_obj and user_obj.company_id and user_obj.company_id.state_id and user_obj.company_id.state_id.name  or '')
         self.vat = user_obj and user_obj.company_id and user_obj.company_id.vat or ''
         
    def get_company_name(self):
        return self.company_name
    
    def get_company_address(self):
        return self.company_address    
    
    def get_company_vat(self):
        return self.vat    
    
    
    def get_sum(self,order_line):
        sumqty =0     
        price_subtotal = 0   
        amount_tax = 0
        vat = 0
        for line in order_line:
            sumqty += line.quantity
            price_subtotal += line.price_subtotal     
#            amount_tax +=  line.amount_tax   
             
        sumqty = self.get_quantity(sumqty)
        
        res = {
               'sumqty': sumqty,
               'price_subtotal':price_subtotal,
               'amount_tax': amount_tax,
               'vat': sumqty and  price_subtotal / sumqty or 0
               }
        return res
    
    def get_tax_line_vn(self,tax_line):
        count = len(tax_line)
        line = tax_line[count-3:count]
        name = u"Thuế GTGT " + line 
        return name
     
    def get_tax_line(self,tax_line):
        for line in tax_line:
            return self.get_tax_line_vn(line.name)
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        strng = date.strftime('%d %m %Y')
        return date.strftime('%d-%m-%Y')
    
    def get_quantity(self,qty):
        b = int(qty)
        if qty - b ==0:
            return b
        else:
            return qty

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
