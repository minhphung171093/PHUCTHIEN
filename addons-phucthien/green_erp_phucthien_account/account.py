# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from datetime import datetime
import datetime
import calendar
import openerp.addons.decimal_precision as dp
import codecs
import time
from datetime import date
from datetime import timedelta
from datetime import datetime
from openerp import netsvc

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def _get_payment_state(self, cr, uid, ids, name, arg, context=None):        
        res = {}          
        for line in self.browse(cr, uid, ids):
            if line.date_due and (line.state !='paid' or line.state !='cancel'):
                result = True     
                b = datetime.now()
                a = line.date_due
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 7:
                    result = False
                res[line.id] = result
            else:
                res[line.id] = False            
        return res
    
    _columns = {
        'hop_dong_nt_id': fields.many2one('hop.dong','Hợp đồng nguyên tắc'),
        'hop_dong_t_id': fields.many2one('hop.dong','Hợp đồng thầu'),
        'hoadon_huy_id': fields.many2one('account.invoice','Hoá đơn huỷ'),
        'payment_mode_id': fields.many2one('res.payment.mode', 'Payment mode'),
        'payment_state': fields.function(_get_payment_state,type='boolean', string='Payment Status'),
        'partner_code': fields.related('partner_id','internal_code', type='char', readonly=True, size=64, relation='res.partner', store=True, string='Mã'),
        'product_id_relate': fields.related('invoice_line','product_id', type='many2one', readonly=True, relation='product.product', string='Sản phẩm'),
        'categ_id_relate': fields.related('product_id_relate', 'categ_id', type='many2one', readonly=True, relation='product.category', string='Danh mục sản phẩm'),
    }
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user, [('number','=',name)] + args, limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('name',operator,name)] + args, limit=limit, context=context)
        if context.get('search_hoadon_huy'):
            if context.get('search_hoadon_huy_partner'):
                sql = '''
                    SELECT id FROM account_invoice where state ='cancel' and partner_id=%s and id 
                        not in (select hoadon_huy_id from account_invoice where hoadon_huy_id is not null)
                '''%(context.get('search_hoadon_huy_partner'))
            else:
                sql = '''
                    SELECT id FROM account_invoice where state ='cancel' and id 
                        not in (select hoadon_huy_id from account_invoice where hoadon_huy_id is not null)
                '''
            cr.execute(sql)
            invoice_ids = [row[0] for row in cr.fetchall()]
            
            ids = self.search(cr, user, [('id','in',invoice_ids)] + args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context)
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
#         if context.get('search_hoadon_huy'):
        res = []
        reads = self.read(cr, uid, ids, ['reference','reference_number'], context)
   
        for record in reads:
            name = (record['reference'] or '')+'/'+(record['reference_number'] or '')
            res.append((record['id'], name))
        return res
#         types = {
#                 'out_invoice': _('Invoice'),
#                 'in_invoice': _('Supplier Invoice'),
#                 'out_refund': _('Refund'),
#                 'in_refund': _('Supplier Refund'),
#                 }
#         return [(r['id'], '%s %s' % (r['number'] or types[r['type']], r['name'] or '')) for r in self.read(cr, uid, ids, ['type', 'number', 'name'], context, load='_classic_write')]
#     
#     def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
#         if context is None:
#             context = {}
#         if context.get('search_hoadon_huy'):
#             sql = '''
#                 SELECT id FROM account_invoice where state ='cancel' 
#             '''
#             cr.execute(sql)
#             invoice_ids = [row[0] for row in cr.fetchall()]
#             args += [('id','in',invoice_ids)]
#         return super(account_invoice, self).search(cr, uid, args, offset, limit, order, context, count)
    
account_invoice()

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
