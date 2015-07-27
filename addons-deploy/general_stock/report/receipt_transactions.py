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
        res_user_obj = pool.get('res.users').browse(cr, uid, uid)
        self.localcontext.update({
            'display_address_partner': self.display_address_partner,
            'convert': self.convert,
            'get_tax_amount': self.get_tax_amount,
            'get_date_hd': self.get_date_hd,
            'get_chungtu': self.get_chungtu,
        })

    def display_address_partner(self, partner):
        address = partner.street and partner.street + ' , ' or ''
        address += partner.street2 and partner.street2 + ' , ' or ''
        address += partner.city and partner.city.name + ' , ' or ''
        address += partner.state_id and partner.state_id.name + ' , ' or ''
        if address:
            address = address[:-3]
        return address
    
    def convert(self, amount):
        user = self.pool.get('res.users')
        amount_text = user.amount_to_text(amount, 'vn', 'VND')
        if amount_text and len(amount_text)>1:
            amount = amount_text[1:]
            head = amount_text[:1]
            amount_text = head.upper()+amount
        return amount_text
    
    def get_date_hd(self,date):
        if date:
            date = date[:10]
            date = datetime.strptime(date, DATE_FORMAT)
            return date.strftime('%m/%Y')
        else:
            return ''
        
    def get_date_invoice(self,date):
        if date:
            date = date[:10]
            date = datetime.strptime(date, DATE_FORMAT)
            return date.strftime('%d/%m/%y')
        else:
            return ''
    
    def get_tax_amount(self,po_line=False):
        amount_tax = 0
        if po_line:
            for t in po_line.taxes_id:
                amount_tax+= t.amount*po_line.price_subtotal
        return amount_tax
    
    def get_chungtu(self,o):
        invoice_obj = self.pool.get('account.invoice')
        invoice_ids = invoice_obj.search(self.cr, self.uid, [('name','=',o.name)])
        vals = {
            'so': '',
            'ngay': '',
        }
        if invoice_ids:
            invoice = invoice_obj.browse(self.cr, self.uid, invoice_ids[0])
            vals = {
                'so': invoice.supplier_invoice_number,
                'ngay': self.get_date_invoice(invoice.date_invoice),
            }
        return vals
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
