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
        res_user_obj = pool.get('res.users').browse(cr, uid, uid)
        self.localcontext.update({
            'dated': time.strftime('%d %b %Y'),
            'get_vietname_date':self.get_vietname_date,
            'user': res_user_obj.name,
            'get_vietname_datetime': self.get_vietname_datetime,
            'get_name_head':self.get_name_head,
            'date_done':self.date_done
        })
    def date_done(self,date_done):
        user_pool = self.pool.get('res.users')
        if not date_done:
            date_done = time.strftime(DATETIME_FORMAT)
        
        date_user_tz = user_pool._convert_user_datetime(self.cr, 1, date_done)
        date = date_user_tz.strftime('%Y-%m-%d')
        return date
    def get_name_head(self,object):
        if object['return'] =='none' and object.type == 'in':
            return u'PHIẾU NHẬP KHO (Stock In Receipt)'
        if object['return'] =='none' and object.type == 'out':
            return u'PHIẾU XUẤT KHO (Stock Out Delivery)'
        if object['return'] =='customer' and object.type == 'in':
            return u'PHIẾU NHẬP KHO (Stock In Receipt)'
        if object['return'] =='supplier' and object.type == 'in':
            return u'PHIẾU XUẤT KHO (Stock Out Delivery)'
        
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)        
        return date.strftime('%d-%m-%Y')
    
    def get_vietname_datetime(self, date):
        if not date:
            date = time.strftime(DATETIME_FORMAT)
        date = datetime.strptime(date, DATETIME_FORMAT)        
        return date.strftime('%d-%m-%Y')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
