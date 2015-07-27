# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

from openerp.osv import fields, osv, orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class average_cost_history(osv.osv):
    _name = "average.cost.history"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _columns = {
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        #'journal_id': fields.many2one('account.journal', 'Account Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'detail_history_ids': fields.one2many('average.cost.detail.history', 'cost_history_id', 'Detail History', readonly=True),
        'move_id': fields.many2one('account.move', 'Account Move'),
        'company_id': fields.related('period_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
        
        'state': fields.selection([
            ('draft','Draft'),
            ('done','Done'),
            ('cancel','Cancelled'),
            ],'Status', select=True, readonly=True, track_visibility='onchange'),
    }
    
    _defaults = {
         'state':'draft',
    }
    
    _sql_constraints = [
        ('name_uniq', 'unique(period_id, company_id)', 'Order Reference must be unique per Company!'),
    ]
    _order = 'period_id desc'
    
    def compute_cost(self,cr,uid,ids,context=None):
        his_pool = self.pool.get('average.cost.detail.history')
        sql = False
        for cost_history_obj in self.browse(cr, uid, ids):
            exist_product_ids = [x.product_id.id for x in cost_history_obj.detail_history_ids]
            his_ids = [x.id for x in cost_history_obj.detail_history_ids]
            if exist_product_ids:
                sql ='''
                    SELECT distinct product_id
                    FROM stock_move sm inner join stock_picking sp on sm.picking_id = sp.id
                    WHERE 
                        date(timezone('UTC',sm.date)) between '%s' and '%s'
                        and sm.state ='done'
                        and product_id not in (%s)
                '''%(cost_history_obj.period_id.date_start,cost_history_obj.period_id.date_stop,','.join(map(str, exist_product_ids)))
            else:
                sql ='''
                    SELECT distinct product_id
                    FROM stock_move sm inner join stock_picking sp on sm.picking_id = sp.id
                    WHERE 
                        date(timezone('UTC',sm.date)) between '%s' and '%s'
                        and sm.state ='done'
                '''%(cost_history_obj.period_id.date_start,cost_history_obj.period_id.date_stop)
            cr.execute(sql)
            for line in cr.dictfetchall():
                vals ={
                       'cost_history_id':ids and ids[0],
                       'product_id':line['product_id'],
                       }
                his_ids.append(self.pool.get('average.cost.detail.history').create(cr,uid,vals))
                
            his_pool.compute_cost(cr, uid, his_ids)
        return True
    
    #Thanh: Generate or update Stock Journal Entry for Stock valuation and COGS
    def post(self, cr, uid, ids, context=None):
        context = context or {}
        his_pool = self.pool.get('average.cost.detail.history')
        move_obj = self.pool.get('stock.move')
        cost_history = self.browse(cr,uid,ids[0])
        his_ids = [x.id for x in cost_history.detail_history_ids]
        his_pool.post(cr,uid,his_ids)
        self.write(cr,uid,ids,{'state':'done'})
        return True
    
average_cost_history()

class average_cost_detail_history(osv.osv):
    _name = "average.cost.detail.history"
    
    def post(self, cr, uid, ids,  context=None):
        context = context or {}
        move_obj = self.pool.get('stock.move')
        for detail_history in self.browse(cr,uid,ids):
            for move in detail_history.move_ids:
                if move.stock_journal_id and move.stock_journal_id and move.stock_journal_id.source_type !='in':
                    move_obj._create_product_valuation_moves(cr, uid, move, context=context)
#             if move.stock_journal_id and move.stock_journal_id and move.stock_journal_id.source_type =='phys_adj':
#                 context.update({'internal':'internal'})
        return True
    
    def compute_cost(self, cr, uid, ids, context=None):
        for history in self.browse(cr, uid, ids, context=context):
            history_ids = []
            start_date = history.cost_history_id.period_id and history.cost_history_id.period_id.date_start or False
            end_date = history.cost_history_id.period_id and history.cost_history_id.period_id.date_stop or False
            avera_cost = 0
            avera_qty = 0
            qty_previous = 0.0
            previous_value = 0.0
            if history.product_id:
                #Tinh Previous Cost => Lay ky truoc, ko co thi lay standard price
                previous_cost = history.previous_cost or history.product_id.standard_price
                #tính tồn kho kỳ trước
                sql ='''
                   SELECT sum(onhand_qty) onhand_qty, sum(val) val
                   FROM
                    (
                        SELECT
                            stm.product_id,
                            case when loc1.usage != 'internal' and loc2.usage = 'internal'
                                then stm.primary_qty
                            else
                                case when loc1.usage = 'internal' and loc2.usage != 'internal'
                                    then -1*stm.primary_qty 
                                else 0.0 end
                            end onhand_qty,
                            case when loc1.usage != 'internal' and loc2.usage = 'internal'
                                then (stm.price_unit * stm.product_qty)
                            else
                                case when loc1.usage = 'internal' and loc2.usage != 'internal'
                                    then -1*(stm.price_unit * stm.product_qty)
                                else 0.0 end
                            end val
                        FROM stock_move stm 
                            join stock_location loc1 on stm.location_id=loc1.id
                            join stock_location loc2 on stm.location_dest_id=loc2.id
                        WHERE stm.state= 'done'
                        and date(timezone('UTC',stm.date)) < '%s'
                        and stm.product_id = %s
                    ) foo
                    GROUP BY foo.product_id
                '''%(start_date ,history.product_id.id)
                cr.execute(sql)
                previous = cr.fetchone()
                qty_previous = previous and previous[0] or 0.0
                previous_value = previous and previous[1] or 0.0
                
                qty_first = qty_previous
                value_first = previous_value
                
                if history.product_id.valuation=='real_time':
                    sql='''
                        SELECT sm.id,(primary_qty * price_unit) as total,primary_qty,sm.type,price_unit,sp.return return
                        FROM
                            stock_move sm inner join stock_picking sp on sp.id = sm.picking_id
                        WHERE 
                            product_id = %s
                            and date(timezone('UTC',sp.date_done)) between '%s' and '%s'
                            and sm.state = 'done'
                        Order by sp.date_done,id
                    '''%(history.product_id.id , start_date ,end_date )
                    cr.execute(sql)
                    res = cr.dictfetchall()
                    
                    current_qty = qty_first
                    current_value = value_first
                    for line in res:
                        if line['type']=='in':
                            if line['return']=='none':
                                current_qty += line['primary_qty']
                                current_value += line['total']
                            else:
                                sql ='''
                                     UPDATE stock_move
                                     SET price_unit = (select m.price_unit 
                                                     from stock_move m join stock_move_history_ids mh on m.id=mh.child_id 
                                                     where mh.parent_id=%s limit 1)
                                     WHERE id = %s    
                                '''%(line['id'],line['id'])
                                cr.execute(sql)
                                current_qty -= line['primary_qty']
                                cr.execute('''
                                SELECT primary_qty * price_unit
                                FROM stock_move
                                WHERE id=%s
                                '''%(line['id']))
                                value = cr.fetchone()
                                current_value -= value and value[0] or 0.0
                                
                        if line['type'] in ['internal','out']:
                            average_cost = current_qty and round(current_value / current_qty,2) or 0.0
                            if line['type'] == 'out':
                                sql ='''
                                    UPDATE 
                                        stock_move 
                                        SET price_unit = %s
                                    WHERE
                                        id = %s
                                '''%(average_cost,line['id'])
                                cr.execute(sql)
                            else:
                                sql ='''
                                    UPDATE 
                                        stock_move 
                                        SET price_unit = %s
                                    WHERE
                                        id = %s and ini_flag=False
                                '''%(average_cost,line['id'])
                                cr.execute(sql)
                                
                                sql ='''
                                    UPDATE 
                                        stock_inventory_line 
                                    SET freeze_cost = %s
                                    WHERE
                                        move_id = %s
                                '''%(average_cost,line['id'])
                                cr.execute(sql)
                                
                            current_qty -= line['primary_qty']
                            current_value = (current_qty * average_cost)
                                
                            
                    avera_qty = current_qty
                    avera_cost = current_qty and round(current_value / current_qty,2) or 0.0
                else:
                    #SUM QTY Nhap va SUM VALUE Nhap
                    sql ='''
                        SELECT sum(primary_qty) qty, sum(price_unit * primary_qty) total
                            FROM
                                stock_move stm 
                            WHERE 
                                product_id = %s
                                and date(timezone('UTC',date)) between '%s' and '%s'
                                and state = 'done'
                                and (stm.type='in' or stm.ini_flag=True) 
                    '''%(history.product_id.id , start_date ,end_date)
                    cr.execute(sql)
                    nhap_res = cr.fetchone()
                    nhap_qty = nhap_res and nhap_res[0] or 0
                    nhap_value = nhap_res and nhap_res[1] or 0
                    peridical_cost = (nhap_qty + qty_previous) and (nhap_value + previous_value)/(nhap_qty + qty_previous) or 0.0
                    
                    if not peridical_cost:
                        peridical_cost = qty_previous and previous_value/qty_previous or 0.0
                        
                    #Tinh Periodical
                    sql = '''
                            UPDATE 
                                stock_move
                            SET price_unit = %s
                            WHERE id in (SELECT stm.id
                                        FROM
                                            stock_move stm
                                        WHERE 
                                            product_id = %s
                                            and date(timezone('UTC',stm.date)) between '%s' and '%s'
                                            and stm.state = 'done'
                                            and stm.type!='in' and stm.ini_flag=False)
                    '''%(peridical_cost, history.product_id.id, start_date, end_date)
                    cr.execute(sql)
                    
                    sql ='''
                        UPDATE 
                            stock_inventory_line 
                        SET freeze_cost = %s
                        WHERE
                            move_id in (SELECT stm.id
                                        FROM
                                            stock_move stm
                                        WHERE 
                                            product_id = %s
                                            and date(timezone('UTC',stm.date)) between '%s' and '%s'
                                            and stm.state = 'done'
                                            and stm.type!='in' and stm.ini_flag=False) 
                    '''%(peridical_cost, history.product_id.id, start_date, end_date)
                    cr.execute(sql)
                                
                    #SUM QTY and VALUE trong ky
                    sql ='''
                       SELECT sum(onhand_qty) onhand_qty --, sum(val) val
                       FROM
                        (
                            SELECT
                                stm.product_id,
                                case when loc1.usage != 'internal' and loc2.usage = 'internal'
                                    then stm.primary_qty
                                else
                                    case when loc1.usage = 'internal' and loc2.usage != 'internal'
                                        then -1*stm.primary_qty 
                                    else 0.0 end
                                end onhand_qty
                                --,
                                --case when loc1.usage != 'internal' and loc2.usage = 'internal'
                                --    then (stm.price_unit * stm.product_qty)
                                --else
                                --    case when loc1.usage = 'internal' and loc2.usage != 'internal'
                                --        then -1*(stm.price_unit * stm.product_qty)
                                --    else 0.0 end
                                --end val
                            FROM stock_move stm 
                                join stock_location loc1 on stm.location_id=loc1.id
                                join stock_location loc2 on stm.location_dest_id=loc2.id
                            WHERE stm.state= 'done'
                            and date(timezone('UTC',stm.date)) between '%s' and '%s'
                            and stm.product_id = %s
                        ) foo
                        GROUP BY foo.product_id
                    '''%(start_date ,end_date, history.product_id.id)
                    cr.execute(sql)
                    current = cr.fetchone()
                    current_qty = current and current[0] or 0.0
#                     current_value = current and current[1] or 0.0
                    
                    avera_qty = qty_previous + current_qty
#                     avera_cost = avera_qty and (previous_value + current_value)/avera_qty or 0.0
                    avera_cost = peridical_cost
                    
                #update lai product standard_price
                sql='''
                    UPDATE product_template SET standard_price = %s
                        WHERE id = (select pt.id from product_product pp inner join product_template pt on
                                        pt.id = pp.product_tmpl_id and pp.id = %s)
                '''%(avera_cost,history.product_id.id)  
                cr.execute(sql)
                
                sql='''
                    SELECT id
                    FROM
                        stock_move
                    WHERE 
                        product_id = %s
                        and date(timezone('UTC',date)) between '%s' and '%s'
                        and state = 'done'
                    Order by date,id
                '''%(history.product_id.id , start_date ,end_date )
                cr.execute(sql)
                history_ids = [x[0] for x in cr.fetchall()]
                var ={
                        'move_ids':[(6, 0, history_ids)],#
                        'previous_cost': qty_previous and previous_value/qty_previous or 0.0,
                        'qty_previous':qty_previous or 0.0,
                        'this_cost':avera_cost or 0,
                        'qty_onhand':avera_qty or 0,
                        'previous_value': previous_value or 0.0,
                        'this_value': avera_cost * avera_qty,
                      }
                self.write(cr,uid,history.id,var)
                
                if len(history_ids):
                    cr.execute('''
                    UPDATE stock_move
                    SET costed=True
                    WHERE id in (%s)
                    '''%(','.join(map(str, history_ids))))
                
        return True 
    
    _columns = {
        'cost_history_id':fields.many2one('average.cost.history', 'Cost History'),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'product_uom_id': fields.related('product_id','uom_id', type="many2one", relation="product.uom", string="UoM", store=True, readonly=True),
        'previous_cost': fields.float('Previous Cost', readonly=True, digits_compute= dp.get_precision('Product Price')),
        'this_cost': fields.float('This Cost', readonly=True, digits_compute= dp.get_precision('Product Price')),
        'this_value': fields.float('This Value', readonly=True, digits_compute= dp.get_precision('Product Price')),
        'qty_previous':fields.float('Previous Onhand Qty', readonly=True, digits_compute= dp.get_precision('Product Unit of Measure')),
        'qty_onhand':fields.float('This Onhand Qty', readonly=True, digits_compute= dp.get_precision('Product Unit of Measure'),),
        'move_ids':fields.many2many('stock.move','stock_move_cost_ref', 'detail_history_id', 'move_id','Move',readonly=True),
        'previous_value': fields.float('Previous Value', readonly=True, digits_compute= dp.get_precision('Product Price')),
    }
    _defaults = {
    }
    
average_cost_detail_history()

class stock_move(osv.osv):
    _inherit = 'stock.move'
    _columns = {
        'type': fields.related('picking_id','type', type="char", string="Type", store=True, readonly=True),
        'move_line_id': fields.many2one('account.move.line', 'Move line'),
        'costed':fields.boolean('Costed'),
    }
stock_move()    

class production_cost_history(osv.osv):
    _name = "production.cost.history"
    _columns = {
        'period_id': fields.many2one('account.period', 'Period', required=True),
        #'journal_id': fields.many2one('account.journal', 'Account Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'finished_good_ds': fields.one2many('product.finished', 'production_id', 'Product Finished', readonly=True),
        'materials_good_ds': fields.one2many('product.materials', 'production_id', 'Product Materials', readonly=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('done','Done'),
            ('cancel','Cancelled'),
            ],'Status', select=True, readonly=True, track_visibility='onchange'),
    }
    _defaults = {
        'state':'draft'
    }
    
    def compute_cost(self,cr,uid,ids,context=None):
        product_ids=[]
        bom_obj = self.pool.get('mrp.bom')
        for production_obj in self.browse(cr, uid, ids):
            
            sql ='''
                DELETE FROM product_finished  where production_id = %s
            '''%(ids[0])
            cr.execute(sql)
            sql='''
                DELETE FROM product_materials  where production_id = %s
            '''%(ids[0])
            sql='''
                DELETE FROM product_materials_finished where finished_id is null
            '''
            cr.execute(sql)
            date_start = production_obj.period_id.date_start
            date_stop  = production_obj.period_id.date_stop
            sql ='''
                select product_id from mrp_bom mb where bom_id is null
            '''
            cr.execute(sql)
            for line in cr.dictfetchall():
                product_ids.append(line['product_id'])
            if not product_ids:
                raise osv.except_osv(_('Error!'), _('Please define Mrp Bom'))
                
            sql ='''
                SELECT product_id,uos_id,sum(quantity)  sum_qty
                FROM account_invoice_line ail 
                    INNER JOIN account_invoice ai on ail.invoice_id = ai.id
                WHERE product_id in (%s)
                    AND ai.date_invoice between '%s' and '%s'
                GROUP BY product_id,uos_id
                ORDER BY product_id
            '''%(','.join(map(str, product_ids)),date_start,date_stop)
            cr.execute(sql)
            for line in cr.dictfetchall():
                vals ={
                           'product_id':line['product_id'],
                           'product_uom':line['uos_id'],
                           'price_unit':0,
                           'product_qty':line['sum_qty'],
                           'production_id':ids[0]
                           }
                new_id =self.pool.get('product.finished').create(cr,uid,vals)
                bom_ids = bom_obj.search(cr,uid,[('product_id','=',line['product_id']),('bom_id','=',False)])
                for i in bom_obj.browse(cr,uid,bom_ids):
                    # add Nguyen vat lieu tinh duoc
                    for i_line in i.bom_lines:
                        val ={
                               'product_id':i_line.product_id and i_line.product_id.id or False,
                               'product_uom':i_line.product_uom and i_line.product_uom.id or False,
                               'product_qty':i_line.product_qty * line['sum_qty'],
                               'finished_id':new_id
                              }
                    self.pool.get('product.materials.finished').create(cr,uid,val)
            
            # Add materials
            sql='''
                SELECT x.product_id,x.product_uom,sum(x.primary_qty)  sum_qty
                FROM
                (
                    SELECT product_id,product_uom,primary_qty
                    FROM stock_move stm 
                        join stock_location loc1 on stm.location_dest_id=loc1.id
                    WHERE
                        loc1.usage = 'production'
                        and date between '%s' and '%s'
                    Union all
                    
                    SELECT product_id,product_uom,primary_qty *-1
                    FROM stock_move stm 
                        join stock_location loc1 on stm.location_id=loc1.id
                    WHERE
                        loc1.usage = 'production'
                        and date between '%s' and '%s'
                )x
                GROUP BY x.product_id,x.product_uom
            '''%(date_start,date_stop,date_start,date_stop)
            cr.execute(sql)
            for line in cr.dictfetchall():
                vals ={
                           'product_id':line['product_id'],
                           'product_uom':line['product_uom'],
                           'price_unit':0,
                           'product_qty':line['sum_qty'],
                           'production_id':ids[0]
                           }
                self.pool.get('product.materials').create(cr,uid,vals)
        return 1
    
production_cost_history()

class product_finished(osv.osv):
    _name = "product.finished"
    _columns = {
        'product_id':fields.many2one('product.product','Product'),
        'product_uom':fields.many2one('product.uom','Product Uom'),
        'price_unit':fields.float('Price Unit'),
        'product_qty':fields.float('Product Qty'),
        'production_id':fields.many2one('production.cost.history', 'Production Cost History'),
        'materials_finished_ids': fields.one2many('product.materials.finished', 'finished_id', 'Product Materials', readonly=True),
        }
    _defaults = {
    } 
product_finished()

class product_materials_finished(osv.osv):
    _name = "product.materials.finished"
    _columns = {
        'product_id':fields.many2one('product.product','Product'),
        'product_uom':fields.many2one('product.uom','Product Uom'),
        'price_unit':fields.float('Price Unit'),
        'product_qty':fields.float('Product Qty'),
        'finished_id':fields.many2one('product.finished', 'Product Finished'),
        }
    _defaults = {
    } 
product_materials_finished()

class product_materials(osv.osv):
    _name = "product.materials"
    _columns = {
        'product_id':fields.many2one('product.product','Product'),
        'product_uom':fields.many2one('product.uom','Product Uom'),
        'price_unit':fields.float('Price Unit'),
        'product_qty':fields.float('Product Qty'),
        'production_id':fields.many2one('production.cost.history', 'Production Cost History'),
        }
    _defaults = {
    }
product_materials()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
