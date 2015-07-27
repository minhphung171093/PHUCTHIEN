# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

import time
from report import report_sxw
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.user_obj = pooler.get_pool(self.cr.dbname).get('res.users')
        self.cr = cr
        self.uid = uid
        self.sum_system_value = 0.0
        self.sum_count_value  = 0.0
        self.sum_adjust_value = 0.0
        self.sum_percent = 0.0
        
        self.localcontext.update({
            'get_header':self.get_header,
            'get_line':self.get_line,
        })
        
    def get_header(self):
        res ={}
        
        wizard_data = self.localcontext['data']['form']
        
        warehouse_id = wizard_data['warehouse_id'][0]
        category_id = wizard_data['category_id'][0]
        from_date = wizard_data['from_date'][0]
        to_date = wizard_data['to_date'][0]
        
        sql ='''

        ''' %(inventory_id)
        
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            res= {
                'default_code':i['default_code'],
                'product_name':i['product_name'],
                'uom':i['uom'],
                'qty_Tondau':i['qty_Tondau'],
                'qty_xuat':i['qty_xuat'],
                'qty_toncuoi':i['qty_toncuoi']
                }
        
        return res
                    
    def get_line(self):
        wizard_data = self.localcontext['data']['form']
        location_id = wizard_data['location_id'][0]
        inventory_id = wizard_data['inventory_id'][0]
        sum_adjust_qty = 0
        sum_count_qty  = 0
        
        sql ='''
            SELECT default_code, product_name ,uom ,sum(qty_tondau) qty_tondau, sum(qty_nhap) qty_nhap,sum(qty_xuat) qty_xuat,
    sum(qty_toncuoi) qty_toncuoi
        FROM
        (
        SELECT pp.default_code,pt.name product_name,uom.name uom, cat.name categ_name,coalesce(n.qty,0) - coalesce(x.qty,0) 
        qty_tondau, 0 qty_nhap, 0 qty_xuat,0 qty_toncuoi
        FROM product_product pp inner join product_template pt on pp.product_tmpl_id = pt.id and pp.active ='True'
             inner join product_category cat on pt.categ_id = cat.id
             inner join product_uom uom on pt.uom_id = uom.id 
             left join
             (
            SELECT sm.product_id, sum(sm.primary_qty) qty
            FROM stock_move sm inner join stock_location sl on sm.location_dest_id = sl.id
            WHERE sl.usage = 'internal' and sm.state='done' and sm.date::date <'01/01/2013'
            group by sm.product_id
             )n on pp.id = n.product_id
             left join 
             (
            SELECT sm.product_id, sum(sm.primary_qty) qty 
            FROM stock_move sm inner join stock_location sl on sm.location_id = sl.id
            WHERE sl.usage = 'internal' and sm.state='done' and sm.date::date <'01/01/2013'
            group by sm.product_id
        
             )x on pp.id = x.product_id
        
         union all
        
        SELECT pp.default_code,pt.name product_name,uom.name uom, cat.name categ_name,0 qty_tondau,
               coalesce(n.qty,0) qty_nhap, coalesce(x.qty,0) qty_xuat,0 qty_toncuoi 
        FROM product_product pp inner join product_template pt on pp.product_tmpl_id = pt.id and pp.active ='True'
             inner join product_category cat on pt.categ_id = cat.id
             inner join product_uom uom on pt.uom_id = uom.id 
             left join
             (
            SELECT sm.product_id, sum(sm.primary_qty) qty
            FROM stock_move sm inner join stock_location sl on sm.location_dest_id = sl.id
            WHERE sl.usage = 'internal' and sm.state='done' and sm.date::date between '01-01-2013' and '5-31-2013'
            group by sm.product_id
             )n on pp.id = n.product_id
             left join 
             (
            SELECT sm.product_id, sum(sm.primary_qty) qty 
            FROM stock_move sm inner join stock_location sl on sm.location_id = sl.id
            WHERE sl.usage = 'internal' and sm.state='done' and sm.date::date between '01-01-2013' and '5-31-2013'
            group by sm.product_id
        
             )x on pp.id = x.product_id
         
        union all
        
        SELECT pp.default_code,pt.name product_name,uom.name uom, cat.name categ_name,0 qty_tondau,
               0 qty_nhap, 0 qty_xuat,coalesce(n.qty,0) - coalesce(x.qty,0) qty_toncuoi
        FROM product_product pp inner join product_template pt on pp.product_tmpl_id = pt.id and pp.active ='True'
             inner join product_category cat on pt.categ_id = cat.id
             inner join product_uom uom on pt.uom_id = uom.id 
             left join
             (
            SELECT sm.product_id, sum(sm.primary_qty) qty,sm.date
            FROM stock_move sm inner join stock_location sl on sm.location_dest_id = sl.id
            WHERE sl.usage = 'internal' and sm.state='done' and sm.date::date <= '5-31-2013'
            group by sm.product_id,sm.date
             )n on pp.id = n.product_id
             left join 
             (
            SELECT sm.product_id, sum(sm.primary_qty) qty 
            FROM stock_move sm inner join stock_location sl on sm.location_id = sl.id
            WHERE sl.usage = 'internal' and sm.state='done' and sm.date::date <= '5-31-2013'
            group by sm.product_id
        
             )x on pp.id = x.product_id)x
             group by default_code, product_name ,uom
        ''' 
        self.cr.execute(sql)
        res =[]
        
        for i in self.cr.dictfetchall():
            res.append(
                       {'default_code':i['default_code'],
                       'product_name':i['product_name'],
                       'uom':i['uom'],
                       'qty_tondau':i['qty_tondau'],
                       
                       'qty_nhap':i['qty_nhap'],
                       'qty_xuat':i['qty_xuat'],
                       'qty_toncuoi':i['qty_toncuoi'],
                       })
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
