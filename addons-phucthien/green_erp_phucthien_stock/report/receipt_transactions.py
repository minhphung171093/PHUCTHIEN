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
            'get_tax_amount': self.get_tax_amount,
            'get_date_hd': self.get_date_hd,
            'get_chungtu': self.get_chungtu,
            'get_picking': self.get_picking,
            'get_date_now': self.get_date_now,
            'get_total': self.get_total,
            'get_stt': self.get_stt,
            'get_print':self.get_print,
            'get_bien_ban_tp':self.get_bien_ban_tp,
            'get_bien_ban_tp_lanh':self.get_bien_ban_tp_lanh,
            
        })
        
        
    def get_bien_ban_tp_lanh(self):
        return self.pool.get('ir.sequence').get(self.cr, self.uid, 'bienban.thanhpham.lanh')
    
    def get_bien_ban_tp(self):
        return self.pool.get('ir.sequence').get(self.cr, self.uid, 'bienban.thanhpham')
    
    
    def get_print(self):
        so_lan_in = self.pool.get('so.lan.in').search(self.cr,self.uid,[])
        if not so_lan_in:
            date = time.strftime('%Y-%m-%d')
            month = date[5:7]
            month = int(month)
            so_lan = 0
            self.pool.get('so.lan.in').create(self.cr, self.uid,{'name':1,'thang':month})
            sql='''
                select id from so_lan_in
            '''
            self.cr.execute(sql)
            so_lan_id = self.cr.dictfetchone()['id']
            so_lan = self.pool.get('so.lan.in').browse(self.cr, self.uid, so_lan_id)
            sl = so_lan.name
            sql='''
                update so_lan_in set name  = name + 1
            '''
            self.cr.execute(sql)
        else:
            date = time.strftime('%Y-%m-%d')
            month = date[5:7]
            month = int(month)
            sql='''
                select id from so_lan_in
            '''
            self.cr.execute(sql)
            so_lan_id = self.cr.dictfetchone()['id']
            so_lan = self.pool.get('so.lan.in').browse(self.cr, self.uid, so_lan_id)
            if so_lan:
                if so_lan.thang == month:
                    sl = so_lan.name
                    self.pool.get('so.lan.in').write(self.cr, self.uid,[so_lan_id],{'name':sl+1})
                else:
                    self.pool.get('so.lan.in').write(self.cr, self.uid,[so_lan_id],{'name':1,'thang':month})
                    sql='''
                        select id from so_lan_in
                    '''
                    self.cr.execute(sql)
                    so_lan_id = self.cr.dictfetchone()['id']
                    so_lan = self.pool.get('so.lan.in').browse(self.cr, self.uid, so_lan_id)
                    sl = so_lan.name
                    sql='''
                        update so_lan_in set name  = name + 1
                    '''
                    self.cr.execute(sql)
        return sl
    
    def get_total(self):
        tong = 0
        for o in self.get_picking():
            for line in o.move_lines:
                tong += line.purchase_line_id.price_unit * line.product_qty + self.get_tax_amount(line.purchase_line_id or 0)
        return tong
    def get_stt(self,seq_1,seq):
        stt = 1
        for s,picking in enumerate(self.get_picking()):
            if s<seq_1:
                stt += len(picking.move_lines)
            if s==seq_1:
                for s2,line in enumerate(picking.move_lines):
                    if s2<seq:
                        stt += 1
        return stt
    
    def get_date_now(self):
        return time.strftime('%Y-%m-%d')
    
    def get_picking(self):
        picking_in_obj = self.pool.get('stock.picking.in')
        picking_in_ids = self.context.get('active_ids',[])
        return picking_in_obj.browse(self.cr, self.uid, picking_in_ids)
        
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
