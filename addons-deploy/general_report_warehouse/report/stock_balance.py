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


def init(self, cr):
       tools.sql.drop_view_if_exists(cr, 'stock_details_analysis')
       sql =
       """
        SELECT
            stm.product_id,
            case when loc1.usage != 'internal' and loc2.usage = 'internal'
                then stm.primary_qty
            else 0.0 
            end nhap_qty,
            case when loc1.usage != 'internal' and loc2.usage = 'internal'
                then (stm.price_unit * stm.product_qty)
             else 0.0 
            end nhap_value,
            case when loc1.usage = 'internal' and loc2.usage != 'internal'
                then stm.primary_qty
            else 0.0 
            end xuat_qty,
            case when loc1.usage = 'internal' and loc2.usage != 'internal'
                then (stm.price_unit * stm.product_qty)
            else 0.0 
            end xuat_value    
            FROM stock_move stm 
            join stock_location loc1 on stm.location_id=loc1.id
            join stock_location loc2 on stm.location_dest_id=loc2.id
            WHERE stm.state= 'done'
        
           
        """
stock_details_analysis()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
