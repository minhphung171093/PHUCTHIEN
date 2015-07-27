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
        pool = pooler.get_pool(self.cr.dbname)
        self.sum_debit = 0
        self.sum_credit = 0
        self.localcontext.update({
            'get_vietname_date':self.get_vietname_date, 
            'amount_to_text':self.amount_to_text,
            'get_string_date':self.get_string_date,
            'get_total_debit':self.get_total_debit,
        })
    
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        strng = date.strftime('%d %m %Y')
        return date.strftime('%d/%m/%Y')
    
    
    def get_total_debit(self,move_line):
        self.sum_debit = 0
        if not move_line:
            return ''
        for line in move_line:
            self.sum_debit  += line.debit
        res = {
             'debit'  :self.sum_debit,
             'credit' :self.sum_debit
             }
        return res
    
    def amount_to_text(self,  lang='vn', currency='USD'):
        if lang == 'vn':
            return  amount_to_text_vn.amount_to_text(self.sum_debit, lang)
        else:
            return amount_to_text_en.amount_to_text(self.sum_debit, 'en', currency)
    
    def get_string_date(self,date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        month = date.strftime('%m')
        day  = date.strftime('%d')
        year = date.strftime('%Y')
        chuoi = u'Ngày ' + str(day) + u' tháng ' + str(month) + u' năm ' + str(year)
        return chuoi
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
