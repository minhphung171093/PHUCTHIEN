import time
from lxml import etree
from openerp.osv import fields, osv
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp import netsvc

class stock_slip_picking(osv.osv_memory):
    _name="stock.slip.picking"
    _rec_name = 'picking_id'
    _columns={
              'date': fields.datetime('Date', required=True),
              'move_ids' : fields.one2many('stock.slip.picking.line', 'wizard_id', 'Product Moves'),
              'picking_id': fields.many2one('stock.picking', 'Picking', required=True, ondelete='CASCADE'),
              }
    
    def _partial_move_for(self, cr, uid, move):
        partial_move = {}
        if move.location_dest_id.usage =='inventory':
            partial_move = {
                'product_id' : move.product_id.id,
                'quantity' : move.product_qty or 0,
                'product_uom' : move.product_uom.id,
                'prodlot_id' : move.prodlot_id.id,
                'move_id' : move.id,
                'location_id' : move.location_id.id,
                'location_dest_id' : move.picking_id and move.picking_id.partner_id.property_stock_customer and move.picking_id.partner_id.property_stock_customer.id or move.location_dest_id.id,
                'currency': move.picking_id and move.picking_id.company_id.currency_id.id or False,
            }
        if move.picking_id.type == 'in' and move.product_id.cost_method == 'average':
            partial_move.update(update_cost=True, **self._product_cost_for_average_update(cr, uid, move))
        return partial_move
    
    def __get_help_text(self, cursor, user, picking_id, context=None):
        text = _("The proposed cost is made based on %s")
        value = _("standard prices set on the products")
        return text % value
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        picking_ids = context.get('active_ids', [])
        res = {}
        moves = []
        picking_id, = picking_ids
        if 'picking_id' in fields:
            res.update(picking_id=picking_id)
        if 'move_ids' in fields:
            picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
            for m in picking.move_lines:
                if m.state in ('done'):
                    if self._partial_move_for(cr, uid, m):
                        moves.append(self._partial_move_for(cr, uid, m))
            res.update(move_ids=moves)
        if 'date' in fields:
            res.update(date=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        res['help_text'] = self.__get_help_text(cr, uid, picking_id, context=context)
        return res
    
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        if context is None:
            context = {}
        else:
            context = dict(context)
        res = {}
        location={}
        wf_service = netsvc.LocalService("workflow")
        pick_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        sequence_obj = self.pool.get('ir.sequence')
        for pick in pick_obj.browse(cr, uid, ids, context=context):
            new_picking = None
            complete, too_many, too_few = [], [], []
            prodlot_ids, move_product_qty,   partial_qty, product_uoms = {}, {}, {},{}
            for move in pick.move_lines:
                if move.state in ('cancel'):
                    continue
                if not move.location_dest_id.usage =='inventory':
                    continue
                partial_data = partial_datas.get('move%s'%(move.id), {})
                product_qty = partial_data.get('product_qty',0.0)
                move_product_qty[move.id] = product_qty
                product_uom = partial_data.get('product_uom',False)
                prodlot_id = partial_data.get('prodlot_id')
                product_uoms[move.id] = product_uom
                partial_qty[move.id] = uom_obj._compute_qty(cr, uid, product_uoms[move.id], product_qty, move.product_uom.id)
                prodlot_ids[move.id] = prodlot_id
                #Kiet thay doi location_dest
                location[move.id] = partial_data.get('location_dest_id',False)
                if move.product_qty == partial_qty[move.id]:
                    complete.append(move)
                elif move.product_qty > partial_qty[move.id]:
                    too_few.append(move)
                else:
                    too_many.append(move)
                
                    
            for move in too_few:
                product_qty = move_product_qty[move.id]
                if not new_picking:
                    new_picking_name = pick.name
                    pick_obj.write(cr, uid, [pick.id], 
                               {'name': sequence_obj.get(cr, uid,
                                            'stock.picking.%s'%(pick.type)),
                               })
                    new_picking = pick_obj.copy(cr, uid, pick.id,
                            {
                                'name': new_picking_name,
                                'move_lines' : [],
                                'state':'draft',
                            })
                if product_qty != 0:
                    defaults = {
                            'product_qty' : product_qty,
                            'product_uos_qty': product_qty, #TODO: put correct uos_qty
                            'picking_id' : new_picking,
                            'state': 'assigned',
                            'move_dest_id': False,
                            'price_unit': move.price_unit,
                            'product_uom': product_uoms[move.id],
                            'location_dest_id':location[move.id]
                    }
                    prodlot_id = prodlot_ids[move.id]
                    if prodlot_id:
                        defaults.update(prodlot_id=prodlot_id)
                    move_obj.copy(cr, uid, move.id, defaults)
                move_obj.write(cr, uid, [move.id],
                        {
                            'product_qty': move.product_qty - partial_qty[move.id],
                            'product_uos_qty': move.product_qty - partial_qty[move.id], #TODO: put correct uos_qty
                            'prodlot_id': False,
                            'tracking_id': False,
                            
                        })
 
            if new_picking:
                move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
            for move in complete:
                defaults = {'location_dest_id':location[move.id],'product_uom': product_uoms[move.id], 'product_qty': move_product_qty[move.id]}
                if prodlot_ids.get(move.id):
                    defaults.update({'prodlot_id': prodlot_ids[move.id]})
                move_obj.write(cr, uid, [move.id], defaults)
            for move in too_many:
                product_qty = move_product_qty[move.id]
                defaults = {
                    'product_qty' : product_qty,
                    'product_uos_qty': product_qty, #TODO: put correct uos_qty
                    'product_uom': product_uoms[move.id],
                    'location_dest_id':location[move.id]
                }
                if prodlot_ids.get(move.id):
                    defaults.update(prodlot_id=prodlot_id)
                if new_picking:
                    defaults.update(picking_id=new_picking)
                move_obj.write(cr, uid, [move.id], defaults)
 
            # At first we confirm the new picking (if necessary)
            if new_picking:
                # Then we finish the good picking
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                pick_obj.write(cr, uid, [pick.id], {'backorder_id': new_picking})
                pick_obj.action_move(cr, uid, [new_picking])
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
                wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
                
                delivered_pack_id = pick.id
                back_order_name = pick_obj.browse(cr, uid, delivered_pack_id, context=context).name
                pick_obj.message_post(cr, uid, new_picking, body=_("Back order <em>%s</em> has been <b>created</b>.") % (back_order_name), context=context)
                pick_obj.update_flag(cr,uid,new_picking)
                
            else:
                pick_obj.action_move(cr, uid, [pick.id])
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
                delivered_pack_id = pick.id
                pick_obj.update_flag(cr,uid,pick.id)
            delivered_pack = pick_obj.browse(cr, uid, delivered_pack_id, context=context)
            res[pick.id] = {'delivered_picking': delivered_pack.id or False}
 
        return res
    
    def do_slip(self,cr,uid,ids,context= None):
        if context is None:
            context = {}
        assert len(ids) == 1, 'Partial picking processing may only be done one at a time.'
        stock_move = self.pool.get('stock.move')
        partial = self.browse(cr, uid, ids[0], context=context)
        partial_data = {
            'delivery_date' : partial.date
        }
        picking_type = partial.picking_id.type
        for wizard_line in partial.move_ids:
            move_id = wizard_line.move_id.id

            if wizard_line.quantity < 0:
                raise osv.except_osv(_('Warning!'), _('Please provide proper Quantity.'))
            if not move_id:
                seq_obj_name =  'stock.picking.' + picking_type
                move_id = stock_move.create(cr,uid,{'name' : self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
                                                    'product_id': wizard_line.product_id.id,
                                                    'product_qty': wizard_line.quantity,
                                                    'product_uom': wizard_line.product_uom.id,
                                                    'location_id' : wizard_line.location_id.id,
                                                    'location_dest_id' : wizard_line.location_dest_id.id,
                                                    'picking_id': partial.picking_id.id
                                                    },context=context)
            partial_data['move%s' % (move_id)] = {
                'product_id': wizard_line.product_id.id,
                'product_qty': wizard_line.quantity,
                'product_uom': wizard_line.product_uom.id,
                'move_id': move_id,
                'prodlot_id':wizard_line.prodlot_id.id
            }
            partial_data['move%s' % (wizard_line.move_id.id)].update(location_dest_id=wizard_line.location_dest_id.id)
        
        
        done = self.do_partial(cr, uid, [partial.picking_id.id], partial_data, context=context)
        
        if done[partial.picking_id.id]['delivered_picking'] == partial.picking_id.id:
            return {'type': 'ir.actions.act_window_close'}
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': context.get('active_model', 'stock.picking'),
            'name': _('Partial Delivery'),
            'res_id': done[partial.picking_id.id]['delivered_picking'],
            'view_type': 'form',
            'view_mode': 'form,tree,calendar',
            'context': context,
        }
        return 1
    
stock_slip_picking()

class stock_slip_picking_line(osv.osv_memory):
    _name = "stock.slip.picking.line"
    _rec_name = 'product_id'
    _columns = {
        'product_id' : fields.many2one('product.product', string="Product", required=True, ondelete='CASCADE'),
        'quantity' : fields.float("Quantity", digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True, ondelete='CASCADE'),
        'location_id': fields.many2one('stock.location', 'Location', required=True, ondelete='CASCADE', domain = [('usage','<>','view')]),
        'location_dest_id': fields.many2one('stock.location', 'Dest. Location', required=True, ondelete='CASCADE',domain = [('usage','<>','view')]),
        'move_id' : fields.many2one('stock.move', "Move", ondelete='CASCADE'),
        'prodlot_id' : fields.many2one('stock.production.lot', 'Serial Number', ondelete='CASCADE'),
        'wizard_id' : fields.many2one('stock.slip.picking', string="Wizard", ondelete='CASCADE'),
        'currency' : fields.many2one('res.currency', string="Currency", help="Currency in which Unit cost is expressed", ondelete='CASCADE'),
    }
stock_slip_picking_line()