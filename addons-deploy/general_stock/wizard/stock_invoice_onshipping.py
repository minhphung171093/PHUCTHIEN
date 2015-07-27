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

from openerp.osv import fields, osv

from openerp.tools.translate import _

class stock_invoice_onshipping(osv.osv_memory):
    _inherit = "stock.invoice.onshipping"
    _columns = {
        'invoiced':fields.boolean('Choose All' ),
        'multi_invoice': fields.boolean('Multi Invoice'),
        'move_ids' : fields.one2many('stock.invoice.line.onshipping', 'wizard_id','Product Moves'),
    }

    _defaults = {
        'multi_invoice':False,
        'invoiced':True
    }
    
    # kiet them 
    def onchange_invoiced(self,cr,uid,ids,invoiced,move_ids):
        res ={}
        i = 0
        for line in move_ids:
            if not line[2]:
                i += 1
                continue
            if invoiced == True:
                move_ids[i][2]['check_invoice'] = True
            else:
                move_ids[i][2]['check_invoice'] = False
            i += 1
        value ={
                 'move_ids': move_ids,
                 }
        return  {'value': value}
    
    def get_return_history(self, cr, uid, picking_id, context=None):
        return_history = {}
        for m  in picking_id.move_lines:
            if m.state == 'done':
                return_history[m.id] = 0
                for rec in m.move_history_ids2:
#                     if rec.location_dest_id.id == m.location_id.id \
#                         and rec.location_id.id == m.location_dest_id.id and rec.state == 'done':
                    return_history[m.id] += (rec.product_qty * rec.product_uom.factor)
        return return_history
    
    def get_returned_qty(self,cr,uid,move,context=None):
        return_qty = 0
        if move.picking_id:
            return_history = self.get_return_history(cr, uid, move.picking_id, context)
            return_qty = return_history[move.id]
        return return_qty
        
    def _invoice_shipping_add(self, cr, uid, move):
        return_qty = self.get_returned_qty(cr,uid,move)
        invoicing_qty = move.product_qty - return_qty - move.invoiced_qty
        invoice_shipping = False
        if invoicing_qty:
        # chua tru` ton=
            invoice_shipping = {
                'product_id' : move.product_id.id,
                'quantity' : invoicing_qty,
                'invoicing_qty':invoicing_qty,
                'product_uom' : move.product_uom.id,
                'move_id' : move.id,
                'check_invoice': True,
                'prodlot_id':move.prodlot_id.id,
            }
        return invoice_shipping
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        
        res = super(stock_invoice_onshipping, self).default_get(cr, uid, fields, context=context)
        stock_picking = self.pool.get('stock.picking')
        stock_move = self.pool.get('stock.move')
        picking_ids = context.get('active_ids')
        if not picking_ids:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        
        move_line_ids = stock_move.search(cr,uid,[('picking_id','in',picking_ids)])
        pick_obj = stock_picking.browse(cr,uid,picking_ids)
        if len(picking_ids) == 1 and pick_obj[0].purchase_id:
             res.update({'multi_invoice':True,'invoiced':True})
        if move_line_ids:
            moves = []
            for line in stock_move.browse(cr,uid,move_line_ids):
                invoicing_line = self._invoice_shipping_add(cr,uid,line)
                if invoicing_line:
                    moves.append(invoicing_line)
            res.update(move_ids=moves)
        return res
    
    def create_invoice(self, cr, uid, ids, context=None):
        wizard_obj =self.browse(cr,uid,ids[0])
        move_ids = wizard_obj.move_ids
        count = 0
        for line in move_ids:
            if line.check_invoice:
                count += 1
        if count == 0:
            raise osv.except_osv(_('Warning'), _('You have to check at least one line to generate invoice!'))
        context.update({'invoicing_list':move_ids})
        return super(stock_invoice_onshipping, self).create_invoice(cr, uid, ids, context=context)

stock_invoice_onshipping()

class stock_invoice_line_onshipping(osv.osv_memory):
    _description = "stock_invoice_line_onshipping"    
    _name ="stock.invoice.line.onshipping" 
    _columns = {
                'product_id' : fields.many2one('product.product', string="Product", required=True, readonly=True),
                'quantity' : fields.float("Quantity",  required=True),
                'invoicing_qty': fields.float("Invoicing Qty", readonly=True), 
                'product_uom': fields.many2one('product.uom', 'Uom', required=True, readonly=True),
                'move_id' : fields.many2one('stock.move', "Move",),
                'wizard_id' : fields.many2one('stock.invoice.onshipping', string="Wizard"),
                'check_invoice':fields.boolean('Choose'),
                #Hung them so lo
                'prodlot_id': fields.many2one('stock.production.lot', 'Số lô', ondelete='restrict',readonly=True),
               }
    _defaults = {
                 'check_invoice': True
                 }
    
    def onchange_quantity(self,cr,uid,ids,quantity,invoicing_qty):
        value ={}
        warning ={}
        if (quantity > invoicing_qty or quantity < 0):
            value.update({'quantity':invoicing_qty,'check_invoice':False})
            warning = {
                 'title': _('Warning!'),
                 'message' : _("Quantity must be smaller than Invoicing Qty or greater than 0 !!!")
                 }
            return {'value': value, 'warning': warning} 
        else:
            value.update({'check_invoice':True})
            return {'value': value, 'warning': warning} 
    
stock_invoice_line_onshipping()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
