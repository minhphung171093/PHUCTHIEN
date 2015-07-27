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

class change_history(osv.osv_memory):
    _name = "change.history"
    _description = "apply new basic salary history"   
    _columns = {
#        'department_id': fields.many2one('hr.department', 'Department'),
#        'employee_ids': fields.many2many('hr.employee',
#            'change_company_basic_employee_rel', 'employee_id','company_basic_struct_id',
#            'Employee List'),
    }
    
    #===========================================================================
    # change department return list employee in department
    #===========================================================================

    
    def action_open_window(self, cr, uid, ids, context=None):
#        data = self.browse(cr, uid, ids)[0] 
#        emp_list = data.employee_ids                
        basic_pool = self.pool.get('hr.basic.company')
        his_pool = self.pool.get('hr.salary.history')
                     
        active_id, = context.get('active_ids', [False])
        
        list_history_ids = his_pool.search(cr, uid, [('basic_company_id','=', active_id)]) 
        
        if not list_history_ids:
            basic = basic_pool.browse(cr, uid, active_id)
            for emp in basic.employee_ids:                                    
                if emp.contract_id: 
                    lastest_his_line_id = his_pool.search(cr, uid, [('contract_id','=',emp.contract_id.id)])
                    lastest_his_line = his_pool.browse(cr, uid, lastest_his_line_id[0])
                    line = {'date' : basic.date_start,                        
                            'contract_id': emp.contract_id.id,
                            'scale_id': lastest_his_line.scale_id.id,        
                            'grade_id': lastest_his_line.grade_id.id, 
                            'total_wage': lastest_his_line.grade_id.ratio and lastest_his_line.incentive_wage + basic.name*lastest_his_line.grade_id.ratio or lastest_his_line.incentive_wage + basic.name}                              
                    line_id = his_pool.create(cr, uid, line)
                    list_history_ids.append(line_id)
        else:
            basic = basic_pool.browse(cr, uid, active_id)
            for emp in basic.employee_ids:                                    
                if emp.contract_id: 
                    lastest_his_line_id = his_pool.search(cr, uid, [('contract_id','=',emp.contract_id.id)])
                    sql = '''select max(id) 
                            from hr_salary_history 
                            where contract_id = %s'''%(emp.contract_id.id)
                    cr.execute(sql)
                    kq = cr.fetchall()
                    lastest_his_line = his_pool.browse(cr, uid, kq[0][0])
                    line = {'date' : basic.date_start,                        
                            'contract_id': emp.contract_id.id,
                            'scale_id': lastest_his_line.scale_id.id,        
                            'grade_id': lastest_his_line.grade_id.id, 
                            'total_wage': lastest_his_line.grade_id.ratio and lastest_his_line.incentive_wage + basic.name*lastest_his_line.grade_id.ratio or lastest_his_line.incentive_wage + basic.name}                              
                    line_id = his_pool.create(cr, uid, line)
                    list_history_ids.append(line_id)
                                              
        return {
            'name': 'New Salary History', 
            'view_type': 'form', 
            'view_mode': 'tree,form', 
            'res_model': 'hr.salary.history', 
            'type': 'ir.actions.act_window', 
            'domain': [('id','in',list_history_ids)],
        }           
         
change_history()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

