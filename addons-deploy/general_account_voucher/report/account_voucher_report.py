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
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        
        self.journal_voucher_id = context.get('active_id',False)
        self.bank_name = ''
        self.bank_state = ''
        self.acc_number = ''
        
        self.bank_names = ''
        self.bank_states = ''
        self.acc_numbers = ''
        
        self.code_cr = ''
        self.code_dr = ''
        self.localcontext.update({
            'get_qty': self.get_qty,
            'get_vietname_date':self.get_vietname_date,
            'amount_to_text':self.amount_to_text,
            'get_string_date':self.get_string_date,
            'get_account': self.get_account,
            'get_account_cr':self.get_account_cr,
            'get_account_dr':self.get_account_dr,
            'get_amount':self.get_amount,
            'get_round':self.get_round,
            'get_account_own':self.get_account_own,
            'get_user_name':self.get_user_name,
            'get_acc_numbers':self.get_acc_numbers,
            'bank_statess':self.bank_statess,
            
            'get_bank_name':self.get_bank_name,
            'get_bank_state':self.get_bank_state,
            'get_bank_names':self.get_bank_names,
            'get_account_drs':self.get_account_drs,
            'get_account_crs':self.get_account_crs,
        })
    
    def get_banks(self):
        obj = self.pool.get('print.account.voucher.report').browse(self.cr,self.uid,self.journal_voucher_id)
        if obj:
            self.acc_numbers = obj.bank_id.acc_number
            self.bank_names = obj.bank_id.bank_name
            self.bank_states = obj.bank_id.state_id and obj.bank_id.state_id.name or ''
        
    def get_bank_names(self):
        if not self.bank_names:
            self.get_banks()
        return self.bank_names
    
    def get_acc_numbers(self):
        if not self.acc_numbers:
            self.get_banks()
        return self.acc_numbers
    
    def bank_statess(self):
        if not self.bank_states:
            self.get_banks()
        return self.bank_states
    
    def get_user_name(self):
        user = self.pool.get('res.users').browse(self.cr,self.uid,self.uid)
        return user.name
        
    def get_qty(self,order_line):
        sumqty =0
        for line in order_line:
            sumqty += line.product_qty
        return sumqty
    
    def get_account_own(self,partner_id):
        for bank in partner_id.bank_ids:
            return bank.owner_name
        return False
        
    def get_round(self,amount):
        return round(amount,0)
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
            
    def amount_to_text(self, nbr, lang='vn', currency='USD'):
        user = self.pool.get('res.users')
        return user.amount_to_text(nbr, lang, currency)
    
    def get_string_date(self,date):
        if not date:
            date = time.strftime(DATE_FORMAT)
            
        date = datetime.strptime(date, DATE_FORMAT)
        month = date.strftime('%m')
        day  = date.strftime('%d')
        year = date.strftime('%Y')
        chuoi = 'Ngay ' + str(day) + ' thang ' + str(month) + ' nam ' + str(year)
        return chuoi
    
    
    def get_account_crs(self,o):
        crs =[]
        Fag =1
        code = ''
        for i in o.move_ids:
            if i.account_id.id != o.account_id.id:
                crs.append(i.account_id.code)
        for i in crs:
            if Fag !=1:
                code = code + ' ,'
            code = code + str(i)
            Fag =Fag+1
        return code
                
    def get_account_cr(self):
        return self.code_cr
     
    def get_account_dr(self):
        return self.code_dr
         
    
    def get_account(self, move_ids, voucher):
        account_ids = []
        if voucher.partner_id and voucher.partner_id.property_account_receivable:
            account_ids.append(voucher.partner_id.property_account_receivable.id)
        if voucher.partner_id and voucher.partner_id.property_account_payable:
            account_ids.append(voucher.partner_id.property_account_payable.id)
        if voucher.journal_id.default_debit_account_id:
            account_ids.append(voucher.journal_id.default_debit_account_id.id)
        if voucher.journal_id.default_credit_account_id:
            account_ids.append(voucher.journal_id.default_credit_account_id.id)
        
        #Get Account Transaction
        for line in voucher.line_dr_ids:
                if line.account_id:
                    account_ids.append(line.account_id.id)
        for line in voucher.line_cr_ids:
            if line.account_id:
                account_ids.append(line.account_id.id)
                    
        for move in move_ids:
            if move.debit and move.account_id.id in account_ids:
                self.code_dr = move.account_id.code + ', '
            if move.credit and move.account_id.id in account_ids:
                self.code_cr = move.account_id.code + ', '
        if self.code_dr:
            self.code_dr = self.code_dr[:-2]
        if self.code_cr:
            self.code_cr = self.code_cr[:-2]
        return True
    
    def get_amount(self,obj):
        amount = 0.0
        for i in obj.voucher_lines:
            amount = amount + i.amount
        return amount
    
    def get_account_drs(self,obj):
        account_code =[]
        Fag =1
        code = ''
        for i in obj.voucher_lines:
            for j in i.line_dr_ids:
                if j.account_id.code not in account_code:
                    account_code.append(j.account_id.code)
        for i in account_code:
            if Fag !=1:
                code = code + ' ,'
            code = code + str(i)
            Fag =Fag+1
        return code
    
    def get_bank_name(self,partner_id,partner_bank_id):
        if not self.bank_name:
            self.get_bank(partner_id, partner_bank_id)
        return self.bank_name
    
    def get_bank_state(self,partner_id,partner_bank_id):
        if not self.bank_state:
            self.get_bank(partner_id, partner_bank_id)
        return self.bank_state
    
    
    def get_bank(self,partner_id,partner_bank_id):
        res=[]
        if partner_bank_id:
            self.bank_name = partner_bank_id.bank_name,
            self.bank_state = partner_bank_id.state_id and partner_bank_id.state_id.name or ''
        else:
            self.bank_name = partner_id.bank_ids and partner_id.bank_ids[0].bank_name or '',
            self.bank_state = partner_id.bank_ids and partner_id.bank_ids[0].state_id and partner_id.bank_ids[0].state_id.name or ''
        return res
    
#    
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
