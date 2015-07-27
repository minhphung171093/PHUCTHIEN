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

class stock_details_analysis(osv.osv):
    _name = "stock.details.analysis"
    _description = "Stock Details Analysis"
    _auto = False
    _columns = {
                'warehouse_id':fields.many2one('stock.warehouse','Warehouse',select=True,readonly=True),
                'stock_journal_id':fields.many2one('stock.journal','Journal', select=True,readonly=True),
                'shipping_type':fields.selection([('out', 'Sending Goods',), 
                                  ('in', 'Getting Goods'), 
                                  ('internal', 'Internal'),
                                  ('phys_adj', 'Physical Adjustment'),
                                  ('stransfer', 'Subinventory Transfer'),
                                  ('wtransfer', 'Warehouse Transfer')], 'Shipping', select=True,readonly=True),
                
                'source_type':fields.char('Source Type', size=100, readonly=True),
                'partner_id':fields.many2one('res.partner','Partner', select=True,readonly=True),
                'address_id':fields.many2one('res.partner.address','Address', select=True,readonly=True),
                'transact_date':fields.date('Trans Date'),
                'transact_no':fields.char('Trans No', size=100, readonly=True),
                'origin':fields.char('Origin', size=100, readonly=True),
                'location_id':fields.many2one('stock.location','Location',select=True,readonly=True),
                'product_id':fields.many2one('product.product','Product',select=True,readonly=True),
                'uom_id':fields.many2one('product.uom','uom',select=True,readonly=True),
                'categ_id':fields.many2one('product.category','Category',select=True,readonly=True),
                'receipt_qty':fields.float('Receipt Qty',digits=(16,3)),
                'issue_qty':fields.float('Issue Qty',digits=(16,3)),
                'trans_cost': fields.float('Trans Cost',digits=(16,2)),
                'year': fields.char('Year', size=4, readonly=True),
                'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                    ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
                    ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
                'day': fields.char('Day', size=128, readonly=True),
            }
    def init(self, cr):
       tools.sql.drop_view_if_exists(cr, 'stock_details_analysis')
       cr.execute("""
            create or replace view stock_details_analysis as 
            (
                SELECT
                    row_number() over(order by transact_date,
                    txn.shipping_type, txn.product_code) id,
                    txn.warehouse_id, txn.stock_journal_id,
                    txn.shipping_type,
                    coalesce(ssa.name, sst.name) source_type,
                    txn.partner_id, txn.address_id,
                    date(txn.transact_date) transact_date,
                    to_char(txn.transact_date,'YYYY') "year",
                    to_char(txn.transact_date,'MM') "month",
                    to_char(txn.transact_date,'DD') "day",
                    txn.transact_no, txn.origin,
                    txn.location_id, txn.product_id,
                    txn.product_code, txn.product_name,
                    txn.uom_id, txn.uom_name, txn.categ_id,
                    coalesce(txn.actual_cost, 0) trans_cost,
                    coalesce(txn.receipt_qty, 0) receipt_qty,
                    coalesce(txn.issue_qty, 0) issue_qty
                FROM (
                        SELECT stm.warehouse_id, swh.warehouse_name,
                            swh.location_id, swh.location_name,
                            coalesce(stm.stock_journal_id,stp.stock_journal_id) stock_journal_id,
                            coalesce(stm.type, stp.type) shipping_type,
                            stm.source_type_id,
                            coalesce(stm.source_account_id,stp.source_id) source_id,
                            coalesce(stp.origin, sih.name) origin,
                            coalesce(stp.name, sih.name) transact_no,
                            timezone('ICT',stm.date at time zone 'UTC') transact_date,
                            stm.partner_id, stm.address_id,
                            stm.product_id, ppt.name product_name,
                            ppp.default_code product_code, ppt.uom_id,
                            uom.name uom_name, ppt.categ_id, stm.actual_cost,
                            case when stm.location_dest_id = swh.location_id
                                then stm.primary_qty
                                else 0 end receipt_qty,
                            case when stm.location_id = swh.location_id
                                then stm.primary_qty
                                else 0 end issue_qty
                        FROM stock_move stm join product_product ppp
                                on stm.product_id = ppp.id
                                and stm.state = 'done' and stm.company_id =1
                            join product_template ppt
                                on ppt.id = ppp.product_tmpl_id
                            join product_uom uom on ppt.uom_id = uom.id
                            join (
                                select whi.id, whi.name warehouse_name,
                                    stl.id location_id, stl.name location_name
                                from stock_warehouse whi
                                    join stock_location loc on whi.lot_stock_id = loc.id
                                    join stock_location stl on loc.location_id = stl.location_id
                                ) swh on stm.warehouse_id = swh.id and
                                    (stm.location_id = swh.location_id or 
                                    stm.location_dest_id = swh.location_id)            
                            left join stock_picking stp on stm.picking_id = stp.id
                            left join stock_inventory_move_rel rel on stm.id = rel.move_id
                            left join stock_inventory sih on rel.inventory_id = sih.id
                    ) txn
                    left join stock_journal stj on txn.stock_journal_id = stj.id
                    left join stock_source_type sst on txn.source_type_id = sst.id
                    left join stock_source_account ssa on txn.source_id = ssa.id
                            )
        """)
stock_details_analysis()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
