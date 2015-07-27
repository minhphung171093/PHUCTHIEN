# -*- coding: utf-8 -*-
##############################################################################
#
#    HLVSolution, Open Source Management Solution
#
##############################################################################

import time
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import tools
from osv import fields, osv

class stock_onhand_analys(osv.osv):
    _name = "stock.onhand.analys"
    _description = "Stock Onhand Analys"
    _auto = False
    _columns = {
                'warehouse_id':fields.many2one('stock.warehouse','Warehouse', readonly=True, size =200),
                'location_id':fields.many2one('stock.location','Location', readonly=True, size =200),
                'product_id':fields.many2one('product.product','Product',readonly=True),
                'uom_id':fields.many2one('product.uom','UoM',readonly=True),
                'categ_id':fields.many2one('product.category','Product Category',readonly=True),
                'onhand_qty':fields.float('Onhand Qty', size=64, readonly=True,digits= (16,3)),
                'onhand_val':fields.float('Onhand Val', size=64, readonly=True,digits= (16,2)),
            }
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'stock_onhand_analys')
        cr.execute("""
            create or replace view stock_onhand_analys
            as
            (
            select row_number() over (order by onh.warehouse_id,
                    onh.location_id, msi.product_code) id,
                    onh.warehouse_id, onh.location_id,
                    onh.location_name, msi.product_id,
                    msi.product_code, msi.product_name,
                    msi.uom_id, msi.uom_name, msi.categ_id,
                    sum(coalesce(onh.onhand_qty,0)) onhand_qty,
                    sum(coalesce(onh.onhand_val,0)) onhand_val,
                    onh.item_cost current_cost
            from (
                    select ppp.id product_id, ppt.name product_name,
                        ppp.default_code product_code, ppt.uom_id,
                        uom.name uom_name, ppt.categ_id
                    from product_template ppt join product_product ppp
                            on ppt.id = ppp.product_tmpl_id
                        join product_uom uom on ppt.uom_id = uom.id
                ) msi
                left join (
                        select stm.warehouse_id, swh.warehouse_name,
                                swh.location_id, swh.location_name,
                                timezone('UTC',stm.date) transact_date,
                                stm.product_id, cst.item_cost ,
                                case when stm.location_dest_id = swh.location_id
                                    then stm.primary_qty
                                    when stm.location_id = swh.location_id
                                    then -stm.primary_qty
                                    else 0 end onhand_qty,
                                round(case when stm.location_dest_id = swh.location_id
                                    then stm.primary_qty
                                    when stm.location_id = swh.location_id
                                    then -stm.primary_qty
                                    else 0 end*stm.actual_cost) onhand_val
                        from stock_move stm 
                            join stock_item_cost_layers cst
                                on stm.product_id = cst.product_id
                                and stm.warehouse_id = cst.warehouse_id
                                   and stm.company_id = 1
                                   and stm.state = 'done'
                            join (
                                select whi.id, whi.name warehouse_name,
                                    stl.id location_id, stl.name location_name
                                from stock_warehouse whi
                                    join stock_location loc on whi.lot_stock_id = loc.id
                                    join stock_location stl on loc.location_id = stl.location_id
                                ) swh on stm.warehouse_id = swh.id 
                                and (stm.location_id = swh.location_id or
                                    stm.location_dest_id = swh.location_id)
                ) onh on msi.product_id = onh.product_id
            group by
                    msi.product_id, 
                    onh.item_cost,
                    msi.product_code, 
                    msi.product_name,
                    msi.uom_id, msi.uom_name, msi.categ_id
        )
        """)
stock_onhand_analys()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
