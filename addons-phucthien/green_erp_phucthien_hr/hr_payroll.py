# # -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import httplib
from openerp import SUPERUSER_ID

class hr_payslip(osv.osv):
    _inherit = 'hr.payslip'
    
    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        def was_on_leave(employee_id, datetime_day, context=None):
            res = False
            day = datetime_day.strftime("%Y-%m-%d")
            holiday_ids = self.pool.get('hr.holidays').search(cr, uid, [('state','=','validate'),('employee_id','=',employee_id),('type','=','remove'),('date_from','<=',day),('date_to','>=',day)])
            if holiday_ids:
                res = self.pool.get('hr.holidays').browse(cr, uid, holiday_ids, context=context)[0].holiday_status_id.name
            return res

        res = []
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            if not contract.working_hours:
                continue
            attendances = {
                 'name': _("Normal Working Days paid at 100%"),
                 'sequence': 1,
                 'code': 'Normal',
                 'number_of_days': 26,
                 'number_of_hours': 208,
                 'contract_id': contract.id,
            }
            res += [attendances]
        return res
    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = []
        contract_obj = self.pool.get('hr.contract')
        rule_obj = self.pool.get('hr.salary.rule')

        structure_ids = contract_obj.get_all_structures(cr, uid, contract_ids, context=context)
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
        
        depend = {'name': 'Người phụ thuộc',
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
    
hr_payslip()

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
        'name' : fields.many2one('hr.salary.rule','Rule', required=True),
        'template_id' : fields.many2one('hr.template','Template'),
        'sequence' : fields.integer('Sequence'),
        }             
hr_template_line()

    
