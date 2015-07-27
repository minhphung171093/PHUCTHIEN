# Embedded file name: D:\Working\Version_7.0\OpenERPV7\addons_hr\general_hr\hr_overtime.py
from functools import partial
import logging
from lxml import etree
from lxml.builder import E
from datetime import datetime, timedelta
import openerp
import time
from openerp import SUPERUSER_ID
from openerp import pooler, tools
import openerp.exceptions
from openerp.osv import fields, osv
from openerp.osv.orm import browse_record
from openerp.tools.translate import _
import datetime
from openerp.tools import append_content_to_html
_logger = logging.getLogger(__name__)

class hr_overtime(osv.osv):
    _name = 'hr.overtime'
    _description = 'Overtime'
    _inherit = 'mail.thread'

    def _employee_get(self, cr, uid, context = None):
        ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)], context=context)
        if ids:
            return ids[0]
        return False

    def _get_number_of_hours(self, hour_start, hour_end):
        timedelta = hour_end - hour_start
        diff_day = timedelta and timedelta or 0
        return diff_day

    def onchange_hour_start(self, cr, uid, ids, hour_start, hour_end):
        if hour_start and hour_end and hour_start > hour_end:
            raise osv.except_osv(_('Warning!'), _('The starting hour must be anterior to the ending hour.'))
        result = {'value': {}}
        if hour_start and hour_end and hour_start <= hour_end:
            diff_day = self._get_number_of_hours(hour_start, hour_end)
            result['value']['durations'] = diff_day
        else:
            result['value']['durations'] = 0
        return result

    def _month_compute(self, cr, uid, ids, fieldnames, args, context = None):
        res = dict.fromkeys(ids, '')
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = time.strftime('%Y-%m', time.strptime(obj.date, '%Y-%m-%d'))

        return res

    def _compute_durations(self, cr, uid, ids, name, args, context = None):
        result = {}
        for over in self.browse(cr, uid, ids, context=context):
            if over.hour_start and over.hour_end and over.hour_start <= over.hour_end:
                diff_day = self._get_number_of_hours(over.hour_start, over.hour_end)
                result[over.id] = diff_day
            else:
                result[over.id] = 0

        return result

    _columns = {'name': fields.char('Subject', size=128, required=True),
     'date': fields.date('Date', required=True),
     'hour_start': fields.float('Starting Hour', required=True),
     'hour_end': fields.float('Ending Hour', required=True),
     'type_id': fields.many2one('hr.overtime.type', 'Overtime Type', select=True, required=True),
     'employee_id': fields.many2one('hr.employee', 'Employee', select=True, required=True),
     'durations': fields.function(_compute_durations, string='Durations', type='float', store=True),
     'state': fields.selection([('to_approve', 'To Approved'),
               ('refuse', 'Refused'),
               ('confirm', 'Approve'),
               ('cancel', 'Cancelled')], 'Status'),
     'month': fields.function(_month_compute, type='char', string='Month', store=True, select=1, size=32),
     'reason': fields.text('Reason')}
    _defaults = {'date': lambda *a: time.strftime('%Y-%m-%d'),
     'employee_id': _employee_get,
     'state': 'to_approve'}
    _sql_constraints = [('date_check', 'CHECK (hour_start <= hour_end)', 'The starting hour must be anterior to the ending hour.'), ('employee_id_uniq', 'unique (date,employee_id)', 'The employee must be unique !')]

    def confirm(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'confirm'})

    def refuse(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'refuse'})

    def cancelled(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'cancel'})


hr_overtime()