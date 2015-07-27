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
from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import openerp.addons.decimal_precision as dp
from lxml import etree

class receivable_payable_reconciliation(osv.osv_memory):
    _name = 'receivable.payable.reconciliation'
    _columns = {
        'date': fields.date('Date', required=True),
        'journal_id': fields.many2one('account.journal', 'Journal', required=False),
        'invoice_balance':fields.float('Invoice Balance', digits_compute=dp.get_precision('Account'), readonly=True),
        'invoice_ids': fields.one2many('receivable.payable.reconciliation.line', 'receivable_payable_reconciliation_id', 'Reconciled Invoices'),
    }
    _defaults = {
        'date': time.strftime(DEFAULT_SERVER_DATE_FORMAT),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        res = {}
        res = super(receivable_payable_reconciliation, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id',False):
            active_obj = self.pool.get('account.invoice').browse(cr,uid,context['active_id'])
            res.update({'invoice_balance': active_obj.residual}) 
        return res
    
    def reconcile(self,cr,uid,ids,context=None):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        this = self.browse(cr,uid,ids[0])
        current_invoice = self.pool.get('account.invoice').browse(cr,uid,context['active_id'])
        journal_id = current_invoice.journal_id.id
        
        sum_invoice_rec = 0.0
        for line in this.invoice_ids:
            sum_invoice_rec += line.paid_amount
        
        if sum_invoice_rec >= this.invoice_balance:
            raise osv.except_osv(_('Error!'), _('Allocated amount is not correct for Invoices!'))
        
        for line in this.invoice_ids:
            invoice_rec = line.invoice_id
            
            #Thanh Create Account Move for Reconciliation
            name = current_invoice.reference
            name += '/' + (current_invoice.reference_number or current_invoice.supplier_invoice_number)
            move = {
                'name': line.note or name,
                'ref': current_invoice.reference,
                'ref_number': current_invoice.reference_number,
                'shop_id': current_invoice.shop_id.id or False,
                'journal_id': journal_id,
                'date': this.date,
                'date_document': this.date,
                'narration': line.note or '',
                'company_id': current_invoice.company_id.id,
            }
            move_id = move_obj.create(cr, uid, move, context=context)
            #Thanh Update many2many on each invoice
#             invoice_obj.write(cr, uid, [current_invoice.id, invoice_rec.id], {'reconciliation_move_ids': [(5,0,[move_id])]})
            
            cr.execute('''
            INSERT INTO reconciliation_move_rel
            VALUES(%s,%s);
            INSERT INTO reconciliation_move_rel
            VALUES(%s,%s);
            '''%(current_invoice.id,move_id, invoice_rec.id,move_id))
            
            invoice_move = {
                    'name': line.note or name,
                    'partner_id': current_invoice.partner_id.parent_id and current_invoice.partner_id.parent_id.id or current_invoice.partner_id.id,
                    'product_id': False,
                    'quantity': False,
                    'ref': name,
                    'date': this.date,
                    'debit': current_invoice.type in ['in_invoice'] and line.paid_amount or 0.0,
                    'credit': current_invoice.type in ['out_invoice'] and line.paid_amount or 0.0,
                    'account_id': current_invoice.account_id.id,
                    'move_id': move_id,
                    }
            invoice_move_line_id = move_line_pool.create(cr, uid, invoice_move, context=context)
            #Thanh: Reconcile current invoice firstly
            cr.execute("SELECT id FROM account_move_line WHERE move_id=%s AND account_id=%s"%(current_invoice.move_id.id, current_invoice.account_id.id))
            rec_ids = [x[0] for x in cr.fetchall()]
            if rec_ids:
                rec_ids.append(invoice_move_line_id)
                move_line_pool.reconcile_partial(cr, uid, rec_ids)
            
            #----
            
            name_rec = invoice_rec.reference
            name_rec += '/' + (invoice_rec.reference_number or invoice_rec.supplier_invoice_number)
            invoice_rec_move = {
                    'name': line.note or name_rec,
                    'partner_id': invoice_rec.partner_id.parent_id and invoice_rec.partner_id.parent_id.id or invoice_rec.partner_id.id,
                    'product_id': False,
                    'quantity': False,
                    'ref': name_rec,
                    'date': this.date,
                    'debit': invoice_rec.type in ['in_invoice'] and line.paid_amount or 0.0,
                    'credit': invoice_rec.type in ['out_invoice'] and line.paid_amount or 0.0,
                    'account_id': invoice_rec.account_id.id,
                    'move_id': move_id,
                    }
            invoice_rec_move_line_id = move_line_pool.create(cr, uid, invoice_rec_move, context=context)
            #Thanh: Reconcile rec invoice firstly
            cr.execute("SELECT id FROM account_move_line WHERE move_id=%s AND account_id=%s"%(invoice_rec.move_id.id, invoice_rec.account_id.id))
            rec_ids = [x[0] for x in cr.fetchall()]
            if rec_ids:
                rec_ids.append(invoice_rec_move_line_id)
                move_line_pool.reconcile_partial(cr, uid, rec_ids)
            
            move_obj.post(cr, uid, [move_id], context=context)
        return True
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(receivable_payable_reconciliation,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        
        if view_type == 'form':
#             doc = etree.XML(res['arch'])
            
            if context.has_key('active_id'):
                invoice = self.pool.get('account.invoice').browse(cr,uid,context['active_id'])
                domain_type = ''
                if invoice.type == 'out_invoice':
                    domain_type = 'in_invoice'
                    form_view_ref = 'account.invoice_supplier_form'
                    tree_view_ref = 'account.invoice_tree'
                    
                if invoice.type == 'in_invoice':
                    domain_type = 'out_invoice'
                    form_view_ref = 'account.invoice_form'
                    tree_view_ref = 'account.invoice_tree'
                if res['fields']['invoice_ids']['views']['tree']['fields']['invoice_id']:
                    res['fields']['invoice_ids']['views']['tree']['fields']['invoice_id']['domain'] = "[('state', '=', 'open'), ('partner_id', '=', %s), ('type','=','%s')]"%(invoice.partner_id.id, domain_type)
                    res['fields']['invoice_ids']['views']['tree']['fields']['invoice_id']['context'] = "{'form_view_ref':'%s', 'tree_view_ref':'%s'}"%(form_view_ref, tree_view_ref)
#                 for node in doc.xpath("//field[@name='invoice_ids']/tree/field[@name='invoice_id']"):
#                     node.set('domain', "[('state', '=', 'open'), ('partner_id', '=', %s), ('type','=','%s')]"%(invoice.partner_id, domain_type))
#                     node.set('context',"{'form_view_ref':'%s', 'tree_view_ref':'%s'}"%(form_view_ref, tree_view_ref))
#                     res['arch'] = etree.tostring(doc)
                    
        return res
    
receivable_payable_reconciliation()

class receivable_payable_reconciliation_line(osv.osv_memory):
    _name = 'receivable.payable.reconciliation.line'
    _columns = {
        'receivable_payable_reconciliation_id': fields.many2one('receivable.payable.reconciliation', 'Wizard parent', required=True),
        'invoice_id':fields.many2one('account.invoice', 'Invoice', readonly=False, required=True),
        'invoice_balance':fields.float('Invoice Balance', digits_compute=dp.get_precision('Account'), readonly=False, required=True),
        'paid_amount': fields.float('Allocated Amount', digits_compute=dp.get_precision('Account'), required=True),
        'note': fields.char('Notes', size=500)
    }
    _defaults = {
    }
    
    def onchange_invoice_id(self, cr, uid, ids, invoice_id=False, context=None):
        result = {}
        if invoice_id:
            invoice = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
            result = {'value': {
                    'invoice_balance': invoice.residual,
                    }
                }
        return result
    
receivable_payable_reconciliation_line()

# class receivable_payable_reconciliation_invoice_lines(osv.osv_memory):
#     _name = "receivable.payable.reconciliation.invoice.lines"
#     _columns = {
#         'line_ids': fields.many2many('account.invoice', 'receivable_payable_reconciliation_invoice_rel', 'wizard_id', 'invoice_id', 'Invoices'),
#     }
# 
#     def get_invoices(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#             statement_line_obj.create(cr, uid, {
#                 'name': line.name or '?',
#                 'amount': amount,
#                 'type': type,
#                 'partner_id': line.partner_id.id,
#                 'account_id': line.account_id.id,
#                 'statement_id': statement_id,
#                 'ref': line.ref,
#                 'voucher_id': voucher_id,
#                 'date': statement.date,
#             }, context=context)
#         return {'type': 'ir.actions.act_window_close'}
# 
# receivable_payable_reconciliation_invoice_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
