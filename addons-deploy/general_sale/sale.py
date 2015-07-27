# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################

from osv import fields, osv
import time
import netsvc
import pooler
import tools
from tools.translate import _
from datetime import datetime
import decimal_precision as dp
from tools import config
import logging
import time
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
_logger = logging.getLogger(__name__)

class sale_shop(osv.osv):
    _inherit = 'sale.shop'
    
    _columns = {
        'code': fields.char('Code', size=5, required=True),
        'parent_id': fields.many2one('sale.shop', 'Parent Shop'),
    }
    
sale_shop()

class sale_order(osv.osv):
    _inherit = 'sale.order'
    
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
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['date_order'], 10),
                }, multi='tz'),
                 
            'day_user_tz': fields.function(_compute_date_user_tz, type='char', method=True, string='Day User TZ', store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['date_order'], 10),
            }, multi='tz'),
    }
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        location_id = order.shop_id.warehouse_id.lot_stock_id.id
        output_id = order.shop_id.warehouse_id.lot_output_id.id
        journal_ids = self.pool.get('stock.journal').search(cr,uid,[('source_type','=','out')])
        if not journal_ids:
            raise osv.except_osv(_('Warning!'), _('Please define Stock Journal for Delivery Order.'))
#             pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        pick_name = '/'
        return {
            'name': pick_name,
            'origin': order.name,
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'type': 'out',
            'state': 'auto',
            'move_type': order.picking_policy,
            'sale_id': order.id,
            'partner_id': order.partner_shipping_id.id,
            'note': order.note,
            'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
            'company_id': order.company_id.id,
            
            #Thanh: add more fields
            'stock_journal_id':journal_ids and journal_ids[0] or False,
            'location_id': location_id,
            'location_dest_id': output_id,
            'shop_id':order.shop_id and order.shop_id.id or False,
        }
    
    #Thanh: Get Location From Order Line
    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        location_id = order.shop_id.warehouse_id.lot_stock_id.id
        output_id = order.shop_id.warehouse_id.lot_output_id.id
        return {
            'name': line.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'product_packaging': line.product_packaging.id,
            'partner_id': line.address_allotment_id.id or order.partner_shipping_id.id,
            'location_id': line.from_location_id.id or location_id,
            'location_dest_id': output_id,
            'sale_line_id': line.id,
            'tracking_id': False,
            'state': 'draft',
            #'state': 'waiting',
            'company_id': order.company_id.id,
            'price_unit': line.product_id.standard_price or 0.0
        }

    #Thanh: Add shop into Invoice
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
            limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'journal_id': journal_ids[0],
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False,
            
            #Thanh: add more fields
            'shop_id': order.shop_id.id or False,
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals
    
    #Thanh: Change the way to get Sequence
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'date_order': fields.date.context_today(self, cr, uid, context=context),
            'state': 'draft',
            'invoice_ids': [],
            'date_confirm': False,
            'client_order_ref': '',
#             'name': self.pool.get('ir.sequence').get(cr, uid, 'sale.order'),
            'name':'/',
            'picking_ids': [],
        })
        return super(osv.osv, self).copy(cr, uid, id, default, context=context)
    
    def create(self, cr, uid, vals, context=None):
        context = context or {}
        context.update({'sequence_obj_ids':[]})
        if vals.get('name','/')=='/':
            if vals.get('shop_id',False):
                context['sequence_obj_ids'].append(['shop',vals['shop_id']])
                cr.execute('SELECT warehouse_id FROM sale_shop WHERE id=%s'%(vals['shop_id']))
                warehouse_id = cr.fetchone()
                if warehouse_id and warehouse_id[0]:
                    context['sequence_obj_ids'].append(['warehouse',warehouse_id[0]])
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.order', context=context) or '/'
        return super(osv.osv, self).create(cr, uid, vals, context=context)
    
    #Thanh: Change the way to get Sequence
    
    def action_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        proc_obj = self.pool.get('procurement.order')
        for sale in self.browse(cr, uid, ids, context=context):
            for pick in sale.picking_ids:
                if pick.state not in ('draft', 'cancel'):
                    raise osv.except_osv(
                        _('Cannot cancel sales order!'),
                        _('You must first cancel all delivery order(s) attached to this sales order.'))
                if pick.state == 'cancel':
                    for mov in pick.move_lines:
                        proc_ids = proc_obj.search(cr, uid, [('move_id', '=', mov.id)])
                        if proc_ids:
                            for proc in proc_ids:
                                wf_service.trg_validate(uid, 'procurement.order', proc, 'button_check', cr)
            for r in self.read(cr, uid, ids, ['picking_ids']):
                for pick in r['picking_ids']:
                    wf_service.trg_validate(uid, 'stock.picking', pick, 'button_cancel', cr)
        return super(sale_order, self).action_cancel(cr, uid, ids, context=context)
sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line' 
    
    _columns = {
        'from_location_id': fields.many2one('stock.location', 'Location', readonly=True, states={'draft':[('readonly',False)]}, domain="[('usage','=','internal')]"),
        'date_order': fields.related('order_id', 'date_order', type='date', store=True, string='Date Order')
    }
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        res = {}
        if not line.invoiced:
            if not account_id:
                if line.product_id:
                    account_id = line.product_id.property_account_income.id
                    if not account_id:
                        account_id = line.product_id.categ_id.property_account_income_categ.id
                    if not account_id:
                        raise osv.except_osv(_('Error!'),
                                _('Please define income account for this product: "%s" (id:%d).') % \
                                    (line.product_id.name, line.product_id.id,))
                else:
                    prop = self.pool.get('ir.property').get(cr, uid,
                            'property_account_income_categ', 'product.category',
                            context=context)
                    account_id = prop and prop.id or False
            uosqty = self._get_line_qty(cr, uid, line, context=context)
            uos_id = self._get_line_uom(cr, uid, line, context=context)
            pu = 0.0
            if uosqty:
                pu = round(line.price_unit * line.product_uom_qty / uosqty,
                        self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
            fpos = line.order_id.fiscal_position or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, account_id)
            if not account_id:
                raise osv.except_osv(_('Error!'),
                            _('There is no Fiscal Position defined or Income category account defined for default properties of Product categories.'))
            res = {
                'name': line.name,
                'sequence': line.sequence,
                'origin': line.order_id.name,
                'account_id': account_id,
                'price_unit': pu,
                'quantity': uosqty,
                'discount': line.discount,
                'uos_id': uos_id,
                'product_id': line.product_id.id or False,
                'invoice_line_tax_id': [(6, 0, [x.id for x in line.tax_id])],
                'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
            }
            
            #Thanh: Get analytic_account from Analytic Default
            rec = self.pool.get('account.analytic.default').account_get(cr, uid, line.product_id.id or False, False, uid, time.strftime('%Y-%m-%d'), context=context)
            if rec:
                res.update({'account_analytic_id': rec.analytic_id.id})
                
        return res
    
sale_order_line()
#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
