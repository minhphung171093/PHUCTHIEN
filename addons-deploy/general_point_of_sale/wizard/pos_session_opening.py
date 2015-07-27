
from openerp import netsvc
from openerp.osv import osv, fields
from openerp.tools.translate import _

from openerp.addons.point_of_sale.point_of_sale import pos_session


class pos_session_opening(osv.osv_memory):
    _inherit = 'pos.session.opening'

    _columns = {
    }

    def open_ui(self, cr, uid, ids, context=None):
        context = context or {}
        data = self.browse(cr, uid, ids[0], context=context)
        context['active_id'] = data.pos_session_id.id
#         return {
#             'type' : 'ir.actions.client',
#             'name' : _('Start Point Of Sale'),
#             'tag' : 'pos.ui',
#             'context' : context
#         }
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'point_of_sale', 'view_pos_pos_form')
        res_id = res and res[1] or False
        context['default_type_pos'] = 'delivery'
        context['default_session_id'] = data.pos_session_id.id
        return {
            'name': _('Point of Sale Orders'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'pos.order',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }

pos_session_opening()
