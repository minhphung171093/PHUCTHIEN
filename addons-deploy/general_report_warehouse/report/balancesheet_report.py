# -*- coding: utf-8 -*-
##############################################################################
#
#    HLVSolution, Open Source Management Solution
#
##############################################################################

import time
from report import report_sxw
import pooler
from osv import osv
from tools.translate import _
import random
from datetime import datetime
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class Parser(report_sxw.rml_parse):
        
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        pool = pooler.get_pool(self.cr.dbname)
        self.shop_ids =False
        self.shop_name =False
        self.category_ids = False
        self.category_name = False
        
        self.product_id = False
        self.start_date = False
        self.date_end = False
        self.short_by = False
        self.company_name = False
        self.company_address = False
        self.location_id = False
        self.total_start_val = 0.0
        self.total_nhap_val = 0.0
        self.total_xuat_val = 0.0
        self.total_end_val = 0.0
        self.get_company(cr, uid)
        
        self.localcontext.update({
            'get_company_name':self.get_company_name,
            'get_company_address':self.get_company_address,
            'get_date_start':self.get_date_start,
            'get_date_end':self.get_date_end,
            'get_total_start_val':self.get_total_start_val,
            'get_total_nhap_val':self.get_total_nhap_val,
            'get_total_xuat_val':self.get_total_xuat_val,
            'get_total_end_val':self.get_total_end_val,
            'get_line_by_product':self.get_line_by_product,
            'get_current_date':self.get_current_date,
            'get_warehouse_name':self.get_warehouse_name,
            'get_category_name':self.get_category_name,
            'get_line_category':self.get_line_category,
            'get_line_product_by_categ':self.get_line_product_by_categ,
            'get_uom_name':self.get_uom_name
            
        })
    
    
    def get_current_date(self):
        date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_total_start_val(self):
        return self.total_start_val
    def get_total_nhap_val(self):
        return self.total_nhap_val
    def get_total_xuat_val(self):
        return self.total_xuat_val
    def get_total_end_val(self):
        return self.total_end_val
    
    def get_company(self,cr,uid):
        user_obj = self.pool.get('res.users').browse(cr,uid,uid)
        self.company_name = user_obj and user_obj.company_id and user_obj.company_id.name or ''
        self.company_address = user_obj and user_obj.company_id and user_obj.company_id.street or ''
        self.vat = user_obj and user_obj.company_id and user_obj.company_id.vat or ''
         
    def get_company_name(self):
        return self.company_name
    def get_company_address(self):
        return self.company_address 
    
    def get_date_start(self):
        if not self.start_date:
            self.get_header()
        return self.get_vietname_date(self.start_date)
    
    def get_date_end(self):
        if not self.date_end:
            self.get_header()
        return self.get_vietname_date(self.date_end)
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def get_warehouse_name(self):
        if not self.shop_name:
            self.get_header()
        return self.shop_name 
    
    
    def get_category_name(self):
        return self.category_name 
    
    
    def get_header(self):
        wizard_data = self.localcontext['data']['form']
        self.shop_ids = wizard_data['shop_ids'] 
        shop_obj = self.pool.get('sale.shop').browse(self.cr,self.uid,self.shop_ids)
        self.shop_name = shop_obj and shop_obj[0].name or False
        self.shop_ids = (','.join(map(str, self.shop_ids)))
        self.short_by = wizard_data['short_by'] and wizard_data['short_by'] or False
        self.start_date = wizard_data['date_start']
        self.date_end = wizard_data['date_end']
        self.location_id = wizard_data['location_id'] and wizard_data['location_id'][0] or False
        self.category_ids = wizard_data['categ_ids'] or False
        if self.category_ids:
            #self.category_ids = self.pool.get('product.category').search(self.cr, self.uid, [('id','child_of',self.category_ids)])
            self.category_ids = (','.join(map(str, self.category_ids)))
        return True
    
    def get_line_category(self):
        sql = False
        if self.category_ids:
            sql ='''
                SELECT name,id FROM product_category 
                WHERE id in (%s)
                order by name
            '''%(self.category_ids)
        else:
            sql ='''
                SELECT name,id FROM product_category 
                order by name
            '''
        self.cr.execute(sql)
        return self.cr.dictfetchall()
    
    def get_uom_name(self,name):
        sql='''
            SELECT pu.name 
            FROM product_template pt inner join product_uom pu on pt.uom_id = pu.id
            inner join product_product pp on pp.id = pt.id
            WHERE pp.default_code= '%s'
        ''' %(name)
        self.cr.execute(sql)
        for i in self.cr.dictfetchall():
            return i['name']
        return ''
    
    def get_line_product_by_categ(self,category_id):
        
        if self.location_id:
            sql ='''  
                SELECT pp.default_code, pp.name_template,sum(start_onhand_qty) start_onhand_qty, sum(start_val) start_val, 
                    sum(nhaptk_qty) nhaptk_qty, sum(nhaptk_val) nhaptk_val,
                    sum(xuattk_qty) xuattk_qty, sum(xuattk_val) xuattk_val,    
                    sum(end_onhand_qty) end_onhand_qty,
                    sum(end_val) end_val
                    From
                    (SELECT
                        stm.product_id,stm.product_uom,    
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end start_onhand_qty,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end start_val,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then stm.primary_qty
                        else 0.0 end nhaptk_qty,
                        
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*stm.primary_qty 
                        else 0.0
                        end xuattk_qty,
                
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else 0.0 end nhaptk_val,
                        
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*(stm.price_unit * stm.product_qty)
                        else 0.0
                        end xuattk_val,        
                         
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end end_onhand_qty,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end end_val            
                    FROM stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                    WHERE stm.state= 'done')foo
                    inner join product_product pp on foo.product_id = pp.id
                    inner join product_uom pu on foo.product_uom = pu.id
                    inner join  (
                            SELECT pt.id from  product_template pt inner join product_category pc on pt.categ_id = pc.id
                                where pc.id in ('%(categ_ids)s')
                    )categ on pp.product_tmpl_id = categ.id
                    WHERE (pp.id in (select product_id  from product_shop_rel where shop_id in('%(shop_ids)s'))
                           or pp.id not in (select product_id  from product_shop_rel))
                    group by pp.default_code,pp.name_template
                    order by pp.default_code,pp.name_template
                
                 '''%({
                  'start_date': self.start_date,
                  'end_date': self.date_end,
                  'shop_ids':self.shop_ids,
                  'categ_ids':category_id
                  }) 
        else:
            sql ='''  
                SELECT pp.default_code, pp.name_template,sum(start_onhand_qty) start_onhand_qty, sum(start_val) start_val, 
                    sum(nhaptk_qty) nhaptk_qty, sum(nhaptk_val) nhaptk_val,
                    sum(xuattk_qty) xuattk_qty, sum(xuattk_val) xuattk_val,    
                    sum(end_onhand_qty) end_onhand_qty,
                    sum(end_val) end_val
                    From
                    (SELECT
                        stm.product_id,stm.product_uom,    
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end start_onhand_qty,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end start_val,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then stm.primary_qty
                        else 0.0 end nhaptk_qty,
                        
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*stm.primary_qty 
                        else 0.0
                        end xuattk_qty,
                
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else 0.0 end nhaptk_val,
                        
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*(stm.price_unit * stm.product_qty)
                        else 0.0
                        end xuattk_val,        
                         
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end end_onhand_qty,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end end_val            
                    FROM stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                    WHERE stm.state= 'done'    )foo
                    inner join product_product pp on foo.product_id = pp.id
                    inner join product_uom pu on foo.product_uom = pu.id
                    inner join  (
                            SELECT pt.id from  product_template pt inner join product_category pc on pt.categ_id = pc.id
                                where pc.id in ('%(categ_ids)s')
                    )categ on pp.product_tmpl_id = categ.id
                    WHERE (pp.id in (select product_id  from product_shop_rel where shop_id in('%(shop_ids)s'))
                           or pp.id not in (select product_id  from product_shop_rel))
                    group by pp.default_code,pp.name_template
                    order by pp.default_code,pp.name_template
                '''%({
                  'start_date': self.start_date,
                  'end_date': self.date_end,
                  'shop_ids':self.shop_ids,
                  'categ_ids':category_id
                  }) 
                
        self.cr.execute(sql)
        res =[]
            
        for i in self.cr.dictfetchall():
            self.total_start_val = self.total_start_val + (i['start_val'] or 0)
            self.total_nhap_val = self.total_nhap_val +(i['nhaptk_val'] or 0.0)
            self.total_xuat_val = self.total_xuat_val +(i['xuattk_val'] or 0.0)
            self.total_end_val = self.total_end_val +(i['end_val'] or 0.0)
            res.append(
                   {
                   'default_code':i['default_code'],
                   'name_template':i['name_template'],
                   'start_onhand_qty':i['start_onhand_qty'],
                   'start_val':i['start_val'] or 0.0,
                   'nhaptk_qty':i['nhaptk_qty'] or 0.0,
                   'nhaptk_val':i['nhaptk_val'] or 0.0,
                   'xuattk_qty':i['xuattk_qty'] or 0.0,
                   'xuattk_val':i['xuattk_val'] or 0.0,
                   'end_onhand_qty':i['end_onhand_qty'] or 0.0,
                   'end_val':i['end_val'] or 0.0
                   })
        return res
    
    def get_line_by_product(self):
        if not self.category_ids:
            if not self.location_id:
                sql ='''  
                SELECT pp.default_code,pp.name_template,sum(start_onhand_qty) start_onhand_qty, sum(start_val) start_val, 
                    sum(nhaptk_qty) nhaptk_qty, sum(nhaptk_val) nhaptk_val,
                    sum(xuattk_qty) xuattk_qty, sum(xuattk_val) xuattk_val,    
                    sum(end_onhand_qty) end_onhand_qty,
                    sum(end_val) end_val
                    From
                    (SELECT
                        stm.product_id,stm.product_uom,    
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end start_onhand_qty,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end start_val,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then stm.primary_qty
                        else 0.0 end nhaptk_qty,
                        
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*stm.primary_qty 
                        else 0.0
                        end xuattk_qty,
                
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else 0.0 end nhaptk_val,
                        
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*(stm.price_unit * stm.product_qty)
                        else 0.0
                        end xuattk_val,        
                         
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end end_onhand_qty,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end end_val            
                    FROM stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                    WHERE stm.state= 'done'    )foo
                    inner join product_product pp on foo.product_id = pp.id
                    inner join product_uom pu on foo.product_uom = pu.id
                    WHERE (pp.id in (select product_id  from product_shop_rel where shop_id in('%(shop_ids)s'))
                           or pp.id not in (select product_id  from product_shop_rel))
                    group by pp.default_code,pp.name_template
                    order by pp.default_code,pp.name_template
                
                '''%({
                  'start_date': self.start_date,
                  'end_date': self.date_end,
                  'shop_ids':self.shop_ids
                  })
               
            else:
                sql ='''  
                SELECT pp.default_code,pp.name_template,sum(start_onhand_qty) start_onhand_qty, sum(start_val) start_val, 
                    sum(nhaptk_qty) nhaptk_qty, sum(nhaptk_val) nhaptk_val,
                    sum(xuattk_qty) xuattk_qty, sum(xuattk_val) xuattk_val,    
                    sum(end_onhand_qty) end_onhand_qty,
                    sum(end_val) end_val
                    From
                    (SELECT  
                        stm.product_id,stm.product_uom,    
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end start_onhand_qty,
                        
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end start_val,
                        
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then stm.primary_qty
                        else 0.0 end nhaptk_qty,
                        
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*stm.primary_qty 
                        else 0.0
                        end xuattk_qty,
                
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else 0.0 end nhaptk_val,
                        
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*(stm.price_unit * stm.product_qty)
                        else 0.0
                        end xuattk_val,        
                         
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end end_onhand_qty,
                        
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end end_val            
                    FROM stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                    WHERE stm.state= 'done'    )foo
                    inner join product_product pp on foo.product_id = pp.id
                    inner join product_uom pu on foo.product_uom = pu.id
                    WHERE (pp.id in (select product_id  from product_shop_rel where shop_id in('%(shop_ids)s'))
                           or pp.id not in (select product_id  from product_shop_rel))
                    group by pp.default_code,pp.name_template
                    order by pp.default_code,pp.name_template
                '''%({
                  'start_date': self.start_date,
                  'end_date': self.date_end,
                  'shop_ids':self.shop_ids,
                  'location_id':self.location_id
                  })
        else:
            if not self.location_id:
                sql ='''  
                SELECT pp.default_code,pp.name_template,sum(start_onhand_qty) start_onhand_qty, sum(start_val) start_val, 
                    sum(nhaptk_qty) nhaptk_qty, sum(nhaptk_val) nhaptk_val,
                    sum(xuattk_qty) xuattk_qty, sum(xuattk_val) xuattk_val,    
                    sum(end_onhand_qty) end_onhand_qty,
                    sum(end_val) end_val
                    From
                    (SELECT
                        stm.product_id,stm.product_uom,    
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end start_onhand_qty,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end start_val,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then stm.primary_qty
                        else 0.0 end nhaptk_qty,
                        
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*stm.primary_qty 
                        else 0.0
                        end xuattk_qty,
                
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else 0.0 end nhaptk_val,
                        
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*(stm.price_unit * stm.product_qty)
                        else 0.0
                        end xuattk_val,        
                         
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end end_onhand_qty,
                        
                        case when loc1.usage != 'internal' and loc2.usage = 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.usage = 'internal' and loc2.usage != 'internal' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end end_val            
                    FROM stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                    WHERE stm.state= 'done'    )foo
                    inner join product_product pp on foo.product_id = pp.id
                    inner join product_uom pu on foo.product_uom = pu.id
                    WHERE (pp.id in (select product_id  from product_shop_rel where shop_id in('%(shop_ids)s'))
                           or pp.id not in (select product_id  from product_shop_rel))
                    group by pp.default_code,pp.name_template
                    order by pp.default_code,pp.name_template
                
                '''%({
                  'start_date': self.start_date,
                  'end_date': self.date_end,
                  'shop_ids':self.shop_ids
                  })
            else:
                sql ='''  
                SELECT pp.default_code,pp.name_template,sum(start_onhand_qty) start_onhand_qty, sum(start_val) start_val, 
                    sum(nhaptk_qty) nhaptk_qty, sum(nhaptk_val) nhaptk_val,
                    sum(xuattk_qty) xuattk_qty, sum(xuattk_val) xuattk_val,    
                    sum(end_onhand_qty) end_onhand_qty,
                    sum(end_val) end_val
                    From
                    (SELECT  lcation_id
                        stm.product_id,stm.product_uom,    
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(lcalocation_idtion_id)s' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end start_onhand_qty,
                        
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) < '%(start_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end start_val,
                        
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then stm.primary_qty
                        else 0.0 end nhaptk_qty,
                        
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*stm.primary_qty 
                        else 0.0
                        end xuattk_qty,
                
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else 0.0 end nhaptk_val,
                        
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) between '%(start_date)s' and '%(end_date)s'
                        then 1*(stm.price_unit * stm.product_qty)
                        else 0.0
                        end xuattk_val,        
                         
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then stm.primary_qty
                        else
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*stm.primary_qty 
                        else 0.0 end
                        end end_onhand_qty,
                        
                        case when loc1.id != '%(location_id)s' and loc2.id = '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then (stm.price_unit * stm.product_qty)
                        else
                        case when loc1.id = '%(location_id)s' and loc2.id != '%(location_id)s' and date(timezone('UTC',stm.date::timestamp)) <= '%(end_date)s'
                        then -1*(stm.price_unit * stm.product_qty)
                        else 0.0 end
                        end end_val            
                    FROM stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                        join stock_location loc2 on stm.location_dest_id=loc2.id
                    WHERE stm.state= 'done'
                        and stm.location_id = %s or stm.location_dest_id = %s)foo
                    inner join product_product pp on foo.product_id = pp.id
                    inner join product_uom pu on foo.product_uom = pu.id
                    inner join  (
                            SELECT pt.id from  product_template pt inner join product_category pc on pt.categ_id = pc.id
                                where pc.id in '%(categ_id)s'
                    )categ on pp.product_tmpl_id = categ.id
                    WHERE (pp.id in (select product_id  from product_shop_rel where shop_id in(%s))
                           or pp.id not in (select product_id  from product_shop_rel))
                    group by pp.default_code,pp.name_template
                    order by pp.default_code,pp.name_template
                
                 '''%({
                      'start_date': self.start_date,
                      'end_date': self.date_end,
                      'shop_ids':self.shop_ids,
                      'categ_id':self.category_ids,
                      'location_id':self.location_id
                  })
            
        self.cr.execute(sql)
        res =[]
        for i in self.cr.dictfetchall():
            self.total_start_val = self.total_start_val + (i['start_val'] or 0)
            self.total_nhap_val = self.total_nhap_val +(i['nhaptk_val'] or 0.0)
            self.total_xuat_val = self.total_xuat_val +(i['xuattk_val'] or 0.0)
            self.total_end_val = self.total_end_val +(i['end_val'] or 0.0)
            res.append(
                   {
                   'default_code':i['default_code'], 
                   'name_template':i['name_template'],
                   'start_onhand_qty':i['start_onhand_qty'],
                   'start_val':i['start_val'] or 0.0,
                   'nhaptk_qty':i['nhaptk_qty'] or 0.0,
                   'nhaptk_val':i['nhaptk_val'] or 0.0,
                   'xuattk_qty':i['xuattk_qty'] or 0.0,
                   'xuattk_val':i['xuattk_val'] or 0.0,
                   'end_onhand_qty':i['end_onhand_qty'] or 0.0,
                   'end_val':i['end_val'] or 0.0
                   })
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
