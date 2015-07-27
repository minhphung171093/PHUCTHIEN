# Embedded file name: D:\Working\Version_7.0\OpenERPV7\addons_hr\vsis_hr_attendance\vsis_hr_attendance.py
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone
import pytz
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp import netsvc

class hr_attendance_late(osv.osv):
    _name = 'hr.attendance.late'
    _order = 'date desc'
    _description = 'Late In Request'
    _columns = {'name': fields.char('Description', size=64, readonly=True, states={'draft': [('readonly', False)]}),
     'employee_id': fields.many2one('hr.employee', 'Employee', required=True, readonly=True, states={'draft': [('readonly', False)]}),
     'state': fields.selection([('draft', 'New'), ('cancel', 'Cancelled'), ('confirm', 'Approve')], 'Status', readonly=True, states={'draft': [('readonly', False)]}),
     'date': fields.date('Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
     'number_of_hours': fields.float('Hours', required=True, readonly=True, states={'draft': [('readonly', False)]})}
    _defaults = {'state': 'draft'}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.employee_id and obj.date:
            name = self.search(cr, uid, [('employee_id', '=', obj.employee_id.id), ('date', '=', obj.date)])
            if name and len(name) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Employee and Date must be unique !', ['name'])]

    def confirm(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'confirm'})

    def cancel(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'cancel'})

    def refuse(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'draft'})


hr_attendance_late()

class hr_attendance_early(osv.osv):
    _name = 'hr.attendance.early'
    _order = 'date desc'
    _description = 'Early Out Request'
    _columns = {'name': fields.char('Description', size=64, readonly=True, states={'draft': [('readonly', False)]}),
     'employee_id': fields.many2one('hr.employee', 'Employee', required=True, readonly=True, states={'draft': [('readonly', False)]}),
     'state': fields.selection([('draft', 'New'), ('cancel', 'Cancelled'), ('confirm', 'Approve')], 'Status', readonly=True, states={'draft': [('readonly', False)]}),
     'date': fields.date('Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
     'number_of_hours': fields.float('Hours', required=True, readonly=True, states={'draft': [('readonly', False)]})}
    _defaults = {'state': 'draft'}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.employee_id and obj.date:
            name = self.search(cr, uid, [('employee_id', '=', obj.employee_id.id), ('date', '=', obj.date)])
            if name and len(name) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Employee and Date must be unique !', ['name'])]

    def confirm(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'confirm'})

    def cancel(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'cancel'})

    def refuse(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'draft'})


hr_attendance_early()

class hr_attendance_overtime(osv.osv):
    _name = 'hr.attendance.overtime'
    _order = 'date desc'
    _description = 'Overtime Request'
    _columns = {'name': fields.char('Description', size=64, readonly=True, states={'draft': [('readonly', False)]}),
     'employee_id': fields.many2one('hr.employee', 'Employee', required=True, readonly=True, states={'draft': [('readonly', False)]}),
     'state': fields.selection([('draft', 'New'), ('cancel', 'Cancelled'), ('confirm', 'Approve')], 'Status', readonly=True, states={'draft': [('readonly', False)]}),
     'date': fields.date('Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
     'number_of_hours': fields.float('Hours', required=True, readonly=True, states={'draft': [('readonly', False)]})}
    _defaults = {'state': 'draft'}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.employee_id and obj.date:
            name = self.search(cr, uid, [('employee_id', '=', obj.employee_id.id), ('date', '=', obj.date)])
            if name and len(name) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Employee and Date must be unique !', ['name'])]

    def confirm(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'confirm'})

    def cancel(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'cancel'})

    def refuse(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'draft'})


hr_attendance_overtime()

class hr_attendance_timesheet(osv.osv):
    _name = 'hr.attendance.timesheet'
    _description = 'Attendance Timesheet'
    _columns = {'name': fields.selection([('approve', 'Approve'), ('invalidtimesheet', 'Invalid Timesheet')], 'Name'),
     'employee_id': fields.many2one('hr.employee', 'Employee', required=True, select=True),
     'date': fields.date('Date', required=True),
     'time_normal': fields.float('Work Hours', store=True),
     'time_ot': fields.float('OT', store=True),
     'time_late': fields.float('Late In', store=True),
     'time_early': fields.float('Early Out', store=True)}


hr_attendance_timesheet

class hr_attendance(osv.osv):
    _inherit = 'hr.attendance'

    def _get_attendance_employee_tz(self, cr, uid, employee_id, date, context = None):
        """ Simulate timesheet in employee timezone
        
        Return the attendance date in string format in the employee
        tz converted from utc timezone as we consider date of employee
        timesheet is in employee timezone
        """
        employee_obj = self.pool['hr.employee']
        tz = False
        if employee_id:
            employee = employee_obj.browse(cr, uid, employee_id, context=context)
            tz = employee.user_id and employee.user_id.partner_id.tz or False
        if not date:
            date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        att_tz = timezone(tz or 'utc')
        attendance_dt = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT)
        att_tz_dt = pytz.utc.localize(attendance_dt)
        att_tz_dt = att_tz_dt.astimezone(att_tz)
        att_tz_date_str = datetime.strftime(att_tz_dt, DEFAULT_SERVER_DATE_FORMAT)
        return att_tz_date_str


hr_attendance()