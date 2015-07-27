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
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.account_id =False
        self.account_code = False
        self.account_name = False
        self.start_date = False
        self.end_date = False
        self.partner_id = False
        self.partner_name = False
        
        self.company_name = False
        self.company_address = False
        self.vat = False
        self.total_residual = 0
        self.type = False
        
        self.localcontext.update({
            'get_vietname_date':self.get_vietname_date, 
            'get_header':self.get_header,
            'get_account_code':self.get_account_code,
            'get_account_name':self.get_account_name,
            'get_start_date':self.get_start_date,
            'get_end_date':self.get_end_date,
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_company_vat':self.get_company_vat,
            'get_line':self.get_line,
            'get_total_residual':self.get_total_residual,
            'get_total_line':self.get_total_line,
            
        })
    
    def get_total_residual(self):
        return self.total_residual
    
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
    
    def get_account_name(self):
        if not self.account_code:
            self.get_account()
        return self.account_name
    
    def get_account_code(self):
        if not self.account_code:
            self.get_account()
        return self.account_code
        
    def get_id(self,get_id):
        wizard_data = self.localcontext['data']['form']
        period_id = wizard_data[get_id][0] or wizard_data[get_id][0] or False
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
        
        if self.times =='periods':
            self.start_date = self.pool.get('account.period').browse(self.cr,self.uid,self.get_id('period_id_start')).date_start
            self.end_date   = self.pool.get('account.period').browse(self.cr,self.uid,self.get_id('period_id_end')).date_stop
            
        elif self.times == 'years':
            self.start_date = self.pool.get('account.fiscalyear').browse(self.cr,self.uid,self.get_id('fiscalyear_start')).date_start
            self.end_date   = self.pool.get('account.fiscalyear').browse(self.cr,self.uid,self.get_id('fiscalyear_stop')).date_stop
        else:
            self.start_date = wizard_data['date_start']
            self.end_date = wizard_data['date_end']
    
    def get_start_date(self):
        if not self.start_date:
            self.get_header()
        return self.get_vietname_date(self.start_date) 
    
    def get_end_date(self):
        if not self.end_date:
            self.get_header()
        return self.get_vietname_date(self.end_date) 
    
    def get_account(self):
        wizard_data = self.localcontext['data']['form']
        self.account_id = wizard_data['account_id']
        if self.account_id:
            sql ='''
                select id,code,name from account_account where id = %s
            '''%(self.account_id)
            self.cr.execute(sql)
            
            for line in self.cr.dictfetchall():
                self.account_code = line['code']
                self.account_name = line['name']
        
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_total_line(self):
        res = self.pool.get('sql.partner.ledger.detail').get_total_line(self.cr, self.start_date,self.end_date,self.account_id)
        return res
    
    def get_line(self):
        res = self.pool.get('sql.partner.ledger.detail').get_line(self.cr, self.start_date,self.end_date,self.account_id)
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
