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
from openerp.osv import osv,fields
from openerp.tools.translate import _


class purchase_line_approve(osv.osv_memory):
    _name = 'purchase.order.line_approve'
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Supplier',required=True),
        'date': fields.date('Order Date',required=True),
    }
    
    _defaults = {
        'date': time.strftime('%Y-%m-%d'),
    }
    
    def make_purchase(self, cr, uid, ids, context=None):
        line_approve = self.browse(cr, uid, ids[0])
        po_line_ids = context.get('active_ids')
        po_obj = self.pool.get('purchase.order')
        po_line_obj = self.pool.get('purchase.order.line')
        default = {'order_line':[],'partner_id':line_approve.partner_id.id,'order_date':line_approve.date}
        po_line = po_line_obj.browse(cr, uid, po_line_ids[0])
        po_id = po_obj.copy(cr, uid, po_line.order_id.id,default)
        po_line_obj.write(cr, uid, po_line_ids,{'order_id':po_id,'approve':True})
            
        mod_obj = self.pool.get('ir.model.data')
        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'),('name', '=', 'purchase_order_form')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'name': _('Purchase Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': po_id,
        }
purchase_line_approve()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

