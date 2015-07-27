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
        pool = pooler.get_pool(self.cr.dbname)
        self.sott = 0        
        self.val_col = []
        self.list_product = []
        
        self.localcontext.update({
            'time': time,
            'convert':self.convert,
            'get_department':self.get_department,
            'get_payslip_lines': self.get_payslip_lines,
            'get_payslip_time': self.get_payslip_time,
            'get_history': self.get_history,
        })
    
    def convert(self,amount):
        amt_vn = amount_to_text_vn.amount_to_text_vn(amount,'VND');
        return amt_vn
    
    def get_job(self,payslip_id):
        job =  self.pool.get('hr.payslip').browse(self.cr,self.uid,payslip_id)
        if job:
            return job.employee_id and \
                    (job.employee_id.job_id and \
                     job.employee_id.job_id.name or None )or ''
    
    def get_department(self,payslip_id):
        job =  self.pool.get('hr.payslip').browse(self.cr,self.uid,payslip_id)
        if job:
            return job.employee_id and \
                    (job.employee_id.department_id and \
                     job.employee_id.department_id.name or None )or ''
                     
    def get_payslip_lines(self, obj):
        bhxh =  0,
        bhyt =  0,
        bhtn =  0,
        com =  0,
        tx = 0,
        dt =  0,
        tncn = 0, 
        net = 0,
        ltc = 0, 
        ltg = 0,  
        
        if len(obj.line_ids):
            for line in obj.line_ids:
                if line.code == 'BHXH':
                    bhxh = line.amount
                if line.code == 'BHYT':
                    bhyt = line.amount
                if line.code == 'BHTN':
                    bhtn = line.amount
                if line.code == 'PCTC':
                    com = line.amount 
                if line.code == 'PCX':
                    tx = line.amount
                if line.code == 'PCDT':
                    dt = line.amount
                if line.code == 'NET':
                    net = line.amount
                if line.code == 'TNCN':
                    tncn = line.amount
                if line.code == 'LTC':
                    ltc = line.amount
                if line.code == 'LTG':
                    ltg = line.amount
                
            dic = {
                    'bhxh': bhxh or 0,
                    'bhyt': bhyt or 0,
                    'bhtn': bhtn or 0,
                    'com':  com or 0,
                    'tx': tx or 0,
                    'dt': dt or 0,
                    'tncn': tncn or 0, 
                    'net': net or 0,
                    'ltc': ltc or 0,
                    'ltg': ltg or 0,
            }
             
        else:
            dic = {
                    'bhxh': '',
                    'bhyt': '',
                    'bhtn': '',
                    'com': '',
                    'tx': '',
                    'dt': '',
                    'tncn': '',
                    'net': '', 
                    'ltc': '', 
                    'ltg': '',
            }
        return dic
    
    
    def get_payslip_time(self, obj):
        ot_150 = 0
        ot_200 = 0
        ot_300 = 0
        ot_normal = 0
        ot_w100 = 0
        paid = 0
        unpaid = 0
        annual = 0
        if len(obj.worked_days_line_ids):
            for  l in obj.worked_days_line_ids:
                if l.code == 'TIME_OT150':
                    ot_150 = l.number_of_days
                if l.code == 'TIME_OT200':
                    ot_200  = l.number_of_days
                if l.code == 'TIME_OT300':
                    ot_300 = l.number_of_days
                if l.code  == 'TIME_NORMAL':
                    ot_normal = l.number_of_days
                if l.code == 'WORK100':
                    ot_w100 = l.number_of_days
                if l.code == 'PAID_LEAVE':
                    paid = l.number_of_days
                if l.code == 'UNPAID_LEAVE':
                    unpaid = l.number_of_days
                if l.code == 'ANNUAL_LEAVE_2013':
                    annual = l.number_of_days
            dic = {
                    'ot_150' : ot_150 ,
                    'ot_200' : ot_200,
                    'ot_300' : ot_300 ,                      
                    'ot_normal': ot_normal,
                    'ot_w100' : ot_w100,
                    'paid' : paid ,                      
                    'unpaid': unpaid,
                    'annual' : annual,
                }        
        else:
            dic = {
                    'ot_150' : '' ,
                    'ot_200' : '',
                    'ot_300' : '' ,                      
                    'ot_normal': '',
                    'ot_w100' : '',
                    'paid' : '' ,                      
                    'unpaid': '',
                    'annual' : '',
                }      
        return dic  
          
    def get_history(self,obj):
        result = []
        net = 0
        if not obj:
            return []
        if len(obj.p_payslips)>0:
            for h in obj.p_payslips:
                for s in h.line_ids:
                    if s.code == 'NET':
                        net = s.total or 0
                        break
                dic = {
                       'name': h.number or '',
                       'date_from': h.date_from and time.strftime('%d/%m/%Y', time.strptime(h.date_from, '%Y-%m-%d')) or '',
                       'date_to': h.date_to and time.strftime('%d/%m/%Y', time.strptime(h.date_to, '%Y-%m-%d')) or '',
                       'net': net
                }
                result.append(dic)
        return result
   
        
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
