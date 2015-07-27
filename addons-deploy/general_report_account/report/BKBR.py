# -*- coding: utf-8 -*-
##############################################################################
#
#    HLVSolution, Open Source Management Solution
#
##############################################################################

import time
from report import report_sxw
from osv import osv
from tools.translate import _
import random
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.account_id =False
        self.times = False
        self.start_date = False
        self.end_date = False
        self.company_name = False
        self.company_address = False
        self.vat = False 
        self.cr = cr
        self.uid = uid
        self.amount = 0
        self.amount_tax = 0
        self.sum_amount = 0
        self.sum_amount_tax = 0
        self.shop_ids =False
        
        self.localcontext.update({
            'get_vietname_date':self.get_vietname_date, 
            'get_header':self.get_header,
            'get_account':self.get_account,
            'get_start_date':self.get_start_date,
            'get_end_date':self.get_end_date,
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_company_vat':self.get_company_vat,
            'get_line_tax_0':self.get_line_tax_0,
            'get_line_tax_5':self.get_line_tax_5,
            'get_line_tax_10':self.get_line_tax_10,
            'get_total_amount_tax':self.get_total_amount_tax,
            'get_total_amount':self.get_total_amount,
            'get_sum_amount':self.get_sum_amount,
            'get_sum_amount_tax':self.get_sum_amount_tax,
        })
    
    def get_company(self, company_id):
        if company_id:
            company_obj = self.pool.get('res.company').browse(self.cr, self.uid,company_id)
            self.company_name = company_obj.name or ''
            self.company_address = company_obj.street or ''
            self.vat = company_obj.vat or ''
        return True
         
    def get_company_name(self):
        self.get_header()
        return self.company_name
    
    def get_company_address(self):
        return self.company_address     
    
    def get_company_vat(self):
        return self.vat    
        
    def get_id(self,get_id):
        wizard_data = self.localcontext['data']['form']
        period_id = wizard_data[get_id][0] or False
        if not period_id:
            return 1
        else:
            return period_id
    
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.times = wizard_data['times']
        #Get company info
        self.company_id = wizard_data['company_id'] and wizard_data['company_id'][0] or False
        self.get_company(self.company_id)
        self.shop_ids = wizard_data['shop_ids'] or False
        if self.shop_ids:
            self.shop_ids = (','.join(map(str,self.shop_ids)))
        
        if self.times =='periods':
            self.start_date = self.pool.get('account.period').browse(self.cr,self.uid,self.get_id('period_id_start')).date_start
            self.end_date   = self.pool.get('account.period').browse(self.cr,self.uid,self.get_id('period_id_end')).date_stop
            
        elif self.times == 'years':
            self.start_date = self.pool.get('account.fiscalyear').browse(self.cr,self.uid,self.get_id('fiscalyear_start')).date_start
            self.end_date   = self.pool.get('account.fiscalyear').browse(self.cr,self.uid,self.get_id('fiscalyear_stop')).date_stop
        else:
            self.start_date = wizard_data['date_start']
            self.end_date = wizard_data['date_end']
        
        return True
        
            
    def get_start_date(self):
        return self.get_vietname_date(self.start_date) 
    
    def get_end_date(self):
        return self.get_vietname_date(self.end_date) 
    
    def get_account(self):
        values ={}
        wizard_data = self.localcontext['data']['form']
        self.account_id = wizard_data['account_id'][0]
        if self.account_id:
            account_obj = self.pool.get('account.account').browse(self.cr,self.uid,self.account_id)
            values ={
                     'account_code': account_obj.code,
                     'account_name':account_obj.name,
                     }
            return values
    
    def get_vietname_date(self, date):
        if not date:
            return ''
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_sum_amount(self):
        return self.sum_amount 
    
    def get_sum_amount_tax(self):
        return self.sum_amount_tax
    
    def get_total_amount_tax(self):
        self.sum_amount_tax = self.sum_amount_tax + self.amount_tax
        return self.amount_tax
    
    def get_total_amount(self):
        self.sum_amount = self.sum_amount + self.amount
        return self.amount
    
    def get_line_tax_0(self):
        res = []
        self.amount = 0
        self.amount_tax = 0
        if self.shop_ids:
            sql='''
                 SELECT agi.reference,agi.reference_number,agi.date_invoice,rp.name partner_name,rp.vat vat_code,
                 SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal else agil.price_subtotal * (-1) end) as price_subtotal,                        
                 SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal *0.05 else agil.price_subtotal *0 end) as price_tax  
                FROM account_invoice agi 
                inner join account_invoice_line agil on agi.id = agil.invoice_id 
                inner join res_partner rp on rp.id = agi.partner_id  
                inner join account_invoice_line_tax agilt on agil.id = agilt.invoice_line_id
                inner join account_tax atx on atx.id = agilt.tax_id 
                WHERE agi.state in ('open','paid')
                AND atx.amount = 0
                AND agi.date_invoice between '%s' and '%s'
                AND agi.shop_id in (%s)
                AND agi.type in ('out_invoice','out_refund')
                GROUP BY agi.reference,agi.reference_number,agi.date_invoice,rp.name,rp.vat
                ORDER BY date_invoice
            '''%(self.start_date,self.end_date,self.shop_ids)
        else:
            sql='''
                 SELECT agi.reference,agi.reference_number,agi.date_invoice,rp.name partner_name,rp.vat vat_code,
                 SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal else agil.price_subtotal * (-1) end) as price_subtotal,                        
                 SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal *0.05 else agil.price_subtotal *0 end) as price_tax  
                FROM account_invoice agi 
                inner join account_invoice_line agil on agi.id = agil.invoice_id 
                inner join res_partner rp on rp.id = agi.partner_id  
                inner join account_invoice_line_tax agilt on agil.id = agilt.invoice_line_id
                inner join account_tax atx on atx.id = agilt.tax_id 
                WHERE agi.state in ('open','paid')
                AND atx.amount = 0
                AND agi.date_invoice between '%s' and '%s'
                AND agi.type in ('out_invoice','out_refund')
                GROUP BY agi.reference,agi.reference_number,agi.date_invoice,rp.name,rp.vat
                ORDER BY date_invoice
            '''%(self.start_date,self.end_date)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            res.append({
                 'reference':line['reference'] or '',
                 'number':line['reference_number'] or '',
                 'date_invoice':self.get_vietname_date(line['date_invoice']),
                 'partner_name':line['partner_name'],
                 'vat_code':line['vat_code'] or '',
                 'price_subtotal':line['price_subtotal'] or '' ,
                 'amount_tax': line['price_tax'],
                 })
            self.amount += line['price_subtotal']
            self.amount_tax += line['price_tax']
        return res
    
    def get_line_tax_5(self):
        res = []
        self.amount = 0
        self.amount_tax = 0
        if self.shop_ids:
            sql='''
                    SELECT agi.reference,agi.reference_number,agi.date_invoice,rp.name partner_name,rp.vat vat_code,
                     SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal else agil.price_subtotal * (-1) end) as price_subtotal,                        
                     SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal *0.05 else agil.price_subtotal *0.05 * (-1) end) as price_tax  
                    FROM account_invoice agi 
                    inner join account_invoice_line agil on agi.id = agil.invoice_id 
                    inner join res_partner rp on rp.id = agi.partner_id  
                    inner join account_invoice_line_tax agilt on agil.id = agilt.invoice_line_id
                    inner join account_tax atx on atx.id = agilt.tax_id 
                    WHERE agi.state in ('open','paid')
                    AND atx.amount = 0.05
                    AND agi.date_invoice between '%s' and '%s'
                    AND agi.shop_id in (%s)
                    AND agi.type in ('out_invoice','out_refund')
                    GROUP BY agi.reference,agi.reference_number,agi.date_invoice,rp.name,rp.vat
                    ORDER BY date_invoice
            '''%(self.start_date,self.end_date,self.shop_ids)
        else:
            sql='''
                    SELECT agi.reference,agi.reference_number,agi.date_invoice,rp.name partner_name,rp.vat vat_code,
                     SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal else agil.price_subtotal * (-1) end) as price_subtotal,                        
                     SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal *0.05 else agil.price_subtotal *0.05 * (-1) end) as price_tax  
                    FROM account_invoice agi 
                    inner join account_invoice_line agil on agi.id = agil.invoice_id 
                    inner join res_partner rp on rp.id = agi.partner_id  
                    inner join account_invoice_line_tax agilt on agil.id = agilt.invoice_line_id
                    inner join account_tax atx on atx.id = agilt.tax_id 
                    WHERE agi.state in ('open','paid')
                    AND atx.amount = 0.05
                    AND agi.date_invoice between '%s' and '%s'
                    AND agi.type in ('out_invoice','out_refund')
                    GROUP BY agi.reference,agi.reference_number,agi.date_invoice,rp.name,rp.vat
                    ORDER BY date_invoice
            '''%(self.start_date,self.end_date)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            res.append({
                 'reference':line['reference'] or '',
                 'number':line['reference_number'] or '',
                 'date_invoice':self.get_vietname_date(line['date_invoice']),
                 'partner_name':line['partner_name'],
                 'vat_code':line['vat_code'] or '',
                 'price_subtotal': line['price_subtotal'] or '',
                 'amount_tax': line['price_tax'],
                 })
            self.amount += line['price_subtotal']
            self.amount_tax += line['price_tax']
        return res
    
    def get_line_tax_10(self):
        res = []
        self.amount = 0
        self.amount_tax = 0
        if self.shop_ids:
            sql='''
                    SELECT agi.reference,agi.reference_number,agi.date_invoice,rp.name partner_name,rp.vat vat_code,
                     SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal else agil.price_subtotal * (-1) end) as price_subtotal,                        
                     SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal *0.05 else agil.price_subtotal *0.1 * (-1) end) as price_tax  
                    FROM account_invoice agi 
                    inner join account_invoice_line agil on agi.id = agil.invoice_id 
                    inner join res_partner rp on rp.id = agi.partner_id  
                    inner join account_invoice_line_tax agilt on agil.id = agilt.invoice_line_id
                    inner join account_tax atx on atx.id = agilt.tax_id 
                    WHERE agi.state in ('open','paid')
                    AND atx.amount = 0.1
                    AND agi.date_invoice between '%s' and '%s'
                    AND agi.shop_id in (%s)
                    AND agi.type in ('out_invoice','out_refund')
                    GROUP BY agi.reference,agi.reference_number,agi.date_invoice,rp.name,rp.vat
                    ORDER BY date_invoice
            '''%(self.start_date,self.end_date,self.shop_ids)
        else:
            sql='''
                    SELECT agi.reference,agi.reference_number,agi.date_invoice,rp.name partner_name,rp.vat vat_code,
                     SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal else agil.price_subtotal * (-1) end) as price_subtotal,                        
                     SUM(CASE WHEN agi.type ='out_invoice' then agil.price_subtotal *0.05 else agil.price_subtotal *0.1 * (-1) end) as price_tax  
                    FROM account_invoice agi 
                    inner join account_invoice_line agil on agi.id = agil.invoice_id 
                    inner join res_partner rp on rp.id = agi.partner_id  
                    inner join account_invoice_line_tax agilt on agil.id = agilt.invoice_line_id
                    inner join account_tax atx on atx.id = agilt.tax_id 
                    WHERE agi.state in ('open','paid')
                    AND atx.amount = 0.1
                    AND agi.date_invoice between '%s' and '%s'
                    AND agi.type in ('out_invoice','out_refund')
                    GROUP BY agi.reference,agi.reference_number,agi.date_invoice,rp.name,rp.vat
                    ORDER BY date_invoice
            '''%(self.start_date,self.end_date)
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            res.append({
                 'reference':line['reference'] or '',
                 'number':line['reference_number'] or '',
                 'date_invoice':self.get_vietname_date(line['date_invoice']),
                 'partner_name':line['partner_name'],
                 'vat_code':line['vat_code'] or '',
                 'price_subtotal':line['price_subtotal'] or '' ,
                 'amount_tax': line['price_tax'],
                 })
            self.amount += line['price_subtotal']
            self.amount_tax += line['price_tax']
        return res
    
        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
