# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################

import pooler
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import fields, osv


class add_template_line(osv.osv_memory):
    _name = "add.template.line"
    _description = "Add Template Line"
    _columns = { 
        'cate_ids': fields.many2many('hr.salary.rule.category',
            'template_cate_rel', 'cate_id','add_id',
            'Category List'),
    }
    
    def action_open_window(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids)[0] 
        cate_list = data.cate_ids        
        template_pool = self.pool.get('hr.template.line')
        active_id, = context.get('active_ids', [False])        
        for cate in cate_list: 
            line = {'name': cate.id, 
                        'template_id': active_id,
                        'sequence': cate.sequence}                                  
            template_pool.create(cr, uid, line)
        return {'type': 'ir.actions.act_window_close'}              

add_template_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

