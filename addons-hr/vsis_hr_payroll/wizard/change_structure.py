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
import netsvc

class change_structure(osv.osv_memory):
    _name = "change.structure"
    _description = "apply new salary structure for many contract of employee"   
    _columns = {
        'struct_id': fields.many2one('hr.payroll.structure', 'New Salary Structure'),
        'department_id': fields.many2one('hr.department', 'Department'),
        'employee_ids': fields.many2many('hr.employee',
            'change_struct_employee_rel', 'employee_id','change_struct_id',
            'Employee List'),
    }
    
    #===========================================================================
    # change department return list employee in department
    #===========================================================================
    def onchange_department(self, cr, uid, ids, depart): 
        if not depart:
            return
        def get_department(depart_pool, depart_list):
            list_depart_ids = depart_list           
            for depart in depart_list:
                child_id = depart_pool.search(cr, uid, [('parent_id','=', depart)])               
                if not child_id:
                    break
                list_depart_ids.extend(child_id)
                child_id = get_department(depart_pool, child_id)             
            return list_depart_ids
        
        depart_list_ids = get_department(self.pool.get('hr.department'), [depart])

        employee_pool = self.pool.get('hr.employee')
        emp_ids = employee_pool.search(cr, uid, [('department_id','in',depart_list_ids)])
        
        return {'value': {'employee_ids': emp_ids}}
    
    def action_open_window(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids)[0] 
        emp_list = data.employee_ids
        list_contract_ids = []
        contract_pool = self.pool.get('hr.contract')
        employee_pool = self.pool.get('hr.employee')
           
        if not emp_list:
            emp_ids = employee_pool.search(cr, uid, [])
            emp_list = employee_pool.browse(cr, uid, emp_ids)
            
        active_id, = context.get('active_ids', [False])
        for emp in emp_list:                 
            if emp.contract_id: 
                contract_pool.write(cr, uid, emp.contract_id.id, {'struct_id': active_id})
                list_contract_ids.append(emp.contract_id.id)                      
        return {
            'name': 'Changed Salary Structure for Contracts', 
            'view_type': 'form', 
            'view_mode': 'tree,form', 
            'res_model': 'hr.contract', 
            'type': 'ir.actions.act_window', 
            'domain': [('id','in',list_contract_ids)],
        }
#        return {'type': 'ir.actions.act_window_close'} 
change_structure()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

