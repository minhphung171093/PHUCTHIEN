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
            'get_family': self.get_family,
            'get_name': self.get_name,         
        })
    def get_name(self,o):
        return o.last_name and o.last_name + ' ' + o.name_related or o.name_related
    
    def get_family(self,o):
        result = []
        family = o.family_ids 
        stt = 0
        if family:
            for f in family:
                stt +=1
                dic = {
                       'stt': stt,
                       'name': f.name or '', 
                       'address': f.address_id and f.address_id.name or '',
                       'home_address_id': f.address_home_id and f.address_home_id.name or '',
                       'phone': f.phone or '',
                       'email': f.email or '',
                       'rel':f.rel_id and f.rel_id.name or '',
                       'birthday': f.birthday and time.strftime('%d/%m/%Y', time.strptime(f.birthday, '%Y-%m-%d')) or '',
                       'id_no': f.id_no or '',
                       'tax_code': f.tax_code or '',
                }
                result.append(dic)
        return result 
    

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
