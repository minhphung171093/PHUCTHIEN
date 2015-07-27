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
        
        self.localcontext.update({
            'get_line':self.get_line,
        })
    
        
    def get_line(self):
        self.company_id = 1
        wizard_data = self.localcontext['data']['form']
        self.shop_id = wizard_data['shop_id'][0]
        self.sale_price_list_id = wizard_data['sale_price_list_id'][0]
        sql = '''
            SELECT * FROM lkp_pda_productlist(%s,%s,%s)
        ''' %(self.company_id,self.shop_id,self.sale_price_list_id)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
