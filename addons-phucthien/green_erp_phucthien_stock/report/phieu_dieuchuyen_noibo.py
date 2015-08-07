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
            'get_dieuchuyen_thanhpham_lanh': self.get_dieuchuyen_thanhpham_lanh,
            'get_dieuchuyen_thanhpham': self.get_dieuchuyen_thanhpham,
        })
        
    def get_dieuchuyen_thanhpham_lanh(self):
        return self.pool.get('ir.sequence').get(self.cr, self.uid, 'dieuchuyen.thanhpham.lanh')
    
    def get_dieuchuyen_thanhpham(self):
        return self.pool.get('ir.sequence').get(self.cr, self.uid, 'dieuchuyen.thanhpham')
    
    def get_date_hd(self,date):
        if date:
            date = date[:10]
            date = datetime.strptime(date, DATE_FORMAT)
            return date.strftime('%m/%Y')
        else:
            return ''
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
