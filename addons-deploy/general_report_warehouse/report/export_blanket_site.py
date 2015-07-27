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
        self.top_n = False
        
        self.vat = False
        self.total_qty = 0
        self.total_val = 0
        self.sub_qty = 0
        self.sub_val = 0
        
        self.localcontext.update({
            'get_partner_name':self.get_partner_name,
            'get_blanket_site':self.get_blanket_site,
            'get_line':self.get_line,
        })
        
    def get_partner_name(self):
        wizard_data = self.localcontext['data']['form']
        partner_name = wizard_data['partner_id'][1]
        return partner_name
    
    def get_blanket_site(self):
        wizard_data = self.localcontext['data']['form']
        blanket_name = wizard_data['blanket_id'][1]
        return blanket_name
    
    def get_line(self):
        res=[]
        self.company_id = 1
        
        wizard_data = self.localcontext['data']['form']
        blanket_id = wizard_data['blanket_id'][0]
        warehouse_id = wizard_data['warehouse_id'][0]
        date = wizard_data['date']
        
        sql ='''
            SELECT line_no,pp.default_code code,ean,pp.name_template,uom.name uom,conversion,po_price 
            FROM
                 po_blanket_getline(%s,%s,'%s') blk
             join product_product pp on blk.product_id = pp.id
             join product_uom uom on blk.product_uom = uom.id
             ORDER BY line_no
            '''%(blanket_id,warehouse_id,date)   
        self.cr.execute(sql)
#         for line in self.cr.dictfetchall():
#             res.append({
#                     'line_no': line['line_no'],
#                     'product':line['name_template'],
#                     'default_code':str(line['code']),
#                     'ean':str(line['ean']),
#                     'uom':line['uom'],
#                     'conversion':line['conversion'],
#                     'po_price':line['po_price'],
#                  })
        return self.cr.dictfetchall()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
