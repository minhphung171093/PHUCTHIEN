# Embedded file name: D:\Working\Version_7.0\OpenERPV7\addons_hr\general_hr_attendance\hr_attendance_config.py
from osv import fields, osv
import time
import netsvc
import pooler
import tools
from tools.translate import _
import datetime
import decimal_precision as dp
from tools import config

class hr_shift(osv.osv):
    _name = 'hr.shift'
    _order = 'code'
    _columns = {'name': fields.char('Name', 128, required=True),
     'code': fields.char('Code', 32, required=True),
     'hour_from': fields.float('Work From', size=8, required=True, help='Working time will start from'),
     'hour_to': fields.float('Work To', size=8, required=True, help='Working time will end at'),
     'shift_rate': fields.many2one('hr_timesheet_invoice.factor', 'Shift Rate'),
     'is_end_next_day': fields.boolean('End Next Day'),
     'break_from': fields.float('Break From', size=8),
     'break_to': fields.float('Break To', size=8),
     'break_time': fields.float('Break Time', size=8),
     'limit_in_early': fields.float('Limit In Early'),
     'limit_in_late': fields.float('Limit In Late'),
     'limit_out_early': fields.float('Limit Out Early'),
     'limit_out_late': fields.float('Limit Out Late'),
     'allow_in_early': fields.float('Allow In Early'),
     'allow_in_late': fields.float('Allow In Late'),
     'allow_out_early': fields.float('Allow Out Early'),
     'allow_out_late': fields.float('Allow Out Late'),
     'ot_hour_from': fields.float('OT From', size=8),
     'ot_hour_to': fields.float('OT To', size=8),
     'ot_break_from': fields.float('OT Break From', size=8),
     'ot_break_to': fields.float('OT Break To', size=8),
     'ot_break_time': fields.float('OT Break Time', size=8),
     'ot_rate': fields.many2one('hr_timesheet_invoice.factor', 'OT Rate')}
    _defaults = {'break_time': 0,
     'limit_in_early': 60,
     'limit_in_late': 60,
     'limit_out_early': 60,
     'limit_out_late': 60,
     'allow_in_early': -1,
     'allow_in_late': 10,
     'allow_out_early': 10,
     'allow_out_late': -1}

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_shift, self).copy(cr, uid, id, default, context=context)

    def _check_hour_to(self, cr, uid, ids, context = None):
        for shf in self.browse(cr, uid, ids, context=context):
            if not shf.is_end_next_day and shf.hour_to <= shf.hour_from:
                return False

        return True

    def _check_break_from(self, cr, uid, ids, context = None):
        for shf in self.browse(cr, uid, ids, context=context):
            if shf.break_from:
                if not shf.is_end_next_day and shf.break_from <= shf.hour_from:
                    return False

        return True

    def _check_break_to(self, cr, uid, ids, context = None):
        for shf in self.browse(cr, uid, ids, context=context):
            if shf.break_to and shf.break_from:
                if not shf.is_end_next_day and (shf.break_to <= shf.break_from or shf.break_to >= shf.hour_to):
                    return False
            elif shf.break_from or shf.break_to:
                return False

        return True

    _constraints = [(_check_hour_to, _('Hour To must after Hour From. Please check your input and End Next checkbox!'), ['hour_to']), (_check_break_from, _('Break From must after Hour From. Please check your input and End Next checkbox!'), ['break_from']), (_check_break_to, _('Break To must after Break From and before Hour To. Please check your input and End Next checkbox!'), ['break_to'])]
    _sql_constraints = [('code_uniq', 'unique (code)', 'The code of the shift must be unique !')]
    _order = 'hour_from'


hr_shift()

class resource_calendar_attendance(osv.osv):
    _inherit = 'resource.calendar.attendance'
    _columns = {'name': fields.char('Name', size=64, required=False),
     'week_no': fields.integer('Week No.'),
     'shift_id': fields.many2one('hr.shift', 'Shift', required=True),
     'hour_from': fields.float('Work from', required=False, help='Start and End time of working.', select=True),
     'hour_to': fields.float('Work to', required=False)}
    _defaults = {'week_no': 1}
    _order = 'week_no, dayofweek'


resource_calendar_attendance()