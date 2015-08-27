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
            'convert_date': self.convert_date,
            'get_chitiet_phongchong_moimot': self.get_chitiet_phongchong_moimot,
        })
    
    
    def convert_date(self, date):
        if date:
            date = datetime.strptime(date, DATE_FORMAT)
            return date.strftime('%d/%m/%Y')
        
    def get_chitiet_phongchong_moimot(self):
        pcmm_obj = self.pool.get('phongchong.moi.mot')
        pcmm_ids = self.context.get('active_ids', [])
        return pcmm_obj.browse(self.cr, self.uid, pcmm_ids)
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
