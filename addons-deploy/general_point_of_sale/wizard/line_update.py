
# -*- coding: utf-8 -*-

from osv import fields, osv
from tools.translate import _
import time
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from openerp import netsvc

class line_point_of_sale(osv.osv_memory):
    _name = "line.point.of.sale"   
    _description = "Update Status"
    
    def update_line_check(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if context.get('active_ids'):
            sql='''
                update pos_order_line set check_flag = True
                    where id in (%s)
            '''%(','.join(map(str,context['active_ids'])))
            cr.execute(sql)
        return True
    
line_point_of_sale()
    