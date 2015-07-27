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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime
import openerp.addons.decimal_precision as dp

class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'deduct_bank_fee_account_id': fields.many2one(
            'account.account',
            string="Deduct Bank Fee Account",
            domain="[('type', '=', 'other')]",),
                
        'deduct_payment_discount_account_id': fields.many2one(
            'account.account',
            string="Discount Allowed",
            domain="[('type', '=', 'other')]",),
        
        'discount_received_account_id': fields.many2one(
            'account.account',
            string="Discount Received",
            domain="[('type', '=', 'other')]",),
    }

res_company()

class account_config_settings(osv.osv_memory):
    _inherit = 'account.config.settings'
    _columns = {
        'deduct_bank_fee_account_id': fields.related(
            'company_id', 'deduct_bank_fee_account_id',
            type='many2one',
            relation='account.account',
            string="Deduct Bank Fee Account", 
            domain="[('type', '=', 'other')]"),
                
        'deduct_payment_discount_account_id': fields.related(
            'company_id', 'deduct_payment_discount_account_id',
            type="many2one",
            relation='account.account',
            string="Discount Allowed",
            domain="[('type', '=', 'other')]"),
        
        'discount_received_account_id': fields.related(
            'company_id', 'discount_received_account_id',
            type="many2one",
            relation='account.account',
            string="Discount Received",
            domain="[('type', '=', 'other')]"),
    }
    
    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = super(account_config_settings, self).onchange_company_id(cr, uid, ids, company_id, context=context)
        if company_id:
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            res['value'].update({'deduct_bank_fee_account_id': company.deduct_bank_fee_account_id and company.deduct_bank_fee_account_id.id or False, 
                                 'deduct_payment_discount_account_id': company.deduct_payment_discount_account_id and company.deduct_payment_discount_account_id.id or False,
                                 'discount_received_account_id': company.discount_received_account_id and company.discount_received_account_id.id or False})
        else: 
            res['value'].update({'deduct_bank_fee_account_id': False, 
                                 'deduct_payment_discount_account_id': False,
                                 'discount_received_account_id': False})
        return res
    
class account_voucher(osv.osv):
    _inherit = "account.voucher"
    
#     def _get_total_to_apply(self, cr, uid, ids, name, args, context=None):
#         res = {}
#         for voucher in self.browse(cr, uid, ids, context=context):
#             res[voucher.id] = voucher.amount + voucher.bank_fee_deducted + voucher.discount_allowed
#         return res
    
    _columns = {
        'bank_fee_deducted': fields.float('Bank Fee Deducted', digits_compute=dp.get_precision('Account'), required=False, readonly=True, states={'draft':[('readonly',False)]}),
        'discount_allowed': fields.float('Discount Allowed', digits_compute=dp.get_precision('Account'), required=False, readonly=True, states={'draft':[('readonly',False)]}),
        'discount_received': fields.float('Discount Received', digits_compute=dp.get_precision('Account'), required=False, readonly=True, states={'draft':[('readonly',False)]}),
#         'total_to_apply': fields.function(_get_total_to_apply, type='float', string='Total to Apply', digits_compute=dp.get_precision('Account'), readonly=True),
        
        'company_currency_id': fields.related('company_id','currency_id', type='many2one', relation='res.currency', string='Company Currency', readonly=True),
    }
    
    #Thanh: New function creating Bank Fee move line
    def move_line_bank_fee(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        cur_obj = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        
        diff_currency = company_currency <> current_currency
        
        deduct_bank_fee_account_id = voucher.company_id.deduct_bank_fee_account_id
        if not deduct_bank_fee_account_id:
            raise osv.except_osv(_('Insufficient Configuration!'),_("You must set an account for Bank Fees in Settings/Configuration/Accounting."))
        
        ctx = {'date': voucher.date or False}
        debit = credit = voucher.bank_fee_deducted
        amount_currency = 0.0
        if diff_currency:
            debit = credit = cur_obj.compute(cr, uid, current_currency, company_currency, voucher.bank_fee_deducted, context=ctx)
            amount_currency = voucher.bank_fee_deducted
            
        if voucher.type in ('receipt','payment'):
            credit = 0.0
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1

        move_line = {
                'name': u'Phí ngân hàng',
                'debit': debit,
                'credit': credit,
                'account_id': deduct_bank_fee_account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * amount_currency or 0.0,
                'date': voucher.date,
                'date_maturity': voucher.date_due,
                'narration': u'Phí ngân hàng',
            }
        move_line_pool.create(cr, uid, move_line)
        
        sign = credit - debit < 0 and -1 or 1
        move_line_counterpart = {
                'name': u'Đối ứng phí ngân hàng',
                'debit': credit,
                'credit': debit,
                'account_id': voucher.account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * amount_currency or 0.0,
                'date': voucher.date,
                'date_maturity': voucher.date_due,
                'Phí ngân hàng': u'Đối ứng phí ngân hàng',
            }
        move_line_pool.create(cr, uid, move_line_counterpart)
        return True
    
    #Thanh: New function creating Discount Allowed move line
    def move_line_discount_allowed(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        cur_obj = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        
        diff_currency = company_currency <> current_currency
        
        deduct_payment_discount_account_id = voucher.company_id.deduct_payment_discount_account_id
        if not deduct_payment_discount_account_id:
            raise osv.except_osv(_('Insufficient Configuration!'),_("You must set an account for Discounts Allowed in Settings/Configuration/Accounting."))
        
        ctx = {'date': voucher.date or False}
        debit = credit = voucher.discount_allowed
        amount_currency = 0.0
        if diff_currency:
            debit = credit = cur_obj.compute(cr, uid, current_currency, company_currency, voucher.discount_allowed, context=ctx)
            amount_currency = voucher.discount_allowed
            
#         if voucher.type in ('payment'):
#             credit = voucher.paid_amount_in_company_currency
        if voucher.type in ('receipt'):
            credit = 0.0
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1

        move_line = {
                'name': u'Chiết khấu thanh toán cho người mua',
                'debit': debit,
                'credit': credit,
                'account_id': deduct_payment_discount_account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * amount_currency or 0.0,
                'date': voucher.date,
                'date_maturity': voucher.date_due,
                'narration': u'Chiết khấu thanh toán cho người mua',
            }
        move_line_pool.create(cr, uid, move_line)
        
        sign = credit - debit < 0 and -1 or 1
        move_line_counterpart = {
                'name': u'Đối ứng chiết khấu thanh toán cho người mua',
                'debit': credit,
                'credit': debit,
                'account_id': voucher.account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * amount_currency or 0.0,
                'date': voucher.date,
                'date_maturity': voucher.date_due,
                'narration': u'Đối ứng chiết khấu thanh toán cho người mua',
            }
        move_line_pool.create(cr, uid, move_line_counterpart)
        return True
    
    #Thanh: New function creating Discount Received move line
    def move_line_discount_received(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        cur_obj = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        
        diff_currency = company_currency <> current_currency
        
        discount_received_account_id = voucher.company_id.discount_received_account_id
        if not discount_received_account_id:
            raise osv.except_osv(_('Insufficient Configuration!'),_("You must set an account for Discounts Received in Settings/Configuration/Accounting."))
        
        ctx = {'date': voucher.date or False}
        debit = credit = voucher.discount_received
        amount_currency = 0.0
        if diff_currency:
            debit = credit = cur_obj.compute(cr, uid, current_currency, company_currency, voucher.discount_received, context=ctx)
            amount_currency = voucher.discount_received
            
        if voucher.type in ('payment'):
            debit = 0.0
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1

        move_line = {
                'name': u'Chiết khấu thanh toán được hưởng',
                'debit': debit,
                'credit': credit,
                'account_id': discount_received_account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * amount_currency or 0.0,
                'date': voucher.date,
                'date_maturity': voucher.date_due,
                'narration': u'Chiết khấu thanh toán được hưởng',
            }
        move_line_pool.create(cr, uid, move_line)
        
        sign = credit - debit < 0 and -1 or 1
        move_line_counterpart = {
                'name': u'Đối ứng chiết khấu thanh toán được hưởng',
                'debit': credit,
                'credit': debit,
                'account_id': voucher.account_id.id,
                'move_id': move_id,
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'partner_id': voucher.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * amount_currency or 0.0,
                'date': voucher.date,
                'date_maturity': voucher.date_due,
                'narration': u'Đối ứng chiết khấu thanh toán được hưởng',
            }
        move_line_pool.create(cr, uid, move_line_counterpart)
        return True
    
    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            local_context = dict(context, force_company=voucher.journal_id.company_id.id)
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the voucher
            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, local_context), local_context)
            move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
            line_total = move_line_brw.debit - move_line_brw.credit
            rec_list_ids = []
            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, local_context)
            
            #Thanh: Create move for Bank Fee and Discount Allowed
            if voucher.type in ('receipt'):
                if voucher.bank_fee_deducted:    
                    self.move_line_bank_fee(cr, uid, voucher.id, move_id, company_currency, current_currency, context)
                if voucher.discount_allowed:
                    self.move_line_discount_allowed(cr, uid, voucher.id, move_id, company_currency, current_currency, context)
            #Thanh: Create move for Bank Fee and Discount Allowed
            
            #Thanh: Create move for Bank Fee and Discount Receive
            if voucher.type in ('payment'):
                if voucher.bank_fee_deducted:    
                    self.move_line_bank_fee(cr, uid, voucher.id, move_id, company_currency, current_currency, context)
                if voucher.discount_received:
                    self.move_line_discount_received(cr, uid, voucher.id, move_id, company_currency, current_currency, context)
            #Thanh: Create move for Bank Fee and Discount Allowed
            
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
        return True
account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
