# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################

from osv import osv, fields
from tools.translate import _
from datetime import datetime, timedelta
import time
import copy

#TODO: should setting SERVER_TZ_OFFSET in company
SERVER_TZ_OFFSET = 7

DEFAULT_TS_DESC = _('/')

def daterange( start_date, end_date ):
    if start_date <= end_date:
        for n in range( ( end_date - start_date ).days + 1 ):
            yield start_date + timedelta( n )
    else:
        for n in range( ( start_date - end_date ).days + 1 ):
            yield start_date - timedelta( n )

class timesheet_from_attendance(osv.osv_memory):
    _name = 'timesheet.from.attendance'
    _description = 'Timesheet From Attendance'

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(timesheet_from_attendance, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            sheet = self.pool.get('hr_timesheet_sheet.sheet').browse(cr, uid, context['active_id'], context=context)
            if 'date_from' in fields:
                res.update({'date_from': sheet.date_from})
            if 'date_to' in fields:
                res.update({'date_to': sheet.date_to})
            if 'department_id' in fields:
                res.update({'department_id': sheet.department_id.id})
            # res.update({'re_cal_ts': True})
        return res

    _columns = {
        'load_machine': fields.boolean('Load attendance from machine'),
        'auto_delete': fields.boolean('Auto delete attendance after loaded'),
        # 're_cal_ts': fields.boolean('Recalculate whole timesheet'),
        'date_from' : fields.date('From Date'),
        'date_to' : fields.date('To Date'),
        'department_id':fields.many2one('hr.department','Department'),
    }

    def on_change_load_machine(self, cr, uid, ids, load_machine, context=None):
        if context is None:
            context = {}
        res = {'value': {'auto_delete': load_machine}}
        return res

    def confirm(self, cr, uid, ids, context=None):
        ts_sheet = False
        if context.get('active_id'):
            ts_sheet = self.pool.get('hr_timesheet_sheet.sheet').browse(cr, uid, context['active_id'], context=context)
            if ts_sheet.state not in ('new', 'draft'):
                raise osv.except_osv(_('Error!'), _('This timesheet has been submited or appoved!'))

        data = self.browse(cr, uid, ids, context=context)[0]

        if data.load_machine:
            mac_pool = self.pool.get('hr.machine')
            if mac_pool:
                conn_ret = mac_pool.get_attendance(cr, uid, mids=None, delete_done=data.auto_delete, context=context)
            else:
                raise osv.except_osv(_('Error!'), _('Please install machine connector module to load attendance!'))
            if not conn_ret:
                raise osv.except_osv(_('Error!'), _('Cannot connect to any attendance machines or there is no machine defined!'))

        emp_list = data.department_id and data.department_id.member_ids or False
        hld_pool = self.pool.get('hr.holidays')
        rescal_obj = self.pool.get('resource.calendar')
        rescal_att_obj = self.pool.get('resource.calendar.attendance')
        att_obj = self.pool.get('hr.attendance')
        ivf_obj = self.pool.get('hr_timesheet_invoice.factor')
        ts_status_obj = self.pool.get('hr.timesheet.status')
        ts_analytic_obj = self.pool.get('hr.analytic.timesheet')

        if not emp_list:
            return
            # raise osv.except_osv(_('Error!'), _('There is no employee to calculate timesheet!'))

        wdate_start = datetime.strptime(data.date_from, '%Y-%m-%d')
        wdate_end = datetime.strptime(data.date_to, '%Y-%m-%d')
        if wdate_start > wdate_end:
            raise osv.except_osv(_('Error!'), _('To Date must be greater or equal From Date!'))
        elif ts_sheet and (wdate_start < datetime.strptime(ts_sheet.date_from, '%Y-%m-%d') or wdate_end > datetime.strptime(ts_sheet.date_to, '%Y-%m-%d')):
            raise osv.except_osv(_('Error!'), _('Please choose days in timesheet range!'))

        # ivf_ids = ivf_obj.search(cr, uid, [], context=context)
        # ivf_code2ids = {}
        # ivf_code2accs = {}
        # for ivf in ivf_obj.browse(cr, uid, ivf_ids, context=context):
            # if ivf.customer_name:
                # ivf_code2ids.update({ivf.customer_name: ivf.id})
                # ivf_code2accs.update({ivf.customer_name: ivf.default_analytic_account and ivf.default_analytic_account.id or False})
        # Invoice factor reference
        # TIME_OT300    OT 300
        # TIME_OT200    OT 200
        # TIME_OT150    OT 150
        # TIME_NORMAL   Default

        default_val = {
            'product_uom_id': ts_analytic_obj._getEmployeeUnit(cr, uid, context=context),
            'product_id': ts_analytic_obj._getEmployeeProduct(cr, uid, context=context),
            'general_account_id': ts_analytic_obj._getGeneralAccount(cr, uid, context=context),
            'journal_id': ts_analytic_obj._getAnalyticJournal(cr, uid, context=context),
            'user_id': context.get('user_id') or uid,
            'name': DEFAULT_TS_DESC,
        }

        ts_status_ids = ts_status_obj.search(cr, uid, [], context=context)
        ts_status_code2ids = {}
        for ts_status in ts_status_obj.browse(cr, uid, ts_status_ids, context=context):
            ts_status_code2ids.update({ts_status.name: ts_status.id})
        # Timesheet status reference
        # T   Late
        # S   Early
        # TS  Late & Early
        # V   Absent
        # X   Worked
        # E   Error
        # P   Paid Leave
        # H   Holiday

        for emp in emp_list:
            #TODO: return warning time sheet confirmed, cannot re-edit
            if not emp.calendar_id:
                #TODO: return warning no working hour set
                continue
            rescal = emp.calendar_id

            # get start working date
            start_wk = emp.contract_id and datetime.strptime(emp.contract_id.date_start, '%Y-%m-%d') or False
            for wdate in daterange(wdate_start, wdate_end):
                wshift_list = rescal_obj.get_wdate_calendar_attendance(cr, uid, rescal.id, wdate, start_wk, emp.id)
                val = copy.deepcopy(default_val)
                ot_val = False
                val.update({
                    'employee_id': emp.id,
                    'date': wdate.strftime('%Y-%m-%d'),
                })

                wdate_zero = wdate + timedelta(hours=0-SERVER_TZ_OFFSET)
                wdate_midnight = wdate + timedelta(days=1, hours=0-SERVER_TZ_OFFSET)
                for wshift in wshift_list:
                    val.update({
                        'to_invoice': wshift.shift_rate.id,
                        'account_id': wshift.shift_rate.default_analytic_account and wshift.shift_rate.default_analytic_account.id,
                    })
                    # val.update({'shift_assign':wshift.id,})

                    wk_start = wdate + timedelta(hours=wshift.hour_from-SERVER_TZ_OFFSET)
                    wk_end = wdate + timedelta(hours=wshift.hour_to-SERVER_TZ_OFFSET)
                    search_in_start = wdate + timedelta(hours=wshift.hour_from-SERVER_TZ_OFFSET, minutes=-wshift.limit_in_early)
                    search_in_end = wdate + timedelta(hours=wshift.hour_from-SERVER_TZ_OFFSET, minutes=wshift.limit_in_late)
                    search_out_start = wdate + timedelta(hours=wshift.hour_to-SERVER_TZ_OFFSET, minutes=-wshift.limit_out_early)
                    search_out_end = wdate + timedelta(hours=wshift.hour_to-SERVER_TZ_OFFSET, minutes=wshift.limit_out_late)
                    if wshift.is_end_next_day:
                        search_out_start = wdate + timedelta(days=1, hours=wshift.hour_to-SERVER_TZ_OFFSET, minutes=-wshift.limit_out_early)
                        search_out_end = wdate + timedelta(days=1, hours=wshift.hour_to-SERVER_TZ_OFFSET, minutes=wshift.limit_out_late)
                        wk_end = wdate + timedelta(days=1, hours=wshift.hour_to-SERVER_TZ_OFFSET)

                    wk_break_start = wshift.break_from and (wdate + timedelta(hours=wshift.break_from-SERVER_TZ_OFFSET)) or False
                    wk_break_end = wshift.break_to and (wdate + timedelta(hours=wshift.break_to-SERVER_TZ_OFFSET)) or False
                    # print 'search_in_start=%s@search_out_end=%s' % (search_in_start,search_out_end)

                    # hlds = hld_pool.get_holiday_by_emp_date(cr, uid, rescal.id, emp.id, wdate)
                    hlds = hld_pool.search(cr, uid,
                        [('employee_id', '=', emp.id), ('date_from','>=',wdate_zero.strftime('%Y-%m-%d %H:%M:%S')),
                        ('date_to','<',wdate_midnight.strftime('%Y-%m-%d %H:%M:%S')),('type','=','remove'),('state','=','validate')],
                       context=context)
                    # print hlds

                    att_ids = []
                    #Get the first in attendance
                    att_in_ids = att_obj.search(cr, uid, [('employee_id','=',emp.id), ('action','=','sign_in'),
                        ('name','>=',search_in_start.strftime('%Y-%m-%d %H:%M:%S')), ('name','<=',search_in_end.strftime('%Y-%m-%d %H:%M:%S'))], order='name ASC')
                    if att_in_ids and len(att_in_ids) > 0:
                        att_ids.append(att_in_ids[0])
                    else:
                        att_ids.append(False)

                    #Get the last out attendance
                    att_out_ids = att_obj.search(cr, uid, [('employee_id','=',emp.id), ('action','=','sign_out'),
                        ('name','>=',search_out_start.strftime('%Y-%m-%d %H:%M:%S')), ('name','<=',search_out_end.strftime('%Y-%m-%d %H:%M:%S'))], order='name DESC')
                    if att_out_ids and len(att_out_ids) > 0:
                        att_ids.append(att_out_ids[0])
                    else:
                        att_ids.append(False)

                    # print 'wdate=%s@shif=%s@att_ids=%s' % (wdate,wshift.name,att_ids)
                    # val.update({'work_from':wk_start,'work_to':wk_end})
                    #Calculate working hours by calendar
                    wking_hours = (wk_end - wk_start).seconds / 3600.0 - wshift.break_time / 60.0
                    # val.update({'working_time':wking_hours,})

                    if att_ids[0] and att_ids[1]:
                        att_list = att_obj.browse(cr, uid, att_ids)
                        att_in = datetime.strptime(att_list[0].name, '%Y-%m-%d %H:%M:%S')
                        att_out = datetime.strptime(att_list[1].name, '%Y-%m-%d %H:%M:%S')
                        att_ot_out = datetime.strptime(att_list[1].name, '%Y-%m-%d %H:%M:%S')

                        #Calculate difference with calendar margin
                        in_soon = att_in < wk_start and ((wk_start - att_in).seconds / 60.0) or 0.0
                        in_late = att_in > wk_start and ((att_in - wk_start).seconds / 60.0) or 0.0
                        out_soon = att_out < wk_end and ((wk_end - att_out).seconds / 60.0) or 0.0
                        out_late = att_out > wk_end and ((att_out - wk_end).seconds / 60.0) or 0.0
                        # val.update({'in_soon': in_soon,
                            # 'in_late': in_late,
                            # 'out_soon': out_soon,
                            # 'out_late': out_late,})

                        is_in_soon = False
                        is_in_late = False
                        is_out_soon = False
                        is_out_late = False

                        # if in/out in allow range --> mark as ontime
                        if in_soon > 0 and (wshift.allow_in_early < 0 or in_soon < wshift.allow_in_early):
                            att_in = wk_start
                        elif in_late > 0 and (wshift.allow_in_late < 0 or in_late < wshift.allow_in_late):
                            att_in = wk_start
                        elif in_late > 0:
                            is_in_late = True
                            val.update({'timesheet_status':ts_status_code2ids['T'],})
                        elif in_soon > 0:
                            is_in_soon = True
                            val.update({'timesheet_status':ts_status_code2ids['SI'],})

                        if out_soon > 0 and (wshift.allow_out_early < 0 or out_soon < wshift.allow_out_early):
                            att_out = wk_end
                        elif out_late > 0 and (wshift.allow_out_late < 0 or out_late < wshift.allow_out_late):
                            att_out = wk_end
                        elif out_soon > 0:
                            is_out_soon = True
                            if not is_in_late:
                                val.update({'timesheet_status':ts_status_code2ids['S'],})
                            else:
                                val.update({'timesheet_status':ts_status_code2ids['TS'],})
                        elif out_late > 0:
                            is_out_late = True
                            val.update({'timesheet_status':ts_status_code2ids['TO'],})

                        wk_break_time = wshift.break_time and wshift.break_time or 0.0
                        # check in/out in break time (result in minute)
                        if wk_break_start and wk_break_end:
                            if att_in > wk_break_start and att_in <= wk_break_end:
                                wk_break_time = wk_break_time - (att_in - wk_break_start).seconds / 60.0
                            elif att_in > wk_break_end:
                                wk_break_time = 0
                            if att_out >= wk_break_start and att_out < wk_break_end:
                                wk_break_time = wk_break_time - (wk_break_end - att_out).seconds / 60.0
                            elif att_out < wk_break_start:
                                wk_break_time = 0

                        #Calculate real worked hour/ot hour
                        wked_hours = (att_out - att_in).seconds / 3600.0 - wk_break_time / 60.0
                        val.update({'unit_amount':wked_hours,})
                        if (not is_in_soon) and (not is_in_late) and (not is_out_soon) and (not is_out_late):
                            val.update({'timesheet_status':ts_status_code2ids['X'],})

                        if wshift.ot_hour_from and wshift.ot_hour_to and wshift.ot_rate:
                            wk_ot_start = wdate + timedelta(hours=wshift.ot_hour_from-SERVER_TZ_OFFSET)
                            wk_ot_end = wdate + timedelta(hours=wshift.ot_hour_to-SERVER_TZ_OFFSET)
                            wk_ot_hours = 0.0
                            wk_ot_break_time = wshift.ot_break_time and wshift.ot_break_time or 0.0
                            if att_ot_out > wk_ot_end:
                                wk_ot_hours = (wk_ot_end - wk_ot_start).seconds / 3600.0 - wk_ot_break_time / 60.0
                            elif att_ot_out > wk_ot_start:
                                wk_ot_hours = (att_ot_out - wk_ot_start).seconds / 3600.0 - wk_ot_break_time / 60.0
                            #TODO: consider work in ot_break_time or not
                            if wk_ot_hours > 0.0:
                                ot_val = copy.deepcopy(default_val)
                                ot_val.update({
                                    'employee_id': emp.id,
                                    'date': wdate.strftime('%Y-%m-%d'),
                                })
                                ot_val.update({'unit_amount':wk_ot_hours,})
                                ot_val.update({'to_invoice': wshift.ot_rate.id,})
                                ot_val.update({'account_id': wshift.ot_rate.default_analytic_account.id,})
                    elif att_ids[0] or att_ids[1]:
                        #TODO: check calculate before out
                        val.update({'timesheet_status':ts_status_code2ids['E'],})
                    elif hlds:
                        val.update({'timesheet_status':ts_status_code2ids['P'],})
                        #TODO: marked as leave, or working in leave?
                        pass
                    elif wdate <= datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d'):
                        val.update({'timesheet_status':ts_status_code2ids['V'],})
                    else:
                        val.update({'account_id': False})

                # delete existed analytic.timesheet line with 'name'=DEFAULT_TS_DESC and the same 'employee_id' and 'date'
                # then create new
                # another ways is override existed, but it not cover all cases
                analytic_tsl_ids = ts_analytic_obj.search(cr, uid,
                    [('employee_id', '=', val['employee_id']), ('date','=',val['date']),
                    ('name','=',DEFAULT_TS_DESC)], context=context)
                if analytic_tsl_ids:
                    ts_analytic_obj.unlink(cr, uid, analytic_tsl_ids, context=context)

                # write generated timesheet_line
                # print val
                if ('account_id' in val) and val.get('account_id', False):
                    ts_analytic_obj.create(cr, uid, val, context=context)
                if ot_val and ('account_id' in ot_val) and ot_val.get('account_id', False):
                    ts_analytic_obj.create(cr, uid, ot_val, context=context)
        return {'type': 'ir.actions.act_window_close'}

timesheet_from_attendance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
