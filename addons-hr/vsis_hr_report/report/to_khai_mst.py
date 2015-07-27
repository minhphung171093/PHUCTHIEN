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
        self.vat = False
        self.localcontext.update({
            'time': time, 
            'get_nv': self.get_nv,         
        })
    def get_nv(self,o): 
        obj = self.pool.get('hr.employee').browse(self.cr,self.uid,o)
        return obj.last_name and obj.last_name + ' ' + obj.name or obj.name
    

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
