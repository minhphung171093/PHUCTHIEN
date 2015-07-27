# -*- coding: utf-8 -*-
##############################################################################
#
#    HLVSolution, Open Source Management Solution
#
##############################################################################
import time
from openerp.report import report_sxw
from openerp import pooler
from openerp.osv import osv
from openerp.tools.translate import _
import random
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
# from green_erp_pharma_report.report import amount_to_text_vn
class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.localcontext.update({
#             'get_sale_order':self.get_sale_order, 
#            'convert':self.convert,
        })
#     def get_sale_order(self,contract_id):
#         sale_order_obj = self.pool.get('sale.order')
#         sale_order_ids = sale_order_obj.search(self.cr, self.uid, [('project_id','=',contract_id)])
#         if sale_order_ids:
#             return sale_order_obj.browse(self.cr, self.uid, sale_order_ids[0])
#         else:
#             return False
#     def convert(self,amount):
#         amt_vn = amount_to_text_vn.amount_to_text(amount,'đồng');
#         return amt_vn
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
