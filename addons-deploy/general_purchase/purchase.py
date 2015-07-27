# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

from osv import osv, fields
import decimal_precision as dp
from openerp import netsvc
import math
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import re
from tools.translate import _
import time
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class purchase_order(osv.osv):
    _inherit = "purchase.order"
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d-%m-%Y')
    def _compute_date_user_tz(self, cr, uid, ids, fieldnames, args, context=None):  
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'date_user_tz': False,
                'day_user_tz': False,
            }
            
            res[obj.id]['date_user_tz'] = obj.date_order
            res[obj.id]['day_user_tz'] = self.get_vietname_date(obj.date_order)
        return res
    _columns={
            'date_user_tz': fields.function(_compute_date_user_tz, type='date', method=True, string='Date User TZ', store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['date_order'], 10),
                }, multi='tz'),
                 
            'day_user_tz': fields.function(_compute_date_user_tz, type='char', method=True, string='Day User TZ', store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['date_order'], 10),
            }, multi='tz'),
    }
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        journal_ids = self.pool.get('stock.journal').search(cr,uid,[('source_type','=','in')])
        if not journal_ids:
            raise osv.except_osv(_('Warning!'), _('Please define Stock Journal for Incomming Order.'))
        
        return {
            'name': '/',#self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in'),
            'origin': order.name + ((order.origin and (':' + order.origin)) or ''),
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'partner_id': order.partner_id.id,
            'invoice_state': '2binvoiced' if order.invoice_method == 'picking' else 'none',
            'type': 'in',
            'purchase_id': order.id,
            'company_id': order.company_id.id,
            'move_lines' : [],
            
            #Thanh: Add more fields
            'stock_journal_id':journal_ids and journal_ids[0] or False,
            'location_id': order.partner_id.property_stock_supplier.id,
            'location_dest_id': order.location_id.id,
            #Hung them san pham lanh hay khong
            'sampham_lanh': order.sampham_lanh,
        }
    
    #Conver Purchase Price Unit into Base Product UoM
    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        uom_obj = self.pool.get('product.uom')
        base_price_unit = uom_obj._compute_price(cr, uid, order_line.product_uom.id, order_line.price_unit, to_uom_id=order_line.product_id.uom_id.id)
        return {
            'name': order_line.name or '',
            'product_id': order_line.product_id.id,
            'product_qty': order_line.product_qty,
            'product_uos_qty': order_line.product_qty,
            'product_uom': order_line.product_uom.id,
            'product_uos': order_line.product_uom.id,
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'date_expected': self.date_to_datetime(cr, uid, order_line.date_planned, context),
            'location_id': order.partner_id.property_stock_supplier.id,
            'location_dest_id': order.location_id.id,
            'picking_id': picking_id,
            'partner_id': order.dest_address_id.id or order.partner_id.id,
            'move_dest_id': order_line.move_dest_id.id,
            'state': 'draft',
            'type':'in',
            'purchase_line_id': order_line.id,
            'company_id': order.company_id.id,
            'price_unit': base_price_unit
#             'price_unit': order_line.product_qty and base_price_unit/order_line.product_qty or 0.0
        }
        
    #Thanh: Add shop into Invoice
    def action_invoice_create(self, cr, uid, ids, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        if context is None:
            context = {}
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')

        res = False
        uid_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        for order in self.browse(cr, uid, ids, context=context):
            context.pop('force_company', None)
            if order.company_id.id != uid_company_id:
                #if the company of the document is different than the current user company, force the company in the context
                #then re-do a browse to read the property fields for the good company.
                context['force_company'] = order.company_id.id
                order = self.browse(cr, uid, order.id, context=context)
            pay_acc_id = order.partner_id.property_account_payable.id
            journal_ids = journal_obj.search(cr, uid, [('type', '=', 'purchase'), ('company_id', '=', order.company_id.id)], limit=1)
            if not journal_ids:
                raise osv.except_osv(_('Error!'),
                    _('Define purchase journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))

            # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
            inv_lines = []
            for po_line in order.order_line:
                acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
                inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                inv_lines.append(inv_line_id)

                po_line.write({'invoice_lines': [(4, inv_line_id)]}, context=context)
            
            #Thanh: Get Shop where Warehouse belonging to
            shop_ids = self.pool.get('sale.shop').search(cr, uid, [('warehouse_id','=',order.warehouse_id.id or False)])
            # get invoice data and create invoice
            inv_data = {
                'name': order.partner_ref or order.name,
                'reference': order.partner_ref or order.name,
                'account_id': pay_acc_id,
                'type': 'in_invoice',
                'partner_id': order.partner_id.id,
                'currency_id': order.pricelist_id.currency_id.id,
                'journal_id': len(journal_ids) and journal_ids[0] or False,
                'invoice_line': [(6, 0, inv_lines)],
                'origin': order.name,
                'fiscal_position': order.fiscal_position.id or False,
                'payment_term': order.payment_term_id.id or False,
                'company_id': order.company_id.id,
                
                #Thanh: add more fields
                'shop_id': shop_ids and shop_ids[0] or False,
            }
            inv_id = inv_obj.create(cr, uid, inv_data, context=context)

            # compute the invoice
            inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

            # Link this new invoice to related purchase order
            order.write({'invoice_ids': [(4, inv_id)]}, context=context)
            res = inv_id
        return res
    
    #Thanh: Change the way to get Sequence
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state':'draft',
            'shipped':False,
            'invoiced':False,
            'invoice_ids': [],
            'picking_ids': [],
            'partner_ref': '',
#             'name': self.pool.get('ir.sequence').get(cr, uid, 'purchase.order'),
            'name':'/',
        })
        return super(osv.osv, self).copy(cr, uid, id, default, context)
    
    def create(self, cr, uid, vals, context=None):
        context = context or {}
        context.update({'sequence_obj_ids':[]})
        if vals.get('name','/')=='/':
            if vals.get('warehouse_id',False):
                context['sequence_obj_ids'].append(['warehouse',vals['warehouse_id']])
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order', context=context) or '/'
        order =  super(osv.osv, self).create(cr, uid, vals, context=context)
        return order
    #Thanh: Change the way to get Sequence
    
    def action_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for purchase in self.browse(cr, uid, ids, context=context):
            for pick in purchase.picking_ids:
                if pick.state in ('done'):
                    raise osv.except_osv(
                        _('Unable to cancel this purchase order.'),
                        _('First cancel all receptions related to this purchase order.'))
            for pick in purchase.picking_ids:
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
                #self.pool.get('stock.picking').unlink(cr,uid,[pick.id])
                sql = '''
                    DELETE 
                    FROM STOCK_MOVE
                    WHERE picking_id = %s
                '''%(pick.id)
                cr.execute(sql)
                
                sql = '''
                    DELETE 
                    FROM STOCK_PICKING 
                    WHERE ID = %s
                ''' %(pick.id)
                cr.execute(sql)
            for inv in purchase.invoice_ids:
                if inv and inv.state not in ('cancel','draft'):
                    raise osv.except_osv(
                        _('Unable to cancel this purchase order.'),
                        _('You must first cancel all receptions related to this purchase order.'))
                if inv:
                    wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
        self.write(cr,uid,ids,{'state':'cancel'})

        for (id, name) in self.name_get(cr, uid, ids):
            wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_cancel', cr)
        return True
    
purchase_order()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
