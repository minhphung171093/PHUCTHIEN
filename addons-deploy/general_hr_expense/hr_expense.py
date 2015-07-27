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

from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_expense_expense(osv.osv):
    _inherit = "hr.expense.expense"
    _description = "Expense"
    _columns = {
                'type': fields.selection([
                        ('advance', 'Advance'),
                        ('expense', 'Expense'),
                        ],
                        'Type', readonly=True),
                
                'job_id':fields.many2one('hr.job','Job', readonly=True, states={'draft': [('readonly', False)]}),
                'department_id':fields.many2one('hr.department','Department', readonly=True, states={'draft': [('readonly', False)]}),
                
                'date_head_valid': fields.date('Head Validation Date', readonly=True, select=True),
                'head_user_valid': fields.many2one('res.users', 'Head Validation By', readonly=True),
                
                'advance_account_id':fields.many2one('account.move', 'Journal Entry', readonly=True),
        
                'state': fields.selection([
                    ('draft', 'New'),
                    ('cancelled', 'Refused'),
                    ('confirm', 'Waiting Approval'),
                    ('accepted', 'Manager Approved'),
                    ('head_accepted', 'Head Approved'),
                    ('done', 'Waiting Payment'),
                    ('paid', 'Paid'),
                    ],
                    'Status', readonly=True, track_visibility='onchange',
                    help='When the expense request is created the status is \'Draft\'.\n It is confirmed by the user and request is sent to admin, the status is \'Waiting Confirmation\'.\
                    \nIf the admin accepts it, the status is \'Accepted\'.\n If the accounting entries are made for the expense request, the status is \'Waiting Payment\'.'),
                
                'related_advance_expense_id': fields.many2one('hr.expense.expense', 'Related Advance Expense', readonly=True),
                'related_expense_expense_id': fields.many2one('hr.expense.expense', 'Related Expense', readonly=True),
                
                'reference': fields.char('Reference', size=32),
                'reference_number': fields.char('Number', size=32),
                
                'payment_lines': fields.one2many('hr.expense.payment', 'expense_id'),
                
                #Overwrite
                'date_confirm': fields.date('Confirmation Date', select=True, readonly=True, help="Date of the confirmation of the sheet expense. It's filled when the button Confirm is pressed."),
                'date_valid': fields.date('Validation Date', select=True, readonly=True, help="Date of the acceptation of the sheet expense. It's filled when the button Accept is pressed."),
                'user_valid': fields.many2one('res.users', 'Validation By', readonly=True),
                'account_move_id': fields.many2one('account.move', 'Ledger Posting', readonly=True),
    }
    
    _defaults = {
        'type': 'expense',
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update(
            account_move_id=False,
            voucher_id=False,
            date_confirm=False,
            date_valid=False,
            user_valid=False,
            
            #Thanh: Update new fields
            related_advance_expense_id=False,
            related_expense_expense_id=False,
            advance_account_id=False,
            date_head_valid=False,
            head_user_valid=False,)
        return super(hr_expense_expense, self).copy(cr, uid, id, default=default, context=context)
    
    #Thanh: Change old function to able to view Advance Expense or Expense Journal Entry
    def action_view_receipt(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing account.move of given expense ids.
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        expense = self.browse(cr, uid, ids[0], context=context)
        account_move_id = False
        if expense.type == 'advance':
            account_move_id = expense.advance_account_id.id
        else:
            account_move_id = expense.account_move_id.id
        
        assert account_move_id
        try:
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'view_move_form')
        except ValueError, e:
            view_id = False
        result = {
            'name': _('Expense Account Move'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': account_move_id,
        }
        return result
    
    #Thanh: New function to view Related Expense from Advance Expense
    def action_view_related_expense(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        expense = self.browse(cr, uid, ids[0], context=context)
        assert expense.related_expense_expense_id
        try:
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_expense', 'view_expenses_form')
        except ValueError, e:
            view_id = False
        result = {
            'name': _('Expenses'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'hr.expense.expense',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': expense.related_expense_expense_id.id,
        }
        return result
    #Thanh: New function to view Related Expense from Advance Expense
    
    #Thanh: New function to create Expense from Advance Expense
    def create_expense_expense(self, cr, uid, ids, context=None):
        default_val = {
                'state': 'draft',
                'type': 'expense',
                'related_advance_expense_id': ids[0],
                'advance_account_id': False,
            }
        new_id = self.copy(cr, uid, ids[0], default_val)
        self.write(cr, uid, ids[0], {'related_expense_expense_id': new_id})
        return new_id
    #Thanh: New function to create Expense from Advance Expense
    
    def move_line_get(self, cr, uid, expense_id, context=None):
        res = []
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        if context is None:
            context = {}
        exp = self.browse(cr, uid, expense_id, context=context)
        company_currency = exp.company_id.currency_id.id
 
        for line in exp.line_ids:
            mres = self.move_line_get_item(cr, uid, line, context)
            if not mres:
                continue
            res.append(mres)
            tax_code_found= False
             
            #Calculate tax according to default tax on product
            taxes = []
            #Taken from product_id_onchange in account.invoice
            if line.product_id:
                fposition_id = False
                fpos_obj = self.pool.get('account.fiscal.position')
                fpos = fposition_id and fpos_obj.browse(cr, uid, fposition_id, context=context) or False
                product = line.product_id
                taxes = product.supplier_taxes_id
                #If taxes are not related to the product, maybe they are in the account
                if not taxes:
                    a = product.property_account_expense.id #Why is not there a check here?
                    if not a:
                        a = product.categ_id.property_account_expense_categ.id
                    a = fpos_obj.map_account(cr, uid, fpos, a)
                    taxes = a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False
                tax_id = fpos_obj.map_tax(cr, uid, fpos, taxes)
            if not taxes:
                continue
            #Calculating tax on the line and creating move?
            for tax in tax_obj.compute_all(cr, uid, taxes,
                    line.unit_amount ,
                    line.unit_quantity, line.product_id,
                    exp.user_id.partner_id)['taxes']:
                tax_code_id = tax['base_code_id']
                tax_amount = line.total_amount * tax['base_sign']
                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(self.move_line_get_item(cr, uid, line, context))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True
                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = cur_obj.compute(cr, uid, exp.currency_id.id, company_currency, tax_amount, context={'date': exp.date_confirm})
                ## 
                is_price_include = tax_obj.read(cr,uid,tax['id'],['price_include'],context)['price_include']
                if is_price_include:
                    ## We need to deduce the price for the tax
                    res[-1]['price'] = res[-1]['price']  - (tax['amount'] * tax['base_sign'] or 0.0)
                assoc_tax = {
                             'type':'tax',
                             'name':tax['name'],
                             'price_unit': tax['price_unit'],
                             'quantity': 1,
                             'price':  tax['amount'] * tax['base_sign'] or 0.0,
                             'account_id': tax['account_collected_id'] or mres['account_id'],
                             'tax_code_id': tax['tax_code_id'],
                             'tax_amount': tax['amount'] * tax['base_sign'],
                             }
                res.append(assoc_tax)
        return res
    
    #Thanh: Modify original function, update Department and Job field when employee change
    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        emp_obj = self.pool.get('hr.employee')
        department_id = False
        company_id = False,
        job_id = False
        if employee_id:
            employee = emp_obj.browse(cr, uid, employee_id, context=context)
            department_id = employee.department_id.id
            company_id = employee.company_id.id
            job_id = employee.job_id.id or False
        return {'value': {'department_id': department_id, 'company_id': company_id,'job_id':job_id}}
    #Thanh: Modify original function, update Department and Job field when employee change
    
    def action_receipt_create(self, cr, uid, ids, context=None):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_obj = self.pool.get('account.move')
        for exp in self.browse(cr, uid, ids, context=context):
            if not exp.employee_id.address_home_id:
                raise osv.except_osv(_('Error!'), _('The employee must have a home address.'))
            if not exp.employee_id.address_home_id.property_account_payable.id:
                raise osv.except_osv(_('Error!'), _('The employee must have a payable account set on his home address.'))
            company_currency = exp.company_id.currency_id.id
            diff_currency_p = exp.currency_id.id <> company_currency
            
            #create the move that will contain the accounting entries
            move_id = move_obj.create(cr, uid, self.account_move_get(cr, uid, exp.id, context=context), context=context)
        
            #one account.move.line per expense line (+taxes..)
            eml = self.move_line_get(cr, uid, exp.id, context=context)
            
            #create one more move line, a counterline for the total on payable account
            total, total_currency, eml = self.compute_expense_totals(cr, uid, exp, company_currency, exp.name, eml, context=context)
            
            
            # Kiet sua add đổi account_id đối ứng
            if total<0:
                acc = exp.journal_id.default_credit_account_id.id
            else:
                acc = exp.journal_id.default_debit_account_id.id
            acc = exp.employee_id.address_home_id.property_account_payable.id
            eml.append({
                    'type': 'dest',
                    'name': '/',
                    'price': total, 
                    'account_id': acc, 
                    'date_maturity': exp.date_confirm, 
                    'amount_currency': diff_currency_p and total_currency or False, 
                    'currency_id': diff_currency_p and exp.currency_id.id or False, 
                    'ref': exp.name
                    })

            #convert eml into an osv-valid format
            lines = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, exp.employee_id.address_home_id, exp.date_confirm, context=context)), eml)
            journal_id = move_obj.browse(cr, uid, move_id, context).journal_id
            # post the journal entry if 'Skip 'Draft' State for Manual Entries' is checked
            if journal_id.entry_posted:
                move_obj.button_validate(cr, uid, [move_id], context)
            move_obj.write(cr, uid, [move_id], {'line_id': lines}, context=context)
            self.write(cr, uid, ids, {'account_move_id': move_id, 'state': 'done'}, context=context)
        return True
    
    def print_report(self, cr, uid, ids, context=None):
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'pdf_report_entertainment_claim',
            }
    
    def print_request_report(self, cr, uid, ids, context=None):
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'pdf_report_entertainment_request',
            }
    
    def head_accepted(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        for expense in self.browse(cr, uid, ids):
            email_template_ids = ir_model_data.search(cr, uid, [('model','=','email.template'),
                                      ('name','=','email_template_advance_manager_approve'),
                                      ('module','=','general_hr_expense')])
            if email_template_ids:
                res_id = ir_model_data.browse(cr, uid, email_template_ids[0]).res_id
                try:
                    self.pool.get('email.template').send_mail(cr, 1,
                                            res_id,
                                            expense.id, False, context=context)
                except:
                    pass
                
        return self.write(cr, uid, ids, {'state': 'head_accepted', 'date_head_valid': time.strftime('%Y-%m-%d'), 'head_user_valid': uid}, context=context)
    
#Thanh: Modify these work-flow function, sending email after confirm, approve or refuse Expenses
    def expense_confirm(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        for expense in self.browse(cr, uid, ids):
            if expense.employee_id and expense.employee_id.parent_id.user_id:
                self.message_subscribe_users(cr, uid, [expense.id], user_ids=[expense.employee_id.parent_id.user_id.id])
                
            if not expense.employee_id.coach_id:
                raise osv.except_osv(_('Warning!'),_("Coach is not set for Employee (%s)."%(expense.employee_id.name)))
            email_template_ids = ir_model_data.search(cr, uid, [('model','=','email.template'),
                                      ('name','=','email_template_advance_submit_to_manager'),
                                      ('module','=','general_hr_expense')])
            if email_template_ids:
                res_id = ir_model_data.browse(cr, uid, email_template_ids[0]).res_id
                try:
                    self.pool.get('email.template').send_mail(cr, 1,
                                            res_id,
                                            expense.id, False, context=context)
                except:
                    pass
            
        return self.write(cr, uid, ids, {'state': 'confirm', 'date_confirm': time.strftime('%Y-%m-%d')}, context=context)
    
    def expense_accept(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        for expense in self.browse(cr, uid, ids):
            if not expense.employee_id.parent_id:
                raise osv.except_osv(_('Warning!'),_("Manager is not set for Employee (%s)."%(expense.employee_id.name)))
            email_template_ids = ir_model_data.search(cr, uid, [('model','=','email.template'),
                                      ('name','=','email_template_advance_approve_to_manager'),
                                      ('module','=','general_hr_expense')])
            if email_template_ids:
                res_id = ir_model_data.browse(cr, uid, email_template_ids[0]).res_id
                try:
                    self.pool.get('email.template').send_mail(cr, 1,
                                            res_id,
                                            expense.id, False, context=context)
                except:
                    pass
                
            email_template_ids = ir_model_data.search(cr, uid, [('model','=','email.template'),
                                      ('name','=','email_template_advance_approve_to_employee'),
                                      ('module','=','general_hr_expense')])
            if email_template_ids:
                res_id = ir_model_data.browse(cr, uid, email_template_ids[0]).res_id
                try:
                    self.pool.get('email.template').send_mail(cr, 1,
                                            res_id,
                                            expense.id, False, context=context)
                except:
                    pass
        
        return self.write(cr, uid, ids, {'state': 'accepted', 'date_valid': time.strftime('%Y-%m-%d'), 'user_valid': uid}, context=context)
    
    def expense_canceled(self, cr, uid, ids, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        for expense in self.browse(cr, uid, ids):
            email_template_ids = False
            if expense.state=='confirm':
                email_template_ids = ir_model_data.search(cr, uid, [('model','=','email.template'),
                                          ('name','=','email_template_advance_coach_refuse'),
                                          ('module','=','general_hr_expense')])
            if expense.state=='accepted':
                email_template_ids = ir_model_data.search(cr, uid, [('model','=','email.template'),
                                          ('name','=','email_template_advance_manager_refuse'),
                                          ('module','=','general_hr_expense')])
            if email_template_ids:
                res_id = ir_model_data.browse(cr, uid, email_template_ids[0]).res_id
                try:
                    self.pool.get('email.template').send_mail(cr, 1,
                                            res_id,
                                            expense.id, False, context=context)
                except:
                    pass
        return self.write(cr, uid, ids, {'state': 'cancelled'}, context=context)
    
hr_expense_expense()

#Thanh: New object for Difference Amount Between Advance Expense and Related Expense
class hr_expense_payment(osv.osv):
    _name = "hr.expense.payment"
    _columns = {
        'journal_id': fields.many2one('account.journal', 'Payment Method', required=True),
        'amount': fields.float('Amount', digits=(16,2), required=True),
        'expense_id': fields.many2one('hr.expense.expense', 'Expense', required=True, ondelete='cascade', select=True),
    }
    _defaults = {
    }
hr_expense_payment()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
