# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

import netsvc
from osv import fields, osv
import tools
from tools.translate import _
import decimal_precision as dp
from tools import config
from tools.translate import _

from tools.safe_eval import safe_eval as eval

import logging
_logger = logging.getLogger(__name__)
#===============================================================================
# worked_days
#===============================================================================
class hr_payslip_worked_days(osv.osv):
    _inherit = 'hr.payslip.worked_days'    
    _columns = {        
        'real_number_of_days': fields.float('Number of Worked Days'),
    }    
hr_payslip_worked_days()
#===============================================================================
# hr_salary_rule_category_template
#===============================================================================
class hr_template(osv.osv):
    _name = "hr.template"    
    _columns = {
        'name' : fields.char('Name', 128, required=True),
        'template_line' : fields.one2many('hr.template.line','template_id','Template Line'),        
        }         
    _sql_constraints = [
        ('name_uniq', 'unique (code)', 'The name must be unique !'),    
    ]
    
    def copy(self, cr, uid, ids, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, ids, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['name'] = (record['name'] or '') + '(copy)'        
        return super(hr_template, self).copy(cr, uid, ids, default, context=context)

hr_template()

class hr_template_line(osv.osv):
    _name = "hr.template.line"
    _columns = {
        'name' : fields.many2one('hr.salary.rule.category','Rule Category', required=True),
        'template_id' : fields.many2one('hr.template','Template'),
        'sequence' : fields.integer('Sequence'),
        }             
hr_template()

#===============================================================================
#salary rule category 
#===============================================================================
class hr_salary_rule_category(osv.osv):
    
    _inherit = 'hr.salary.rule.category'
    _columns = {
        'sequence': fields.integer('Sequence'),        
    }
hr_salary_rule_category()

#===============================================================================
# salary rule
#===============================================================================
class hr_salary_rule(osv.osv):

    _inherit = 'hr.salary.rule'
    _order = 'sequence,code'
    _columns = {
        'compute_option':fields.selection([
            ('first','First Month'),
            ('last','Last Month'),
            ('manual_one','One Times in Month'),
            ('manual_many','Many Times in Month'),
            ('all','All Times in Month'),
        ],'Compute Option', required=True),
        
    }
    _defaults = {
        'compute_option': lambda * a: 'all',
        'amount_python_compute': 
'''
# Available variables:
#----------------------
# payslip: object containing the payslips
# p_payslip: object containing the payslip line code (sum of amount of all payslip line with the same rule belonging to history payslips).
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days.
# inputs: object containing the computed inputs.

# Note: returned value have to be set in the variable 'result'

result = contract.wage * 0.10''',
        'condition_python':
'''
# Available variables:
#----------------------
# payslip: object containing the payslips
# p_payslip: object containing the payslip line code (sum of amount of all payslip line with the same rule belonging to history payslips).
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days
# inputs: object containing the computed inputs

# Note: returned value have to be set in the variable 'result'

result = rules.NET > categories.NET * 0.10''',
     }
hr_salary_rule()                

class hr_payslip(osv.osv):

    _inherit = 'hr.payslip'
    
    def _get_p_payslips(self, cr, uid, ids, field_names, arg=None, context=None):
        result = {}
        if not ids: return result
        for slip in self.browse(cr, uid, ids):
            p_payslip_ids = slip.period_id and self.search(cr, uid, [('state','=','done'),('id','!=',slip.id),('employee_id','=',slip.employee_id.id),('period_id','=',slip.period_id.id)]) or []
            result[slip.id] = p_payslip_ids 
        return result

    _columns = {
        'department_id': fields.related('employee_id', 'department_id', type='many2one', relation='hr.department', string='Department', store=True, readonly=True),
        'p_payslips': fields.function(_get_p_payslips, method=True, type='one2many', relation='hr.payslip', string='Payslips'),
    }
    _default = {
     
    }
    
    def compute_sheet(self, cr, uid, ids, context=None):
        slip_line_pool = self.pool.get('hr.payslip.line')
        sequence_obj = self.pool.get('ir.sequence')
        for payslip in self.browse(cr, uid, ids, context=context):            
            number = payslip.number or sequence_obj.get(cr, uid, 'salary.slip')
            #delete old payslip lines
            old_slipline_ids = slip_line_pool.search(cr, uid, [('slip_id', '=', payslip.id)], context=context)
#            old_slipline_ids
            if old_slipline_ids:
                slip_line_pool.unlink(cr, uid, old_slipline_ids, context=context)                
            if payslip.contract_id:
                #set the list of contract for which the rules have to be applied
                contract_ids = [payslip.contract_id.id]                
            else:
                #if we don't give the contract, then the rules to apply should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, payslip.employee_id, payslip.date_from, payslip.date_to, context=context)
            lines = [(0,0,line) for line in self.pool.get('hr.payslip').get_payslip_lines(cr, uid, contract_ids, payslip.id, context=context)]            
            self.write(cr, uid, [payslip.id], {'line_ids': lines, 'number': number,}, context=context)
        return True
    
    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
#        print 'VAO HAM GET WORKED DAYS'
        res = super(hr_payslip, self).get_worked_day_lines(cr, uid, contract_ids, date_from, date_to, context=None)
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
#            if not contract.working_hours:
#                #fill only if the contract as a working schedule linked
#                continue  

            def get_ot(employee_id, date_from, date_to, ot_id):              
                ot_str = ot_id and '= %s'%(ot_id) or 'is null'
                sql = '''SELECT 
                        count(CASE WHEN anl.unit_amount > 0 THEN anl.unit_amount ELSE NULL END) as number_of_days, 
                        sum(anl.unit_amount - (anl.unit_amount *  CASE WHEN anl.to_invoice is not null THEN fa.factor/100 ELSE 0 END)) as number_of_hours
                        FROM hr_analytic_timesheet ant JOIN account_analytic_line anl ON ant.line_id = anl.id
                        LEFT JOIN hr_timesheet_invoice_factor fa ON anl.to_invoice = fa.id
                        WHERE date >= '%s' AND  date <= '%s' 
                        AND ant.employee_id = %s 
                        AND anl.to_invoice %s
                        AND ant.sheet_id IS NOT NULL
                        GROUP BY ant.employee_id'''%(date_from, date_to,employee_id, ot_str)
                cr.execute(sql)
                res = cr.dictfetchone()
                return res and res or {'number_of_days': 0.0, 'number_of_hours': 0.0}
            
            ot_pool = self.pool.get('hr_timesheet_invoice.factor')
            ot_ids = ot_pool.search(cr, uid, [])
            ot_lines = []
            for ot in ot_pool.browse(cr, uid, ot_ids):
                days = get_ot(contract.employee_id.id, date_from, date_to, ot.id)['number_of_days']
                hours = get_ot(contract.employee_id.id, date_from, date_to, ot.id)['number_of_hours']
                ot_line = {
                 'name': ot.name,
                 'sequence': 1,
                 'code': ot.customer_name,
                 'real_number_of_days': contract.salary_type == 'day' and days or hours/8,
                 'number_of_days': days,
                 'number_of_hours': hours,
                 'contract_id': contract.id,
                 }
                ot_lines.append(ot_line)
                       
            res += ot_lines
        return res
    
    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = []
        contract_obj = self.pool.get('hr.contract')
        rule_obj = self.pool.get('hr.salary.rule')

        structure_ids = contract_obj.get_all_structures(cr, uid, contract_ids, context=context)
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        
        depend = {'name': 'DEPEND',
                  'code': 'DEPEND',}
        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
            for rule in rule_obj.browse(cr, uid, sorted_rule_ids, context=context):
                if rule.input_ids:
                    for input in rule.input_ids:
                        inputs = {
                             'name': input.name,
                             'code': input.code,
                             'contract_id': contract.id,
                        }
                        res += [inputs]
            depend.update({'amount': contract.employee_id.depend_qty,'contract_id': contract.id,})            
        res += [depend]
        return res
# check compute option 
    def satisfy_compute_option(self, cr, uid, rule, payslip, context=None):
        compute_option = rule.compute_option
        if compute_option == 'all':
            return 'compute'
        elif (compute_option == 'first' and payslip.period_id and payslip.date_from == payslip.period_id.date_start):
            return 'compute'
        elif (compute_option == 'last' and payslip.period_id and payslip.date_to == payslip.period_id.date_stop):
            return 'compute'
        elif compute_option in ('manual_one', 'manual_many'): 
            p_payslip_ids = [p.id for p in payslip.p_payslips]
            line_exist = self.pool.get('hr.payslip.line').search(cr, uid, [('slip_id','in',p_payslip_ids),('salary_rule_id','=',rule.id)])
#            print 'check compute option', p_payslip_ids, line_exist  
            if compute_option =='manual_one' and len(line_exist)>=1:
#                print 'invalid_manual_one'
                return 'invalid_manual_one'                         
            return 'manual'
        else:
            return 'invalid'
        
# override check compute option        
    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context):
        if context == None: context = {}
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, pool, cr, uid, employee_id, dict):
                self.pool = pool
                self.cr = cr
                self.uid = uid
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(amount) as sum\
                            FROM hr_payslip as hp, hr_payslip_input as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()[0]
                return res or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours\
                            FROM hr_payslip as hp, hr_payslip_worked_days as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done'\
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                return self.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.cr.execute("SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)\
                            FROM hr_payslip as hp, hr_payslip_line as pl \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s",
                            (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()
                return res and res[0] or 0.0
            
        def _sum_payslip_line(localdict, slip_line, amount):
            localdict['p_payslip'].dict[slip_line.code] = slip_line.code in localdict['p_payslip'].dict and localdict['p_payslip'].dict[slip_line.code] + amount or amount
            return localdict

        #we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules = {}
        categories_dict = {}
        p_payslip_lines = {}
        blacklist = []
        obj_rule = self.pool.get('hr.salary.rule')
        payslip_obj = self.pool.get('hr.payslip')
          
        payslip = payslip_obj.browse(cr, uid, payslip_id, context=context)        
        
        worked_days = {}
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days[worked_days_line.code] = worked_days_line
        inputs = {}
        for input_line in payslip.input_line_ids:
            inputs[input_line.code] = input_line

        categories_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, categories_dict)
        input_obj = InputLine(self.pool, cr, uid, payslip.employee_id.id, inputs)
        worked_days_obj = WorkedDays(self.pool, cr, uid, payslip.employee_id.id, worked_days)
        current_payslip_obj = Payslips(self.pool, cr, uid, payslip.employee_id.id, payslip)
        rules_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, rules)        
        p_payslip_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, p_payslip_lines)
        
        localdict = {'p_payslip': p_payslip_obj, 'categories': categories_obj, 'rules': rules_obj, 'payslip': current_payslip_obj, 'worked_days': worked_days_obj, 'inputs': input_obj}
        
        for slip in payslip.p_payslips:
            for line in slip.line_ids:   
                localdict = _sum_payslip_line(localdict, line, line.total)
        
        #get the ids of the structures on the contracts and their parent id as well
        structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        #get the rules of the structure and thier children        
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        ctx_rule_ids = 'rule_ids' in context and rule_ids.extend(context['rule_ids']) or rule_ids
        #run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(list(set(ctx_rule_ids)), key=lambda x:x[1])]

        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            employee = contract.employee_id
            localdict.update({'employee': employee, 'contract': contract})
            for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                # check compute option
                compute_option = self.satisfy_compute_option(cr, uid, rule, payslip, context=None)
#                _logger.warning("%s", 'RULE %s %s compute check %s' % (rule.name, rule.compute_option, compute_option))
                
                if 'rule_ids' in context:
                    if compute_option != 'compute' and (rule.id, rule.sequence) not in context['rule_ids']:
                        continue
                    if compute_option == 'invalid_manual_one' and (rule.id, rule.sequence) in context['rule_ids']:
                        continue
                else:
                    if compute_option != 'compute':
                        continue
                    
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                #check if the rule can be applied
                if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
                    #compute the amount of the rule
                    amount, qty, rate = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    
                    #create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else: 
                    #blacklist this rule and its children
                    blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]

        result = [value for code, value in result_dict.items()]
        return result   
hr_payslip() 
#===============================================================================
# history payslip line with the same rule 
#===============================================================================
#class hr_payslip_line_same_rule(osv.osv):
#    _name = "hr.payslip.line.same.rule"
#    _auto = False
#    _columns = {
#        'name': fields.char('Name', size=64),
#        'code': fields.char('Code', size=64),
#        'rule_id': fields.many2one('hr.salary.rule', 'Rule'),
#        'slip_id': fields.many2one('hr.payslip', 'Payslip'),
#        'total': fields.float('Total'),
#        }
#
#    def init(self, cr):
#        tools.drop_view_if_exists(cr, 'hr_payslip_line_same_rule')
#        cr.execute("""
#            CREATE or REPLACE view hr_payslip_line_same_rule as (
#                 SELECT                 
#                   sum(sl.total) AS total,
#                   sl.salary_rule_id AS rule_id,
#                   sl.name AS name, 
#                   sl.code AS code 
#                FROM
#                    hr_payslip_line sl JOIN hr_payslip pl ON sl.slip_id = pl.id 
#                WHERE
#                    sl.slip_id IN
#                    (SELECT id FROM hr_payslip JOIN account_period ap ON pl.period_id = ap.id  WHERE 
#                GROUP BY
#                    salary_rule_id, name, code
#            )
#        """)
#hr_payslip_line_same_rule()

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
