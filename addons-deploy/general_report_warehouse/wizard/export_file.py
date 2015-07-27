# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

import time
from datetime import datetime
from osv import fields, osv
from tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import decimal_precision as dp
from tools.translate import _


class export_file(osv.osv_memory):
    _name = "export.file"
    _columns = {
        'shop_id':fields.many2one('sale.shop','Shop'),
        'sale_price_list_id':fields.many2one('sale.pricelist','Sale Price List'),
        'partner_id':fields.many2one('res.partner','Supplier',domain="[('supplier', '=', True)]"),
#         'blanket_id':fields.many2one('purchase.blanket.site', 'Purchase Blanket Site', domain="[('partner_id','=',partner_id)]",),
        'warehouse_id':fields.many2one('stock.warehouse','Warehouse'),
        'date':fields.date('Date')
     }
    _defaults = {
         'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    def sale_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'export.file'
        datas['form'] = self.read(cr, uid, ids)[0]
        report_name = context['type_report'] 
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
export_file()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
