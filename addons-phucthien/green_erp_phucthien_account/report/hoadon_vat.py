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
from openerp.addons.green_erp_phucthien_account.report import amount_to_text_vn

# from green_erp_pharma_report.report import amount_to_text_vn
class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.index_address = -1
        self.localcontext.update({
            'get_line':self.get_line,
            'get_tax': self.get_tax,
            'display_address': self.display_address,
            'get_date': self.get_date,
            'convert':self.convert,
            'convert_amount': self.convert_amount,
            'get_address': self.get_address,
            'get_address2': self.get_address2,
            'get_songayno': self.get_songayno,
        })
        
    def get_songayno(self, o):
        songayno = 10000
        for line in o.invoice_line:
            cate_id = line.product_id.categ_id.id
            manufacturer_product_id = line.product_id.manufacturer_product_id and line.product_id.manufacturer_product_id.id or False
            if cate_id and manufacturer_product_id:
                sql = '''
                    select so_ngay from so_ngay_no where product_category_id=%s and manufacturer_product_id=%s and partner_id=%s
                '''%(cate_id,manufacturer_product_id,o.partner_id.id)
                self.cr.execute(sql)
                so_ngay = self.cr.fetchone()
                if so_ngay and so_ngay[0]<songayno:
                    songayno=so_ngay
        if songayno==10000:
            return ''
        return songayno
    
    def get_address(self, address):
        if address and len(address)>=30:
            address = address[:30]
            self.index_address = 30
            for i in range(30,0,-1):
                if address[i-1] in [' ',',']:
                    self.index_address = i
                    break
            return address[:self.index_address]
        return address
    
    def get_address2(self, address):
        a = ''
        if address and len(address)>30 and self.index_address!=-1:
            return address[self.index_address:]
        return a
    
    def convert(self, amount):
        amount_text = amount_to_text_vn.amount_to_text(amount, 'vn')
        if amount_text and len(amount_text)>1:
            amount = amount_text[1:]
            head = amount_text[:1]
            amount_text = head.upper()+amount
        return amount_text
    
    def get_date(self, date=False):
        if not date:
            date = time.strftime('%Y-%m-%d')
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_tax(self,line_tax):
        tax = 0
        base_amount = 0
        tax_amount  = 0
        for line in line_tax:
            base_amount = line.base
            tax_amount  = line.amount
        tax = (tax_amount and  base_amount / tax_amount or 0 )  and  1 / (tax_amount and  base_amount / tax_amount or 0 ) or 0
        tax = round(tax,3)
        tax = tax * 100
        a = int(tax)
        if a - tax ==0:
            return a
        else:
            return tax
    
    def convert_amount(self, amount):
        a = format(int(amount),',')
        return a.replace(',',' ')
    
    def convert_f_amount(self, amount):
        a = format(amount,',')
        b = a.split('.')
        if len(b)==2 and len(b[1])==1:
            a+='0'
        return a.replace(',',' ')
    
    def get_date_hd(self,date):
        if not date:
            date = time.strftime('%Y-%m-%d')
        else:
            date = date[:10]
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%m/%Y') 
    
    def get_line(self,line,o):
        count = 0
        subtotal =0
        res =[]
        line_limit = 10
        for data in line:
            count += 1
            res.append({
                            'stt': count,
                            'name': data.product_id and data.product_id.name or data.name,
                            'nuoc_sx': data.product_id.product_country_id and data.product_id.product_country_id.name or '',
                            'so_lo': data.prodlot_id and data.prodlot_id.name or '',
                            'han_dung': data.prodlot_id and self.get_date_hd(data.prodlot_id.life_date) or '',
                            'uos_id': data.uos_id.name,
                            'quantity': self.convert_amount(data.quantity),
                            'price_unit': self.convert_f_amount(data.price_unit),
                            'price_subtotal': self.convert_amount(data.price_subtotal),
                            })
        for data in line:
            if line_limit and line_limit > count:
                while(line_limit != count):
                    res.append({
                                'stt': ' ',
                                'name': ' ',
                                'nuoc_sx': ' ',
                                'so_lo': ' ',
                                'han_dung': ' ',
                                'uos_id': ' ',
                                'quantity': ' ',
                                'price_unit': ' ',
                                'price_subtotal': ' ',
                                })
                    count +=1
        return res
    
    def display_address(self, partner):
        address = partner.street and partner.street + ' , ' or ''
        address += partner.street2 and partner.street2 + ' , ' or ''
        address += partner.city and partner.city.name + ' , ' or ''
        if address:
            address = address[:-3]
        return address
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
