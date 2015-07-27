import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

from itertools import groupby
from operator import itemgetter

import math
from openerp import netsvc
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class hr_salary_rule_category(osv.osv):
    _inherit = 'hr.salary.rule.category'
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['code'], context=context)
        res = []
        for record in reads:
            name = record['code']
            res.append((record['id'], name))
        return res
    
hr_salary_rule_category()

class hr_salary_rule(osv.osv):
    _inherit = 'hr.salary.rule'
    _order = 'sequence'
    
    #Thanh: add Product UoM
    _columns = {
        'uom_id': fields.many2one('product.uom', 'UoM'),
    }
hr_salary_rule()

class hr_payslip(osv.osv):
    _inherit = "hr.payslip"
    
    def _get_user_department(self, cr, uid, ids, field_name, arg, context=None):
        employee_pool = self.pool.get('hr.employee')
        res = {}
        for payslip in self.browse(cr, uid, ids, context=context):
            res[payslip.id] = payslip.employee_id.department_id and payslip.employee_id.department_id.id or False
        return res
    
    def _compute_advance_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for payslip in self.browse(cr, uid, ids, context=context):
            res[payslip.id] = 0.0
            for line in payslip.advance_payment_ids:
                if line.state == 'confirmed':
                    res[payslip.id] += line.amount * line.exchange_rate
        return res
    
    def _compute_overtime_hours(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for payslip in self.browse(cr, uid, ids, context=context):
            res[payslip.id] = 0.0
            for line in payslip.overtime_ids:
                if line.state == 'validate':
                    res[payslip.id] += round(line.number_of_hours_temp * line.rate / 100, 2)
        return res
    
    def _get_attendances(self, cr, uid, ids, name, args, context=None):
        result = {}
        user_pool = self.pool.get('res.users')
        for ho in self.browse(cr, uid, ids, context=context):
            usertz_vs_utctz = user_pool.get_diff_hours_usertz_vs_utctz(cr, ho.employee_id.user_id.id or uid) or 7
            lines = []
            result.setdefault(ho.id, {
                'attendances_ids': lines,
            })
            cr.execute("""
                    SELECT a.id
                      FROM hr_attendance a
                    WHERE   a.action = 'sign_in'
                            AND %(date_to)s >= (a.name + interval '%(usertz_vs_utctz)s hour')::date
                            AND %(date_from)s <= (a.name + interval '%(usertz_vs_utctz)s hour')::date
                            AND %(employee_id)s = a.employee_id
                     GROUP BY a.id""", {'date_from': ho.date_from,
                                        'date_to': ho.date_to,
                                        'usertz_vs_utctz': usertz_vs_utctz,
                                        'employee_id': ho.employee_id.id,})
            lines.extend([row[0] for row in cr.fetchall()])
            result[ho.id]['attendances_ids'] = lines
                
        return result
    
    _columns = {
                'default_work_days': fields.float('Default Work Days'),
                
                'advance_payment_ids':fields.many2many('hr.advance.payment', 'hr_advance_payment_payslip_rel', 'payslip_id', 'payment_id', 'Advance Payments', readonly=True),
                'advance_total': fields.function(_compute_advance_total, string='Advance Total', type='float', digits_compute=dp.get_precision('Payroll'), 
                    store={
                        'hr.payslip': (lambda self, cr, uid, ids, c={}: ids, ['advance_payment_ids'], 10),
                    }, readonly=True),
                
                'attendances_ids' : fields.function(_get_attendances, type='many2many', relation='hr.attendance', method=True, string='Attendances',
#                     store={
#                         'hr.payslip': (lambda self, cr, uid, ids, c={}: ids, ['advance_payment_ids'], 10),
#                     }, 
                    readonly=True, multi="_attendance"),
                
                'overtime_ids':fields.many2many('hr.overtime', 'hr_overtime_payslip_rel', 'payslip_id', 'overtime_id', 'Overtime Requests', readonly=True),
                'overtime_hours': fields.function(_compute_overtime_hours, string='Overtime Hours', type='float', digits=(16,2), 
                    store={
                        'hr.payslip': (lambda self, cr, uid, ids, c={}: ids, ['overtime_ids'], 10),
                    }, readonly=True),
                
                'department_id': fields.function(_get_user_department, type='many2one', relation='hr.department', string='Department',
                    store={
                        'hr.payslip': (lambda self, cr, uid, ids, c={}: ids, ['employee_id'], 10),
                    }, readonly=True),
                }
    _defaults = {
    }
    
    def get_default_worked_day(self, cr, uid, contract_ids, date_from, date_to, context=None):
        number_of_days = 0.0
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            if not contract.working_hours:
                continue
            day_from = datetime.strptime(date_from,"%Y-%m-%d")
            day_to = datetime.strptime(date_to,"%Y-%m-%d")
            nb_of_days = (day_to - day_from).days + 1
            for day in range(0, nb_of_days):
                working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + timedelta(days=day), context)
                if working_hours_on_day:
                    number_of_days += 1.0
        return number_of_days

    def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        empolyee_obj = self.pool.get('hr.employee')
        res = super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id=employee_id, contract_id=contract_id, context=context)
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        employee_id = empolyee_obj.browse(cr, uid, employee_id, context=context)
        if contract_id:
            contract_ids = [contract_id]
        else:
            contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)
        default_work_days = self.get_default_worked_day(cr, uid, contract_ids, date_from, date_to, context)
        res['value']['default_work_days'] = default_work_days
        return res
    
    def _payslip_date(self, cr, uid, ids, forced_user_id=False, context=None):
        for payslip in self.browse(cr, uid, ids, context=context):
            if payslip.contract_id:
                sql = '''SELECT id 
                    FROM hr_payslip 
                    WHERE (date_from <= '%s' and '%s' <= date_to) 
                        AND employee_id=%s
                        AND coalesce(contract_id, %s) = %s
                        AND state != 'cancel'
                        AND id <> %s'''%(payslip.date_to, payslip.date_from, payslip.employee_id.id, 
                                         payslip.contract_id.id or False,
                                         payslip.contract_id.id or False,
                                         payslip.id)
                cr.execute(sql)
                if cr.fetchall():
                    return False
        return True

    _constraints = [
        (_payslip_date, 'You cannot have 2 Payslips that overlap!', ['date_from','date_to']),
    ]
    
    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        def was_on_leave(employee_id, datetime_day, usertz_vs_utctz, context=None):
            res = False
            day = datetime_day.strftime("%Y-%m-%d")
#             holiday_ids = self.pool.get('hr.holidays').search(cr, uid, [('state','=','validate'),('employee_id','=',employee_id),('type','=','remove'),('date_from','<=',day),('date_to','>=',day)])
            #Thanh: Fix Timezone
            cr.execute("""
                    SELECT id, 
                    to_char((date_from + interval '%(usertz_vs_utctz)s hour')::date, 'DD/MM/YYYY') date_from, 
                    to_char((date_to + interval '%(usertz_vs_utctz)s hour')::date, 'DD/MM/YYYY') date_to
                      FROM hr_holidays
                    WHERE   state = 'validate'
                            AND type = 'remove'
                            AND %(date)s >= (date_from + interval '%(usertz_vs_utctz)s hour')::date
                            AND %(date)s <= (date_to + interval '%(usertz_vs_utctz)s hour')::date
                            AND %(employee_id)s = employee_id"""
                                     , {'date': day,
                                        'usertz_vs_utctz': usertz_vs_utctz,
                                        'employee_id': employee_id,})
            holiday_ids = cr.fetchall() #[x[0] for x in cr.fetchall()]
            if holiday_ids and holiday_ids[0]:
                res = [self.pool.get('hr.holidays').browse(cr, uid, holiday_ids[0][0], context=context), holiday_ids[0][1], holiday_ids[0][2]]
            return res
        
        user_pool = self.pool.get('res.users')
        res = []
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            if not contract.working_hours:
                #fill only if the contract as a working schedule linked
                continue
            #Thanh: Add User Timezone Hours
            usertz_vs_utctz = user_pool.get_diff_hours_usertz_vs_utctz(cr, contract.employee_id.user_id.id or uid) or 7
            
            attendances = {
                 'name': _("Normal Working Days paid at 100%"),
                 'sequence': 1,
                 'code': 'WORK100',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            leaves = {}
            day_from = datetime.strptime(date_from,"%Y-%m-%d")
            day_to = datetime.strptime(date_to,"%Y-%m-%d")
            nb_of_days = (day_to - day_from).days + 1
            for day in range(0, nb_of_days):
                working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + timedelta(days=day), context)
                if working_hours_on_day:
                    #the employee had to work
                    leave_type = was_on_leave(contract.employee_id.id, day_from + timedelta(days=day), usertz_vs_utctz, context=context)
                    if leave_type and not leave_type[0].id in leaves:
                        #if he was on leave, fill the leaves dict
                        #Thanh: Fix Group by Leave Requests
#                         if leave_type[0].id in leaves:
#                             leaves[leave_type[0].id]['number_of_days'] += 1.0
#                             leaves[leave_type[0].id]['number_of_hours'] += working_hours_on_day
#                         else:
                        leaves[leave_type[0].id] = {
                            'name': '['+ leave_type[1] + ' / ' + leave_type[2] + '] ' + (leave_type[0].name or leave_type[0].holiday_status_id.name),
                            'sequence': 5,
                            'code': leave_type[0].holiday_status_id.name,
#                                 'number_of_days': 1.0,
                            'number_of_days': leave_type[0].number_of_days_temp,
                            'number_of_hours': leave_type[0].number_of_days_temp * working_hours_on_day,
                            'contract_id': contract.id,
                            'paid_method': leave_type[0].holiday_status_id.paid_method,
                        }
#                     else:
                    #add the input vals to tmp (increment if existing)
                    attendances['number_of_days'] += 1.0
                    attendances['number_of_hours'] += working_hours_on_day
            leaves = [value for key,value in leaves.items()]
            
            #Thanh: Update Worked Days
            for leave in leaves:
                #Thanh: reduce Un-paid Leaved Days
                if leave['paid_method'] == 'un-paid':
                    attendances['number_of_days'] -= leave['number_of_days']
                    attendances['number_of_hours'] -= leave['number_of_hours']
                
            res += [attendances] + leaves
        return res
    
    def compute_sheet(self, cr, uid, ids, context=None):
        context = context or {}
        worked_days_obj = self.pool.get('hr.payslip.worked_days')
        for payslip in self.browse(cr, uid, ids, context=context):
            cr.execute('''SELECT id
            FROM hr_advance_payment
            WHERE employee_id=%s AND date >= '%s' AND date <='%s' and state = 'confirmed'
            '''%(payslip.employee_id.id, payslip.date_from, payslip.date_to))
            advance_payment_ids = [x[0] for x in cr.fetchall()]
            
            cr.execute('''SELECT id
            FROM hr_overtime
            WHERE employee_id=%s AND date_from >= '%s'
                              AND date_to <= '%s'
                              AND state = 'validate'
            '''%(payslip.employee_id.id, payslip.date_from, payslip.date_to))
            overtime_ids = [x[0] for x in cr.fetchall()]
            
            self.write(cr, uid, [payslip.id], {'advance_payment_ids': [(6,0,advance_payment_ids)], 'overtime_ids': [(6,0,overtime_ids)]}, context=context)
        
            if context.get('reload_worked_lines',False):
                old_worked_days_ids = ids and worked_days_obj.search(cr, uid, [('payslip_id', '=', payslip.id)], context=context) or False
                if old_worked_days_ids:
                    worked_days_obj.unlink(cr, uid, old_worked_days_ids, context=context)
                worked_days_line_ids = self.get_worked_day_lines(cr, uid, [payslip.contract_id.id], payslip.date_from, payslip.date_to, context)
                worked_days_line_ids = [(0,0,x) for x in worked_days_line_ids]
                self.write(cr, uid, [payslip.id], {'worked_days_line_ids': worked_days_line_ids,
                                                   }, context=context)
                
        super(hr_payslip, self).compute_sheet(cr, uid, ids, context)
        return True
    
    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context):
        res = super(hr_payslip,self).get_payslip_lines(cr, uid, contract_ids, payslip_id, context)
        
        #Thanh: Add UoM into payslip line
        payslip_rule_pool = self.pool.get('hr.salary.rule')
        result = []
        for line in res:
            uom_id = line['salary_rule_id'] and payslip_rule_pool.browse(cr, uid, line['salary_rule_id']).uom_id.id or False
            line.update({'uom_id': uom_id})
            result.append(line)
            
        return result

hr_payslip()

class hr_payslip_line(osv.osv):
    _inherit = 'hr.payslip.line'

    _columns = {
        #Thanh: Prevent rouding Quantity for these cases (Hours, ...)
        'quantity': fields.float('Quantity', digits_compute=dp.get_precision('Payroll Rate')),
#         'uom_id': fields.related('salary_rule_id', 'uom_id', type="many2one", relation='product.uom', string='UoM', readonly=True, store=True),
        'uom_id': fields.many2one('product.uom', 'UoM'),
    }
    