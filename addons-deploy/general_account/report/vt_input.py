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
        self.localcontext.update({
            'get_qty': self.get_qty,
            'get_vietname_date':self.get_vietname_date,
            'get_string_date':self.get_string_date,
            'get_address_warehouse':self.get_address_warehouse,
            'get_name_des':self.get_name_des,
        })
    
    def get_qty(self,order_line):
        sumqty =0
        for line in order_line:
            sumqty += line.product_qty
        return sumqty
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        strng = date.strftime('%d %m %Y')
        return date.strftime('%d/%m/%Y')

    def get_string_date(self,date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        month = date.strftime('%m')
        day  = date.strftime('%d')
        year = date.strftime('%Y')
        chuoi = u'Ngày ' + str(day) + u' tháng ' + str(month) + u' năm ' + str(year)
        return chuoi
    
    def get_name_des(self,name,product_id):
        if product_id:
            return product_id.name[0:35]
        return name[0:36]
    
    def get_address_warehouse(self,warehouse_id):
        if not warehouse_id:
            return ''
        if warehouse_id.partner_address_id: 
                address = warehouse_id.partner_address_id.street
                address += u' ' + warehouse_id.partner_address_id.state_id.name
        return address
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
