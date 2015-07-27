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
import amount_to_text_vn
import amount_to_text_en

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.account_id =False
        self.times = False
        self.start_date = False
        self.end_date = False
        self.company_name = False
        self.company_address = False
        self.showdetail = False
        self.vat = False
        self.shop_ids = []
        self.localcontext.update({
            'get_vietname_date':self.get_vietname_date, 
            'get_line':self.get_line,
            'get_header':self.get_header,
            'get_account':self.get_account,
            'get_start_date':self.get_start_date,
            'get_end_date':self.get_end_date,
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_company_vat':self.get_company_vat,
            'show_dauky':self.show_dauky,
            'get_cuoiky':self.get_cuoiky,
            'get_sum_trongky':self.get_sum_trongky,
            'get_trongky':self.get_trongky,
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
        period_id = wizard_data[get_id][0] or wizard_data[get_id][0] or False
        if not period_id:
            return 1
        else:
            return period_id
        
    def get_quarter_date(self,year,quarter):
        self.start_date = False
        self.end_date  = False
        if quarter == '1':
            self.start_date = '''%s-01-01'''%(year)
            self.end_date = year + '-03-31'
        elif quarter == '2':
            self.start_date = year+'-04-01'
            self.end_date =year+'-06-30'
        elif quarter == '3':
            self.start_date = year+'-07-01'
            self.end_date = year+'-09-30'
        else:
            self.start_date = year+'-10-01'
            self.end_date = year+'-12-31'
    
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.times = wizard_data['times']
        #Get company info
        self.company_id = wizard_data['company_id'] and wizard_data['company_id'][0] or False
        self.get_company(self.company_id)
        #Get shops
        self.shop_ids = wizard_data['shop_ids'] or []
        
        if self.times =='periods':
            self.start_date = self.pool.get('account.period').browse(self.cr,self.uid,self.get_id('period_id_start')).date_start
            self.end_date   = self.pool.get('account.period').browse(self.cr,self.uid,self.get_id('period_id_start')).date_stop
        elif self.times == 'years':
            self.start_date = self.pool.get('account.fiscalyear').browse(self.cr,self.uid,self.get_id('fiscalyear_start')).date_start
            self.end_date   = self.pool.get('account.fiscalyear').browse(self.cr,self.uid,self.get_id('fiscalyear_start')).date_stop
        elif self.times == 'dates':
            self.start_date = wizard_data['date_start']
            self.end_date   = wizard_data['date_end']
            
        else:
            quarter = wizard_data['quarter'] or False
            year = self.pool.get('account.fiscalyear').browse(self.cr,self.uid,self.get_id('fiscalyear_start')).name
            self.get_quarter_date(year, quarter)
            
        self.showdetail = wizard_data['showdetails'] or False
            
    def get_start_date(self):
        self.get_header()
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
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def show_dauky(self):
        wizard_data = self.localcontext['data']['form']
        self.shop_ids = wizard_data['shop_ids'] and wizard_data['shop_ids'][0] or False
        sql='''
            select 'So du dau ky' as description,                   
                    case when dr_amount > cr_amount then dr_amount - cr_amount
                        else 0 end dr_amount,
                    case when dr_amount < cr_amount then  cr_amount - dr_amount
                        else 0 end cr_amount
                from (
                        select sum(debit) dr_amount, sum(credit) cr_amount
                        from (
                            select aml.debit,aml.credit
                            from account_move amh join account_move_line aml
                                    on amh.id = aml.move_id
                                    and amh.shop_id = ('%(shop_ids)s')
                                    and amh.company_id= '%(company_id)s'
                                    and amh.state = 'posted'
                                    and aml.state = 'valid' and date_trunc('year', aml.date) = date_trunc('year', '%(start_date)s'::date)
                                join account_journal ajn on amh.journal_id = ajn.id and ajn.type = 'situation'
                                join fn_get_account_child_id(%(account_id)s) acc on aml.account_id = acc.id
                            union all
                            select aml.debit,aml.credit
                            from account_move amh join account_move_line aml
                                    on amh.id = aml.move_id
                                    and amh.shop_id = ('%(shop_ids)s')
                                    and amh.company_id= '%(company_id)s'
                                    and amh.state = 'posted'
                                    and aml.state = 'valid' and date(aml.date) between
                                    date(date_trunc('year', '%(start_date)s'::date)) and date('%(start_date)s'::date - 1)
                                join account_journal ajn on amh.journal_id = ajn.id and ajn.type <> 'situation'
                                join fn_get_account_child_id(%(account_id)s) acc on aml.account_id = acc.id
                            )x)y
                    
         '''%({
                  'start_date': self.start_date,
                  'end_date': self.end_date,
                  'shop_ids':self.shop_ids,
                  'company_id':self.company_id,
                  'account_id':self.account_id
          }) 
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_trongky(self):
        res =[]
        sql='''
            SELECT aml.move_id,sum(abs(aml.debit-aml.credit)) sum_cr
                FROM account_move_line aml 
                    JOIN account_move am on am.id = aml.move_id
                WHERE aml.account_id in (SELECT id from fn_get_account_child_id('%(account_id)s'))
                and aml.shop_id = ('%(shop_ids)s')
                and aml.company_id= '%(company_id)s'
                and am.state = 'posted'
                and aml.state = 'valid' and date(aml.date) between '%(start_date)s'::date and '%(end_date)s'::date
                group by aml.move_id,am.date,am.date_document
                order by am.date,am.date_document
        '''%({
                  'start_date': self.start_date,
                  'end_date': self.end_date,
                  'shop_ids':self.shop_ids,
                  'company_id':self.company_id,
                  'account_id':self.account_id
          })
        self.cr.execute(sql)
        for line in self.cr.dictfetchall():
            sql='''
               SELECT sum(abs(aml.debit-aml.credit)) sum_dr
                    FROM account_move_line aml 
                        JOIN account_move am on am.id = aml.move_id
                    WHERE aml.account_id not in (SELECT id from fn_get_account_child_id('%(account_id)s'))
                    and aml.shop_id = ('%(shop_ids)s')
                    and aml.company_id= '%(company_id)s'
                    and am.state = 'posted'
                    and aml.state = 'valid' and date(aml.date) between '%(start_date)s'::date and '%(end_date)s'::date
                    and am.id = %(move_id)s
            '''%({
                      'start_date': self.start_date,
                      'end_date': self.end_date,
                      'shop_ids':self.shop_ids,
                      'company_id':self.company_id,
                      'account_id':self.account_id,
                      'move_id':line['move_id']
              })
            self.cr.execute(sql)
            for i in self.cr.dictfetchall():
                if line['sum_cr'] == i['sum_dr']:    
                    sql='''
                    SELECT  am.date gl_date, coalesce(am.date_document,am.date) doc_date, am.name doc_no, 
                            coalesce(aih.comment, coalesce(avh.narration,
                                coalesce(am.narration, am.ref))) description,acc.code acc_code,                    
                    aml.debit,aml.credit
                    FROM account_move_line aml 
                        JOIN account_move am on am.id = aml.move_id
                        LEFT JOIN account_invoice aih on aml.move_id = aih.move_id -- lien ket voi invoice
                        LEFT JOIN account_voucher avh on aml.move_id = avh.move_id -- lien ket thu/chi
                        LEFT JOIN account_account acc on acc.id = aml.account_id
                    WHERE aml.account_id not in (SELECT id from fn_get_account_child_id('%(account_id)s'))
                    and aml.shop_id = ('%(shop_ids)s')
                    and aml.company_id= '%(company_id)s'
                    and am.state = 'posted'
                    and aml.state = 'valid' and date(aml.date) between '%(start_date)s'::date and '%(end_date)s'::date
                            and am.id = %(move_id)s
                    ORDER BY am.date,am.date_document
                    '''%({
                              'start_date': self.start_date,
                              'end_date': self.end_date,
                              'shop_ids':self.shop_ids,
                              'company_id':self.company_id,
                              'account_id':self.account_id,
                              'move_id':line['move_id']
                      })
                    self.cr.execute(sql)
                    for j in self.cr.dictfetchall():
                        res.append({
                                     'gl_date':j['gl_date'],
                                     'doc_date':j['doc_date'],
                                     'doc_no':j['doc_no'],
                                     'description':j['description'],
                                     'acc_code':j['acc_code'],
                                     'debit':j['credit'] or 0.0,
                                     'credit':j['debit'] or 0.0
                                 })
                else:
                    # truong hop lien ket nhiều nhiều
                    sql='''
                        select row_number() over(order by am.date, am.date_document, am.name)::int seq, 
                            am.date gl_date, coalesce(am.date_document,am.date) doc_date, am.name doc_no, 
                            coalesce(aih.comment, coalesce(avh.narration,
                                coalesce(am.narration, am.ref))) description,
                            case when aml.debit != 0
                                then
                                    array_to_string(ARRAY(SELECT DISTINCT a.code
                                                          FROM account_move_line m2
                                                          LEFT JOIN account_account a ON (m2.account_id=a.id)
                                                          WHERE m2.move_id = aml.move_id
                                                          AND m2.credit != 0.0), ', ') 
                                else
                                    array_to_string(ARRAY(SELECT DISTINCT a.code
                                                          FROM account_move_line m2
                                                          LEFT JOIN account_account a ON (m2.account_id=a.id)
                                                          WHERE m2.move_id = aml.move_id
                                                          AND m2.credit = 0.0), ', ')
                                end acc_code,
                            aml.debit, aml.credit
                        from account_move_line aml
                            join account_move am on aml.move_id=am.id
                            and am.id=%(move_id)s
                            and am.state = 'posted'
                            and aml.state = 'valid'
                            and aml.account_id in (SELECT id from fn_get_account_child_id('%(account_id)s'))
                        left join account_invoice aih on aml.move_id = aih.move_id -- lien ket voi invoice
                        left join account_voucher avh on aml.move_id = avh.move_id -- lien ket thu/chi
                        order by am.date, am.date_document, am.name, acc_code
                     '''%({
                          'move_id':line['move_id'],
                          'account_id':self.account_id,
                      })
                    self.cr.execute(sql)
                    for j in self.cr.dictfetchall():
                        res.append({
                                     'gl_date':j['gl_date'],
                                     'doc_date':j['doc_date'],
                                     'doc_no':j['doc_no'],
                                     'description':j['description'],
                                     'acc_code':j['acc_code'],
                                     'debit':j['debit'] or 0.0,
                                     'credit':j['credit'] or 0.0
                                 })
            
        return res
        
        
    
    def get_sum_trongky(self):
        sql='''
            SELECT 'So phat sinh trong ky'::character varying description,
                    sum(aml.debit) dr_amount, sum(aml.credit) cr_amount
                FROM account_move_line aml
                    join account_move am on aml.move_id=am.id
                    and aml.shop_id = ('%(shop_ids)s')
                    and aml.company_id= '%(company_id)s'
                    and am.state = 'posted'
                    and aml.state = 'valid' and date(aml.date) between '%(start_date)s'::date and '%(end_date)s'::date
                    join fn_get_account_child_id('%(account_id)s') acc on aml.account_id = acc.id
        '''%({
                  'start_date': self.start_date,
                  'end_date': self.end_date,
                  'shop_ids':self.shop_ids,
                  'company_id':self.company_id,
                  'account_id':self.account_id
          })
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_cuoiky(self):
        sql='''
            SELECT 'So du cuoi ky' as description,
                case when dr_amount > cr_amount then dr_amount - cr_amount
                    else 0 end dr_amount,
                case when dr_amount < cr_amount then  cr_amount - dr_amount
                    else 0 end cr_amount
            from (
                    select sum(aml.debit) dr_amount, sum(aml.credit) cr_amount
                    from account_move amh join account_move_line aml 
                            on amh.id = aml.move_id
                            and amh.shop_id = ('%(shop_ids)s')
                            and amh.company_id= '%(company_id)s'
                            and amh.state = 'posted'
                            and aml.state = 'valid' and date(aml.date)
                            between date(date_trunc('year', '%(end_date)s'::date)) and '%(end_date)s'::date
                        join fn_get_account_child_id('%(account_id)s') acc on aml.account_id = acc.id)x 
        '''%({
              'start_date': self.start_date,
              'end_date': self.end_date,
              'shop_ids':self.shop_ids,
              'company_id':self.company_id,
              'account_id':self.account_id
          })
        self.cr.execute(sql)
        return self.cr.dictfetchall()
            
    
    def get_line(self):
        if not self.start_date:
            self.get_header()
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
