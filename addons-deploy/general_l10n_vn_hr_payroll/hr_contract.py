#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

from openerp import netsvc
from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

from openerp.tools.safe_eval import safe_eval as eval

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    _description = 'Contract'
    
    def _get_default_working_hours(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        calendar_ids = self.pool.get('resource.calendar').search(cr, uid, [('company_id','=',company_id)], context=context)
        return calendar_ids and calendar_ids[0] or False
    
    _columns = {
        'other_wage': fields.float('Other Wage', digits=(16,2), required=True, help='Use this field to calculate Insurances'),
        
        #Set Working Schedule to be required - Relating to calculate Default Working Days
        'working_hours': fields.many2one('resource.calendar','Working Schedule', required=True),
        
        #Overtime Section
        'overtime_rate': fields.float('Amount by an Hour', digits=(16,2), required=True),
        'hours_by_day': fields.float('Hours by day', digits=(16,2), required=True),
        'days_by_month': fields.float('Days by month', digits=(16,2), required=True),
        
        #Setting Salary Rules
        'contract_salary_rule_ids': fields.one2many('hr.contract.salary.rule', 'contract_id', 'Salary Rules')
    }
    
    _defaults ={
                'other_wage': 0.0,
                'overtime_rate': 0.0,
                'hours_by_day': 8,
                'days_by_month': 26,
                
                'working_hours': _get_default_working_hours,
                }
    
#     def create(self, cr, uid, vals, context=None):
#         if vals.get('insurance_method',False) and vals['insurance_method'] == 'on_wage':
#             vals['wage_extra'] = 0.0
#         return super(hr_contract, self).create(cr, uid, vals, context)
    
hr_contract()

class hr_contract_salary_rule(osv.osv):
    _name = 'hr.contract.salary.rule'
    _description = 'Contract Salary Rules'
    _order = 'sequence'
    
    def _onchange_salary_rule(self, cr, uid, ids, context=None):
        # direct access to the m2m table is the less convoluted way to achieve this (and is ok ACL-wise)
        cr.execute('''SELECT id FROM hr_contract_salary_rule
        WHERE salary_rule_id in (%s)
        '''%(','.join(map(str, ids))))
        return [i[0] for i in cr.fetchall()]
    
    _columns = {
        'contract_id': fields.many2one('hr.contract', 'Contract', required=True, ondelete='cascade'),
        'salary_rule_id': fields.many2one('hr.salary.rule', 'Rule', required=True),
        'sequence': fields.related('salary_rule_id', 'sequence', type='integer', readonly=True, 
               store={
                'hr.contract.salary.rule': (lambda self, cr, uid, ids, c={}: ids, ['salary_rule_id'], 10),
                'hr.salary.rule': (_onchange_salary_rule, ['sequence'], 10)}, 
               string='Sequence'),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Payroll'), required=True),
    }
    
    _defaults ={
    }
hr_contract_salary_rule()