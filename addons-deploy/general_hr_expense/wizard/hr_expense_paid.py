# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################
import time
from datetime import datetime
from osv import fields, osv
from tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import decimal_precision as dp
from tools.translate import _


class hr_expense_paid(osv.osv_memory):
    _name = "hr.expense.paid"

    _columns = {
                'journal_id':fields.many2one('account.journal','Journal',domain="[('type','in',['bank', 'cash'])]", required=False),
                'amount':fields.float('Amount', required=False),
                'date':fields.date('Date', required=True),
                'note': fields.text('Note'),
                }
    
    def _get_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        ids = self.pool.get('account.journal').search(cr, uid, [('type','in',['bank', 'cash'])], context=context)
        if ids:
            return ids[0]
        return False

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'journal_id': _get_journal,
    }
    
    def validate(self, cr, uid, ids, context=None):
        expense = self.pool.get('hr.expense.expense')
        move_obj = self.pool.get('account.move')
        cur_obj = self.pool.get('res.currency')
        wizard = self.browse(cr, uid, ids[0])
        
        for exp in expense.browse(cr, uid, context['active_ids'], context=context):
            expense.write(cr, uid, exp.id, {'journal_id': wizard.journal_id.id}, context=context)
            
            if not exp.employee_id.address_home_id:
                raise osv.except_osv(_('Error!'), _('The employee must have a home address.'))
            if not exp.employee_id.address_home_id.property_account_receivable.id:
                raise osv.except_osv(_('Error!'), _('The employee must have a receivable account set on his home address.'))
            company_currency = exp.company_id.currency_id.id
            diff_currency_p = wizard.journal_id.currency and wizard.journal_id.currency.id <> company_currency or False
                
            if exp.type == 'advance':
                amount_currency = diff_currency_p and cur_obj.compute(cr, uid,
                            company_currency, wizard.journal_id.currency.id, abs(exp.amount),
                            context=context) or False

                #Partner move
                move_line_partner = {
                    'date_maturity': wizard.date,
                    'partner_id': exp.employee_id.address_home_id.id,
                    'name': exp.name,
                    'date': wizard.date,
                    'debit': exp.amount > 0 and exp.amount,
                    'credit': exp.amount < 0 and -exp.amount,
                    'account_id': exp.employee_id.address_home_id.property_account_receivable.id,
                    'analytic_lines': False,
                    'amount_currency': diff_currency_p and amount_currency or False,
                    'currency_id': diff_currency_p and wizard.journal_id.currency.id or False,
                }
                
                #Payment move
                acc_id = False
                if exp.amount < 0:
                    acc_id = wizard.journal_id.default_debit_account_id.id or False
                else:
                    acc_id = wizard.journal_id.default_credit_account_id.id or False
                    
                if not acc_id:
                    raise osv.except_osv(_('Error!'), _('Please define default credit/debit accounts on the journal.'))
                
                move_line_payment = {
                    'date_maturity': wizard.date,
                    'partner_id': exp.employee_id.address_home_id.id,
                    'name': wizard.note or '/',
                    'date': wizard.date,
                    'debit': exp.amount < 0 and -exp.amount,
                    'credit': exp.amount > 0 and exp.amount,
                    'account_id': acc_id,
                    'analytic_lines': False,
                    'amount_currency': diff_currency_p and amount_currency or False,
                    'currency_id': diff_currency_p and wizard.journal_id.currency.id or False,
                }
                
                lines = [(0,0,move_line_partner),(0,0,move_line_payment)]
                move_vals = move_obj.account_move_prepare(cr, uid, wizard.journal_id.id, date=wizard.date, ref=exp.name, company_id=exp.company_id.id, context=context)
                move_vals.update({
                                  'line_id': lines,
                                  'narration': wizard.note or exp.note})
                move_id = move_obj.create(cr, uid, move_vals, context=context)
                move_obj.button_validate(cr, uid, [move_id], context)
                
                expense.write(cr, uid, context['active_ids'], {'advance_account_id': move_id, 'state': 'paid'}, context=context)
            else:
                #Partner move
                move_line_partner = {
                    'date_maturity': wizard.date,
                    'partner_id': exp.employee_id.address_home_id.id,
                    'name': exp.name,
                    'date': wizard.date,
                    'debit': exp.amount > 0 and exp.amount,
                    'credit': exp.amount < 0 and -exp.amount,
                    'account_id': exp.employee_id.address_home_id.property_account_receivable.id,
                    'analytic_lines': False,
                    'amount_currency': diff_currency_p and amount_currency or False,
                    'currency_id': diff_currency_p and wizard.journal_id.currency.id or False,
                }
                
                lines = [(0,0,move_line_partner),(0,0,move_line_payment)]
                move_vals = move_obj.account_move_prepare(cr, uid, wizard.journal_id.id, date=wizard.date, ref=exp.name, company_id=exp.company_id.id, context=context)
                move_vals.update({
                                  'line_id': lines,
                                  'narration': wizard.note or exp.note})
                move_id = move_obj.create(cr, uid, move_vals, context=context)
                move_obj.button_validate(cr, uid, [move_id], context)
                
                expense.write(cr, uid, context['active_ids'], {'account_move_id': move_id, 'state': 'paid'}, context=context)
        return True
    
    def default_get(self, cr, uid, fields, context=None):
        expense_pool =self.pool.get('hr.expense.expense')
        res = super(hr_expense_paid, self).default_get(cr, uid, fields, context=context)
        if context.get('active_ids'):
            expense = expense_pool.browse(cr, uid, context['active_ids'][0])
            if expense.type == 'advance':
                res['amount'] = expense.amount
        return res
        
hr_expense_paid()




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
