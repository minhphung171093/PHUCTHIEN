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
        self.context = context
        pool = pooler.get_pool(self.cr.dbname)
        res_user_obj = pool.get('res.users').browse(cr, uid, uid)
        self.localcontext.update({
            'get_date_hd': self.get_date_hd,
            'get_thua_thieu':self.get_thua_thieu,
            'get_baocao_chenhlech': self.get_baocao_chenhlech,
        })
    
    def get_baocao_chenhlech(self):
        return self.pool.get('ir.sequence').get(self.cr, self.uid, 'chenhlech.thuathieu')
    
    def get_date_hd(self,date):
        if date:
            date = date[:10]
            date = datetime.strptime(date, DATE_FORMAT)
            return date.strftime('%m/%Y')
        else:
            return ''

    def get_thua_thieu(self,hethong,thucte,dongia):
        res={}

        if hethong > thucte:
            sl_thieu = hethong - thucte
            tt_thieu = sl_thieu * dongia
            sl_thua = 0
            tt_thua = 0 
        else:
            sl_thua = thucte - hethong
            tt_thua = sl_thua * dongia
            sl_thieu = 0
            tt_thieu = 0 
        res = {
               'sl_thieu':sl_thieu,
               'tt_thieu':tt_thieu,          
               'sl_thua':sl_thua,
               'tt_thua':tt_thua,            
               }
        return res
       

        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
