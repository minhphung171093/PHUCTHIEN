# -*- coding: utf-8 -*-
# #############################################################################
# 
# #############################################################################
from osv import fields, osv
from tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _order = "internal_code,name"
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.name
            #Thanh: Change the way show name - Dont need to show company name
#             if record.parent_id and not record.is_company:
#                 name =  "%s, %s" % (record.parent_id.name, name)
            if record.internal_code:
                name = '[' + record.internal_code + '] ' + name
            #Thanh: Change the way show name
            if context.get('show_address'):
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
                name = name.replace('\n\n','\n')
                name = name.replace('\n\n','\n')
            if context.get('show_email') and record.email:
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        return res
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
            #Thanh: Search by internal_code and VAT
            if not ids:
                ids = self.search(cr, uid, [('internal_code', operator, name)] + args, limit=limit, context=context)
            
            if not ids:
                ids = self.search(cr, uid, [('vat', operator, name)] + args, limit=limit, context=context)
            #Thanh: Search by internal_code and VAT
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)
    
    
    _columns = {
        'internal_code': fields.char('Internal Code', size=50),
    }
    
    def _check_internal_code(self, cr, uid, ids, context=None):
        partner = self.browse(cr, uid, ids[0], context=context)
        if partner.internal_code:
            e_ids = self.search(cr, uid, [('id','!=',partner.id),('internal_code','=',partner.internal_code)])
            if e_ids:
                raise osv.except_osv(_('Duplicate Partner!'),_("Internal Code '%s' is already exist for Partner '%s'. Try another Code")%(partner.internal_code,self.browse(cr, uid, e_ids[0], context=context).name))
        return True

    _constraints = [
        (_check_internal_code, "Internal Code is already exist", ['value_amount']),
    ]
    
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
