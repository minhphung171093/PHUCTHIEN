# -*- coding: utf-8 -*-
##############################################################################
#
#    HLVSolution, Open Source Management Solution
#
##############################################################################

import time
import datetime
from report import report_sxw
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
import amount_to_text_en
import amount_to_text_vn
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        
        self.account_voucher_type = context.get('account_voucher_type',False)
        self.journal_voucher_id = context.get('active_id',False)
        pool = pooler.get_pool(self.cr.dbname)
        self.bank_name = False
        self.bank_state = False
        self.acc_number = False
        
        self.bank_names = False
        self.bank_states = False
        self.acc_numbers = False
        
        self.code_cr = False
        self.code_dr = False
        self.localcontext.update({
            'get_vietname_date':self.get_vietname_date,
            'get_string_date':self.get_string_date,
            'get_user': self.get_user,
            'get_acc_numbers': self.get_acc_numbers,
            'amount_to_text': self.amount_to_text,
            'get_amount_all': self.get_amount_all,
        })
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def amount_to_text(self, nbr, lang='vn', currency='USD'):
        if lang == 'vn':
            return  amount_to_text_vn.amount_to_text(nbr, lang)
        else:
            return amount_to_text_en.amount_to_text(nbr, 'en', currency)
    
    def get_string_date(self,date):
        if not date:
            date = time.strftime(DATE_FORMAT)
            
        date = datetime.strptime(date, DATE_FORMAT)
        month = date.strftime('%m')
        day  = date.strftime('%d')
        year = date.strftime('%Y')
        chuoi = u'Ngày ' + str(day) + u' tháng ' + str(month) + u' năm ' + str(year)
        return chuoi
    
    def amount_to_text(self, nbr, lang='vn', currency='USD'):
        if lang == 'vn':
            return  amount_to_text_vn.amount_to_text(nbr, lang)
        else:
            return amount_to_text_en.amount_to_text(nbr, 'en', currency)
        
    def get_user(self):
        company = self.pool.get('res.company').browse(self.cr,self.uid,self.uid)
        return company.name
    
    def get_acc_numbers(self,o):
        for line in o.company_id.bank_ids:
            return line.acc_number
        return False
    
    def get_amount_all(self,o):
        val = 0.0
        for line in o.voucher_lines:
            val += line.amount
        return val
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
