# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP SA (<http://openerp.com>).
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
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
from openerp.tools.translate import _


class stock_partial_move_line(osv.osv_memory):
    _inherit = "stock.partial.move.line"
                
    _columns = {
            'solo':fields.char('Số lô'),
            'life_date':fields.date('Ngày hết hạn'),
     }
    _defaults = {
            'solo':'/',
            'life_date':time.strftime('%Y-%m-%d'),
    }
stock_partial_move_line()


class stock_partial_move(osv.osv_memory):
    _inherit = 'stock.partial.move'
    _columns = {
     }
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        # no call to super!
        res = {}
        new_moves = []
        partial_obj = self.pool.get('stock.partial.picking')
        move_ids = context.get('active_ids', [])
        if not move_ids or not context.get('active_model') == 'stock.move':
            return res
        if 'move_ids' in fields:
            move_ids = self.pool.get('stock.move').browse(cr, uid, move_ids, context=context)
            moves = [partial_obj._partial_move_for(cr, uid, m) for m in move_ids if m.state not in ('done','cancel')]
            
            for lines in moves:
                for line in lines:
                    new_moves.append(line)
            res.update(move_ids=new_moves)
            
        if 'date' in fields:
            res.update(date=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        return res
    
    def do_partial(self, cr, uid, ids, context=None):
        # no call to super!
        lot_obj = self.pool.get('stock.production.lot')
        assert len(ids) == 1, 'Partial move processing may only be done one form at a time.'
        partial = self.browse(cr, uid, ids[0], context=context)
        partial_data = {
            'delivery_date' : partial.date
        }
        moves_ids = []
        for move in partial.move_ids:
            if not move.move_id:
                raise osv.except_osv(_('Warning !'), _("You have manually created product lines, please delete them to proceed"))
            if (not move.product_id.track_production) or (not move.product_id.track_incoming) or (not move.product_id.track_outgoing):
                raise osv.except_osv(_('Warning !'), _("You  much define track_production, track_incoming, track_outgoing in Product"))
            
            if not move.prodlot_id:
                
                if move.solo =='/':
                    lot_id = lot_obj.create(cr, uid, {
                    'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.lot.serial'),
                    'product_id': move.product_id.id,
                    'life_date':move.life_date
                    })
                else:
                    lot_id = lot_obj.create(cr, uid, {
                    'name': move.solo,
                    'product_id': move.product_id.id,
                    'life_date':move.life_date
                    })
            else:
                lot_id = move.prodlot_id.id
            move_id = move.move_id.id
            
            partial_data['move%s' % (move_id)] = {
                'product_id': move.product_id.id,
                'product_qty': move.quantity,
                'product_uom': move.product_uom.id,
                'prodlot_id': lot_id,
            }
            moves_ids.append(move_id)
            if (move.move_id.picking_id.type == 'in') and (move.product_id.cost_method == 'average'):
                partial_data['move%s' % (move_id)].update(product_price=move.cost,
                                                          product_currency=move.currency.id)
        self.pool.get('stock.move').do_partial(cr, uid, moves_ids, partial_data, context=context)
        return {'type': 'ir.actions.act_window_close'}
    
stock_partial_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
