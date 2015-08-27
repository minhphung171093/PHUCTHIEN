# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from datetime import datetime
import datetime
from openerp import netsvc
import openerp.addons.decimal_precision as dp

class purchase_order(osv.osv):
    _inherit = "purchase.order"
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                if line.approve:
                   val1 += line.price_subtotal
                   for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
                        val += c.get('amount', 0.0)
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    _columns = {
        'duyet_vuotcap_id': fields.many2one('res.users','Duyệt vượt cấp',readonly=1, track_visibility='onchange'),
        'amount_untaxed': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute= dp.get_precision('Account'), string='Total',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total amount"),
        'sampham_lanh':fields.boolean('Sản phẩm lạnh'),
    }
    
    def print_purchase_order(self, cr, uid, ids, context=None): 
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'don_dat_hang_report',
            }
    
    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Creates pickings and appropriate stock moves for given order lines, then
        confirms the moves, makes them available, and confirms the picking.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: purchase order to which the order lines belong
        :param list(browse_record) order_lines: purchase order line records for which picking
                                                and moves should be created.
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if omitted.
        :return: list of IDs of pickings used/created for the given order lines (usually just one)
        """
        if not picking_id:
            picking_id = self.pool.get('stock.picking').create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
        todo_moves = []
        stock_move = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        for order_line in order_lines:
            if not order_line.product_id:
                continue
            if order_line.product_id.type in ('product', 'consu') and order_line.approve:
                move = stock_move.create(cr, uid, self._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context))
                if order_line.move_dest_id and order_line.move_dest_id.state != 'done':
                    order_line.move_dest_id.write({'location_id': order.location_id.id})
                todo_moves.append(move)
        stock_move.action_confirm(cr, uid, todo_moves)
        stock_move.force_assign(cr, uid, todo_moves)
        wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        return [picking_id]
    
    def duyet_vuot_cap(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'duyet_vuotcap_id' : uid})
        self.cd = {'duyet_vuotcap_id' :1}
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'purchase.order', ids[0], 'purchase_confirm', cr)
        return True
    
    def action_cancel_draft(self, cr, uid, ids, context=None):
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state':'draft','shipped':0, 'validator' : False,'tp_duyet_id': False, 'gd_duyet_id': False,'duyet_vuotcap_id': False})
        for purchase in self.browse(cr, uid, ids, context=context):
            self.pool['purchase.order.line'].write(cr, uid, [l.id for l in  purchase.order_line], {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for p_id in ids:
            # Deleting the existing instance of workflow for PO
            wf_service.trg_delete(uid, 'purchase.order', p_id, cr)
            wf_service.trg_create(uid, 'purchase.order', p_id, cr)
        return True
    
purchase_order()

class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"
    
    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total']) + line.adjust_price
        return res
    
    _columns = {
        'partner_id': fields.many2one('res.partner','Khách hàng'),
        'approve': fields.boolean('Approve'),
        'adjust_price':fields.float('Điều chỉnh đơn giá'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
    }
    
    _defaults = {
        'approve': True,
        'adjust_price':0.0
    }
    
purchase_order_line()

class manufacturer_product(osv.osv):
    _name = "manufacturer.product"
    
    _columns = {
        'name': fields.char('Tên hãng sản xuất',size=64,required=True),
        'code': fields.char('Mã hãng sản xuất',size=9),
    }
    
manufacturer_product()

class product_category(osv.osv):
    _inherit = "product.category"
    _columns = {
        'manufacturer_product_ids': fields.many2many('manufacturer.product','manufacturer_product_category_ref','category_id','manufacturer_product_id','Hãng sản xuất'),
    }
    
product_category()    
class product_product(osv.osv):
    _inherit = "product.product"
    
    _columns = {
        'manufacturer_product_id': fields.many2one('manufacturer.product','Hãng sản xuất'),
        'product_country_id': fields.many2one('res.country', 'Nước sản xuất'),
    }
    
    def create(self, cr, uid, vals, context=None):
        product_id = super(product_product, self).create(cr, uid, vals, context=context)
        categ_id = self.browse(cr,uid,product_id).categ_id.id
        manufacturer_product_id = self.browse(cr,uid,product_id).manufacturer_product_id and self.browse(cr,uid,product_id).manufacturer_product_id.id or False
        partner_ids = self.pool.get('res.partner').search(cr,uid,[('customer','=',True)])
        for partner in partner_ids:
            partner_id = self.pool.get('res.partner').browse(cr,uid,partner)
            so_ngay_no_ids = self.pool.get('so.ngay.no').search(cr,uid,[('partner_id','=',partner_id.id),('product_category_id','=',categ_id),('manufacturer_product_id','=',manufacturer_product_id)])
            if not so_ngay_no_ids:
                self.pool.get('so.ngay.no').create(cr,uid,{'partner_id':partner_id.id,'product_category_id':categ_id,'manufacturer_product_id':manufacturer_product_id,'so_ngay':30})
        return product_id
    def write(self, cr, uid, ids, vals, context=None):
        super(product_product, self).write(cr, uid, ids, vals, context=context)
        if 'categ_id' in vals or 'manufacturer_product_id' in vals:
            for product_id in self.browse(cr,uid,ids):
                categ_id = product_id.categ_id.id
                manufacturer_product_id = product_id.manufacturer_product_id and product_id.manufacturer_product_id.id or False
                partner_ids = self.pool.get('res.partner').search(cr,uid,[('customer','=',True)])
                for partner in partner_ids:
                    partner_id = self.pool.get('res.partner').browse(cr,uid,partner)
                    so_ngay_no_ids = self.pool.get('so.ngay.no').search(cr,uid,[('partner_id','=',partner_id.id),('product_category_id','=',categ_id),('manufacturer_product_id','=',manufacturer_product_id)])
                    if not so_ngay_no_ids:
                        self.pool.get('so.ngay.no').create(cr,uid,{'partner_id':partner_id.id,'product_category_id':categ_id,'manufacturer_product_id':manufacturer_product_id,'so_ngay':30})
        return ids
    
    def name_get(self, cr, uid, ids, context=None):
        res = []
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            return res
        reads = self.read(cr, uid, ids, ['name'], context)
  
        for record in reads:
            name = record['name']
            res.append((record['id'], name))
        return res
     
product_product()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
