##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import datetime
from openerp.osv import fields, osv
from openerp import pooler
from openerp.tools.translate import _


class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'

    # Assign dates according to products data
    def create(self, cr, uid, vals, context=None):
        newid = super(stock_production_lot, self).create(cr, uid, vals, context=context)
        obj = self.browse(cr, uid, newid, context=context)
        if obj.product_id.flag_expirate_date == True:
            if not obj.life_date:
                raise osv.except_osv(_('Error!'), _('Please define Flag Expirate Date on the Product'))
            
        towrite = []
        for f in ('life_date', 'use_date', 'removal_date', 'alert_date'):
            if not getattr(obj, f):
                towrite.append(f)
        if context is None:
            context = {}
        context['product_id'] = obj.product_id.id
        self.write(cr, uid, [obj.id], self.default_get(cr, uid, towrite, context=context))
        return newid    
    
    def write(self, cr, uid, ids, vals, context=None):
        update_id = super(osv.osv, self).write(cr, uid, ids, vals, context=context)
        for lot in self.browse(cr, uid, ids, context=context):
            if lot.product_id.flag_expirate_date == True:
                if not lot.life_date:
                    raise osv.except_osv(_('Error!'), _('Please define Flag Expirate Date on the Product'))
        return update_id

stock_production_lot()

class product_product(osv.osv):
    _inherit = 'product.product'
    _columns = {
        'flag_expirate_date':fields.boolean('Expiration Date Flag')
    }
    
    
    
product_product()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
