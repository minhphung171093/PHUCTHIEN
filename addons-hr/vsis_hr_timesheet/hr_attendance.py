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

class hr_attendance(osv.osv):
    _inherit = "hr.attendance"

    def _get_hr_timesheet_sheet(self, cr, uid, ids, context=None):
        attendance_ids = []
        for ts in self.browse(cr, uid, ids, context=context):
            cr.execute("""
                        SELECT a.id
                          FROM hr_attendance a
                         INNER JOIN hr_employee e
                               INNER JOIN resource_resource r
                                       ON (e.resource_id = r.id)
                            ON (a.employee_id = e.id)
                        WHERE %(date_to)s >= date_trunc('day', a.name)
                              AND %(date_from)s <= a.name
                              AND %(user_id)s = r.user_id
                         GROUP BY a.id""", {'date_from': ts.date_from,
                                            'date_to': ts.date_to,
                                            'user_id': ts.employee_id.user_id.id,})
            attendance_ids.extend([row[0] for row in cr.fetchall()])
        return attendance_ids

    def _sheet(self, cursor, user, ids, name, args, context=None):
        sheet_obj = self.pool.get('hr_timesheet_sheet.sheet')
        res = {}.fromkeys(ids, False)
        for attendance in self.browse(cursor, user, ids, context=context):
            date_to = datetime.strftime(datetime.strptime(attendance.name[0:10], '%Y-%m-%d'), '%Y-%m-%d %H:%M:%S')
            if attendance.employee_id.department_id:
                sheet_ids = sheet_obj.search(cursor, user,
                    [('date_to', '>=', date_to), ('date_from', '<=', attendance.name),
                     ('department_id', '=', attendance.employee_id.department_id.id)],
                    context=context)
                if sheet_ids:
                    # [0] because only one sheet possible for an employee between 2 dates
                    res[attendance.id] = sheet_obj.name_get(cursor, user, sheet_ids, context=context)[0]
        return res

    _columns = {
        'sheet_id': fields.function(_sheet, string='Sheet',
            type='many2one', relation='hr_timesheet_sheet.sheet',
            store={
                      'hr_timesheet_sheet.sheet': (_get_hr_timesheet_sheet, ['employee_id', 'date_from', 'date_to'], 10),
                      'hr.attendance': (lambda self,cr,uid,ids,context=None: ids, ['employee_id', 'name', 'day'], 10),
                  },
            )
    }

    def _altern_si_so(self, cr, uid, ids, context=None):
        """ Always return True, needn't check here
        """
        return True

    _constraints = [(_altern_si_so, 'Error ! Sign in (resp. Sign out) must follow Sign out (resp. Sign in)', ['action'])]

hr_attendance()

class hr_shift(osv.osv):
    _name = "hr.shift"
    _order = "code"
    _columns = {
        'name': fields.char('Name', 128, required=True),
        'code' : fields.char('Code', 32, required=True),
        'hour_from' : fields.float('Work From', size=8, required=True, help="Working time will start from"),
        'hour_to' : fields.float("Work To", size=8, required=True, help="Working time will end at"),
        'shift_rate': fields.many2one('hr_timesheet_invoice.factor', 'Shift Rate'),
        'is_end_next_day': fields.boolean('End Next Day'),
        'break_from' : fields.float('Break From', size=8),
        'break_to' : fields.float('Break To', size=8),
        'break_time': fields.float('Break Time', size=8),
        'limit_in_early': fields.float('Limit In Early'),
        'limit_in_late': fields.float('Limit In Late'),
        'limit_out_early': fields.float('Limit Out Early'),
        'limit_out_late': fields.float('Limit Out Late'),
        'allow_in_early': fields.float('Allow In Early'),
        'allow_in_late': fields.float('Allow In Late'),
        'allow_out_early': fields.float('Allow Out Early'),
        'allow_out_late': fields.float('Allow Out Late'),
        'ot_hour_from' : fields.float('OT From', size=8),
        'ot_hour_to' : fields.float("OT To", size=8),
        'ot_break_from' : fields.float('OT Break From', size=8),
        'ot_break_to' : fields.float('OT Break To', size=8),
        'ot_break_time': fields.float('OT Break Time', size=8),
        'ot_rate': fields.many2one('hr_timesheet_invoice.factor', 'OT Rate'),
    }

    _defaults = {
        'break_time' : 0,
        'limit_in_early' : 60,
        'limit_in_late' : 60,
        'limit_out_early' : 60,
        'limit_out_late' : 60,
        'allow_in_early' : -1,
        'allow_in_late' : 10,
        'allow_out_early' : 10,
        'allow_out_late' : -1,
    }
    
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_shift, self).copy(cr, uid, id, default, context=context)

    def _check_hour_to(self, cr, uid, ids, context=None):
        for shf in self.browse(cr, uid, ids, context=context):
            if (not shf.is_end_next_day) and shf.hour_to <= shf.hour_from:
                return False
        return True

    def _check_break_from(self, cr, uid, ids, context=None):
        for shf in self.browse(cr, uid, ids, context=context):
            if shf.break_from:
                if (not shf.is_end_next_day) and (shf.break_from <= shf.hour_from):
                    return False
        return True

    def _check_break_to(self, cr, uid, ids, context=None):
        for shf in self.browse(cr, uid, ids, context=context):
            if shf.break_to and shf.break_from:
                if (not shf.is_end_next_day) and ((shf.break_to <= shf.break_from) or (shf.break_to >= shf.hour_to)):
                    return False
                # TODO: Should check break_time must = break to - break from
            elif shf.break_from or shf.break_to:
                return False
        return True

    _constraints = [(_check_hour_to, _('Hour To must after Hour From. Please check your input and End Next checkbox!'), ['hour_to']),
                    (_check_break_from, _('Break From must after Hour From. Please check your input and End Next checkbox!'), ['break_from']),
                    (_check_break_to, _('Break To must after Break From and before Hour To. Please check your input and End Next checkbox!'), ['break_to'])]

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the shift must be unique !'),
    ]

    _order = 'hour_from'

hr_shift()

class resource_calendar_attendance(osv.osv):
    _inherit = "resource.calendar.attendance"

    _columns = {
        'name' : fields.char("Name", size=64, required=False),
        'week_no': fields.integer('Week No.'),
        'shift_id': fields.many2one('hr.shift', 'Shift', required=True),
        'hour_from' : fields.float('Work from', required=False, help="Start and End time of working.", select=True),
        'hour_to' : fields.float("Work to", required=False),
    }

    _defaults = {
        'week_no' : 1,
    }
    _order = 'week_no, dayofweek'
resource_calendar_attendance()

class resource_calendar(osv.osv):
    _inherit = "resource.calendar"

    _columns = {
        'employee_ids': fields.one2many('resource.resource', 'calendar_id', 'Resources'),
        'apply_start': fields.selection([('week','Begin of Week'),('month','Begin of Month'),('year','Begin of Year'),('contract','Begin of Contract'),('daily','Daily'),('manual','Manual')], 'Applying Start'),
        'apply_date': fields.date('Applying Date'),
    }

    _defaults = {
        'apply_start' : 'week',
    }

    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['name'] = (record['name'] or '') + '_(copy)'
        default['employee_ids'] = False
        return super(resource_calendar, self).copy(cr, uid, id, default, context=context)

    # Get list of calendar attendance applying for a specified date
    # Return list of shift
    def get_wdate_calendar_attendance(self, cr, uid, id, wdate, start_wk=False, emp_id=False):
        ret = []

        mapping_obj = self.pool.get('working.schedule.mapping')
        mapping_ids = mapping_obj.search(cr, uid, [('name','=',emp_id), ('new_date','=',wdate.strftime('%Y-%m-%d')), ('state','=','approved')])
        if mapping_ids:
            return [mapping_obj.browse(cr, uid, mapping_ids)[0].new_shift]

        # NOTCHECK
        # mapping_obj = self.pool.get('working.schedule.mapping')
        # mapping_ids = mapping_obj.search(cr, uid, [('name','=',emp_id), ('mapping_date','=',wdate.strftime('%Y-%m-%d')), ('state','=','approved')])
        # if mapping_ids:
            # return []

        rescal_att_obj = self.pool.get('resource.calendar.attendance')
        rescal = self.browse(cr, uid, id)
        # print 'apply_start=%s' % (rescal.apply_start,)
        if rescal.apply_start == 'week':
            if rescal.attendance_ids:
                applying_week = 1
                rescal_att_ids = rescal_att_obj.search(cr, uid, [('calendar_id','=',id), ('week_no','=',applying_week), ('dayofweek','=',str(wdate.weekday()))])
                for rescal_att in rescal_att_obj.browse(cr, uid, rescal_att_ids):
                    ret.append(rescal_att.shift_id)
        elif rescal.apply_start == 'month':
            pass
        elif rescal.apply_start == 'year':
            pass
        elif rescal.apply_start == 'contract' and start_wk:
            if rescal.attendance_ids:
                max_week = rescal.attendance_ids[-1].week_no
                dif_start_wk = wdate - start_wk
                dif_to_sun_nearest = 7 - start_wk.weekday() - 1
                if dif_start_wk.days <= dif_to_sun_nearest:
                    dif_weeks = 0
                elif (dif_start_wk.days - dif_to_sun_nearest) % 7 > 0:
                    dif_weeks = (dif_start_wk.days - dif_to_sun_nearest) / 7 + 1
                else:
                    dif_weeks = (dif_start_wk.days - dif_to_sun_nearest) / 7
                # print 'dif_days=%s@dif_to_sun_nearest=%s@dif_weeks=%s' % (dif_start_wk.days,dif_to_sun_nearest,dif_weeks)
                applying_week = (dif_weeks % max_week) + 1
                rescal_att_ids = rescal_att_obj.search(cr, uid, [('calendar_id','=',id), ('week_no','=',applying_week), ('dayofweek','=',str(wdate.weekday()))])
                # print 'rescal_att_ids=%s' % (rescal_att_ids,)
                for rescal_att in rescal_att_obj.browse(cr, uid, rescal_att_ids):
                    ret.append(rescal_att.shift_id)
                # print 'applying_week=%s@ngay=%s@ca=%s' % (applying_week,wdate,ret)
        elif rescal.apply_start == 'daily':
            pass
        elif rescal.apply_start == 'manual' and rescal.apply_date:
            if rescal.attendance_ids:
                start_wk = datetime.strptime(rescal.apply_date, '%Y-%m-%d')
                max_week = rescal.attendance_ids[-1].week_no
                dif_start_wk = wdate - start_wk
                dif_to_sun_nearest = 7 - start_wk.weekday() - 1
                if dif_start_wk.days <= dif_to_sun_nearest:
                    dif_weeks = 0
                elif (dif_start_wk.days - dif_to_sun_nearest) % 7 > 0:
                    dif_weeks = (dif_start_wk.days - dif_to_sun_nearest) / 7 + 1
                else:
                    dif_weeks = (dif_start_wk.days - dif_to_sun_nearest) / 7

                applying_week = (dif_weeks % max_week) + 1
                rescal_att_ids = rescal_att_obj.search(cr, uid, [('calendar_id','=',id), ('week_no','=',applying_week), ('dayofweek','=',str(wdate.weekday()))])
                for rescal_att in rescal_att_obj.browse(cr, uid, rescal_att_ids):
                    ret.append(rescal_att.shift_id)
        return ret

    # Get calendar attendance appling for a specified real datetime (attendance record)
    def get_applying_calendar_attendance(self, cr, uid, id, rdate, wdate=False, emp_id=False):
        return False

resource_calendar()

class hr_holidays_status(osv.osv):
    _inherit = "hr.holidays.status"

    _columns = {
        'leave_rate': fields.many2one('hr_timesheet_invoice.factor', 'Leave Rate'),
    }
hr_holidays_status()

class hr_holidays(osv.osv):
    _inherit = "hr.holidays"

    def get_holiday_by_emp_date(self, cr, uid, id, emp_id, wdate):
        sql = '''
            SELECT
                hrs.id as leave_id,
                hrs.name as leave_type,
                abs(hrs.number_of_days) as leave_count,
                fac.customer_name as leave_rate
            FROM
                hr_holidays as hrs,
                hr_holidays_status as hhs
                left join hr_timesheet_invoice_factor as fac on fac.id = hhs.leave_rate
            WHERE
                hrs.employee_id = %s
                and hhs.id = hrs.holiday_status_id
                and hrs.type='remove'
                and hrs.state='validate'
                and hrs.date_from <= date %s + '23:59:59'::time
                and hrs.date_to >= date %s + '00:00:00'::time
            LIMIT 1
            '''
        cr.execute(sql,(str(emp_id),str(wdate),str(wdate)))
        res = cr.fetchall()
        if res:
            return res[0]
        else:
            return False
hr_holidays()

class working_schedule_mapping(osv.osv):
    _name = "working.schedule.mapping"
    _description = "Working Schedule Mapping"

    _columns = {
        'name': fields.many2one('hr.employee', "Employee", required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'mapping_date': fields.date('Mapping Date', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'mapping_shift': fields.many2one('hr.shift', 'Mapping Shift', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'new_date': fields.date('New Date', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'new_shift': fields.many2one('hr.shift', 'New Shift', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'note': fields.char('Note', size=256, readonly=True, states={'draft':[('readonly',False)]}),
        'state': fields.selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('approved', 'Approved')], "State", readonly=True),
    }

    _defaults = {
        'mapping_date': lambda *a: time.strftime('%Y-%m-%d'),
        'state' : 'draft',
    }
    _order = 'mapping_date, name'

    _sql_constraints = [
        ('name_date_uniq', 'unique(name,mapping_date)', _('Working schedule of selected employee and date has been mapped!')),
    ]

    def action_confirm(self, cr, uid, ids, *args):
        map = self.browse(cr, uid, ids)[0]
        rescal_obj = self.pool.get('resource.calendar')

        rescal = map.name.calendar_id
        start_wk = map.name.contract_id and datetime.strptime(map.name.contract_id.date_start, '%Y-%m-%d') or False
        wdate = datetime.strptime(map.mapping_date, '%Y-%m-%d')
        wshift_list = rescal_obj.get_wdate_calendar_attendance(cr, uid, rescal.id, wdate, start_wk, map.name.id)
        shift_ids = []
        for shift in wshift_list:
            shift_ids += [shift.id]
        if map.mapping_shift.id in shift_ids:
            self.write(cr, uid, [map.id], {'state': 'confirmed',})
        else:
            raise osv.except_osv(_('Invalid Mapping Shift!'), _('Selected employee does not assigned with selected shift in date %s! Please choose again!' % map.mapping_date))
        return True

    def action_approve(self, cr, uid, ids, *args):
        map = self.browse(cr, uid, ids)[0]
        self.write(cr, uid, [map.id], {'state': 'approved',})
        return True

    def action_cancel(self, cr, uid, ids, *args):
        map = self.browse(cr, uid, ids)[0]
        self.write(cr, uid, [map.id], {'state': 'draft',})
        return True

working_schedule_mapping()
