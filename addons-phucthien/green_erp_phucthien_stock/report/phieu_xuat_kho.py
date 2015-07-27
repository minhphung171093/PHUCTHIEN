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
            'get_partner_address':self.get_partner_address,
            'get_date_hd': self.get_date_hd,
            'get_tax': self.get_tax,
            'total_get_tax': self.total_get_tax,
            'total_get_thanhtien': self.total_get_thanhtien,
        })
        
    def get_date_hd(self,date):
        if not date:
            date = time.strftime('%Y-%m-%d')
        else:
            date = date[:10]
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%m/%Y') 
    
    def get_tax(self, line):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(self.cr, self.uid, line.sale_line_id.tax_id, line.sale_line_id.price_unit * (1-(line.sale_line_id.discount or 0.0)/100.0), line.product_qty, line.product_id.id, line.picking_id.partner_id.id)['taxes']:
            val += c.get('amount', 0.0)
        return val
    
    def total_get_tax(self, move_lines):
        total = 0.0
        for line in move_lines:
            val = 0.0
            for c in self.pool.get('account.tax').compute_all(self.cr, self.uid, line.sale_line_id.tax_id, line.sale_line_id.price_unit * (1-(line.sale_line_id.discount or 0.0)/100.0), line.product_qty, line.product_id.id, line.picking_id.partner_id.id)['taxes']:
                val += c.get('amount', 0.0)
            total += val
        return total
    
    def total_get_thanhtien(self, move_lines):
        total = 0.0
        for line in move_lines:
            val = line.product_qty*line.sale_price
            total += val
        return total
        
    def get_partner_address(self, order):
        address = ''
        if order.partner_id:
            address += order.partner_id.street or ''
            address += order.partner_id.state_id and ', ' + order.partner_id.state_id.name or ''
            address += order.partner_id.country_id and ', ' + order.partner_id.country_id.name or ''
        return address
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
