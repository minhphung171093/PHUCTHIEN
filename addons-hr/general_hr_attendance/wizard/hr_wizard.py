# Embedded file name: D:\GSProject\GSOpenERP\Ver7x\Server\openerp\addons\gs_mkp_hr_report\wizard\hr_wizard.py
import netsvc
import time
import pooler
from tools import config
from osv import osv, fields
from datetime import date, datetime, timedelta
from tools.translate import _
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

def _default_month(self, cr, uid, ids, context = {}):
    month = time.strftime('%m', time.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d'))
    return str(int(month))


def _default_year(self, cr, uid, ids, context = {}):
    year = time.strftime('%Y', time.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d'))
    return int(year)


class wizard_list_employee_ct(osv.gosv_memory):
    _name = 'list.employee.ct'
    _columns = {'department': fields.many2many('hr.department', 'att_department_rel', 'department_id', 'att_id', 'Deparment', required=True)}
    _defaults = {}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['department'], context=context)
        print 'res ne ', res, self.browse(cr, uid, ids)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'list_employee_ct',
         'datas': datas}


wizard_list_employee_ct()

class wizard_list_employee_nv(osv.gosv_memory):
    _name = 'list.employee.nv'
    _columns = {'date_from': fields.date('Date_from'),
     'date_to': fields.date('Date_to', required=True),
     'department': fields.many2many('hr.department', 'att_department_rel_nv', 'department_id', 'att_id', 'Deparment', required=True)}
    _defaults = {'date_to': lambda *a: time.strftime('%Y-%m-%d')}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_from', 'date_to', 'department'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'list_employee_nv',
         'datas': datas}


wizard_list_employee_nv()

class wizard_list_employee_tn(osv.gosv_memory):
    _name = 'list.employee.tn'
    _columns = {'number_month': fields.integer('Number month Working', required=True, help='Number month input must than one or equal one'),
     'department': fields.many2many('hr.department', 'att_department_rel_tn', 'department_id', 'att_id', 'Deparment', required=True)}
    _defaults = {'number_month': lambda *a: 1}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['department', 'all', 'number_month'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'list_employee_tn',
         'datas': datas}

    def onchange_department(self, cr, uid, ids, all):
        if all:
            return {'value': {'department': False}}


wizard_list_employee_tn()

class wizard_list_employee_tuoi(osv.gosv_memory):
    _name = 'list.employee.tuoi'
    _columns = {'startday': fields.integer('From Age'),
     'endday': fields.integer('To Age'),
     'option_age': fields.selection([('under18', '< 18 Age'), ('nghihuu', 'Retired'), ('tuychon', 'Option')], 'Option'),
     'department': fields.many2many('hr.department', 'att_department_rel_tuoi', 'department_id', 'att_id', 'Deparment', required=True),
     'all': fields.boolean('All')}
    _defaults = {'option_age': lambda *a: 'tuychon',
     'endday': lambda *a: 60}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['startday',
         'endday',
         'option_age',
         'department'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'list_employee_tuoi',
         'datas': datas}


wizard_list_employee_tuoi()

class wizard_gs_employee_dt(osv.gosv_memory):
    _name = 'gs.employee.dt'
    _columns = {'month': fields.selection([('1', 'January'),
               ('2', 'February'),
               ('3', 'March'),
               ('4', 'April'),
               ('5', 'May'),
               ('6', 'June'),
               ('7', 'July'),
               ('8', 'August'),
               ('9', 'September'),
               ('10', 'October'),
               ('11', 'November'),
               ('12', 'December')], 'Month'),
     'year': fields.integer('Of Year'),
     'option': fields.many2one('hr.salary.rule', 'Option', required=True),
     'department': fields.many2many('hr.department', 'att_department_rel_pc', 'department_id', 'att_id', 'Deparment', required=True)}
    _defaults = {'month': _default_month,
     'year': _default_year}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['month',
         'year',
         'option',
         'department'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'gs_employee_dt',
         'datas': datas}


wizard_gs_employee_dt()

class wizard_list_employee_tv(osv.gosv_memory):
    _name = 'list.employee.tv'
    _columns = {'date_from': fields.date('Date_from'),
     'date_to': fields.date('Date_to', required=True),
     'department': fields.many2many('hr.department', 'att_department_rel_tv', 'department_id', 'att_id', 'Deparment', required=True)}
    _defaults = {'date_to': lambda *a: time.strftime('%Y-%m-%d')}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_from', 'date_to', 'department'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'list_employee_tv',
         'datas': datas}


wizard_list_employee_tv()

class wizard_list_employee_hdct(osv.gosv_memory):
    _name = 'list.employee.hdct'
    _columns = {'date_from': fields.date('Date_from'),
     'date_to': fields.date('Date_to', required=True),
     'department': fields.many2many('hr.department', 'att_department_rel_hdct', 'department_id', 'att_id', 'Deparment', required=True)}
    _defaults = {'date_to': lambda *a: time.strftime('%Y-%m-%d')}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_from', 'date_to', 'department'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'list_employee_hdct',
         'datas': datas}


wizard_list_employee_hdct()

class wizard_list_employee_b(osv.gosv_memory):
    _name = 'list.employee.b'
    _columns = {'date_from': fields.date('Date_from', required=True),
     'date_to': fields.date('Date_to', required=True),
     'department': fields.many2many('hr.department', 'att_department_rel_b', 'department_id', 'att_id', 'Deparment', required=True)}
    _defaults = {'date_from': lambda *a: time.strftime('%Y-%m-%d')}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_from', 'date_to', 'department'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'list_employee_b',
         'datas': datas}


wizard_list_employee_b()

class wizard_gs_employee_payslip2(osv.gosv_memory):
    _name = 'gs.employee.payslip2'
    _columns = {'template': fields.many2one('gs.hr.template', 'Template'),
     'date_start': fields.date('Start Date'),
     'date_stop': fields.date('End Date'),
     'department': fields.many2many('hr.department', 'att_department_rel_pay', 'department_id', 'att_id', 'Deparment', required=True)}
    _defaults = {'date_start': lambda *a: time.strftime('%Y-%m-01'),
     'date_stop': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10]}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['template',
         'department',
         'date_start',
         'date_stop'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'gs_employee_payslip2',
         'datas': datas}

    def check(self, cr, uid, ids, date_stop, date_start):
        if date_stop < date_start:
            raise osv.except_osv(_('Error !'), _('Date End must than Date From.'))
        else:
            return {'value': {'date_stop': date_stop}}


wizard_gs_employee_payslip2()

class wizard_gs_income_tax_year(osv.gosv_memory):
    _name = 'gs.income.tax.year'
    _columns = {'year': fields.integer('Year'),
     'type': fields.selection([('ab_k', '05AK'), ('bb_k', '05BK')], 'Form', required=True)}
    _defaults = {'year': _default_year}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['year', 'type'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'gs_income_tax_year',
         'datas': datas}


wizard_gs_income_tax_year()

class wizard_gs_income_tax(osv.gosv_memory):
    _name = 'gs.income.tax'
    _columns = {'year': fields.integer('Year')}
    _defaults = {'year': _default_year}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['year'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'gs_income_tax',
         'datas': datas}


wizard_gs_income_tax()

class wizard_list_employee_bhxh(osv.gosv_memory):
    _name = 'list.employee.bhxh'
    _columns = {'date_start': fields.date('Start Date'),
     'date_stop': fields.date('End Date')}
    _defaults = {'date_start': lambda *a: time.strftime('%Y-%m-01'),
     'date_stop': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10]}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_start', 'date_stop', 'department'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'list_employee_bhxh',
         'datas': datas}


wizard_list_employee_bhxh()

class wizard_gs_su_dung_ld(osv.gosv_memory):
    _name = 'gs.su.dung.ld'
    _columns = {'date_start': fields.date('Start Date'),
     'date_stop': fields.date('End Date')}
    _defaults = {'date_start': lambda *a: time.strftime('%Y-%m-01'),
     'date_stop': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10]}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_start', 'date_stop'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'gs_su_dung_ld',
         'datas': datas}


wizard_gs_su_dung_ld()

class wizard_gs_giam_ld(osv.gosv_memory):
    _name = 'gs.giam.ld'
    _columns = {'date_start': fields.date('Start Date'),
     'date_stop': fields.date('End Date')}
    _defaults = {'date_start': lambda *a: time.strftime('%Y-%m-01'),
     'date_stop': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10]}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_start', 'date_stop'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'gs_giam_ld',
         'datas': datas}


wizard_gs_giam_ld()

class wizard_gs_employee_time(osv.gosv_memory):

    def list_nv(self, cr, uid, context = None):
        return self.pool.get('hr.employee').search(cr, uid, [])

    _name = 'gs.employee.time'
    _columns = {'date_start': fields.date('Start Date', required=True),
     'date_stop': fields.date('End Date', required=True),
     'department': fields.many2one('hr.department', 'Department'),
     'employee_ids': fields.many2many('hr.employee', 'att_employee_rel', 'employee_id', 'att_id', 'Employee')}
    _sql_constraints = []
    _defaults = {'date_start': lambda *a: time.strftime('%Y-%m-01'),
     'date_stop': lambda *a: time.strftime('%Y-%m-%d')}

    def check(self, cr, uid, ids, date_stop, date_start):
        if date_stop < date_start:
            raise osv.except_osv(_('Error !'), _('Date End must than Date From.'))
        else:
            return {'value': {'date_stop': date_stop}}

    def onchange_department(self, cr, uid, ids, department):
        if not department:
            return {}
        result = []
        depart_obj = self.pool.get('hr.department').browse(cr, uid, department)
        if len(depart_obj.member_ids):
            for em in depart_obj.member_ids:
                result.append(em.id)

        return {'value': {'employee_ids': result}}

    def print_report(self, cr, uid, ids, context = None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['department',
         'employee_ids',
         'date_start',
         'date_stop'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        datas['model'] = 'hr.employee'
        return {'type': 'ir.actions.report.xml',
         'report_name': 'gs_employee_time_new_d',
         'datas': datas}


wizard_gs_employee_time()