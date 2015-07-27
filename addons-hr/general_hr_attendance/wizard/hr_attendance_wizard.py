#import wizard
import netsvc
import time
import pooler
from tools import config
from osv import osv, fields
#from mx import DateTime
from datetime import date, datetime, timedelta
from tools.translate import _    

from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


class vsis_hr_attendance_wizard(osv.osv_memory):
    _name = 'hr.attendance.wizard'
    _columns = {
                'date_from': fields.date('Date From'),
                'date_to': fields.date('Date To'),
                'employee_ids': fields.many2many('hr.employee','attendance_wizard_employee_ref', 'attendance_wizard_id', 'employee_id', 'Employee', required=True),
    }
    
    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-01'),
        'date_to': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
    }  
    
    def compute_attendance_timesheet(self, cr, uid, ids, context=None):
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        hr_attendance_obj = self.pool.get('hr.attendance')
        hr_overtime_obj = self.pool.get('hr.overtime')
        hr_late_in_obj = self.pool.get('hr.attendance.late')
        hr_early_out_obj = self.pool.get('hr.attendance.early')
        hr_attendance_timesheet_obj = self.pool.get('hr.attendance.timesheet')
        for attendance_wizard_id in self.browse(cr, uid, ids, context=context):
            if not attendance_wizard_id.employee_ids or not attendance_wizard_id.date_from or not attendance_wizard_id.date_to:
                raise osv.except_osv(_('Warning!'), _('Please Input.')) 
            date_from = attendance_wizard_id.date_from
            date_to = attendance_wizard_id.date_to
            hr_attendance_timesheet_ids = hr_attendance_timesheet_obj.search(cr, uid, [('date', '>=', date_from), ('date', '<=', date_to)], context=context)
            if hr_attendance_timesheet_ids:
                hr_attendance_timesheet_obj.unlink(cr, uid, hr_attendance_timesheet_ids, context=context)    
            for emp in attendance_wizard_id.employee_ids:
                list_day_emp = []
                list_signin = []
                list_signout = []
                employee_id = emp.id
                shift_id = emp.calendar_id and emp.calendar_id.attendance_ids[0].shift_id or False
                if not shift_id:
                    raise osv.except_osv(_('Warning!'), _('Please select working time in %s !'% emp.name)) 
                list_attendance_emp = hr_attendance_obj.search(cr, uid, [('employee_id', '=', employee_id), ('day', '>=', date_from), ('day', '<=', date_to)], context=context)
                for attendance_emp_id in hr_attendance_obj.browse(cr, uid, list_attendance_emp, context=context):
                    list_day_emp.append(attendance_emp_id.day[:10])
                list_day_emp = list(set(list_day_emp))
                # duyet tung ngay lam viec de lay list in/out
                for day in sorted(list_day_emp):
                    day = datetime.strptime(day, "%Y-%m-%d")
                    date1 = day.date()
                    list_signin = hr_attendance_obj.search(cr, uid, [('employee_id', '=', employee_id), ('day', '=', date1), ('action', '=', 'sign_in')], context=context)
                    list_signin = sorted(list_signin)
                    list_signout = hr_attendance_obj.search(cr, uid, [('employee_id', '=', employee_id), ('day', '=', date1), ('action', '=', 'sign_out')], context=context)
                    list_signout = sorted(list_signout)
                    total_hours = 0
                    if not list_signin or not list_signout:
                        val = {
                           'name': 'invalidtimesheet',
                           'employee_id' : employee_id,
                           'shift_id' : shift_id.id,
                           'date' : date1,
                           'time_normal' :0,
                           'time_ot' : 0,
                           'time_late' : 0,
                           'time_early' : 0,
                           }
                        hr_attendance_timesheet_obj.create(cr, uid, val)
                    else:
                        count_signin = len(list_signin)
                        count_signout = len(list_signout)
                        if count_signin <> count_signout:
                            val = {
                                   'name': 'invalidtimesheet',
                                   'employee_id' : employee_id,
                                   'shift_id' : shift_id.id,
                                   'date' : date1,
                                   'time_normal' :0,
                                   'time_ot' : 0,
                                   'time_late' : 0,
                                   'time_early' : 0,
                                   }
                            hr_attendance_timesheet_obj.create(cr, uid, val)
                        else:
                            late_in = 0
                            early_out = 0
                            total_leave = 0
                            overtime = 0
                            team = 0
                            for i in xrange(count_signin):
                                signin_id = list_signin[i]
                                signout_id = list_signout[i]
                                time_in = datetime.strptime(hr_attendance_obj.browse(cr, uid, signin_id, context=context).name, DATETIME_FORMAT)
                                time_out = datetime.strptime(hr_attendance_obj.browse(cr, uid, signout_id, context=context).name, DATETIME_FORMAT)
                                team += (time_out - time_in).days*24 + float((time_out - time_in).seconds) / 3600
                            late_in_ids = hr_late_in_obj.search(cr, uid, [('employee_id', '=', employee_id), ('date', '=', date1), ('state', '=', 'confirm')], context=context)
                            if late_in_ids:
                                late_in = hr_late_in_obj.browse(cr, uid, late_in_ids[0], context=context).number_of_hours
                            early_out_ids = hr_early_out_obj.search(cr, uid, [('employee_id', '=', employee_id), ('date', '=', date1), ('state', '=', 'confirm')], context=context)
                            if early_out_ids:
                                early_out = hr_early_out_obj.browse(cr, uid, early_out_ids[0], context=context).number_of_hours
                            total_hours = team + late_in + early_out + total_leave - shift_id.break_time
                            overtime_ids = hr_overtime_obj.search(cr, uid, [('employee_id', '=', employee_id), ('date', '=', date1), ('state', '=', 'confirm')], context=context)
                            if overtime_ids:
                                overtime = hr_overtime_obj.browse(cr, uid, overtime_ids[0], context=context).durations
                            val = {
                               'name': 'approve', 
                               'employee_id': employee_id,
                               'shift_id' : shift_id.id,
                               'date' : date1,
                               'time_normal' : total_hours or 0,
                               'time_ot' : overtime,
                               'time_late' : late_in,
                               'time_early' : early_out,
                               }
                            hr_attendance_timesheet_obj.create(cr, uid, val)                          
                sql_leave_full = '''
                                select hh.employee_id,hh.date_from ::DATE as day, number_of_days_temp*hhs.ratio as number_of_days_temp
                                from hr_holidays hh
                                inner join  hr_holidays_status hhs on hh.holiday_status_id = hhs.id
                                where type = 'remove' and state ='validate'  
                                and employee_id = %s
                                and date_from :: DATE >= '%s'
                                and date_from :: DATE <= '%s'
                                '''%(employee_id,date_from,date_to)
                cr.execute(sql_leave_full)
                kq_leave_full = cr.fetchall()
                if kq_leave_full:
                    for line in kq_leave_full:
                        timesheet_ids = hr_attendance_timesheet_obj.search(cr, uid, [('employee_id', '=', line[0]), ('date', '=', line[1])], context=context)
                        if not timesheet_ids:
                            val = {
                                   'name': 'approve',
                                   'employee_id' : line[0],
                                   'shift_id' : shift_id.id,
                                   'date' : line[1],
                                   'time_normal' :line[2],
                                   'time_ot' : 0,
                                   'time_late' : 0,
                                   'time_early' : 0,
                                   }
                            hr_attendance_timesheet_obj.create(cr, uid, val)
                        else:
                            timesheet_id = hr_attendance_timesheet_obj.browse(cr, uid, timesheet_ids[0], context=context).id
                            work_hours = hr_attendance_timesheet_obj.browse(cr, uid, timesheet_ids[0], context=context).time_normal
                            hr_attendance_timesheet_obj.write(cr, uid,timesheet_id , {'time_normal':work_hours + line[2]})
        return True
      
        
vsis_hr_attendance_wizard()

class hr_attendance_report(osv.osv_memory):
    _name = 'hr.attendance.report'
    _columns = {
                'month': fields.integer('Month',required = True),
                'year': fields.integer('Year',required = True),
                'employee_ids': fields.many2many('hr.employee','att_employee_rel_report','employee_id','att_id','Employee',required = True),                           
    }
    
    def print_report(self, cr, uid, ids, context=None):
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'hr.attendance.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {'type': 'ir.actions.report.xml', 'report_name': 'hr_attendance_report' , 'datas': datas
        }  
         
hr_attendance_report()

