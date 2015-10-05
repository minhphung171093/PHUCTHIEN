# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import osv, fields
import decimal_precision as dp
from tools.translate import _

from openerp import SUPERUSER_ID

class account_asset_category(osv.osv):
    _inherit = 'account.asset.category'
    _description = 'Asset category'

    _columns = {
#         'analytics_id': fields.many2one('account.analytic.plan.instance', 'Analytic Distribution'),
        'account_asset_id': fields.many2one('account.account', 'Asset Account', required=True,domain=[('type','<>','view')]),
        'account_depreciation_id': fields.many2one('account.account', 'Depreciation Account', required=True ,domain=[('type','<>','view')]),
        'account_expense_depreciation_id': fields.many2one('account.account', 'Depr. Expense Account', required=False, domain=[('type','<>','view')]),
    }

    _defaults = {
        'prorata':True,
        'method_period': 1,
    }
    
#     def onchange_account_analytic_id(self, cr, uid, ids, account_analytic_id):
#         value = {}
#         if account_analytic_id:
#             value.update({'analytics_id':False})
#         return {'value': value}
    
#     def onchange_analytics_id(self, cr, uid, ids, analytics_id):
#         value = {}
#         if analytics_id:
#             value.update({'account_analytic_id':False})
#         return {'value': value}
    
account_asset_category()

class account_asset_asset(osv.osv):
    _inherit = 'account.asset.asset'
    _description = 'Asset'

    def _amount_amortization(self, cr, uid, ids, name, args, context=None):
        res = {}
        for asset in self.browse(cr, uid, ids, context):
            res[asset.id] = asset.purchase_value - asset.value_residual
        return res


    _columns = {
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', readonly=True, states={'draft':[('readonly',False)]}),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic account'),
#         'analytics_id': fields.many2one('account.analytic.plan.instance', 'Analytic Distribution'),
        'code': fields.char('Asset Code', size=32, readonly=True, states={'draft':[('readonly',False)]}),
        'account_expense_depreciation_id':fields.many2one('account.account', 'Depr. Expense Account', required=True, domain=[('type','<>','view')] , readonly=True, states={'draft':[('readonly',False)]}),
        'asset_type':fields.selection([
                                ('asset', 'Asset'),
                                ('prepaid', 'Prepaid Expense'),
                                ], 'Asset Type',size=32, readonly=True, required=True, states={'draft':[('readonly',False)]} ),
        'voucher_number':fields.char('Voucher Number', size=32,required=True),
        'voucher_date':fields.date('Voucher Date',),
        'value_amortization': fields.function(_amount_amortization, method=True, digits_compute=dp.get_precision('Account'), string='Giá trị đã khấu hao'),
    }
    _defaults = {
        'asset_type': 'asset',
        'voucher_number': '/',
    }
    
    def onchange_category_id(self, cr, uid, ids, category_id, context=None):
        res = {'value':{}}
        asset_categ_obj = self.pool.get('account.asset.category')
        if category_id:
            category_obj = asset_categ_obj.browse(cr, uid, category_id, context=context)
            res['value'] = {
                            'method': category_obj.method,
                            'method_number': category_obj.method_number,
                            'method_time': category_obj.method_time,
                            'method_period': category_obj.method_period,
                            'method_progress_factor': category_obj.method_progress_factor,
                            'method_end': category_obj.method_end,
                            'prorata': category_obj.prorata,
                            'account_expense_depreciation_id':category_obj.account_expense_depreciation_id and category_obj.account_expense_depreciation_id.id or False
            }
        return res
    
#     def onchange_account_analytic_id(self, cr, uid, ids, account_analytic_id):
#         value = {}
#         if account_analytic_id:
#             value.update({'analytics_id':False})
#         return {'value': value}
    
#     def onchange_analytics_id(self, cr, uid, ids, analytics_id):
#         value = {}
#         if analytics_id:
#             value.update({'account_analytic_id':False})
#         return {'value': value}
    
    def _compute_board_undone_dotation_nb(self, cr, uid, asset, depreciation_date, total_days, context=None):
        undone_dotation_number = asset.method_number
        if asset.method_time == 'end':
            end_date = datetime.strptime(asset.method_end, '%Y-%m-%d')
            undone_dotation_number = 0
            while depreciation_date <= end_date:
                depreciation_date = (datetime(depreciation_date.year, depreciation_date.month, depreciation_date.day) + relativedelta(months=+asset.method_period))
                undone_dotation_number += 1
        if asset.prorata:
#             undone_dotation_number += 1
            #Thanh: no need to add one more depreciation time
            undone_dotation_number += 0
        return undone_dotation_number
    
    def compute_depreciation_board(self, cr, uid, ids, context=None):
        depreciation_lin_obj = self.pool.get('account.asset.depreciation.line')
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.value_residual == 0.0:
                continue
            posted_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_check', '=', True)])
            old_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_id', '=', False)])
            if old_depreciation_line_ids:
                depreciation_lin_obj.unlink(cr, uid, old_depreciation_line_ids, context=context)

            amount_to_depr = residual_amount = asset.value_residual
            if asset.prorata:
#                 depreciation_date = datetime.strptime(self._get_last_depreciation_date(cr, uid, [asset.id], context)[asset.id], '%Y-%m-%d')
                depreciation_date = datetime.strptime(asset.purchase_date, '%Y-%m-%d')
            else:
                # depreciation_date = 1st January of purchase year
                purchase_date = datetime.strptime(asset.purchase_date, '%Y-%m-%d')
                depreciation_date = datetime(purchase_date.year, 1, 1)
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366

            undone_dotation_number = self._compute_board_undone_dotation_nb(cr, uid, asset, depreciation_date, total_days, context=context)
            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                i = x + 1
                amount = self._compute_board_amount(cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=context)
                #Thanh: Rounding Depreciation Amount to zero digit
                amount = round(amount,0)
                
                residual_amount -= amount
                vals = {
                     'amount': amount,
                     'asset_id': asset.id,
                     'sequence': i,
                     'name': str(asset.id) +'/' + str(i),
                     'remaining_value': residual_amount,
                     'depreciated_value': (asset.purchase_value - asset.salvage_value) - (residual_amount + amount),
                     'depreciation_date': depreciation_date.strftime('%Y-%m-%d'),
                }
                depreciation_lin_obj.create(cr, uid, vals, context=context)
                # Considering Depr. Period as months
                depreciation_date = (datetime(year, month, day) + relativedelta(months=+asset.method_period))
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year
        return True
    
    def _compute_board_amount(self, cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=None):
        #by default amount = 0
        amount = 0
        if i == undone_dotation_number:
            amount = residual_amount
        else:
            if asset.method == 'linear':
                amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
                #Thanh: No need this feature
#                 if asset.prorata:
#                     amount = amount_to_depr / asset.method_number
#                     days = total_days - float(depreciation_date.strftime('%j'))
#                     if i == 1:
#                         amount = (amount_to_depr / asset.method_number) / total_days * days
#                     elif i == undone_dotation_number:
#                         amount = (amount_to_depr / asset.method_number) / total_days * (total_days - days)
            elif asset.method == 'degressive':
                amount = residual_amount * asset.method_progress_factor
                #Thanh: No need this feature
#                 if asset.prorata:
#                     days = total_days - float(depreciation_date.strftime('%j'))
#                     if i == 1:
#                         amount = (residual_amount * asset.method_progress_factor) / total_days * days
#                     elif i == undone_dotation_number:
#                         amount = (residual_amount * asset.method_progress_factor) / total_days * (total_days - days)
        return amount
    
    def unlink(self, cr, uid, ids, context=None):
        for asset in self.browse(cr, uid, ids):
            if asset.state != 'draft':
                raise osv.except_osv(_('Error !'),
                                _("You just can delete this asset in State 'Draft'"))
        return super(account_asset_asset, self).unlink(cr, uid, ids, context=context)
    
account_asset_asset()

class account_asset_depreciation_line(osv.osv):
    _inherit = 'account.asset.depreciation.line'
    _description = 'Asset depreciation line'

    _columns = {
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True, ondelete='cascade'),
        'warehouse_id': fields.related('asset_id', 'warehouse_id', type='many2one', relation='stock.warehouse', string='Warehouse', readonly=True, store=True),
        'company_id': fields.related('asset_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True, store=True),
    }

    def create_move(self, cr, uid, ids, context=None):
        can_close = False
        if context is None:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            # Kiet: Lay ngay` tren wizard
            #depreciation_date = line.asset_id.prorata and line.asset_id.purchase_date or time.strftime('%Y-%m-%d')
            if 'date' in context and context['date']:
                depreciation_date = context['date']
            else:
                depreciation_date = time.strftime('%Y-%m-%d')
                
            period_ids = period_obj.find(cr, uid, depreciation_date, context=context)
            company_currency = line.asset_id.company_id.currency_id.id
            current_currency = line.asset_id.currency_id.id
            context.update({'date': depreciation_date})
            #Thanh: Round Depreciation Amount to zero digit
            amount = round(currency_obj.compute(cr, uid, current_currency, company_currency, line.amount, context=context),0)
            sign = line.asset_id.category_id.journal_id.type = 'purchase' and 1 or -1
            asset_name = line.asset_id.name
            reference = line.depreciation_date  + (line.asset_id.code and ': ' + line.asset_id.code or '')
            
            #Thanh: Get related Shop of Warehouse
            shop_id = False
            if line.asset_id.warehouse_id:
                sql='''
                    SELECT id FROM sale_shop WHERE warehouse_id = %s
                '''%(line.asset_id.warehouse_id.id)
                cr.execute(sql)
                shop_res = cr.fetchone()
                shop_id = shop_res and shop_res[0] or False
                
            move_vals = {
                'name': '/',
                'date': depreciation_date,
                'ref': reference,
                'date_document':depreciation_date,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': line.asset_id.category_id.journal_id.id,
                'warehouse_id': line.asset_id.warehouse_id and line.asset_id.warehouse_id.id or False,
                'shop_id': shop_id,
                'source_obj': 'account_asset_asset',
                'narration': asset_name,
                }
            move_id = move_obj.create(cr, 1, move_vals, context=context)
            journal_id = line.asset_id.category_id.journal_id.id
            partner_id = line.asset_id.partner_id.id
            move_line_obj.create(cr, 1, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_depreciation_id.id,
                'debit': 0.0,
                'credit': amount,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and - sign * line.amount or 0.0,
                'date': depreciation_date,
                'source_obj': 'account.asset.asset',
            })
            move_line_obj.create(cr, 1, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.account_expense_depreciation_id.id,
                'credit': 0.0,
                'debit': amount,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * line.amount or 0.0,
                'analytic_account_id': line.asset_id.account_analytic_id.id or False,
#                 'analytics_id': line.asset_id.analytics_id.id or False,
                'date': depreciation_date,
                'asset_id': line.asset_id.id,
                'source_obj': 'account.asset.asset',
            })
            self.write(cr, 1, line.id, {'move_id': move_id}, context=context)
            created_move_ids.append(move_id)
            asset_ids.append(line.asset_id.id)
#             if can_close:
#                 asset_obj.write(cr, 1, [line.asset_id.id], {'state': 'close'}, context=context)
            if move_id:
                move_obj.post(cr,1,[move_id],context)
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(cr, uid, list(set(asset_ids)), context=context):
            if currency_obj.is_zero(cr, uid, asset.currency_id, asset.value_residual):
                asset.write({'state': 'close'})
        return created_move_ids
    

account_asset_depreciation_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
