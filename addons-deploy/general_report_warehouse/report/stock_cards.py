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
        self.warehouse_id = False
        self.warehouse_name = False
        self.product_id = False
        self.product_name = False
        self.prod_lot_id = False
        self.company_name = False
        self.company_address = False
        self.date_start = False
        self.date_end = False
        self.location_id = False
        self.qty_fist = 0.0
        self.sum_nhap_qty = 0.0
        self.sum_xuat_qty =0.0
        self.get_company(cr, uid)
        
        self.localcontext.update({
            'get_line':self.get_line,
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_warehouse_name':self.get_warehouse_name,
            'get_product_name':self.get_product_name,
            'get_date_start':self.get_date_start,
            'get_date_end':self.get_date_end,
            'get_uom_base':self.get_uom_base,
            'get_current_date':self.get_current_date,
            'get_vietname_date':self.get_vietname_date,
            'get_fist':self.get_fist,
            'get_sum_rcv':self.get_sum_rcv,
            'get_sum_issue':self.get_sum_issue,
            'get_ton_cuoi':self.get_ton_cuoi,
            'get_hd':self.get_hd,
            'get_solo':self.get_solo,
            'get_date_hd':self.get_date_hd,
            'get_so_hd':self.get_so_hd
            
        })
        
    def get_company(self,cr,uid):
        user_obj = self.pool.get('res.users').browse(cr,uid,uid)
        self.company_name = user_obj and user_obj.company_id and user_obj.company_id.name or ''
        self.company_address = user_obj and user_obj.company_id and user_obj.company_id.street or ''
        self.vat = user_obj and user_obj.company_id and user_obj.company_id.vat or ''
         
    def get_product_name(self):
        if not self.product_name:
            self.get_header()
        return self.product_name
    
    def get_warehouse_name(self):
        if not self.warehouse_name:
            self.get_header()
        return self.warehouse_name
    
    def get_company_name(self):
        return self.company_name
    
    def get_company_address(self):
        return self.company_address
    
    def get_date_start(self):
        if not self.date_start:
            self.get_header()
        return self.get_vietname_date(self.date_start)
    
    def get_date_end(self):
        if not self.date_end:
            self.get_header()
        return self.get_vietname_date(self.date_end)
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_current_date(self):
        date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
        
    def get_header(self):
        
        res ={}
        wizard_data = self.localcontext['data']['form']        
        self.warehouse_id = wizard_data['warehouse_id'] and wizard_data['warehouse_id'][0] or False
        self.warehouse_name = wizard_data['warehouse_id'] and wizard_data['warehouse_id'][1]
        self.product_id = wizard_data['product_id'][0]
        self.product_name = wizard_data['product_id'][1]
        self.prod_lot_id = wizard_data['prod_lot_id'][0]
        self.date_start = wizard_data['date_start']
        self.date_end = wizard_data['date_end']
        self.location_id = wizard_data['location_id'][0]
        return res
    
    def get_uom_base(self):
        if not self.product_id:
            self.get_header()
        sql ='''
            SELECT uom.name
            FROM
                product_product pp inner 
                join product_template pt on pp.product_tmpl_id = pt.id
                join product_uom uom on pt.uom_id = uom.id
                where pp.id = %s
            '''%(self.product_id)
        self.cr.execute(sql)
        
        for item in  self.cr.dictfetchall():
            return item['name']
        return False
    
    def get_solo(self):
        if not self.prod_lot_id:
            self.get_header()
        sql ='''
            SELECT name
            FROM stock_production_lot
                where id = %s
            '''%(self.prod_lot_id)
        self.cr.execute(sql)
        for item in  self.cr.dictfetchall():
            return item['name']
        return False
    
    def get_hd(self):
        if not self.prod_lot_id:
            self.get_header()
        sql ='''
            SELECT life_date
            FROM stock_production_lot
                where id = %s
            '''%(self.prod_lot_id)
        self.cr.execute(sql)
        for item in  self.cr.dictfetchall():
            return item['life_date']
        return False
    
    
    def get_date_hd(self,date):
        if not date:
            date = time.strftime('%Y-%m-%d')
        else:
            date = date[:10]
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%m/%Y')
    
    
    def get_fist(self):
        if self.location_id:
            self.get_header()
        location_obj = self.pool.get('stock.location')
        location_ids = location_obj.search(self.cr, self.uid, [('id','child_of',self.location_id)])
        location_ids = (','.join(map(str, location_ids)))
        
        sql='''
            SELECT sum(onhand_qty) onhand_qty
               FROM
                (
                    SELECT
                        stm.product_id,
                        case when loc2.usage = 'internal' and loc2.id in (%s)
                            then stm.primary_qty
                        else
                            case when loc1.usage = 'internal' and loc1.id in (%s)
                                then -1*stm.primary_qty 
                            else 0.0 end
                        end onhand_qty
                    FROM stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                    WHERE stm.state= 'done'
                    and stm.product_id = %s
                    and date(timezone('UTC',stm.date)) < '%s'
                ) foo
                GROUP BY foo.product_id
        '''%(location_ids ,location_ids,self.product_id,self.date_start)
        self.cr.execute(sql)
        previous = self.cr.fetchone()
        self.qty_fist = previous and previous[0] or 0.0
        return self.qty_fist
    
    def get_so_hd(self, picking_name):
        invoice_ids = self.pool.get('account.invoice').search(self.cr,self.uid,[('name','=',picking_name)])
        if invoice_ids:
            invoice = self.pool.get('account.invoice').browse(self.cr,self.uid,invoice_ids[0])
            so_hd = invoice.number
        else:
            so_hd = ''
        return so_hd
        
    def get_line(self):
        if self.location_id:
            self.get_header()
        location_obj = self.pool.get('stock.location')
        location_ids = location_obj.search(self.cr, self.uid, [('id','child_of',self.location_id),('usage','=','internal')])
        location_ids = (','.join(map(str, location_ids)))
        sql = '''
            SELECT date,name_template,note,journal_name,picking_name,name,nhap_qty,xuat_qty
            FROM
            (
            SELECT
                date(timezone('UTC',stm.date)),pp.name_template,stm.note,x.journal_name,
                case when x.picking_name is not null then x.picking_name else y.name end as picking_name,x.name,
                case when loc2.usage = 'internal' and loc2.id in (%s)
                then stm.primary_qty
                else
                0.0 end nhap_qty,
                case when loc1.usage = 'internal' and loc1.id in (%s)
                then stm.primary_qty 
                else 
                0.0 end xuat_qty
            FROM stock_move stm 
            left join stock_location loc1 on stm.location_id=loc1.id
            left join stock_location loc2 on stm.location_dest_id=loc2.id 
            left join product_product pp on stm.product_id = pp.id   
            left join (select sj.name journal_name,
                 sp.name picking_name,sp.id, rp.name
                  from stock_picking sp 
                  left join stock_journal sj on sp.stock_journal_id = sj.id
                  left join res_partner rp on sp.partner_id = rp.id
                  )x
                  on stm.picking_id = x.id     
            left join (select cknbl.move_source_id,cknb.name
                        from  chuyenkho_noibo_line cknbl 
                        left join chuyenkho_noibo cknb on cknbl.chuyenkho_noibo_id = cknb.id) y on y.move_source_id = stm.id
            WHERE stm.state= 'done'               
                  and stm.product_id = %s
                  and stm.prodlot_id = %s
                  and date(timezone('UTC',stm.date)) between '%s' and '%s'
            order by date(timezone('UTC',stm.date))) x
            where (nhap_qty !=0 or xuat_qty!= 0)
        '''%(location_ids,location_ids,self.product_id,self.prod_lot_id,self.date_start,self.date_end)
        self.cr.execute(sql)
        res =[]
        for i in self.cr.dictfetchall():
            self.qty_fist = self.qty_fist + (i['nhap_qty'] or 0 ) - (i['xuat_qty'] or 0 )
            self.sum_nhap_qty = self.sum_nhap_qty + i['nhap_qty']
            self.sum_xuat_qty = self.sum_xuat_qty + i['xuat_qty']
            res.append(
                   {'date':self.get_vietname_date(i['date']),
                   'des':i['picking_name'],
                   'name':i['name'],
                   'journal_name':i['journal_name'],
                   'nhap_qty':i['nhap_qty'] or 0.0,
                   'xuat_qty':i['xuat_qty'] or 0.0,
                   'ton_qty':self.qty_fist or 0.0,
                   'note':i['note']
                   })
        return res
    
    def get_sum_rcv(self):
        return self.sum_nhap_qty
    def get_sum_issue(self):
        return self.sum_xuat_qty
    
    def get_ton_cuoi(self):
        return self.qty_fist
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
