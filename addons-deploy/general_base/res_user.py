# -*- coding: utf-8 -*-
##############################################################################
#
#    HLVSolution, Open Source Management Solution
#
##############################################################################

import openerp
from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp.addons.general_base import amount_to_text_vn
from openerp.addons.general_base import amount_to_text_en

class users(osv.osv):
    _inherit = 'res.users'
    _columns = {
        'context_shop_id': fields.many2one('sale.shop', 'Shop', required=False, context={'user_preference': True}),
        'shop_ids':fields.many2many('sale.shop', 'sale_shop_users_rel', 'user_id', 'shop_id', 'Shops'),
    }
    
    def on_change_shop_id(self, cr, uid, ids, context_shop_id):
        return {
                'warning' : {
                    'title': _("Shop Switch Warning"),
                    'message': _("Please keep in mind that documents currently displayed may not be relevant after switching to another Shop. If you have unsaved changes, please make sure to save and close all forms before switching to a different Shop. (You can click on Cancel in the User Preferences now)"),
                }
        }
    
    def _check_shop(self, cr, uid, ids, context=None):
        for this in self.browse(cr, uid, ids):
            if this.context_shop_id and this.shop_ids and this.context_shop_id not in this.shop_ids:
                return False
        return True

    _constraints = [
        (_check_shop, 'The chosen Shop is not in the allowed Shops for this user', ['context_shop_id', 'shop_ids']),
    ]
    
    def amount_to_text(self, nbr, lang='vn', currency='USD'):
        if lang == 'vn':
            return amount_to_text_vn.amount_to_text(nbr, lang)
        else:
            return amount_to_text_en.amount_to_text(nbr, 'en', currency)
        
users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
