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
# 
 
class stock_balancesheet_report(osv.osv_memory):
    _name = "stock.balancesheet.report"
    
    def _get_default_shop(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id','=',company_id)], context=context)
        if not shop_ids:
            raise osv.except_osv(_('Error!'), _('There is no default shop for the current user\'s company!'))
        return shop_ids[0]
    
    _columns = {
        'short_by':fields.selection([
            (1 , 'By Category'),
            (2 , 'By Product')], 'Short By',required=True),
        'date_start':fields.date('Date Start',required=True),
        'date_end':fields.date('Date End',required=True),
        'shop_ids': fields.many2many('sale.shop', 'balancesheet_shop_rel', 'balanceshe_id', 'shop_id', 'Product Shop',required=True),
        'categ_ids': fields.many2many('product.category', 'balancesheet_category_rel', 'balanceshe_id', 'categ_id', 'Category',domain=[('type','<>','view')]),
        'location_id':fields.many2one('stock.location','Location',domain=[('usage','<>','view')]),
     }
    _defaults = {
        'date_start':time.strftime('%Y-%m-01'),
        'short_by':2,
        #'shop_ids': _get_default_shop,
        }
    
    
    
    def stock_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'stock.balancesheet.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        short_by = datas['form'] and datas['form']['short_by']
        if short_by and short_by==1:
            report_name = 'stock_balancesheet_categ_report'
        else:
            report_name = 'stock_balancesheet_product_report'
            
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
     
stock_balancesheet_report()

class stock_cards_report(osv.osv_memory):
    _name = "stock.cards.report"
    _columns = {
        'date_start':fields.date('Date Start',required=True),
        'date_end':fields.date('Date End',required=True),
        'warehouse_id':fields.many2one('stock.warehouse','Warehouse',required=False),
        'product_id':fields.many2one('product.product','Product',required=True),
        'location_id': fields.many2one('stock.location', 'Location',required=True, select=True,domain=[('usage','=','internal')]),
     }
    _defaults = {
        'date_start':time.strftime('%Y-%m-01')
        }
    
    def stock_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'stock.cards.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        report_name = context['type_report']
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
    
stock_cards_report()

class stock_cards_many_report(osv.osv_memory):
    _name = "stock.cards.many.report"
    _columns = {
        'date_start':fields.date('Date Start',required=True),
        'date_end':fields.date('Date End',required=True),
        'product_ids':fields.many2many('product.product', 'product_cards_rel', 'cards_id', 'product_id', 'Product'),
        'location_id': fields.many2one('stock.location', 'Location',required=False, select=True,domain=[('usage','=','internal')]),
     }
    _defaults = {
        'date_start':time.strftime('%Y-%m-01')
        }
    
    def stock_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'stock.cards.many.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        report_name = context['type_report']
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
    
stock_cards_many_report()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
