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


class change_calendar(osv.osv_memory):
    _name = "change.calendar"
    _description = "Change calendar for employee"
    _columns = {
#        'calendar_id': fields.many2one('resource.calendar', 'Working Calendar'),
        'cate_id': fields.many2one('hr.employee.category', 'Category'),
        'department_id': fields.many2one('hr.department', 'Department'),
        'employee_ids': fields.many2many('hr.employee',
            'change_calendar_employee_rel', 'employee_id','change_calendar_id',
            'Employee List'),
    }
    
    #===========================================================================
    # change category return list employee in department
    #===========================================================================
    def onchange_category(self, cr, uid, ids, category): 
        if not category:
            return
        def get_category(category_pool, category_list):
            list_category_ids = category_list           
            for category in category_list:
                child_id = category_pool.search(cr, uid, [('parent_id','=', category)])               
                if not child_id:
                    break
                list_category_ids.extend(child_id)
                child_id = get_category(category_pool, child_id)             
            return list_category_ids
        
        category_list_ids = get_category(self.pool.get('hr.employee.category'), [category])

        employee_pool = self.pool.get('hr.employee')
        emp_ids = employee_pool.search(cr, uid, [('category_ids','child_of',category_list_ids)])
        
        return {'value': {'employee_ids': emp_ids}}
    
    def action_open_window(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids)[0] 
        emp_list = data.employee_ids
        emp_ids = [x.id for x in emp_list]
        employee_pool = self.pool.get('hr.employee')
        if not emp_list:
            emp_ids = employee_pool.search(cr, uid, [])
        
        active_id, = context.get('active_ids', [False])                          
        employee_pool.write(cr, uid, emp_ids, {'calendar_id': active_id})
        return {'type': 'ir.actions.act_window_close'}              
#        return {
#            'name': 'Working Calendar', 
#            'view_type': 'form', 
#            'view_mode': 'tree,form', 
#            'res_model': 'resource.calendar', 
#            'type': 'ir.actions.act_window', 
#            'domain': [('id','=',active_id)],
#        }
change_calendar()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

