
# -*- coding: utf-8 -*-

from osv import fields, osv
from tools.translate import _
import time
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from openerp import netsvc

class flag_point_of_sale(osv.osv_memory):
    _name = "flag.point.of.sale"   
    _description = "flag Update"
    
    def update_flag(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if context.get('active_ids'):
            #self.pool.get('pos.order').write(cr,uid,ibs,{'check_flag':True})
            sql='''
                update pos_order set check_flag = True
                    where id in (%s)
            '''%(','.join(map(str,context['active_ids'])))
            cr.execute(sql)
        return True
    
flag_point_of_sale()
    