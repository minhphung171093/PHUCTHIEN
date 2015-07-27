# -*- coding: utf-8 -*-
# #############################################################################
# 
# #############################################################################
from osv import fields, osv
from tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'
    
    _columns = {
    }
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        if context is None:
            context = {}
        
        #Thanh: Extend search for Internal Partner (usually Employee)
        user = self.pool.get('res.users').browse(cr, uid, uid)
        if user.company_id and user.company_id.partner_id:
            if context.get('auto_search_my_company',False):
                arg = ('parent_id','=',user.company_id.partner_id.id)
                args.append(arg)
            # else:
            #     args.append('|')
            #     args.append(('parent_id','!=',user.company_id.partner_id.id))
            #     args.append(('parent_id','=',False))
        return super(res_partner, self).search(cr, uid, args, offset, limit, order, context=context, count=count)
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(res_partner, self).default_get(cr, uid, fields, context=context)
        
        #Thanh: Default get Parent compnay for Internal Partner (usually Employee)
        user = self.pool.get('res.users').browse(cr, uid, uid)
        if user.company_id and user.company_id.partner_id and context and context.get('auto_default_my_company',False):
            res.update({
                'parent_id': user.company_id.partner_id.id,
            })
        return res
    
res_partner()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
