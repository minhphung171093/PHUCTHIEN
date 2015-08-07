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
        self.context = context
        pool = pooler.get_pool(self.cr.dbname)
        res_user_obj = pool.get('res.users').browse(cr, uid, uid)
        self.localcontext.update({
            'display_address_partner': self.display_address_partner,
            'convert': self.convert,
            'get_date_hd': self.get_date_hd,
            'get_chungtu': self.get_chungtu,
            'get_qty':self.get_qty,
            'get_bien_ban_thuhoi_hangtrave':self.get_bien_ban_thuhoi_hangtrave,
        })
        
    def get_bien_ban_thuhoi_hangtrave(self):
        return self.pool.get('ir.sequence').get(self.cr, self.uid, 'bienban.thuhoi.hangtrave')
    
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
    
    def get_qty(self,o,product_id):
        invoice_obj = self.pool.get('account.invoice')
        vals = {
            'qty': 0,
        }
        sql ='''
            select acl.product_id, sum(acl.quantity) as qty
            from account_invoice ac
            left join account_invoice_line acl on acl.invoice_id = ac.id
            where ac.name = '%s' and acl.product_id = %s
            group by acl.product_id
        ''' %(o.origin,product_id.id)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            vals = {
                        'qty': line['qty'],
                    }
        return vals
    
    
    def get_chungtu(self,o,product_id):
        invoice_obj = self.pool.get('account.invoice')
        vals = {
            'so': '',
            'ngay': '',
        }
        sql ='''
            select acl.product_id, ac.reference_number,ac.date_invoice
            from account_invoice ac
            left join account_invoice_line acl on acl.invoice_id = ac.id
            where ac.name = '%s' and acl.product_id = %s
        ''' %(o.origin,product_id.id)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            vals = {
                        'so': line['reference_number'],
                        'ngay': line['date_invoice'],
                    }
        return vals
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
