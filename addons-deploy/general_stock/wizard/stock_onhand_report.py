import time
from report import report_sxw
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
import tools
from osv import fields, osv


class stock_onhand_report(osv.osv):
    _name = "stock.onhand.report"
    _description = "Stock Onhand Report"
    _auto = False
    
    _columns = {
            'location_name':fields.char('Location Name', size =128),
            'product_id':fields.many2one('product.product','Product'),
            'onhand':fields.float('On hand'),
            'uom_id':fields.many2one('product.uom','Product Uom'),
            'warehouse_id':fields.many2one('stock.warehouse','Warehouse')
    }
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'stock_onhand_report')
        cr.execute("""
        create or replace view stock_onhand_report as 
        (
               SELECT ROW_NUMBER() OVER() id,location_name,foo.warehouse_id, foo.product_id, pt.name, sum(onhand_qty) as onhand, uom.id as uom_id
                FROM
                (
                    select stm.product_id,sp.warehouse_id,
                    case when loc2.usage = 'internal'
                        then loc2.name
                        else
                        case when loc1.usage = 'internal'
                            then loc1.name
                        else '' end
                        end location_name,
                    
                    case when loc2.usage = 'internal'
                        then stm.primary_qty
                        else
                        case when loc1.usage = 'internal'
                            then -1*stm.primary_qty 
                        else 0.0 end
                        end onhand_qty,
                    stm.date
                    from stock_move stm 
                    join stock_location loc1 on stm.location_id=loc1.id
                    join stock_location loc2 on stm.location_dest_id=loc2.id
                    join stock_picking sp on sp.id = stm.picking_id
                    where stm.state ='done'
                    
                ) foo
                    join product_product p on foo.product_id = p.id
                    join product_template pt on p.product_tmpl_id=pt.id
                        join product_uom uom on pt.uom_id=uom.id
                GROUP BY foo.warehouse_id, foo.product_id, location_name, pt.name, uom.id
                ORDER bY name
        )
        """)
stock_onhand_report()