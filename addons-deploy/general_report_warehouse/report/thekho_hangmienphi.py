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
        self.product_id = False
        self.product_name = False
        self.company_name = False
        self.company_address = False
        self.date_start = False
        self.date_end = False
        self.location_id = False
        self.product_ids = False
        self.qty_fist = 0.0
        self.sum_nhap_qty = 0.0
        self.sum_xuat_qty =0.0
        self.qty_fist = 0.0
        self.get_company(cr, uid)
        
        self.localcontext.update({
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_date_start':self.get_date_start,
            'get_date_end':self.get_date_end,
            'get_current_date':self.get_current_date,
            'get_vietname_date':self.get_vietname_date,
            'get_fist':self.get_fist,
            'get_list_product':self.get_list_product,
            'get_list_date':self.get_list_date,
            'get_xuatkho':self.get_xuatkho,
            'get_total_xuatkho':self.get_total_xuatkho,
            'get_nhapkho':self.get_nhapkho,
            'get_date_nhapkho':self.get_date_nhapkho,
            'get_total_nhapkho':self.get_total_nhapkho,
            'get_tondauky':self.get_tondauky,
            'get_total_qty':self.get_total_qty,
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
    
    def get_total_qty(self,product_id):
        nhap_qty = self.get_total_nhapkho(product_id)
        xuat_qty= self.get_total_xuatkho(product_id)
        nhap_tondau_qty = self.get_tondauky(product_id)
        return nhap_qty + nhap_tondau_qty - xuat_qty
    
    def get_tondauky(self,product_id):
        location_ids = False
        if not self.date_start:
            self.get_header()
        
        if self.location_id:
            location_obj = self.pool.get('stock.location')
            location_ids = location_obj.search(self.cr, self.uid, [('id','child_of',self.location_id)])
            location_ids = (','.join(map(str, location_ids)))
        if location_ids:
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
            '''%(location_ids,location_ids,product_id,self.date_start)
        else:
            sql='''
                SELECT sum(onhand_qty) onhand_qty
                   FROM
                    (
                        SELECT
                            stm.product_id,
                            case when loc2.usage = 'internal' 
                                then stm.primary_qty
                            else
                                case when loc1.usage = 'internal' 
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
            '''%(product_id,self.date_start)
        self.cr.execute(sql)
        previous = self.cr.fetchone()
        self.qty_fist = previous and previous[0] or 0.0
        return self.qty_fist
    
    def get_total_xuatkho(self,product_id):
        location_ids = False
        if not self.date_end:
            self.get_header()
        if self.location_id:
            location_obj = self.pool.get('stock.location')
            location_ids = location_obj.search(self.cr, self.uid, [('id','child_of',self.location_id)])
            location_ids = (','.join(map(str, location_ids)))
        if location_ids:
            sql='''
                SELECT sum(primary_qty) primary_qty
                FROM     stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                            join stock_location loc2 on stm.location_dest_id=loc2.id
                WHERE 
                    date(timezone('UTC',date)) between '%s' and '%s'
                    and product_id = %s
                    and loc1.usage ='internal' and loc2.usage !='internal'    
                    and loc1.id in (%s)      
            '''%(self.date_start,self.date_end,product_id,location_ids)
        else:
            sql='''
                SELECT sum(primary_qty) primary_qty
                FROM     stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                            join stock_location loc2 on stm.location_dest_id=loc2.id
                WHERE 
                    date(timezone('UTC',date)) between '%s' and '%s'
                    and product_id = %s
                    and loc1.usage ='internal' and loc2.usage !='internal'           
            '''%(self.date_start,self.date_end,product_id)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['primary_qty'] or 0.0
        return 0.0
    
    def get_total_nhapkho(self,product_id):
        location_ids = False
        if not self.date_end:
            self.get_header()
        if self.location_id:
            location_obj = self.pool.get('stock.location')
            location_ids = location_obj.search(self.cr, self.uid, [('id','child_of',self.location_id)])
            location_ids = (','.join(map(str, location_ids)))
        if location_ids:
            sql='''
                SELECT sum(primary_qty) primary_qty
                FROM     stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                            join stock_location loc2 on stm.location_dest_id=loc2.id
                WHERE 
                    date(timezone('UTC',date)) between '%s' and '%s'
                    and product_id = %s
                    and loc2.usage ='internal'       
                    and loc2.id in (%s)                     
            '''%(self.date_start,self.date_end,product_id,location_ids)
        else:
            sql='''
                SELECT sum(primary_qty) primary_qty
                FROM     stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                            join stock_location loc2 on stm.location_dest_id=loc2.id
                WHERE 
                    date(timezone('UTC',date)) between '%s' and '%s'
                    and product_id = %s
                    and loc2.usage ='internal'       
            '''%(self.date_start,self.date_end,product_id)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['primary_qty'] or 0.0
        return 0.0
    
    def get_date_nhapkho(self):
        location_ids = False
        if self.location_id:
            location_obj = self.pool.get('stock.location')
            location_ids = location_obj.search(self.cr, self.uid, [('id','child_of',self.location_id)])
            location_ids = (','.join(map(str, location_ids)))
        if location_ids:
            sql='''
                SELECT date(timezone('UTC',date)) date
                FROM     stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                WHERE 
                    date(timezone('UTC',date)) between '%s' and '%s'
                    and product_id in (%s)
                    and loc2.usage ='internal'
                    and loc2.id in (%s)                   
                GROUP BY date(timezone('UTC',date))
                ORDER BY date(timezone('UTC',date))
            '''%(self.date_start,self.date_end,self.product_ids,location_ids)
        else:
            sql='''
                SELECT date(timezone('UTC',date)) date
                FROM     stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                WHERE 
                    date(timezone('UTC',date)) between '%s' and '%s'
                    and product_id in (%s)
                    and loc2.usage ='internal'
                GROUP BY date(timezone('UTC',date))
                ORDER BY date(timezone('UTC',date))
            '''%(self.date_start,self.date_end,self.product_ids)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
                                    
    def get_nhapkho(self,date,product_id):
        location_ids = False
        res=[]
        if self.location_id:
            location_obj = self.pool.get('stock.location')
            location_ids = location_obj.search(self.cr, self.uid, [('id','child_of',self.location_id)])
            location_ids = (','.join(map(str, location_ids)))
        if location_ids:
            sql='''
                SELECT date(timezone('UTC',date)),sum(primary_qty) primary_qty
                FROM    stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                WHERE 
                    date(timezone('UTC',date)) = '%s'
                    and product_id = %s
                    and loc2.usage ='internal'
                    and loc2.id in (%s)                    
                GROUP BY date(timezone('UTC',date))
                ORDER BY date(timezone('UTC',date))
            '''%(date,product_id,location_ids)
        else:
            sql='''
                SELECT date(timezone('UTC',date)),sum(primary_qty) primary_qty
                FROM    stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                WHERE 
                    date(timezone('UTC',date)) = '%s'
                    and product_id = %s
                    and loc2.usage ='internal'                    
                GROUP BY date(timezone('UTC',date))
                ORDER BY date(timezone('UTC',date))
            '''%(date,product_id)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['primary_qty'] or 0.0
        return res
    
    def get_xuatkho(self,date,product_id):
        location_ids = False
        if self.location_id:
            location_obj = self.pool.get('stock.location')
            location_ids = location_obj.search(self.cr, self.uid, [('id','child_of',self.location_id)])
            location_ids = (','.join(map(str, location_ids)))
        if location_ids:
            sql='''
                SELECT date(timezone('UTC',date)),sum(primary_qty) primary_qty
                FROM     stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                            join stock_location loc2 on stm.location_dest_id=loc2.id
                WHERE 
                    date(timezone('UTC',date)) = '%s'
                    and product_id = %s
                    and loc1.usage ='internal' and loc2.usage !='internal'                    
                    and loc1.id in (%s)
                GROUP BY date(timezone('UTC',date))
                ORDER BY date(timezone('UTC',date))
            '''%(date,product_id,location_ids)
        else:
            sql='''
                SELECT date(timezone('UTC',date)),sum(primary_qty) primary_qty
                FROM     stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                            join stock_location loc2 on stm.location_dest_id=loc2.id
                WHERE 
                    date(timezone('UTC',date)) = '%s'
                    and product_id = %s
                    and loc1.usage ='internal' and loc2.usage !='internal'
                GROUP BY date(timezone('UTC',date))
                ORDER BY date(timezone('UTC',date))
            '''%(date,product_id)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['primary_qty'] or 0.0
        return 0.0
    
    def get_list_product(self):
        self.product_ids =False
        if not self.product_ids:
            self.get_header()
        self.product_ids = (','.join(map(str, self.product_ids)))
        sql ='''
            SELECT name_template ,id
            FROM 
                product_product 
            WHERE id in (%s) 
        '''%(self.product_ids)
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_list_date(self):
        res=[]
        if not self.date_start:
            self.get_header()
        while self.date_start <= self.date_end:
            res.append({
                        'date':self.date_start
                        })
            sql ='''
                select '%s'::date + 1 date
            '''%(self.date_start)
            self.cr.execute(sql)
            for i in self.cr.dictfetchall():
                self.date_start = i['date']
                break;
        return res
                        
    
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
        wizard_data = self.localcontext['data']['form']        
        self.product_ids = wizard_data['product_ids']
        self.date_start = wizard_data['date_start']
        self.date_end = wizard_data['date_end']
        self.location_id = wizard_data['location_id'] and wizard_data['location_id'][0]
        return True
    
    
    def get_fist(self):
        if self.location_id:
            self.get_header()
        if self.location_id:
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
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
