#-*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import logging
import pdb
import time

from openerp import netsvc
import openerp
from openerp import netsvc, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp
import openerp.addons.product.product

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class account_bank_statement_line(osv.osv):
    _inherit = 'account.bank.statement.line'
    _columns= {
        #Thanh: add field payment datetime
        'payment_datetime': fields.datetime('Payment Datetime'),
    }

account_bank_statement_line()

class pos_order(osv.osv):
    _inherit="pos.order"
    
    # kiet Xoá luôn Picking đã xuat kho lien quan
    
    def unlink(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state not in ('draft','cancel'):
                raise osv.except_osv(_('Unable to Delete!'), _('In order to delete a sale, it must be new or cancelled.'))
            if rec.picking_id:
                sql='''
                    DELETE FROM stock_move where picking_id = %s
                '''%(rec.picking_id.id)
                cr.execute(sql)
                sql='''
                    DELETE FROM stock_picking where id =%s
                '''%(rec.picking_id.id)
                cr.execute(sql)
        return super(pos_order, self).unlink(cr, uid, ids, context=context)
    #Thanh: Add field payment datetime to bank statement line
    def add_payment(self, cr, uid, order_id, data, context=None):
        """Create a new payment for the order"""
        if not context:
            context = {}
        
        #Thanh: Convert payment datetime to user date time
        user_pool = self.pool.get('res.users')
        date_user_tz = user_pool._convert_user_datetime(cr, uid, data.get('payment_date', time.strftime(DATETIME_FORMAT)))
        date_user_tz = date_user_tz.strftime(DATE_FORMAT)
        #Thanh: Convert payment datetime to user date time
        
        statement_line_obj = self.pool.get('account.bank.statement.line')
        property_obj = self.pool.get('ir.property')
        order = self.browse(cr, uid, order_id, context=context)
        args = {
            'amount': data['amount'],
            'date': date_user_tz,
            
            #Thanh: Add payment datetime
            'payment_datetime': data.get('payment_date', time.strftime(DATETIME_FORMAT)),
            #Thanh: Add payment datetime
            
            'name': order.name + ': ' + (data.get('payment_name', '') or ''),
            'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(order.partner_id).id or False,
        }

        account_def = property_obj.get(cr, uid, 'property_account_receivable', 'res.partner', context=context)
        args['account_id'] = (order.partner_id and order.partner_id.property_account_receivable \
                             and order.partner_id.property_account_receivable.id) or (account_def and account_def.id) or False

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account defined to make payment.')
            else:
                msg = _('There is no receivable account defined to make payment for the partner: "%s" (id:%d).') % (order.partner_id.name, order.partner_id.id,)
            raise osv.except_osv(_('Configuration Error!'), msg)

        context.pop('pos_session_id', False)

        journal_id = data.get('journal', False)
        statement_id = data.get('statement_id', False)
        assert journal_id or statement_id, "No statement_id or journal_id passed to the method!"

        for statement in order.session_id.statement_ids:
            if statement.id == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == journal_id:
                statement_id = statement.id
                break

        if not statement_id:
            raise osv.except_osv(_('Error!'), _('You have to open at least one cashbox.'))

        args.update({
            'statement_id' : statement_id,
            'pos_statement_id' : order_id,
            'journal_id' : journal_id,
            'type' : 'customer',
            'ref' : order.session_id.name,
        })

        new_id = statement_line_obj.create(cr, uid, args, context=context)
        return new_id
    
    def unlink(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state not in ('draft','cancel'):
                raise osv.except_osv(_('Unable to Delete!'), _('In order to delete a sale, it must be new or cancelled.'))
        return super(pos_order, self).unlink(cr, uid, ids, context=context)
    
    
    def _compute_date_user_tz(self, cr, uid, ids, fieldnames, args, context=None):  
        user_pool = self.pool.get('res.users')
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'date_user_tz': False,
                'day_user_tz': False,
            }
            
            date_user_tz = user_pool._convert_user_datetime(cr, uid, obj.date_order)
            res[obj.id]['date_user_tz'] = date_user_tz.strftime('%Y-%m-%d')
            res[obj.id]['day_user_tz'] = date_user_tz.strftime('%d-%m-%Y')
        return res
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_paid': 0.0,
                'amount_return':0.0,
                'amount_tax':0.0,
                'amount_unpaid':0.0
            }
            val1 = val2 = 0.0
            payments =0.0
            cur = order.pricelist_id.currency_id
            for payment in order.statement_ids:
                payments +=  payment.amount 
                res[order.id]['amount_paid'] +=  payment.amount
                res[order.id]['amount_return'] += (payment.amount < 0 and payment.amount or 0)
            for line in order.lines:
                val1 += line.price_subtotal_incl
                val2 += line.price_subtotal
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val1-val2)
            res[order.id]['amount_total'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_unpaid'] = cur_obj.round(cr, uid, cur, val1 - payments)
        return res
    
    _columns={
          'type_pos': fields.selection([('delivery', 'Delivery'),('receipt', 'Receipt')],'Type', required=False),
          'invoiced_flag':fields.boolean('Invoiced Flag'),
          'private_inv_flag':fields.boolean('Private Inv Flag'),
          'date_invoice':fields.date('Date Invoiced'),
          'date_user_tz': fields.function(_compute_date_user_tz, type='date', method=True, string='Date User TZ', store={
                'pos.order': (lambda self, cr, uid, ids, c={}: ids, ['date_order'], 10),
                }, multi='tz'),
        
          'day_user_tz': fields.function(_compute_date_user_tz, type='char', method=True, string='Day User TZ', store={
                'pos.order': (lambda self, cr, uid, ids, c={}: ids, ['date_order'], 10),
            }, multi='tz'),
          'date_order': fields.datetime('Order Date', readonly=False, select=True),
          'check_flag':fields.boolean('Đã xem'),
          #Thanh: Require User
          'user_id': fields.many2one('res.users', 'Salesman', required=True, states={'draft': [('readonly', False)], 'paid': [('readonly', False)]},
                                     help="Person who uses the the cash register. It can be a reliever, a student or an interim employee."),
          
          'amount_tax': fields.function(_amount_all, string='Taxes', digits_compute=dp.get_precision('Point Of Sale'), multi='all'),
          'amount_total': fields.function(_amount_all, string='Total', multi='all'),
          'amount_paid': fields.function(_amount_all, string='Paid', states={'draft': [('readonly', False)]}, readonly=True, digits_compute=dp.get_precision('Point Of Sale'), multi='all'),
          'amount_return': fields.function(_amount_all, 'Returned', digits_compute=dp.get_precision('Point Of Sale'), multi='all'),
          'amount_unpaid': fields.function(_amount_all, string='Unpaid', digits_compute=dp.get_precision('Point Of Sale'), multi='all'),
          }
    
    _default = {
        'type_pos' : 'delivery',
        'invoiced_flag': False,
        'private_inv_flag': False,
        'check_flag':False
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        res = super(pos_order, self).write(cr, uid, ids, vals, context=context)
        #If you change the partner of the PoS order, change also the partner of the associated bank statement lines
        partner_obj = self.pool.get('res.partner')
        bsl_obj = self.pool.get("account.bank.statement.line")
        if 'partner_id' in vals:
            for posorder in self.browse(cr, uid, ids, context=context):
                if posorder.invoice_id:
                    raise osv.except_osv( _('Error!'), _("You cannot change the partner of a POS order for which an invoice has already been issued."))
                if vals['partner_id']:
                    p_id = partner_obj.browse(cr, uid, vals['partner_id'], context=context)
                    part_id = partner_obj._find_accounting_partner(p_id).id
                else:
                    part_id = False
                bsl_ids = [x.id for x in posorder.statement_ids]
                bsl_obj.write(cr, uid, bsl_ids, {'partner_id': part_id}, context=context)
                
        for line in self.browse(cr,uid,ids):
            if line.check_flag and vals:
                raise osv.except_osv(_('Warning!'),
               _('You cannot changed data !!!'))
            
        #Thanh update section when changed
        if vals.get('user_id',False):
            for id in ids:
                cr.execute('''
                UPDATE pos_order
                SET section_id=(select default_section_id from res_users where id=%s limit 1)
                WHERE id=%s
                '''%(vals['user_id'], id))
        
        return res
    
    def action_paid(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'paid','type_pos':'delivery'}, context=context)
        self.button_create_picking(cr, uid, ids, context=context)
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr,uid,ids):
            if line.invoice_id:
                raise osv.except_osv(_('Warning!'),
               _('You have to delete Related Invoice first .'))
            if line.picking_id:
                sql='''
                    DELETE from stock_move 
                    WHERE picking_id = %s
                '''%(line.picking_id.id)
                cr.execute(sql)
                sql='''
                    DELETE FROM stock_picking
                    WHERE id = %s
                '''%(line.picking_id.id)
                cr.execute(sql)
            for i in line.statement_ids:
                sql='''
                    DELETE FROM 
                    account_bank_statement_line 
                    where id = %s
                '''%(i.id)
                cr.execute(sql)
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True
    
    
    def button_create_picking(self,cr,uid,ids,context):
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        partner_obj = self.pool.get('res.partner')
        move_ids =False
        for i in self.browse(cr,uid,ids):
            if not i.picking_id:
                self.create_picking(cr, uid, ids, context)
            else:
                picking_obj.action_revert_done(cr,uid,[i.picking_id.id],context)
                location_id = i.shop_id.warehouse_id.lot_stock_id.id
                if i.partner_id:
                    destination_id = i.partner_id.property_stock_customer.id
                else:
                    destination_id = partner_obj.default_get(cr, uid, ['property_stock_customer'], context=context)['property_stock_customer']
                
                sql='''
                    DELETE FROM stock_move where picking_id = %s
                '''%(i.picking_id.id)
                cr.execute(sql)
                for line in i.lines:
                    if line.product_id and line.product_id.type == 'service':
                        continue
    
                    move_ids = move_obj.create(cr, uid, {
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uos': line.product_id.uom_id.id,
                        'picking_id': i.picking_id.id,
                        'product_id': line.product_id.id,
                        'product_uos_qty': abs(line.qty),
                        'product_qty': abs(line.qty),
                        'tracking_id': False,
                        'state': 'draft',
                        'location_id': location_id if line.qty >= 0 else destination_id,
                        'location_dest_id': destination_id if line.qty >= 0 else location_id,
                    }, context=context)
                    
                if move_ids:
                    self.write(cr, uid, [i.id], {'picking_id': i.picking_id.id}, context=context)
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'stock.picking', i.picking_id.id, 'button_confirm', cr)
                    picking_obj.force_assign(cr, uid, [i.picking_id.id], context)
                else:
                    sql='''
                        DELETE from stock_picking where id = %s
                    '''%(i.picking_id.id)
                    cr.execute(sql)
                
        return True
    
    def create_picking(self, cr, uid, ids, context=None):
        """Create a picking for each order and validate it."""
        #picking_out_obj = self.pool.get('stock.picking.out')
        #picking_in_obj = self.pool.get('stock.picking.in')
        picking_obj = self.pool.get('stock.picking')
        partner_obj = self.pool.get('res.partner')
        move_obj = self.pool.get('stock.move')
        move_ids =False
        
        for order in self.browse(cr, uid, ids, context=context):
            location_id = order.shop_id.warehouse_id.lot_stock_id.id
            if order.partner_id:
                destination_id = order.partner_id.property_stock_customer.id
            else:
                destination_id = partner_obj.default_get(cr, uid, ['property_stock_customer'], context=context)['property_stock_customer']
            if order.type_pos == 'delivery' or not order.type_pos:
                journal_ids = self.pool.get('stock.journal').search(cr,uid,[('source_type','=','out')])
                if not journal_ids:
                    raise osv.except_osv(_('Warning!'), _('Please define Stock Journal for Incomming Order.'))
            
                addr = order.partner_id and partner_obj.address_get(cr, uid, [order.partner_id.id], ['delivery']) or {}
                picking_out_id = picking_obj.create(cr, uid, {
                    'origin': order.name,
                    'partner_id': addr.get('delivery',False),
                    'type': 'out',
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'invoice_state': 'none',
                    'auto_picking': True,
                    'stock_journal_id':journal_ids and journal_ids[0] or False,
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                }, context=context)
                
                location_id = order.shop_id.warehouse_id.lot_stock_id.id
                if order.partner_id:
                    destination_id = order.partner_id.property_stock_customer.id
                else:
                    destination_id = partner_obj.default_get(cr, uid, ['property_stock_customer'], context=context)['property_stock_customer']
    
                for line in order.lines:
                    if line.product_id and line.product_id.type == 'service':
                        continue
    
                    move_ids = move_obj.create(cr, uid, {
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uos': line.product_id.uom_id.id,
                        'picking_id': picking_out_id,
                        'product_id': line.product_id.id,
                        'product_uos_qty': abs(line.qty),
                        'product_qty': abs(line.qty),
                        'tracking_id': False,
                        'state': 'draft',
                        'location_id': location_id if line.qty >= 0 else destination_id,
                        'location_dest_id': destination_id if line.qty >= 0 else location_id,
                    }, context=context)
                if move_ids:
                    self.write(cr, uid, [order.id], {'picking_id': picking_out_id}, context=context)
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'stock.picking', picking_out_id, 'button_confirm', cr)
                    picking_obj.force_assign(cr, uid, [picking_out_id], context)
                else:
                    sql='''
                        DELETE from stock_picking where id = %s
                    '''%(picking_out_id)
                    cr.execute(sql)
            
            elif order.type_pos == 'receipt':
                journal_ids = self.pool.get('stock.journal').search(cr,uid,[('source_type','=','return_customer')])
                if not journal_ids:
                    raise osv.except_osv(_('Warning!'), _('Please define Stock Journal for Incomming Order.'))
    
                for order in self.browse(cr, uid, ids, context=context):
                    addr = order.partner_id and partner_obj.address_get(cr, uid, [order.partner_id.id], ['delivery']) or {}
                    picking_in_id = picking_obj.create(cr, uid, {
                        'origin': order.name,
                        'partner_id': addr.get('delivery',False),
                        'type': 'in',
                        'return': 'customer',
                        'company_id': order.company_id.id,
                        'move_type': 'direct',
                        'note': order.note or "",
                        'invoice_state': 'none',
                        'auto_picking': True,
                        'stock_journal_id':journal_ids and journal_ids[0] or False,
                    }, context=context)
                   
                    location_id = order.shop_id.warehouse_id.lot_stock_id.id
                    if order.partner_id:
                        destination_id = order.partner_id.property_stock_customer.id
                    else:
                        destination_id = partner_obj.default_get(cr, uid, ['property_stock_customer'], context=context)['property_stock_customer']
                    for line in order.lines:
                        if line.product_id and line.product_id.type == 'service':
                            continue
        
                        move_ids = move_obj.create(cr, uid, {
                            'name': line.name,
                            'product_uom': line.product_id.uom_id.id,
                            'product_uos': line.product_id.uom_id.id,
                            'picking_id': picking_in_id,
                            'product_id': line.product_id.id,
                            'product_uos_qty': abs(line.qty),
                            'product_qty': abs(line.qty),
                            'tracking_id': False,
                            'state': 'draft',
                            'location_id': location_id if line.qty >= 0 else destination_id,
                            'location_dest_id': destination_id if line.qty >= 0 else location_id,
                        }, context=context)
                if move_ids:
                    self.write(cr, uid, [order.id], {'picking_id': picking_in_id}, context=context)
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'stock.picking', picking_in_id, 'button_confirm', cr)
                    picking_obj.force_assign(cr, uid, [picking_in_id], context)
                else:
                    sql='''
                        DELETE FROM stock_picking where id = %s
                    '''%(picking_out_id)
                    cr.execute(sql)
        return True
pos_order() 

class pos_order_line(osv.osv):
    _inherit = "pos.order.line"
    _columns = {
                'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True),('available_in_pos', '=', True)], required=True, change_default=True),
                'from_location_id': fields.many2one('stock.location', 'Location', domain="[('usage','=','internal')]"),
                'partner_id': fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', store=True, string='Customer'),
                'partner_reference': fields.related('order_id', 'partner_reference', type='char', store=True, string='Partner Ref'),
                'date_order': fields.related('order_id', 'date_order', type='datetime', store=True, string='Date Order User TZ'),
                'date_user_tz': fields.related('order_id', 'date_user_tz', type='date', store=True, string='Day Order User TZ'),
                'day_user_tz': fields.related('order_id', 'day_user_tz', type='char', store=True, string='Day Order'),
                'user_id': fields.related('order_id', 'user_id', type='many2one', relation='res.users', store=True, string='Salesman'),
                'note':fields.char('Descript',size=128),
                'section_id': fields.many2one('crm.case.section', 'POS Team'),
                'state': fields.related('order_id', 'state', type='selection',store=True,selection=([('draft', 'New'),
                                   ('cancel', 'Cancelled'),
                                   ('paid', 'Paid'),
                                   ('done', 'Posted'),
                                   ('invoiced', 'Invoiced')])),
                
                'relate_name': fields.related('order_id', 'name', type='char', store=True, string='Pos Order Name'),
                'check_flag':fields.boolean('Đã xem'),
                'date':fields.date('Ngày giao dịch',required=True,),
                'invoice_qty':fields.float('Invoiced Qty')
        }
    
    _default = {
        'check_flag':False,
        'date': time.strftime('%Y-%m-%d'),
        #'date': fields.date.context_today,
    }
    
    def create(self, cr, uid, vals, context=None):
        new_id = super(pos_order_line, self).create(cr, uid, vals, context=None)
        if not vals.get('section_id',False) and vals.get('order_id',False):
            cr.execute('''
            UPDATE pos_order_line
            SET section_id=(select section_id from pos_order where id=%s limit 1)
            WHERE id=%s
            '''%(vals['order_id'],new_id))
        return new_id
    
    def write(self, cr, uid, ids, vals, context=None):
        for line in self.browse(cr, uid, ids):
            if vals.has_key('check_flag'):
                if vals['check_flag']==True:
                    raise osv.except_osv( _('Error!'), _("You cannot change the information of POS order line when status is checking ."))
            if (not line.section_id and not vals.get('section_id',False)) or (vals.has_key('section_id') and not vals['section_id']):
                vals.update({'section_id': line.order_id.section_id.id or False})
        return super(pos_order_line, self).write(cr, uid, ids, vals, context=None)

pos_order_line()

class res_partner(osv.osv):
    _inherit = "res.partner"
    _columns = {
                'customer_type': fields.boolean('Is Anonymous Customer'),
        }
    _default = {
                'customer_type' : False
                }
res_partner()


class account_bank_statement(osv.osv):
    _inherit = "account.bank.statement"
    
    def button_confirm_bank(self, cr, uid, ids, context=None):
        obj_seq = self.pool.get('ir.sequence')
        if context is None:
            context = {}

        for st in self.browse(cr, uid, ids, context=context):
            j_type = st.journal_id.type
            company_currency_id = st.journal_id.company_id.currency_id.id
            if not self.check_status_condition(cr, uid, st.state, journal_type=j_type):
                continue

            self.balance_check(cr, uid, st.id, journal_type=j_type, context=context)
            if (not st.journal_id.default_credit_account_id) \
                    or (not st.journal_id.default_debit_account_id):
                raise osv.except_osv(_('Configuration Error!'),
                        _('Please verify that an account is defined in the journal.'))

            if not st.name == '/':
                st_number = st.name
            else:
                c = {'fiscalyear_id': st.period_id.fiscalyear_id.id}
                if st.journal_id.sequence_id:
                    st_number = obj_seq.next_by_id(cr, uid, st.journal_id.sequence_id.id, context=c)
                else:
                    st_number = obj_seq.next_by_code(cr, uid, 'account.bank.statement', context=c)

            for line in st.move_line_ids:
                if line.state <> 'valid':
                    raise osv.except_osv(_('Error!'),
                            _('The account entries lines are not in valid state.'))
            for st_line in st.line_ids:
                if st_line.analytic_account_id:
                    if not st.journal_id.analytic_journal_id:
                        raise osv.except_osv(_('No Analytic Journal!'),_("You have to assign an analytic journal on the '%s' journal!") % (st.journal_id.name,))
                if not st_line.amount:
                    continue
#                 kiệt sửa không phát sinh bút toán
#                 st_line_number = self.get_next_st_line_number(cr, uid, st_number, st_line, context)
#                 self.create_move_from_st_line(cr, uid, st_line.id, company_currency_id, st_line_number, context)

            self.write(cr, uid, [st.id], {
                    'name': st_number,
                    'balance_end_real': st.balance_end
            }, context=context)
            self.message_post(cr, uid, [st.id], body=_('Statement %s confirmed, journal items were created.') % (st_number,), context=context)
        return self.write(cr, uid, ids, {'state':'confirm'}, context=context)
    
account_bank_statement()


class pos_session(osv.osv):
    _inherit = "pos.session"
    
    def wkf_action_close(self, cr, uid, ids, context=None):
        # Close CashBox
        bsl = self.pool.get('account.bank.statement.line')
        for record in self.browse(cr, uid, ids, context=context):
            for st in record.statement_ids:
                if abs(st.difference) > st.journal_id.amount_authorized_diff:
                    # The pos manager can close statements with maximums.
                    if not self.pool.get('ir.model.access').check_groups(cr, uid, "point_of_sale.group_pos_manager"):
                        raise osv.except_osv( _('Error!'),
                            _("Your ending balance is too different from the theoretical cash closing (%.2f), the maximum allowed is: %.2f. You can contact your manager to force it.") % (st.difference, st.journal_id.amount_authorized_diff))
                if (st.journal_id.type not in ['bank', 'cash']):
                    raise osv.except_osv(_('Error!'), 
                        _("The type of the journal for your payment method should be bank or cash "))
                if st.difference and st.journal_id.cash_control == True:
                    if st.difference > 0.0:
                        name= _('Point of Sale Profit')
                        account_id = st.journal_id.profit_account_id.id
                    else:
                        account_id = st.journal_id.loss_account_id.id
                        name= _('Point of Sale Loss')
                    if not account_id:
                        raise osv.except_osv( _('Error!'),
                        _("Please set your profit and loss accounts on your payment method '%s'. This will allow OpenERP to post the difference of %.2f in your ending balance. To close this session, you can update the 'Closing Cash Control' to avoid any difference.") % (st.journal_id.name,st.difference))
                    bsl.create(cr, uid, {
                        'statement_id': st.id,
                        'amount': st.difference,
                        'ref': record.name,
                        'name': name,
                        'account_id': account_id
                    }, context=context)

                if st.journal_id.type == 'bank':
                    st.write({'balance_end_real' : st.balance_end})
                    
                # Kiet không phát sinh bút toán
                #getattr(st, 'button_confirm_%s' % st.journal_id.type)(context=context)
        self._confirm_orders(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state' : 'closed'}, context=context)

        obj = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'point_of_sale', 'menu_point_root')[1]
        return {
            'type' : 'ir.actions.client',
            'name' : 'Point of Sale Menu',
            'tag' : 'reload',
            'params' : {'menu_id': obj},
        }
    # kiệt hàm sinh bút toán 
    def _confirm_orders(self, cr, uid, ids, context=None):
#         wf_service = netsvc.LocalService("workflow")
 
#         for session in self.browse(cr, uid, ids, context=context):
#             local_context = dict(context or {}, force_company=session.config_id.journal_id.company_id.id)
#             order_ids = [order.id for order in session.order_ids if order.state == 'paid']
#             move_id = self.pool.get('account.move').create(cr, uid, {'ref' : session.name, 'journal_id' : session.config_id.journal_id.id, }, context=local_context)
#             self.pool.get('pos.order')._create_account_move_line(cr, uid, order_ids, session, move_id, context=local_context)
#             for order in session.order_ids:
#                 if order.state not in ('paid', 'invoiced'):
#                     raise osv.except_osv(
#                         _('Error!'),
#                         _("You cannot confirm all orders of this session, because they have not the 'paid' status"))
#                 else:
#                     wf_service.trg_validate(uid, 'pos.order', order.id, 'done', cr)

        return True
    
pos_session()



