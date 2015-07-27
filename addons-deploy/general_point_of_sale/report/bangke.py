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
        self.start_date = False
        self.end_date = False
        self.total = 0.0
        self.cash =0.0
        self.banks =0.0
        self.conlai = 0.0
        self.section_id=False
        self.localcontext.update({
            'get_line':self.get_line,
            'get_start_date':self.get_start_date,
            'get_end_date':self.get_end_date,
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_company_vat':self.get_company_vat,
            'get_vietname_datetime':self.get_vietname_datetime,
            'get_total':self.get_total,
            'get_cash':self.get_cash,
            'get_banks':self.get_banks,
            'get_conlai':self.get_conlai,
            'get_pos':self.get_pos,
            'get_tm':self.get_tm,
            'get_ck':self.get_ck,
            'get_sum_total':self.get_sum_total,
            'get_con':self.get_con,
            'get_string_date':self.get_string_date,
        })
        
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.company_id = wizard_data['company_id'] and wizard_data['company_id'][0] or False
        self.get_company(self.company_id)
        
        self.start_date = wizard_data['from_date']
        self.end_date = wizard_data['to_date']
        self.section_id = wizard_data['section_id'] and wizard_data['section_id'][0] or False
        return True
    
    def get_total(self):
        self.get_payment()
        self.conlai = self.total - self.cash - self.banks
        return self.total
    
    def get_conlai(self):
        return self.conlai
    
    def get_start_date(self):
        return self.get_vietname_datetime(self.start_date) 
    
    def get_end_date(self):
        return self.get_vietname_datetime(self.end_date) 
    
    def get_vietname_date(self, date):
        if not date:
            return ''
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_vietname_datetime(self, date):
        if not date:
            return ''
        date = datetime.strptime(date, DATETIME_FORMAT)
        user_pool = self.pool.get('res.users')
        date_user_tz = user_pool._convert_user_datetime(self.cr, self.uid, date.strftime(DATETIME_FORMAT))
        date_user_tz = date_user_tz.strftime('%d/%m/%Y')
        return date_user_tz
    
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
    
    def get_cash(self):
        if not self.cash:
            self.get_payment()
        return self.cash
    def get_banks(self):
        if not self.banks:
            self.get_payment()
        return self.banks
    
    def get_payment(self):
        if self.section_id:
            sql='''
                SELECT aj.type, sum(amount) amount
                FROM account_bank_statement_line absl 
                    inner join account_journal aj on absl.journal_id = aj.id
                    inner join pos_order pos on pos.id = absl.pos_statement_id  and pos.state not in ('cancel')
                WHERE aj.type in ('cash','bank')
                    and absl.payment_datetime between '%s' and '%s'
                    and pos.section_id = %s
                GROUP BY  aj.type'''%(self.start_date,self.end_date,self.section_id)   
        else:
            sql='''
                SELECT aj.type, sum(amount) amount
                FROM account_bank_statement_line absl 
                    inner join account_journal aj on absl.journal_id = aj.id
                    inner join pos_order pos on pos.id = absl.pos_statement_id  and pos.state not in ('cancel')
                WHERE aj.type in ('cash','bank')
                    and absl.payment_datetime between '%s' and '%s'
                GROUP BY  aj.type'''%(self.start_date,self.end_date)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            if i['type']=='bank':
                self.banks = i['amount']
            else:
                self.cash = i['amount']
        return 1
    
    def get_tm(self, id):
        sql ='''
          SELECT aj.type, sum(amount) amount
            FROM account_bank_statement_line absl 
                inner join account_journal aj on absl.journal_id = aj.id
                inner join pos_order pos on pos.id = absl.pos_statement_id
            WHERE aj.type in ('cash','bank')
                and absl.payment_datetime between '%s' and '%s'
                and pos.id = %s
            GROUP BY  aj.type'''%(self.start_date,self.end_date,id)    
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            if i['type']=='cash':
                return i['amount'] or 0.0
        return 0.0
    
    def get_ck(self, id):
        sql ='''
          SELECT aj.type, sum(amount) amount
            FROM account_bank_statement_line absl 
                inner join account_journal aj on absl.journal_id = aj.id
                inner join pos_order pos on pos.id = absl.pos_statement_id
            WHERE aj.type in ('cash','bank')
                and absl.payment_datetime between '%s' and '%s'
                and pos.id = %s
            GROUP BY  aj.type'''%(self.start_date,self.end_date,id)   
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            if i['type']=='bank':
                return i['amount'] or 0.0
        return 0.0
    
    def get_sum_total(self, id):
        sql='''
            select sum(price_subtotal_incl)  sum_total
                from pos_order_line
                where order_id = %s
        '''%(id)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['sum_total'] or 0.0
        return 0.0
        
    def get_pos(self):
        if self.section_id:
            sql ='''
                SELECT  distinct pos.id,pos.name ,coalesce(pos.partner_reference,rpt.name) partner_reference,
                        pos.date_order,pos.note
                    FROM pos_order pos inner join pos_order_line pol on pos.id = pol.order_id and pos.state not in ('cancel')
                    inner join res_partner rpt on pos.partner_id = rpt.id
                    inner join account_bank_statement_line absl on pos.id = absl.pos_statement_id
                WHERE 
                    absl.payment_datetime between '%s' and '%s'
                    and pos.section_id = %s
                ORDER BY date_order
            '''%(self.start_date,self.end_date,self.section_id) 
        else:
            sql ='''
                SELECT  distinct pos.id,pos.name ,coalesce(pos.partner_reference,rpt.name) partner_reference,
                        pos.date_order,pos.note
                    FROM pos_order pos inner join pos_order_line pol on pos.id = pol.order_id and pos.state not in ('cancel')
                    inner join res_partner rpt on pos.partner_id = rpt.id
                    inner join account_bank_statement_line absl on pos.id = absl.pos_statement_id
                WHERE 
                    absl.payment_datetime between '%s' and '%s'
                ORDER BY date_order
            '''%(self.start_date,self.end_date) 
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_con(self,id):
        sql='''
            SELECT 
                (select sum(price_subtotal_incl) from pos_order_line where order_id = %s) - sum(amount) amount
                FROM account_bank_statement_line absl 
                    inner join account_journal aj on absl.journal_id = aj.id
                    inner join pos_order pos on pos.id = absl.pos_statement_id
                WHERE aj.type in ('cash','bank')
                    and pos.id = %s
        '''%(id,id)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['amount'] or 0.0
        return 0.0
    
    def get_string_date(self):
        date = time.strftime(DATE_FORMAT)
        #string = 'Ngay ' +str(date[8:10])+ u'Thang ' +str(date[5:7])+ +u'Nam ' + str(date[0:4])
        return date
        
    def get_line(self,id):
        res=[]
        if not self.end_date:
            self.get_header()
        sql ='''
            SELECT pp.name_template,pol.qty,pol.price_unit,pol.price_subtotal_incl,
                coalesce(pos.partner_reference,rpt.name) partner_reference,
                pol.name,pos.date_order,uom.name uom_name,sl.name location_name,pol.note
            FROM pos_order_line pol
                inner join pos_order pos on pol.order_id = pos.id
                inner join product_product pp on pol.product_id = pp.id
                inner join res_partner rpt on pos.partner_id = rpt.id
                inner join product_template pt on pp.product_tmpl_id = pt.id
                inner join product_uom uom on pt.uom_id = uom.id
                left join stock_location sl on pol.from_location_id = sl.id 
            WHERE
                 pos.id = %s
            ORDER BY pos.date_order
            '''%(id)   
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            self.total += i['price_subtotal_incl'] or 0.0
            res.append(
                   {
                   'name_template':i['name_template'],
                   'qty':i['qty'],
                   'price_unit':i['price_unit'] or 0.0,
                   'price_subtotal_incl':i['price_subtotal_incl'] or 0.0,
                   'partner_reference':i['partner_reference'] or '',
                   'name':i['name'] or '',
                   'date_order':i['date_order'] or False,
                   'uom_name':i['uom_name'],
                   'location_name':i['location_name'] or False,
                   'note':i['note'] or False
                   })
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
