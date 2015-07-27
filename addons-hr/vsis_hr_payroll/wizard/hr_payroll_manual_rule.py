# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from osv import fields, osv
from openerp.tools.translate import _


class hr_manual_rule(osv.osv_memory):

    _name = "hr.manual.rule"
    _description = "Select manual rule"
    _columns = {
        'rule_ids':fields.many2many('hr.salary.rule', 'hr_structure_salary_rule_manual_rel', 'struct_id', 'rule_id', 'Salary Rules', domain=[('compute_option','in',('manual_one', 'manual_many'))]),
    }
    _defaults= {
        
    }
#TODO: default manual rule belong to structure of employee, domain rule_ids get manual rule of employee

#    def on_change_rule(self, cr, uid, ids, context=None):
#        
#        return

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id',False)
        res = {}
        contract_ids = []
        payslip_obj = self.pool.get('hr.payslip')
        rule_obj = self.pool.get('hr.salary.rule')
        payslip = payslip_obj.browse(cr, uid, record_id, context=context)
        if payslip.contract_id:
            contract_ids = [payslip.contract_id.id]
        else:
            contract_ids = self.get_contract(cr, uid, payslip.employee_id, payslip.date_from, payslip.date_to, context=context)
        structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)    
        struct_rule_ids = [x[0] for x in rule_ids]
        exist_slip_rule_ids = [x.salary_rule_id.id for x in payslip.line_ids]
        valid_rule_ids = rule_obj.search(cr, uid, [('id','in', struct_rule_ids),('id','not in', exist_slip_rule_ids),('compute_option','in', ('manual_one','manual_many'))])
        
        for rule in rule_obj.browse(cr, uid, valid_rule_ids):
            compute_option = payslip_obj.satisfy_compute_option(cr, uid, rule, payslip, context=None)
            if compute_option != 'manual':
                valid_rule_ids.remove(rule.id)  
        res.update({'rule_ids': valid_rule_ids})
        
        return res
    
    def compute_sheet(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        # include valid rule in context, call method compute_sheet 
        wizard = self.browse(cr, uid, ids, context=context)[0]
        rule_ids = [(x.id,x.sequence) for x in wizard.rule_ids]
        ctx = context.copy()
        ctx.update({'rule_ids': rule_ids})
        active_ids = context and context.get('active_id',False)
        payslip_obj = self.pool.get('hr.payslip')
        rule_obj = self.pool.get('hr.salary.rule')
        payslip = payslip_obj.browse(cr, uid, active_ids, context=context)
        
        for rule in rule_obj.browse(cr, uid, [x.id for x in wizard.rule_ids]):
            compute_option = payslip_obj.satisfy_compute_option(cr, uid, rule, payslip, context=None)
            if compute_option == 'invalid_manual_one':
                raise osv.except_osv(
                         _("Invalid Action"),
                         _("You cannot compute rule %s many time in month. Please check compute option for this rule!") % (rule.name,))

        self.pool.get('hr.payslip').compute_sheet(cr, uid, [active_ids], context=ctx)
        return {
                'nodestroy': True,
                }
        
hr_manual_rule()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
