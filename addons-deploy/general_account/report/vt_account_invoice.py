# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
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
import amount_to_text_vn
import amount_to_text_en

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.subtotal = 0
        self.localcontext.update({
            'get_qty': self.get_qty,
            'get_vietname_date':self.get_vietname_date, 
            'get_line':self.get_line,
            'amount_to_text':self.amount_to_text,
            'get_tax':self.get_tax,
            'get_name_des':self.get_name_des,
            'convert_qty':self.convert_qty,
            'get_warehouse_vat':self.get_warehouse_vat,
            'get_warehouse_address':self.get_warehouse_address,
            'get_warehouse_phone':self.get_warehouse_phone,
            'get_total_discount':self.get_total_discount,
            'get_price':self.get_price,
            'get_account_number':self.get_account_number
        })
        
    def get_warehouse_address(self,warehouse_id):
        if warehouse_id:
            sql='''
                SELECT rpa.street || ', ' || rcs.name as streest,
                       rpa.street2|| ', ' || rcs.name as streest2
                FROM stock_warehouse sw
                left join res_partner_address   rpa
                on sw.partner_address_id=rpa.id
                left join res_country_state rcs
                on rpa.state_id=rcs.id
                where
                    sw.id = %s
            '''%(warehouse_id.id)
            self.cr.execute(sql)
            for line in self.cr.dictfetchall():
                if line['streest2']:
                    return line['streest2']
                return line['streest']
            return False
        else:
            return False
    
    def get_warehouse_phone(self,warehouse_id):
        if warehouse_id:
            sql='''
                 SELECT rpa.phone as phone
                FROM stock_warehouse sw
                left join res_partner_address   rpa
                on sw.partner_address_id=rpa.id
                left join res_country_state rcs
                on rpa.state_id=rcs.id
                where
                    sw.id = %s
            '''%(warehouse_id.id)
            self.cr.execute(sql)
            for line in self.cr.dictfetchall():
                return line['phone']
            return False
        else:
            return False
    
    def get_warehouse_vat(self,warehouse_id):
        sql='''
            SELECT vat_num 
            FROM 
                sale_shop
            WHERE warehouse_id = %s
        '''%(warehouse_id.id)
        self.cr.execute(sql)
        data = self.cr.dictfetchone()
        if data:
            return data['vat_num']
        else:
            return False
    
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
    
    def convert_qty (self,qty):
        a = float(qty)
        return a

    def get_name_des(self,name,product_id):
        
        if name:
            if name[0] == '[':
                return name[11:39]
            else:
                return name[0:29]
                
        if product_id:
            return product_id.name[0:29]
        return name[0:36]
        
        
    def get_line(self,line,o):
        count = 0
        subtotal =0
        res =[]
        line_limit = 15
        for data in line:
            subtotal = subtotal + self.get_price(data,data.price_subtotal) - data.price_subtotal
            count += 1
#         if subtotal:
#             count += 1
#             res.append({
#                             'line': '',
#                             'discount_total': subtotal,
#                             'description':'Chiet khau'
#                             })
        for data in line:
            if line_limit and line_limit > count:
                while(line_limit != count):
                    res.append({
                                'line': ' ',
                                'discount_total': False,
                                'description': '',
                                })
                    count +=1
        return res

    def amount_to_text(self, nbr, lang='vn', currency='USD'):
        if lang == 'vn':
#            chuoi = amount_to_text_vn.amount_to_text(nbr, lang)
#            kt = chuoi[0].upper()
#
#            bt = chuoi[0]
#            chuoi = chuoi.replace(bt,kt,1) 
            return  amount_to_text_vn.amount_to_text(nbr, lang)
        else:
            return amount_to_text_en.amount_to_text(nbr, 'en', currency)
    
    def get_tax(self,line_tax):
        tax = 0
        base_amount = 0
        tax_amount  = 0
        for line in line_tax:
            base_amount = line.base_amount
            tax_amount  = line.tax_amount
        tax = (tax_amount and  base_amount / tax_amount or 0 )  and  1 / (tax_amount and  base_amount / tax_amount or 0 ) or 0
        tax = round(tax,3)
        tax = tax * 100
        a = int(tax)
        if a - tax ==0:
            return a
        else:
            return tax
        
    def get_total_discount(self,line):
        subtotal =0
        res ={
              'line': '',
              'discount_total':'',
              'description': ''
              }
        for data in line:
            subtotal = subtotal + self.get_price(data,data.price_subtotal) - data.price_subtotal
        if subtotal:
            res = {
                   'line': '',
                   'discount_total':subtotal,
                   'description': 'Chiet khau'
                   }
        return res
    
    def get_account_number(self,warehouse_id):
        if warehouse_id:
            if warehouse_id.partner_bank_id:
                return warehouse_id.partner_bank_id.acc_number
            else:
                return ''
        else:
            return ''
        
    def get_price(self,line,subtotal):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {
                'price_subtotal': 0.0,
                'amount_tax': 0.0,
            }
        price = line.price_unit 
        taxes = tax_obj.compute_all(self.cr, self.uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, address_id=line.invoice_id.address_invoice_id, partner=line.invoice_id.partner_id)
        res['price_subtotal'] = taxes['total']
        cur = line.invoice_id.currency_id
        self.subtotal = self.subtotal + cur_obj.round(self.cr, 1, cur, res['price_subtotal']) - subtotal
        return cur_obj.round(self.cr, 1, cur, res['price_subtotal'])
                
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
