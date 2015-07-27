import time
from lxml import etree
from openerp.osv import fields, osv
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class stock_partial_picking(osv.osv_memory):
    _inherit="stock.partial.picking"
    
    _columns={
              }
    
    def update_lot(self, cr, uid, ids, context=None):
        lot_obj = self.pool.get('stock.production.lot')
        for picking in self.browse(cr, uid, ids):
            for line in picking.move_ids:
                lot_id = lot_obj.create(cr, uid, {
                    'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.lot.serial'),
                    'product_id': line.product_id.id,
                })
                cr.execute('update stock_partial_picking_line set prodlot_id = %s where id = %s',(lot_id,line.id))
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.partial.picking',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': ids[0],
            'context': context,
            'nodestroy': True,
        }
#     
#     def _partial_move_for(self, cr, uid, move):
#         partial_move = {
#             'product_id' : move.product_id.id,
#             'quantity' : move.product_qty if move.state == 'assigned' or move.picking_id.type == 'in' else 0,
#             'product_uom' : move.product_uom.id,
#             'prodlot_id' : move.prodlot_id.id,
#             'solo':move.prodlot_id.name or '/',
#             'move_id' : move.id,
#             'location_id' : move.location_id.id,
#             'location_dest_id' : move.location_dest_id.id,
#             'currency': move.picking_id and move.picking_id.company_id.currency_id.id or False,
#         }
#         if move.picking_id.type == 'in' and move.product_id.cost_method == 'average':
#             partial_move.update(update_cost=True, **self._product_cost_for_average_update(cr, uid, move))
#         return partial_move
    
stock_partial_picking()