# -*- coding: utf-8 -*-
import time
from lxml import etree
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare
import netsvc
from openerp import tools
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

def resolve_o2m_operations(cr, uid, target_osv, operations, fields, context):
    results = []
    for operation in operations:
        result = None
        if not isinstance(operation, (list, tuple)):
            result = target_osv.read(cr, uid, operation, fields, context=context)
        elif operation[0] == 0:
            # may be necessary to check if all the fields are here and get the default values?
            result = operation[2]
        elif operation[0] == 1:
            result = target_osv.read(cr, uid, operation[1], fields, context=context)
            if not result: result = {}
            result.update(operation[2])
        elif operation[0] == 4:
            result = target_osv.read(cr, uid, operation[1], fields, context=context)
        if result != None:
            results.append(result)
    return results

class invoice(osv.osv):
    _inherit = 'account.invoice'

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')

        inv = self.browse(cr, uid, ids[0], context=context)
        return {
            'name':_("Pay Invoice"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
                #Thanh: Remove Reference
                'default_reference': inv.reference,
                'default_reference_number': inv.reference_number,
                'close_after_process': True,
                'invoice_type': inv.type,
                'invoice_id': inv.id,
                'default_shop_id':inv.shop_id.id or False,
                'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
            }
        }

invoice()

class account_voucher_batch(osv.osv):
    _name = 'account.voucher.batch'
    _order = 'name desc'
    
    def _get_total(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            amount = 0.0
            for voucher in record.voucher_lines:
                amount += voucher.amount
            res[record.id] =  amount
        return res
    
    _columns = {
            'name': fields.char('Number', size=128, required=False, readonly=False),
            'shop_id': fields.many2one('sale.shop', 'Shop', required=True, states={'draft':[('readonly',False)]}),
            'description': fields.text('Description', required=True),
            'date': fields.date('Date', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'assign_user': fields.char('Assign User', size = 128, required = True, readonly=True, states={'draft':[('readonly',False)]},),
            'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'voucher_lines': fields.one2many('account.voucher', 'batch_id', 'Voucher lines', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'account_id':fields.many2one('account.account', 'Account', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'type':fields.selection(
                [('receive','Receive'),
                 ('payment','Payment'),
                ], 'Type', size=32),
                
            'write_date':  fields.datetime('Last Modification', readonly=True),
            'create_date': fields.datetime('Creation Date', readonly=True),
            'write_uid':  fields.many2one('res.users', 'Updated by', readonly=True),
            'create_uid': fields.many2one('res.users', 'Created by', readonly=True),
            
            'amount': fields.function(_get_total, string='Amount', type='float', digits_compute=dp.get_precision('Account'), readonly=True), 
                                               
            'state':fields.selection(
                [('draft','Draft'),
                 ('cancel','Cancelled'),
                 ('posted','Posted')
                ], 'Status', readonly=True, size=32),
            'partner_bank_id':fields.many2one('res.partner.bank', 'Partner Bank', required=False, readonly=True, states={'draft':[('readonly',False)]}),
            'company_bank_id':fields.many2one('res.partner.bank', 'Company Bank', required=False, readonly=True, states={'draft':[('readonly',False)]}),
        }
    
    def _get_assign_user(self, cr, uid, context=None):
        res = self.pool.get('res.users').read(cr, uid, uid, ['name'])['name']
        return res
    
    def _get_journal(self, cr, uid, context=None):
        ttype = ['cash','bank']
        journal_pool = self.pool.get('account.journal')
        res = journal_pool.search(cr, uid, [('type', 'in', ttype)], limit=1)
        return res and res[0] or False
    
    def _get_shop_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid)
        return user.context_shop_id.id or False
    
    _defaults = {
        'state': 'draft',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'assign_user':_get_assign_user,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher.batch',context=c),
        #get Bank and Cash Journal firstly
        'journal_id':_get_journal,
        'shop_id': _get_shop_id,
        'type': 'payment',
    }
    
    def onchange_journal(self, cr, uid, ids, journal_id, context=None):
        if not journal_id:
            return False
        res = {'value': {}}
        if journal_id:
            journal_data = self.pool.get('account.journal').browse(cr, uid,journal_id)
            res['value']['account_id'] = journal_data.default_debit_account_id.id or journal_data.default_credit_account_id.id or False
        return res
    
    def validate(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for record in self.browse(cr, uid, ids, context=context):
            for voucher in record.voucher_lines:
                if record.state == 'draft':
                    wf_service.trg_validate(uid, 'account.voucher', voucher.id, 'proforma_voucher', cr)
            number = record.name
            if not record.name:
                number = self.pool.get('ir.sequence').get(cr, uid, 'account.voucher.batch')
            self.write(cr, uid, [record.id], {'state':'posted','name':number})
        return True
    
    def cancel(self, cr, uid, ids, context=None):
#         wf_service = netsvc.LocalService("workflow")
#         for record in self.browse(cr, uid, ids, context=context):
#             for voucher in record.voucher_lines:
#                 if record.state in ['draft','posted']:
#                     wf_service.trg_validate(uid, 'account.voucher', voucher.id, 'cancel_voucher', cr)
        
        voucher_pool = self.pool.get('account.voucher')
        for record in self.browse(cr, uid, ids, context=context):
            for voucher in record.voucher_lines:
                if record.state in ['draft','posted']:
                    voucher_pool.cancel_voucher(cr, uid, [voucher.id])
                      
        self.write(cr, uid, ids, {'state':'cancel'})
        return True
    
    def action_cancel_draft(self, cr, uid, ids, context=None):
        voucher_pool = self.pool.get('account.voucher')
        for record in self.browse(cr, uid, ids, context=context):
            for voucher in record.voucher_lines:
                if record.state in ['cancel']:
                    voucher_pool.action_cancel_draft(cr, uid, [voucher.id])
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        journal_obj = self.pool.get('account.journal')
        partner_banks_pool = self.pool.get('res.partner.bank')
        if context is None:
            context = {}
        res = super(account_voucher_batch,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        type = context.get('voucher_journal_type', False)
                
        doc = etree.XML(res['arch'])
        if type and type[0] == 'cash':
            for node in doc.xpath("//field[@name='company_bank_id']"):
                node.set('invisible', '1')
            for node in doc.xpath("//field[@name='partner_bank_id']"):
                node.set('invisible', '1')
            
            xarch, xfields = self._view_look_dom_arch(cr, uid, doc, view_id, context=context)
            res['arch'] = xarch
            res['fields'] = xfields
        
        for field in res['fields']:
            if field == 'journal_id' and type:
                journal_select = journal_obj._name_search(cr, uid, '', [('type', 'in', type)], context=context, limit=None, name_get_uid=1)
                res['fields'][field]['selection'] = journal_select
                
            if field == 'company_bank_id':
                company = self.pool.get('res.users').browse(cr, uid, uid).company_id
                banks_ids = partner_banks_pool.search(cr, uid, [('partner_id','=', company.partner_id.id)])
                partner_banks_ids = [(line.id, line.bank_name) for line in partner_banks_pool.browse(cr, uid, banks_ids)] 
                res['fields'][field]['selection'] = partner_banks_ids
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        for t in self.read(cr, uid, ids, ['state'], context=context):
            if t['state'] not in ('draft', 'cancel'):
                raise osv.except_osv(_('Invalid Action!'), _('Cannot delete Voucher Batch which are already posted.'))
        return super(account_voucher_batch, self).unlink(cr, uid, ids, context=context)
    
    def print_phieuchi(self, cr, uid, ids, context=None): 
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'general_phieu_chi',
            }
account_voucher_batch()

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
        result = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=context)
        if result == {} or not result:
            result = {'value':{}}
        if partner_id:
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
            result['value'].update({'number_register':p.number_register})
        return result

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        journal_obj = self.pool.get('account.journal')
        partner_banks_pool = self.pool.get('res.partner.bank')
        own_id = False
        if context is None:
            context = {}
        res = super(account_voucher,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        type = context.get('voucher_journal_type', False)
        for field in res['fields']:
            if field == 'journal_id' and type:
                journal_select = journal_obj._name_search(cr, uid, '', [('type', 'in', type)], context=context, limit=None, name_get_uid=1)
                res['fields'][field]['selection'] = journal_select
            
            if field == 'company_bank_id':
                for com in self.pool.get('res.users').browse(cr,uid,[uid]):
                    own_id = com.company_id.id
                banks_ids = partner_banks_pool.search(cr,uid,[('partner_id','=',own_id)])
                partner_banks_ids = [(line.id, line.bank_name) for line in partner_banks_pool.browse(cr, uid, banks_ids)] 
                res['fields'][field]['selection'] = partner_banks_ids
        return res
    
    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        if not journal_id:
            return False
        res = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=context)
        if journal_id:
            journal_data = self.pool.get('account.journal').browse(cr, uid,journal_id)
            res['value']['account_id'] = journal_data.default_debit_account_id.id or journal_data.default_credit_account_id.id or False
        return res
    
    _columns = {
            'number': fields.char('Number', size=32, readonly=False),
            'shop_id': fields.many2one('sale.shop', 'Shop', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'number_register': fields.char('Number Register', size=64, readonly=True, states={'draft':[('readonly',False)]}),
            'reference_number': fields.char('Number', size=32, readonly=True, states={'draft':[('readonly',False)]}),
            'assign_user': fields.char('Assign User', size = 128, required = True, readonly=True, states={'draft':[('readonly',False)]},),
            'partner_id':fields.many2one('res.partner', 'Partner', change_default=1, required = False,readonly=True, states={'draft':[('readonly',False)]}),
            'date':fields.date('Date', required = True, readonly=True, select=True, states={'draft':[('readonly',False)]}, help="Effective date for accounting entries"),
            'date_document': fields.date('Document Date', readonly=True, states={'draft':[('readonly',False)]},),
            'tax_amount':fields.float('Tax Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly',False)]}),
            
            'batch_id': fields.many2one('account.voucher.batch', 'Related Batch', ondelete='cascade'),
            'partner_bank_id':fields.many2one('res.partner.bank', 'Partner Bank', required=False, readonly=True, states={'draft':[('readonly',False)]}),
            'company_bank_id':fields.many2one('res.partner.bank', 'Company Bank', required=False, readonly=True, states={'draft':[('readonly',False)]}),
            'unshow_financial_report':fields.boolean('Không khai báo thuế')
        }
    
    def _get_assign_user(self, cr, uid, context=None):
        res = self.pool.get('res.users').read(cr, uid, uid, ['name'])['name']
        return res
#    
    def _make_journal_search(self, cr, uid, ttype, context=None):
        journal_pool = self.pool.get('account.journal')
        return journal_pool.search(cr, uid, [('type', 'in', ttype)], limit=1)
    
    def _get_journal(self, cr, uid, context=None):
        if context is None: context = {}
        invoice_pool = self.pool.get('account.invoice')
        journal_pool = self.pool.get('account.journal')
        if context.get('invoice_id', False):
            currency_id = invoice_pool.browse(cr, uid, context['invoice_id'], context=context).currency_id.id
            journal_id = journal_pool.search(cr, uid, [('currency', '=', currency_id)], limit=1)
            return journal_id and journal_id[0] or False
        if context.get('journal_id', False):
            return context.get('journal_id')
        if not context.get('journal_id', False) and context.get('search_default_journal_id', False):
            return context.get('search_default_journal_id')

#         ttype = context.get('type', 'bank')
#         if ttype in ('payment', 'receipt'):
#             ttype = 'bank'

        #Thanh: Always get type cash and bank
        ttype = ['cash','bank']
        res = self._make_journal_search(cr, uid, ttype, context=context)
        return res and res[0] or False
    
    def _get_shop_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid)
        return user.context_shop_id.id or False
    
    _defaults = {
        'assign_user':_get_assign_user,
        
        #get Bank and Cash Journal firstly
        'journal_id':_get_journal,
        'shop_id': _get_shop_id,
        'unshow_financial_report':False
    }
    
    def _check_amount(self, cr, uid, ids, context=None):
        context = context or {}
        account_voucher = self.browse(cr,uid,ids[0])
        type = context.get('type',False)
        if type and type =='general':
            return True
        
#         if account_voucher.type == 'receipt' and account_voucher.amount < 0:
#             raise osv.except_osv(_('Error !'), _('Paid Amount must be greater than 0'))
#         if account_voucher.type == 'payment' and account_voucher.amount < 0:
#             raise osv.except_osv(_('Error !'), _('Paid Amount must be greater than 0'))
        return True

    _constraints = [
        (_check_amount, 'Wrong amount', []),
    ]
    
    def onchange_tax_amount(self, cr, uid, ids, line_ids, tax_amount, context=None):
        context = context or {}
        line_pool = self.pool.get('account.voucher.line')
        if not line_ids:
            line_ids = []
        res = {
            'amount': False,
        }
        voucher_total = 0.0

        line_ids = resolve_o2m_operations(cr, uid, line_pool, line_ids, ["amount"], context)

        for line in line_ids:
            line_amount = 0.0
            line_amount = line.get('amount',0.0)
            voucher_total += line_amount
        total = voucher_total + tax_amount

        res.update({
            'amount': total or voucher_total,
        })
        return {
            'value': res
        }
        
    def _auto_init(self, cr, context=None):
        super(account_voucher, self)._auto_init(cr, context)
        cr.execute('''
        select avh.id, rp.name
        from account_voucher avh join res_users u on avh.write_uid = u.id
        join res_partner rp on u.partner_id = rp.id
        where avh.assign_user IS NULL
        ''')
        res = cr.fetchall()
        for line in res:
            cr.execute("UPDATE account_voucher SET assign_user='%s' WHERE id=%s"%(line[1],line[0]))
        
        #Thanh: update Document Date
        cr.execute('''
        UPDATE account_voucher
        SET date_document = date
        where date_document IS NULL
        ''')
        
        #Thanh: Update Voucher Narration (Noi Dung Thu Chi) dua vao Line dau tien cua Voucher Line
        ids = self.search(cr, SUPERUSER_ID, [('narration','=',False)])
        for id in ids:
            cr.execute('''
                UPDATE account_voucher
                SET narration = (select name from account_voucher_line avl where avl.voucher_id=%s limit 1)
                WHERE id=%s
                '''%(id,id))
        
    def create(self, cr, uid, vals, context=None):
        if vals.get('date',False) and not vals.get('date_document',False):
            vals.update({'date_document': vals['date']})
        return super(account_voucher, self).create(cr, uid, vals, context)
    
#     def onchange_price(self, cr, uid, ids, line_ids, tax_id, partner_id=False, context=None):
#         context = context or {}
# #         tax_pool = self.pool.get('account.tax')
# #         partner_pool = self.pool.get('res.partner')
# #         position_pool = self.pool.get('account.fiscal.position')
#         line_pool = self.pool.get('account.voucher.line')
#         res = {
#             'tax_amount': False,
#             'amount': False,
#         }
#         voucher_total = 0.0
# 
#         line_ids = resolve_o2m_operations(cr, uid, line_pool, line_ids, ["tax_amount","amount"], context)
# 
#         total_tax = 0.0
#         for line in line_ids:
#             line_amount = 0.0
#             line_amount = line.get('amount',0.0)
# 
# #             if tax_id:
# #                 tax = [tax_pool.browse(cr, uid, tax_id, context=context)]
# #                 if partner_id:
# #                     partner = partner_pool.browse(cr, uid, partner_id, context=context) or False
# #                     taxes = position_pool.map_tax(cr, uid, partner and partner.property_account_position or False, tax)
# #                     tax = tax_pool.browse(cr, uid, taxes, context=context)
# # 
# #                 if not tax[0].price_include:
# #                     for tax_line in tax_pool.compute_all(cr, uid, tax, line_amount, 1).get('taxes', []):
# #                         total_tax += tax_line.get('amount')
#             #Thanh: Change the way of getting Tax Amount
#             total_tax += line.get('tax_amount',0.0)
#             #Thanh: Change the way of getting Tax Amount
# 
#             voucher_total += line_amount
#         total = voucher_total
# 
#         res.update({
#             'amount': total or voucher_total,
#             'tax_amount': total_tax
#         })
#         return {
#             'value': res
#         }
        
    def account_move_get(self, cr, uid, voucher_id, context=None):
        seq_obj = self.pool.get('ir.sequence')
        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        if voucher_brw.number:
            name = voucher_brw.number
        elif voucher_brw.journal_id.sequence_id:
            if not voucher_brw.journal_id.sequence_id.active:
                raise osv.except_osv(_('Configuration Error !'),
                    _('Please activate the sequence of selected journal !'))
            c = dict(context)
            c.update({'fiscalyear_id': voucher_brw.period_id.fiscalyear_id.id})
            name = seq_obj.next_by_id(cr, uid, voucher_brw.journal_id.sequence_id.id, context=c)
        else:
            raise osv.except_osv(_('Error!'),
                        _('Please define a sequence on the journal.'))
        if not voucher_brw.reference:
            ref = name.replace('/','')
        else:
            ref = voucher_brw.reference

        move = {
            'name': name,
            'journal_id': voucher_brw.journal_id.id,
            'narration': voucher_brw.narration,
            'date': voucher_brw.date,
            'date_document': voucher_brw.date_document,
            'ref': ref,
            #Thanh: update reference_number
            'ref_number': voucher_brw.reference_number,
            'shop_id': voucher_brw.shop_id.id or False,
            #Thanh: update reference_number
            'period_id': voucher_brw.period_id.id,
            'unshow_financial_report':voucher_brw.unshow_financial_report or False
        }
        return move
    
#     #Thanh: If Voucher Line is added Tax then create Move Line for that Tax
#     def get_tax_entry(self, cr, uid, line, move_id, context=None):
#         context = context or {}
#         cur_obj = self.pool.get('res.currency')
#         tax = line.tax_id
#         voucher_brw = line.voucher_id
#         company_currency = voucher_brw.company_id.currency_id.id or False
#         move_line = {
#                 'journal_id': voucher_brw.journal_id.id or False,
#                 'period_id': voucher_brw.period_id.id or False,
#                 'name':tax.description and tax.description + " - " + tax.name or tax.name,
#                 'account_id': tax.account_collected_id.id,
#                 'move_id': move_id,
#                 'partner_id': voucher_brw.partner_id.id or False,
#                 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
#                 'quantity': 1,
#                 'date': voucher_brw.date,
#                 'tax_code_id': tax.tax_code_id.id or False,
#                 'credit': 0.0,
#                 'debit': 0.0,
# #                 'tax_amount': line.tax_amount,
#             }
#         if voucher_brw.journal_id.currency and voucher_brw.journal_id.currency.id != company_currency:
#             context.update({'date': voucher_brw.date or time.strftime('%Y-%m-%d')})
#             move_line['currency_id'] = voucher_brw.journal_id.currency.id
#             move_line['amount_currency'] = line.tax_amount or 0.0
#             comp_cur_tax_amount = cur_obj.compute(cr, uid, voucher_brw.journal_id.currency.id,
#                     company_currency, line.tax_amount,
#                     context=context)
#             if line.type == 'cr':
#                 move_line['credit'] = comp_cur_tax_amount
#             else:
#                 move_line['debit'] = comp_cur_tax_amount
#         else:
#             move_line['amount_currency'] = False
#             move_line['currency_id'] = False
#             if line.type == 'cr':
#                 move_line['credit'] = line.tax_amount
#             else:
#                 move_line['debit'] = line.tax_amount
#         return move_line
    
    
    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        tot_line = line_total
        rec_lst_ids = []

        date = self.read(cr, uid, voucher_id, ['date'], context=context)['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
        voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
            'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        for line in voucher.line_ids:
            #create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
                sign = voucher.type in ('payment', 'purchase') and -1 or 1
                currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            move_line = {
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher.date
            }
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount
            
            #Thanh: Get Amount Tax on Form View, not compute from Line
#             if voucher.tax_id and voucher.type in ('sale', 'purchase'):
#                 move_line.update({
#                     'account_tax_id': voucher.tax_id.id,
#                 })
            
            
#             if move_line.get('account_tax_id', False):
#                 tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
#                 if not (tax_data.base_code_id and tax_data.tax_code_id):
#                     raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
            #Thanh: Get Amount Tax on Form View, not compute from Line
            
            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                if line.amount == line.amount_unreconciled:
                    sign = voucher.type in ('payment', 'purchase') and -1 or 1
                    foreign_currency_diff = sign * line.move_line_id.amount_residual_currency + amount_currency

            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)
            rec_ids = [voucher_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': -1 * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,
                }
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        
        #Thanh: Generate Tax Move Line
        if voucher.tax_id and voucher.type in ('sale', 'purchase'):
#             if voucher.tax_amount > 0:
            tax = tax_obj.browse(cr, uid, voucher.tax_id.id, context=context)
            #create the Tax movement
            data = {
                'move_id': move_id,
                'name': tools.ustr(line.name or ''),
                'partner_id': voucher.partner_id.id or False,
                'ref': False,
                'account_tax_id': False,
                'tax_code_id': tax.tax_code_id.id or False,
                'tax_amount': tax.tax_sign * abs(voucher.tax_amount),
                'account_id': tax.account_collected_id.id or False,
            }
            if data['tax_code_id']:
                move_line_obj.create(cr, uid, data, context)
            if voucher.type == 'purchase':
                data.update({'debit': voucher.tax_amount})
            else:
                data.update({'credit': voucher.tax_amount})
#             else:
#                 raise osv.except_osv(_('Tax amount Error!'),_("Tax amount must be bigger than zero!"))
        #Thanh: Generate Tax Move Line
        
        return (tot_line, rec_lst_ids)
            
    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
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
            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context), context)
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
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, context)
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            
            #Thanh: Auto update Narration when confirm a Voucher
            cr.execute('''
                UPDATE account_voucher
                SET narration = (select name from account_voucher_line avl where avl.voucher_id=%s limit 1)
                WHERE id=%s and narration is null
                '''%(voucher.id,voucher.id))
            #Thanh: Auto update Narration when confirm a Voucher
            
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
            
            #Thanh: Remove unpaid voucher line
            cr.execute("DELETE FROM account_voucher_line WHERE voucher_id=%s AND reconcile=False AND amount=0.0"%(voucher.id))
        return True
    
    #Thanh: Order Move Line by Due Date (Paying the older invoice firstly)
    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()
        if date:
            context_multi_currency.update({'date': date})

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')

        #set default values
        default = {
            'value': {'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
        }

        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id
        account_id = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id

        default['value']['account_id'] = account_id

        if journal.type not in ('cash', 'bank'):
            return default

        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'
        if ttype == 'payment':
            account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            account_type = 'receivable'
        
        #Thanh: Order Move Line by Due Date (Paying the older invoice firstly)
        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], 
                                        order='date_maturity', context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_line_found = False

        #order the lines by most old first
#         ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_line_found = line.id
                    break
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_line_found = line.id
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_line_found = line.id
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        #voucher line creation
        for line in account_move_lines:

            if _remove_noise_in_o2m():
                continue

            if line.currency_id and currency_id==line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual))
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': (move_line_found == line.id) and min(abs(price), amount_unreconciled) or 0.0,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            if not move_line_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        rs['amount'] = amount
                        total_debit -= amount
                    else:
                        amount = min(amount_unreconciled, abs(total_credit))
                        rs['amount'] = amount
                        total_credit -= amount

            if rs['amount_unreconciled'] == rs['amount']:
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
        return default
    
    def print_phieuthu(self, cr, uid, ids, context=None): 
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'general_phieu_thu',
            }
    
account_voucher()