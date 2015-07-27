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
            'get_thue':self.get_thue,
            'get_tong':self.get_tong,
        })
    
    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val
    
    def get_thue(self,order,line):
        cur_obj = self.pool.get('res.currency')
        cur = order.pricelist_id.currency_id
        val = self._amount_line_tax(self.cr, self.uid, line)
        return cur_obj.round(self.cr, self.uid, cur, val)
    
    def get_tong(self,order):
        cur_obj = self.pool.get('res.currency')
        cur = order.pricelist_id.currency_id
        val = 0
        val1 = 0
        for line in order.order_line:
            val += self._amount_line_tax(self.cr, self.uid, line)
            val1 += line.price_subtotal
        tax = cur_obj.round(self.cr, self.uid, cur, val)
        total = cur_obj.round(self.cr, self.uid, cur, val1)
        return {
                'tax': tax,
                'total': tax+total,
                }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
