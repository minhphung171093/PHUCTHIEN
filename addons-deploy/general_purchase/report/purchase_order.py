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
        
        self.res_name = False
        self.get_create_name(cr,uid)
        
        pool = pooler.get_pool(self.cr.dbname)
        self.localcontext.update({
            'get_qty': self.get_qty,
            'get_vietname_date':self.get_vietname_date,
            'get_partner_address':self.get_partner_address,
            'get_quantity':self.get_quantity,
            'get_warehouse_address':self.get_warehouse_address,
            'get_user_create':self.get_user_create,
            'get_partner_code':self.get_partner_code
        })
    
    def get_partner_code(self,partner_id):
        partner_name = False
        if partner_id:
            partner_name = '['+ partner_id.ref + '] ' + partner_id.name
        return partner_name
        
    def get_create_name(self,cr,uid):
        res_obj = self.pool.get('res.users').browse(cr,uid,uid)
        if res_obj:
            self.res_name = res_obj.name or ''
        else:
            return self.res_name
        
    def get_user_create(self):
        return self.res_name
        
    def get_quantity(self,qty):
#         b = int(qty)
#         if qty - b ==0:
#             return b
#         else:
        return qty
    
    def get_qty(self,order_line):
        sumqty =0
        for line in order_line:
            sumqty += line.product_qty
#         b = int(sumqty)
#         if sumqty - b ==0:
#             return b
#         else:
        return sumqty
        
    def get_warehouse_address(self,order):
        address = ''
        if order.warehouse_id and order.warehouse_id.partner_address_id: 
            address = order.warehouse_id.partner_address_id.street
        if order.warehouse_id and order.warehouse_id.partner_address_id.phone:
            address += u' - ĐT: ' + order.warehouse_id.partner_address_id.phone
        return address
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d-%m-%Y')
    
    def get_partner_address(self, order):
        address = ''
        if order.partner_id:
            if order.partner_id.street:
                for line in order.partner_id.street:
                    if line.type =='default':
                        address = line.street
                        if line.state_id:                
                            address += line.state_id and ', ' + line.state_id.name or ''
        return address
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
