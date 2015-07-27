# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round
from lxml import etree

class account_tax_code(osv.osv):
    _inherit = 'account.tax.code'
    
    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        #Thanh: Just get name only
        reads = self.read(cr, uid, ids, ['name','code'], context, load='_classic_write')
#         return [(x['id'], (x['code'] and (x['code'] + ' - ') or '') + x['name']) \
#                 for x in reads]
        return [(x['id'], x['name']) for x in reads]
        
account_tax_code()

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'
    
    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        #Thanh: Just get name only
#         for id in ids:
#             elmt = self.browse(cr, uid, id, context=context)
#             res.append((id, self._get_one_full_name(elmt)))
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            res.append((id, elmt.name))
        return res
    
account_analytic_account()
  
class account_journal(osv.osv):
    _inherit = "account.journal"
 
    _columns = {
        #Thanh: Link Bank Account to Journal
        'res_partner_bank_id': fields.many2one('res.partner.bank', 'Bank Account'),
        'shop_ids': fields.many2many('sale.shop', 'account_journal_shop_rel', 'journal_id', 'shop_id', 'Shops'),
    }
     
account_journal()

class account_tax(osv.osv):
    _inherit = 'account.tax'
    _columns = {
    }
    
    def _unit_compute_inv(self, cr, uid, taxes, price_unit, product=None, partner=None):
        taxes = self._applicable(cr, uid, taxes, price_unit,  product, partner)
        res = []
        taxes.reverse()
        cur_price_unit = price_unit

        tax_parent_tot = 0.0
        for tax in taxes:
            if (tax.type=='percent') and not tax.include_base_amount:
                tax_parent_tot += tax.amount

        for tax in taxes:
            if (tax.type=='fixed') and not tax.include_base_amount:
                cur_price_unit -= tax.amount
        
        #Thanh: Compute for Tax based on after compute previous Tax (Like special tax after compute VAT) -- Reorder Taxes
        if taxes:
            cr.execute("SELECT id FROM account_tax WHERE id in (%s) order by sequence"%(','.join(map(str, [x.id for x in taxes]))))
            taxes = self.browse(cr, uid, [x[0] for x in cr.fetchall()])
        #Thanh: Compute for Tax based on after compute previous Tax (Like special tax after compute VAT) -- Reorder Taxes
        for tax in taxes:
            if tax.type=='percent':
                if tax.include_base_amount:
                    amount = cur_price_unit - (cur_price_unit / (1 + tax.amount))
                else:
                    amount = (cur_price_unit / (1 + tax_parent_tot)) * tax.amount

            elif tax.type=='fixed':
                amount = tax.amount

            elif tax.type=='code':
                localdict = {'price_unit':cur_price_unit, 'product':product, 'partner':partner}
                exec tax.python_compute_inv in localdict
                amount = localdict['result']
            elif tax.type=='balance':
                amount = cur_price_unit - reduce(lambda x,y: y.get('amount',0.0)+x, res, 0.0)

            if tax.include_base_amount:
                cur_price_unit -= amount
                todo = 0
            else:
                todo = 1
            res.append({
                'id': tax.id,
                'todo': todo,
                'name': tax.name,
                'amount': amount,
                'account_collected_id': tax.account_collected_id.id,
                'account_paid_id': tax.account_paid_id.id,
                'account_analytic_collected_id': tax.account_analytic_collected_id.id,
                'account_analytic_paid_id': tax.account_analytic_paid_id.id,
                'base_code_id': tax.base_code_id.id,
                'ref_base_code_id': tax.ref_base_code_id.id,
                'sequence': tax.sequence,
                'base_sign': tax.base_sign,
                'tax_sign': tax.tax_sign,
                'ref_base_sign': tax.ref_base_sign,
                'ref_tax_sign': tax.ref_tax_sign,
                'price_unit': cur_price_unit,
                'tax_code_id': tax.tax_code_id.id,
                'ref_tax_code_id': tax.ref_tax_code_id.id,
            })
            if tax.child_ids:
                if tax.child_depend:
                    del res[-1]
                    amount = price_unit

            parent_tax = self._unit_compute_inv(cr, uid, tax.child_ids, amount, product, partner)
            res.extend(parent_tax)

        total = 0.0
        for r in res:
            if r['todo']:
                total += r['amount']
        for r in res:
            r['price_unit'] -= total
            r['todo'] = 0
        return res
    
    def _unit_compute(self, cr, uid, taxes, price_unit, product=None, partner=None, quantity=0):
        taxes = self._applicable(cr, uid, taxes, price_unit ,product, partner)
        res = []
        cur_price_unit=price_unit
        #Thanh: Compute for Tax based on after compute previous Tax (Like special tax after compute VAT) -- Reorder Taxes
        if taxes:
            cr.execute("SELECT id FROM account_tax WHERE id in (%s) order by sequence"%(','.join(map(str, [x.id for x in taxes]))))
            taxes = self.browse(cr, uid, [x[0] for x in cr.fetchall()])
        #Thanh: Compute for Tax based on after compute previous Tax (Like special tax after compute VAT) -- Reorder Taxes
        for tax in taxes:
            # we compute the amount for the current tax object and append it to the result
            data = {'id':tax.id,
                    'name':tax.description and tax.description + " - " + tax.name or tax.name,
                    'account_collected_id':tax.account_collected_id.id,
                    'account_paid_id':tax.account_paid_id.id,
                    'account_analytic_collected_id': tax.account_analytic_collected_id.id,
                    'account_analytic_paid_id': tax.account_analytic_paid_id.id,
                    'base_code_id': tax.base_code_id.id,
                    'ref_base_code_id': tax.ref_base_code_id.id,
                    'sequence': tax.sequence,
                    'base_sign': tax.base_sign,
                    'tax_sign': tax.tax_sign,
                    'ref_base_sign': tax.ref_base_sign,
                    'ref_tax_sign': tax.ref_tax_sign,
                    'price_unit': cur_price_unit,
                    'tax_code_id': tax.tax_code_id.id,
                    'ref_tax_code_id': tax.ref_tax_code_id.id,
            }
            res.append(data)
            if tax.type=='percent':
                amount = cur_price_unit * tax.amount
                data['amount'] = amount

            elif tax.type=='fixed':
                data['amount'] = tax.amount
                data['tax_amount']=quantity
               # data['amount'] = quantity
            elif tax.type=='code':
                localdict = {'price_unit':cur_price_unit, 'product':product, 'partner':partner}
                exec tax.python_compute in localdict
                amount = localdict['result']
                data['amount'] = amount
            elif tax.type=='balance':
                data['amount'] = cur_price_unit - reduce(lambda x,y: y.get('amount',0.0)+x, res, 0.0)
                data['balance'] = cur_price_unit

            amount2 = data.get('amount', 0.0)
            if tax.child_ids:
                if tax.child_depend:
                    latest = res.pop()
                amount = amount2
                child_tax = self._unit_compute(cr, uid, tax.child_ids, amount, product, partner, quantity)
                res.extend(child_tax)
                for child in child_tax:
                    amount2 += child.get('amount', 0.0)
                if tax.child_depend:
                    for r in res:
                        for name in ('base','ref_base'):
                            if latest[name+'_code_id'] and latest[name+'_sign'] and not r[name+'_code_id']:
                                r[name+'_code_id'] = latest[name+'_code_id']
                                r[name+'_sign'] = latest[name+'_sign']
                                r['price_unit'] = latest['price_unit']
                                latest[name+'_code_id'] = False
                        for name in ('tax','ref_tax'):
                            if latest[name+'_code_id'] and latest[name+'_sign'] and not r[name+'_code_id']:
                                r[name+'_code_id'] = latest[name+'_code_id']
                                r[name+'_sign'] = latest[name+'_sign']
                                r['amount'] = data['amount']
                                latest[name+'_code_id'] = False
            if tax.include_base_amount:
                cur_price_unit+=amount2
            
        return res
    
account_tax()

class account_account(osv.osv):
    _inherit = "account.account"
    _columns = {
        # 'bank_account_id': fields.many2one('res.partner.bank', 'Bank Account'),
    }
    
account_account()

class account_payment_term(osv.osv):
    _inherit = "account.payment.term"
    _columns = {
    }

    def compute(self, cr, uid, id, value, date_ref=False, context=None):
        if not date_ref:
            date_ref = datetime.now().strftime('%Y-%m-%d')
        pt = self.browse(cr, uid, id, context=context)
        amount = value
        result = []
        obj_precision = self.pool.get('decimal.precision')
        prec = obj_precision.precision_get(cr, uid, 'Account')
        for line in pt.line_ids:
            if line.value == 'fixed':
                amt = round(line.value_amount, prec)
            elif line.value == 'procent':
                amt = round(value * line.value_amount, prec)
            elif line.value == 'balance':
                amt = round(amount, prec)
            if amt or value == 1:
                next_date = (datetime.strptime(date_ref, '%Y-%m-%d') + relativedelta(days=line.days))
                if line.days2 < 0:
                    next_first_date = next_date + relativedelta(day=1,months=1) #Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=line.days2)
                if line.days2 > 0:
                    next_date += relativedelta(day=line.days2, months=1)
                result.append( (next_date.strftime('%Y-%m-%d'), amt) )
                amount -= amt

        amount = reduce(lambda x,y: x+y[1], result, 0.0)
        dist = round(value-amount, prec)
        if dist:
            result.append( (time.strftime('%Y-%m-%d'), dist) )
        return result
    
account_payment_term()
# class account_tax(osv.osv):
#     _inherit = "account.tax"
#     _columns = {
#     }
#     
#     #Thanh: Show All Tax for Supplier Invoice Refund
#     def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
#         journal_pool = self.pool.get('account.journal')
# 
#         if context and context.has_key('type'):
#             if context.get('type') in ('out_invoice','out_refund'):
#                 args += [('type_tax_use','in',['sale','all'])]
#             elif context.get('type') in ('in_invoice','in_refund'):
#                 domain = ('type_tax_use','in',['purchase','all'])
#                 #Thanh: add more domain
#                 if context.get('type') == 'in_refund':
#                     domain = ('type_tax_use','in',['purchase','all','sale'])
#                 args += [domain]
# 
#         if context and context.has_key('journal_id'):
#             journal = journal_pool.browse(cr, uid, context.get('journal_id'))
#             if journal.type in ('sale', 'purchase'):
#                 args += [('type_tax_use','in',[journal.type,'all'])]
# 
#         return super(osv.osv, self).search(cr, uid, args, offset, limit, order, context, count)
#     
# account_tax()

class account_move(osv.osv):
    _inherit = "account.move"

    def name_get(self, cursor, user, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            return []
        res = []
        data_move = self.pool.get('account.move').browse(cursor, user, ids, context=context)
        for move in data_move:
            name = move.name or move.ref
            res.append((move.id, name))
        return res
    
    _columns = {
        'ref_number': fields.char('Reference Number', size=64, states={'posted':[('readonly',True)]}),
        'date_document': fields.date('Document Date', states={'posted':[('readonly',True)]}),
        
        'account_model_id': fields.many2one('account.model', 'Model', states={'posted':[('readonly',True)]}),
        'shop_id': fields.many2one('sale.shop', 'Shop', states={'posted':[('readonly',True)]}),
        'invoice_date':fields.date('Invoice Date', states={'posted':[('readonly',True)]}),
        'unshow_financial_report':fields.boolean('Không khai báo thuế')
    }
    
    def _get_shop_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid)
        return user.context_shop_id.id or False
    
    _defaults = {
#         'date_document': fields.date.context_today,
        'shop_id': _get_shop_id,
        'unshow_financial_report':False
    }
    
    def onchage_account_model(self, cr, uid, ids, account_model_id, period_id, date):
        if not account_model_id:
            return True
        model = self.pool.get('account.model').browse(cr, uid, account_model_id)
        default = {
            'value': {'line_id': [] ,'journal_id': model.journal_id.id, 'narration': model.name},
        }
        for line in model.lines_id:
            val = {
                    'journal_id': model.journal_id.id,
                    'period_id': period_id,
                    'analytic_account_id': line.analytic_account_id.id or False,
                    'name': line.name,
                    'quantity': line.quantity,
                    'debit': line.debit,
                    'credit': line.credit,
                    'account_id': line.account_id.id,
                    'partner_id': line.partner_id.id,
                    'date': date,
                    'date_created': date,
#                     'date_maturity': date_maturity
                }
            default['value']['line_id'].append(val)
        return default
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('date',False) and not vals.get('date_document',False):
            vals.update({'date_document': vals['date']})
        return super(account_move, self).create(cr, uid, vals, context)
    
    def _auto_init(self, cr, context=None):
        super(account_move, self)._auto_init(cr, context)
        cr.execute('''
        UPDATE account_move
        SET date_document = date
        where date_document IS NULL
        ''')
        
account_move()

views_account_move_line = {'search':'view_account_move_line_filter',
                           'tree':'view_move_line_tree',
                           'form':'view_move_line_form'}

class account_move_line(osv.osv):
    _inherit = "account.move.line"
    _order = "date desc, date_maturity, sequence"
    
    _columns = {
#         #'warehouse_id': fields.related('move_id', 'warehouse_id', type='many2one', relation='stock.warehouse', string='Warehouse', readonly=True, store=True),
#         'warehouse_id': fields.many2one('stock.warehouse', string='Warehouse'),
#         'location_id': fields.many2one('stock.location', 'Location'),
#         'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice line'),
#         'stock_move_id': fields.many2one('stock.move', 'Stock Move'),
#         'source_obj': fields.char('Source Object', size=61),
        'sequence': fields.integer('Sequence', readonly=True),
        'shop_id': fields.related('move_id', 'shop_id', type='many2one', relation='sale.shop', string='Shop', readonly=True, store=True),
        'ref_number': fields.char('Reference Number', size=64),
#         'line_type':fields.integer('Line Type'),
#         'quantity': fields.float('Quantity', digits=(16,3), help="The optional quantity expressed by this line, eg: number of product sold. The quantity is not a legal requirement but is very useful for some reports."),
    }
    _defaults = {
    }
    
       
    def _update_check(self, cr, uid, ids, context=None):
        reconcile_obj = self.pool.get('account.move.reconcile')
        done = {}
        for line in self.browse(cr, uid, ids, context=context):
            err_msg = _('Move name (id): %s (%s)') % (line.move_id.name, str(line.move_id.id))
            if line.move_id.state <> 'draft' and (not line.journal_id.entry_posted):
                raise osv.except_osv(_('Error !'), _('You can not do this modification on a confirmed entry! You can just change some non legal fields or you must unconfirm the journal entry first! \n%s') % err_msg)
            #Thanh: Allow delete Reconcilie Entry
            if line.reconcile_id:
                reconcile_obj.unlink(cr, uid, [line.reconcile_id.id], context)
#                 raise osv.except_osv(_('Error !'), _('You can not do this modification on a reconciled entry! You can just change some non legal fields or you must unreconcile first!\n%s') % err_msg)
            t = (line.journal_id.id, line.period_id.id)
            if t not in done:
                self._update_journal_check(cr, uid, line.journal_id.id, line.period_id.id, context)
                done[t] = True
        return True
    
#     def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
#         mod_obj = self.pool.get('ir.model.data')
#         if context is None: context = {}
#         if view_type in ['search','tree','form']:
#             xml_view_id = views_account_move_line.get(view_type,False)
#             result = mod_obj.get_object_reference(cr, uid, 'account', xml_view_id)
#             view_id = result and result[1] or False
#         res = super(osv.osv, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
#         return res
    
    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids):
            if line.move_id:
                update_ids = self.search(cr, uid,[('move_id','=',line.move_id.id),('sequence','>',line.sequence)])
                if update_ids:
                    cr.execute("UPDATE account_move_line SET sequence=sequence-5 WHERE id in %s",(tuple(update_ids),))
        return super(account_move_line, self).unlink(cr, uid, ids, context)  
    
    def create(self, cr, uid, vals, context=None):
            
        if vals.get('move_id',False):
            if not vals.get('sequence',False):
                args = [('move_id', '=', vals['move_id'])]
                if vals.get('debit',0.0):
                    args.append(('debit', '!=', 0.0))
                vals['sequence'] = len(self.search(cr, uid,args)) + 5
            if vals.get('debit',0.0):
                update_ids = self.search(cr, uid,[('move_id','=',vals['move_id']),('sequence','>',vals['sequence'] - 5)])
                if update_ids:
                    cr.execute("UPDATE account_move_line SET sequence=sequence+5 WHERE id in %s",(tuple(update_ids),))
        return super(account_move_line, self).create(cr, uid, vals, context)
    
    #Thanh: Allow add Account Tax and auto generate Move line for tax
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        if context is None:
            context={}
        move_obj = self.pool.get('account.move')
        account_obj = self.pool.get('account.account')
        journal_obj = self.pool.get('account.journal')
        tax_obj = self.pool.get('account.tax')
        if isinstance(ids, (int, long)):
            ids = [ids]
        #Thanh: Allow add Account Tax and auto generate Move line for tax
        if vals.get('account_tax_id', False):
            for line in self.browse(cr, uid, ids, context=context):
                tax_id = tax_obj.browse(cr, uid, vals['account_tax_id'])
                debit = vals.get('debit', line.debit)
                credit = vals.get('credit', line.credit)
                total = debit - credit
#             if journal.type in ('purchase_refund', 'sale_refund'):
#                 base_code = 'ref_base_code_id'
#                 tax_code = 'ref_tax_code_id'
#                 account_id = 'account_paid_id'
#                 base_sign = 'ref_base_sign'
#                 tax_sign = 'ref_tax_sign'
#             else:
                base_code = 'base_code_id'
                tax_code = 'tax_code_id'
                account_id = 'account_collected_id'
                base_sign = 'base_sign'
                tax_sign = 'tax_sign'
                tmp_cnt = 0
                for tax in tax_obj.compute_all(cr, uid, [tax_id], total, 1.00, force_excluded=True).get('taxes'):
                    #create the base movement
                    if tmp_cnt == 0:
                        if tax[base_code]:
                            tmp_cnt += 1
                            self.write(cr, uid, [line.id], {
                                'tax_code_id': tax[base_code],
                                'tax_amount': tax[base_sign] * abs(total)
                            })
                    else:
                        data = {
                            'move_id': line.move_id.id,
                            'name': tools.ustr(line.name or '') + ' ' + tools.ustr(tax['name'] or ''),
                            'date': line.date,
                            'partner_id': line.partner_id.id or False,
                            'ref': line.ref or False,
                            'account_tax_id': False,
                            'tax_code_id': tax[base_code],
                            'tax_amount': tax[base_sign] * abs(total),
                            'account_id': line.account_id.id,
                            'credit': 0.0,
                            'debit': 0.0,
                            'sequence': line.sequence,
                        }
                        if data['tax_code_id']:
                            self.create(cr, uid, data, context)
                    #create the Tax movement
                    data = {
                        'move_id': line.move_id.id,
                        'name': tools.ustr(line.name or '') + ' ' + tools.ustr(tax['name'] or ''),
                        'date': line.date,
                        'partner_id': line.partner_id.id or False,
                        'ref': line.ref or False,
                        'account_tax_id': False,
                        'tax_code_id': tax[tax_code],
                        'tax_amount': tax[tax_sign] * abs(tax['amount']),
                        'account_id': tax[account_id] or line.account_id.id,
                        'credit': tax['amount']<0 and -tax['amount'] or 0.0,
                        'debit': tax['amount']>0 and tax['amount'] or 0.0,
                        'sequence': line.sequence,
                    }
                    if data['tax_code_id']:
                        self.create(cr, uid, data, context)
            del vals['account_tax_id']
#             raise osv.except_osv(_('Unable to change tax!'), _('You cannot change the tax, you should remove and recreate lines.'))
        if ('account_id' in vals) and not account_obj.read(cr, uid, vals['account_id'], ['active'])['active']:
            raise osv.except_osv(_('Bad Account!'), _('You cannot use an inactive account.'))
        if update_check:
            if ('account_id' in vals) or ('journal_id' in vals) or ('period_id' in vals) or ('move_id' in vals) or ('debit' in vals) or ('credit' in vals) or ('date' in vals):
                self._update_check(cr, uid, ids, context)

        todo_date = None
        if vals.get('date', False):
            todo_date = vals['date']
            del vals['date']

        for line in self.browse(cr, uid, ids, context=context):
            ctx = context.copy()
            if not ctx.get('journal_id'):
                if line.move_id:
                   ctx['journal_id'] = line.move_id.journal_id.id
                else:
                    ctx['journal_id'] = line.journal_id.id
            if not ctx.get('period_id'):
                if line.move_id:
                    ctx['period_id'] = line.move_id.period_id.id
                else:
                    ctx['period_id'] = line.period_id.id
            #Check for centralisation
            journal = journal_obj.browse(cr, uid, ctx['journal_id'], context=ctx)
            if journal.centralisation:
                self._check_moves(cr, uid, context=ctx)
        #Thanh: get super osv.osv instead of account.move.line
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        if check:
            done = []
            for line in self.browse(cr, uid, ids):
                if line.move_id.id not in done:
                    done.append(line.move_id.id)
                    move_obj.validate(cr, uid, [line.move_id.id], context)
                    if todo_date:
                        move_obj.write(cr, uid, [line.move_id.id], {'date': todo_date}, context=context)
        return result
    
#     def _auto_init(self, cr, context=None):
#         super(account_move, self)._auto_init(cr, context)
#         cr.execute('''
#         UPDATE account_move_line
#         SET date = date,
#         where date_document IS NULL
#         ''')
        
account_move_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
