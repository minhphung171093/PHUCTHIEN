# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from osv import fields, osv
from tools.translate import _

def daterange( start_date, end_date ):
    if start_date <= end_date:
        for n in range( ( end_date - start_date ).days + 1 ):
            yield start_date + timedelta( n )
    else:
        for n in range( ( start_date - end_date ).days + 1 ):
            yield start_date - timedelta( n )

class hr_timesheet_status(osv.osv):
    _name = "hr.timesheet.status"
    _description = "Timesheet Status"

    _columns = {
        'name': fields.char('Code', size=2, required=True, help="Programing code. Please do not change"),
        'description': fields.char('Description', size=64, required=True, translate=True),
    }

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The code of the status must be unique!'),
    ]

hr_timesheet_status()

class hr_timesheet_line(osv.osv):
    _inherit = "hr.analytic.timesheet"
    def _sheet(self, cursor, user, ids, name, args, context=None):
        sheet_obj = self.pool.get('hr_timesheet_sheet.sheet')
        res = {}.fromkeys(ids, False)
        for ts_line in self.browse(cursor, user, ids, context=context):
            sheet_ids = sheet_obj.search(cursor, user,
                [('date_to', '>=', ts_line.date), ('date_from', '<=', ts_line.date),
                 ('employee_id.user_id', '=', ts_line.user_id.id)],
                context=context)
            if sheet_ids:
            # [0] because only one sheet possible for an employee between 2 dates
                res[ts_line.id] = sheet_obj.name_get(cursor, user, sheet_ids, context=context)[0]
        return res

    def _get_hr_timesheet_sheet(self, cr, uid, ids, context=None):
        ts_line_ids = []
        for ts in self.browse(cr, uid, ids, context=context):
            cr.execute("""
                    SELECT l.id
                        FROM hr_analytic_timesheet l
                    INNER JOIN account_analytic_line al
                        ON (l.line_id = al.id)
                    WHERE %(date_to)s >= al.date
                        AND %(date_from)s <= al.date
                        AND %(user_id)s = al.user_id
                    GROUP BY l.id""", {'date_from': ts.date_from,
                                        'date_to': ts.date_to,
                                        'user_id': ts.employee_id.user_id.id,})
            ts_line_ids.extend([row[0] for row in cr.fetchall()])
        return ts_line_ids

    def _get_account_analytic_line(self, cr, uid, ids, context=None):
        ts_line_ids = self.pool.get('hr.analytic.timesheet').search(cr, uid, [('line_id', 'in', ids)])
        return ts_line_ids
    def _day_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, '')
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = obj.date
        return res
    
    def _month_compute(self, cr, uid, ids, fieldnames, args, context=None):
        res = dict.fromkeys(ids, '')
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = time.strftime('%Y-%m', time.strptime(obj.date, '%Y-%m-%d'))
        return res
    
    _columns = {
        'sheet_id': fields.function(_sheet, string='Sheet', type='many2one', relation='hr_timesheet_sheet.sheet', ondelete="cascade", store={
                                            'hr_timesheet_sheet.sheet': (_get_hr_timesheet_sheet, ['employee_id', 'date_from', 'date_to'], 10),
                                            'account.analytic.line': (_get_account_analytic_line, ['user_id', 'date'], 10),
                                            'hr.analytic.timesheet': (lambda self,cr,uid,ids,context=None: ids, None, 10),
          },),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'timesheet_status': fields.many2one('hr.timesheet.status', 'Status'),
        'day': fields.function(_day_compute, type='char', string='Day', store=True, select=1, size=32),
        'month': fields.function(_month_compute, type='char', string='Month', store=True, select=1, size=32),
        'department': fields.related('employee_id', 'department_id','name', type='char', string='Department', store=True, readonly=True)
    }
hr_timesheet_line()

class hr_timesheet_sheet(osv.osv):
    _inherit = "hr_timesheet_sheet.sheet"

    _columns = {
        'date_from': fields.date('Date from', required=True, select=1, readonly=True, states={'new':[('readonly', False)],'draft':[('readonly', False)]}),
        'date_to': fields.date('Date to', required=True, select=1, readonly=True, states={'new':[('readonly', False)],'draft':[('readonly', False)]}),
    }

    # return [ivf_id,default_analytic_account_id]
    def get_default_analytic_account(self, cr, uid, code, context=None):
        ivfobj = self.pool.get('hr_timesheet_invoice.factor')
        ivf_ids = ivfobj.search(cr, uid, [('customer_name','=',code)], context=context)
        res = False
        if ivf_ids:
            ivf = ivfobj.browse(cr, uid, ivf_ids[0], context=context)
            res = [ivf_ids[0],ivf.default_analytic_account and ivf.default_analytic_account.id or False]
        return res

    def check_employee_attendance_state(self, cr, uid, sheet_id, context=None):
        # needn't check here
        return True
    
    # Hung moi sua ham _sheet_date de co the cham nhieu phong ban cung 1 nguoi truong phong    
    def _sheet_date(self, cr, uid, ids, forced_department_id = False, context=None):
        for sheet in self.browse(cr, uid, ids, context=context):
            department_id = forced_department_id or sheet.department_id and sheet.department_id.id
            if not department_id:
                department_id = sheet.employee_id.department_id and sheet.employee_id.department_id.id or False
            if department_id:
                cr.execute('''SELECT  id 
                              FROM hr_timesheet_sheet_sheet 
                              WHERE (date_from >= %s  and date_to <= %s ) 
                                AND department_id = %s 
                                AND id <> %s ''', (sheet.date_from, sheet.date_to, department_id , sheet.id ))
                if cr.fetchall():
                    return False
        return True
    _constraints = [
        (_sheet_date, 'You cannot have 2 timesheets that overlap!\nPlease use the menu \'My Current Timesheet\' to avoid this problem.', ['date_from','date_to']),
    ]
    
    def create(self, cr, uid, vals, *args, **argv):
        if 'department_id' in vals:
            ids_employee = self.pool.get('hr.employee').search(cr, uid, [('department_id','=', vals['department_id'])])
            if ids_employee and not self.pool.get('hr.employee').browse(cr, uid, ids_employee[0]):
                 raise osv.except_osv(_('Error!'), _('In order to create a timesheet for this employee, you must assign it to a department.'))
            if ids_employee and not self.pool.get('hr.employee').browse(cr, uid, ids_employee[0]).product_id:
                raise osv.except_osv(_('Error!'), _('In order to create a timesheet for this employee, you must link the employee to a product, like \'Consultant\'.'))
            if ids_employee and not self.pool.get('hr.employee').browse(cr, uid, ids_employee[0]).journal_id:
                raise osv.except_osv(_('Configuration Error!'), _('In order to create a timesheet for this employee, you must assign an analytic journal to the employee, like \'Timesheet Journal\'.'))
        return super(osv.osv, self).create(cr, uid, vals, *args, **argv)
    
    def write(self, cr, uid, ids, vals, *args, **argv):        
        if 'department_id' in vals:            
            new_department_id = vals['department_id'] or False
            if not new_department_id:
                raise osv.except_osv(_('Error!'), _('In order to create a timesheet for this employee, you must assign it to a department.'))
            if not self._sheet_date(cr, uid, ids, forced_department_id = new_department_id):
                raise osv.except_osv(_('Error!'), _('You cannot have 2 timesheets that overlap!\nYou should use the menu \'My Timesheet\' to avoid this problem.'))
            ids_employee = self.pool.get('hr.employee').search(cr, uid, [('department_id','=', vals['department_id'])])
            if ids_employee and not self.pool.get('hr.employee').browse(cr, uid, ids_employee[0]).product_id:
                raise osv.except_osv(_('Error!'), _('In order to create a timesheet for this employee, you must link the employee to a product.'))
            if ids_employee and not self.pool.get('hr.employee').browse(cr, uid, ids_employee[0]).journal_id:
                raise osv.except_osv(_('Configuration Error!'), _('In order to create a timesheet for this employee, you must assign an analytic journal to the employee, like \'Timesheet Journal\'.'))
        
        return super(osv.osv, self).write(cr, uid, ids, vals, *args, **argv)

#    
hr_timesheet_sheet()

class hr_timesheet_invoice_factor(osv.osv):
    _inherit = "hr_timesheet_invoice.factor"
    _columns = {
        'default_analytic_account': fields.many2one('account.analytic.account', 'Default Analytic Account'),
    }

hr_timesheet_invoice_factor()
