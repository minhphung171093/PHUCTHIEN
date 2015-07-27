# # -*- coding: utf-8 -*-
##############################################################################
#

#
##############################################################################

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import httplib

class purchase_order_rule(osv.osv):
    _name = "purchase.order.rule"
    
    _columns = {
        'name': fields.many2one('product.product','Product', required=True),
        'partner_id': fields.many2one('res.partner','Supplier'),
        'from_date': fields.date('From Date', required=True),
        'to_date': fields.date('To Date', required=True),
        'uom_id': fields.many2one('product.uom','Units of Measure'),
        'operator': fields.selection([('>=','>='),('<=','<=')],'Operator', required=True),
        'quantity': fields.float('Quatity', required=True),
        'value': fields.float('Value', required=True),
        'active': fields.boolean('Active'),
        'message': fields.text('Message'),
    }
    
    _defaults = {
        'active': True,
    }
    
    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        product_product = self.pool.get('product.product')
        product = product_product.browse(cr, uid, product_id)
        return {'value':{'uom_id': product.uom_po_id.id},'domain':{'uom_id': [('category_id','=',product.uom_id.category_id.id)]}}
    
purchase_order_rule()

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    
    _columns = {
        'validator' : fields.many2one('res.users', 'Validated by', readonly=True, track_visibility='onchange'),
        'tp_duyet_id': fields.many2one('res.users','Manager Validated',readonly=1, track_visibility='onchange'),
        'gd_duyet_id': fields.many2one('res.users','Boss Validated',readonly=1, track_visibility='onchange',),
                  'purchase_type': fields.selection([
                        ('normal', 'Normal'),
                        ('asset', 'Asset'),
                        ], 'Purchase Type'),
    }
    
    def wkf_confirm_order(self, cr, uid, ids, context=None):
        todo = []
        if context is None:
            context = {}
        po_rule_obj = self.pool.get('purchase.order.rule')
        po_line_obj = self.pool.get('purchase.order.line')
        product_uom_obj = self.pool.get('product.uom')
        for po in self.browse(cr, uid, ids, context=context):
            kiemtra_ngayhethan = True
            if po.partner_id.gpkd and po.partner_id.date_gpkd < po.date_order:
                kiemtra_ngayhethan = False
            if po.partner_id.cchn and po.partner_id.date_cchn < po.date_order:
                kiemtra_ngayhethan = False
            if po.partner_id.gptn and po.partner_id.date_gptn < po.date_order:
                kiemtra_ngayhethan = False
            if po.partner_id.gpp and po.partner_id.date_gpp < po.date_order:
                kiemtra_ngayhethan = False
            if po.partner_id.gdp and po.partner_id.date_gdp < po.date_order:
                kiemtra_ngayhethan = False
            if po.partner_id.gsp and po.partner_id.date_gsp < po.date_order:
                kiemtra_ngayhethan = False  
            if not kiemtra_ngayhethan:
                raise osv.except_osv(_('Cảnh báo!'),_('Kiểm tra lại ngày hết hạn của giấy phép!'))
            if not po.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            
            cd = hasattr(self,'cd') and self.cd or False
            if not cd:
                
                sql = '''
                    select case when count(column_name)=1 then 1 else 0 end check_partner
                       from INFORMATION_SCHEMA.columns
                       where table_name = 'purchase_order_line'
                             and column_name = 'partner_id'
                '''
                cr.execute(sql)
                check_partner = cr.dictfetchone()['check_partner']
                if check_partner:
                    sql = '''
                        select partner_id,product_id,date_planned,sum(product_qty) as product_qty from purchase_order_line where order_id = %s group by partner_id,product_id,date_planned
                    '''%(po.id)
                else:
                    sql = '''
                        select product_id,date_planned,sum(product_qty) as product_qty from purchase_order_line where order_id = %s group by product_id,date_planned
                    '''%(po.id)
                cr.execute(sql)
                product_lines = cr.dictfetchall()
                for product_line in product_lines:
                    
                    if check_partner:
                        sql = '''
                            select product_uom,price_unit, sum(product_qty) as product_qty from purchase_order_line where product_id = %s and %s and order_id=%s group by product_uom,price_unit
                        '''%(product_line['product_id'],product_line['partner_id'] and '''partner_id = %s'''%(product_line['partner_id']) or 'partner_id is null',po.id)
                    else:
                        sql = '''
                            select product_uom,price_unit,sum(product_qty) as product_qty from purchase_order_line where product_id = %s and order_id=%s group by product_uom,price_unit
                        '''%(product_line['product_id'],po.id)
                    cr.execute(sql)
                    uom_lines = cr.dictfetchall()
                    
                    if check_partner:
                        po_rule_ids = po_rule_obj.search(cr, uid, [('from_date','<=',product_line['date_planned']),('to_date','>=',product_line['date_planned']),('partner_id','=',product_line['partner_id'] or False),('name','=',product_line['product_id'])])
                    else:
                        po_rule_ids = po_rule_obj.search(cr, uid, [('from_date','<=',product_line['date_planned']),('to_date','>=',product_line['date_planned']),('name','=',product_line['product_id'])])
                    for po_rule in po_rule_obj.browse(cr, uid, po_rule_ids):
                        uom_qty = 0
                        for uom in uom_lines:
                            uom_qty += product_uom_obj._compute_qty(cr, uid, uom['product_uom'], uom['product_qty'], po_rule.uom_id.id)
                            if po_rule.operator=='>=':
                                if uom_qty < po_rule.quantity:
                                    if po_rule.message:
                                        raise osv.except_osv(_('Warning!'),_(po_rule.message))
                                    else:
                                        raise osv.except_osv(_('Warning!'),_('Không thể duyệt sản phẩm với số lượng bé hơn số lượng tối thiểu: %s!')%(po_rule.quantity))
                                else:
                                    if uom['price_unit'] > po_rule.value:
                                        if po_rule.message:
                                            raise osv.except_osv(_('Warning!'),_(po_rule.message))
                                        else:
                                            raise osv.except_osv(_('Warning!'),_('Không thể duyệt sản phẩm với đơn giá lớn hơn: %s!')%(po_rule.value))
                            if po_rule.operator=='<=':
                                if uom_qty > po_rule.quantity:
                                    if po_rule.message:
                                        raise osv.except_osv(_('Warning!'),_(po_rule.message))
                                    else:
                                        raise osv.except_osv(_('Warning!'),_('Không thể duyệt sản phẩm với số lượng lớn hơn số lượng tối đa: %s!')%(po_rule.quantity))
                                else:
                                    if uom['price_unit'] < po_rule.value:
                                        if po_rule.message:
                                            raise osv.except_osv(_('Warning!'),_(po_rule.message))
                                        else:
                                            raise osv.except_osv(_('Warning!'),_('Không thể duyệt sản phẩm với đơn giá bé hơn: %s!')%(po_rule.value))
            for line in po.order_line:
                if line.state=='draft':
                    todo.append(line.id)

        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid})
        if cd:
            self.cd=False
        return True
    
    def wkf_approve_order(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids):
            if line.purchase_type == 'asset':
                self.write(cr, uid, [line.id], {'state': 'approved', 'date_approve': fields.date.context_today(self,cr,uid,context=context),'gd_duyet_id':uid})
            else:
                self.write(cr, uid, [line.id], {'state': 'approved', 'date_approve': fields.date.context_today(self,cr,uid,context=context),'tp_duyet_id':uid})
        return True
    
    def purchase_approve_level2(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'tp_duyet_id':uid})
    
    def action_cancel_draft(self, cr, uid, ids, context=None):
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state':'draft','shipped':0, 'validator' : False,'tp_duyet_id': False, 'gd_duyet_id': False})
        for purchase in self.browse(cr, uid, ids, context=context):
            self.pool['purchase.order.line'].write(cr, uid, [l.id for l in  purchase.order_line], {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for p_id in ids:
            # Deleting the existing instance of workflow for PO
            wf_service.trg_delete(uid, 'purchase.order', p_id, cr)
            wf_service.trg_create(uid, 'purchase.order', p_id, cr)
        return True
    
purchase_order()

class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = {
                'categ_asset_id':fields.many2one('account.asset.category','Category Asset'),
    }
product_category()

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    
    def create_acount_asset(self,cr,uid,ids,pick,context=None):
        asset = self.pool.get('account.asset.asset')
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        fields_list = ['voucher_number', 'code', 'method_end', 'prorata', 'salvage_value', 'currency_id', 'partner_id', 
                 'method_progress_factor', 'company_id', 'note', 'parent_id', 'state', 'method_period', 'purchase_date', 
                 'history_ids', 'method', 'method_number', 'depreciation_line_ids', 'warehouse_id', 'account_analytic_id', 
                 'method_time', 'value_residual', 'asset_type', 'account_expense_depreciation_id', 'name', 
                 'purchase_value', 'voucher_date', 'account_move_line_ids', 'category_id']
        
        
        for move in pick.move_lines:
            if not move.product_id.categ_id.categ_asset_id:
                raise osv.except_osv(_('No Category Asset Defined!'), _('You must define Category Asset '))
            val = val1 = 0.0
            # lay subtotal
            taxes = tax_obj.compute_all(cr, uid, move.purchase_line_id.taxes_id, move.purchase_line_id.price_unit, move.product_qty, move.purchase_line_id.product_id, move.purchase_line_id.order_id.partner_id)
            cur = move.purchase_line_id.order_id.pricelist_id.currency_id
            val1 = cur_obj.round(cr, uid, cur, taxes['total'])
            
            # lay tax 
            for c in self.pool.get('account.tax').compute_all(cr, uid, move.purchase_line_id.taxes_id, move.purchase_line_id.price_unit, move.product_qty, move.purchase_line_id.product_id, move.purchase_line_id.order_id.partner_id)['taxes']:
                val += c.get('amount', 0.0)
            val=cur_obj.round(cr, uid, cur, val)
            
            asset_context ={
                    'default_name': move.product_id.name or False,
                    'default_purchase_date':pick.date_done or move.date,
                    'default_code':move.product_id.default_code or False,
                    'default_account_expense_depreciation_id':move.product_id.categ_id.property_account_expense_categ.id,
                    'default_asset_type':'prepaid',
                    'default_purchase_value': val+val1,
                    'default_method_number':move.product_id.categ_id.categ_asset_id.method_number,
                    'default_method_period':move.product_id.categ_id.categ_asset_id.method_period,
                    'default_prorata':True,
                    'default_category_id':move.product_id.categ_id.categ_asset_id.id or False
                  }
            vals = asset.default_get(cr, uid, fields_list,context=asset_context)
            asset.create(cr,uid,vals)
            
        return True
        
    def create_invoice(self,cr,uid,ids,context=None):
        
        if context is None:
            context = {}
            
        onshipping = self.pool.get('stock.invoice.onshipping')
        onshipping_line = self.pool.get('stock.invoice.line.onshipping')
        fields_list=  ['invoice_date', 'group', 'journal_id']
        context={
                 'active_ids': ids,
                 'active_model':'stock.picking.in',
                 'active_id':ids[0],
                 }
        
        vals = onshipping.default_get(cr, uid, fields_list,context=context)
        res= {
              'journal_id':vals['journal_id'],
              'multi_invocie':True,
              'invoiced':True}
        new_id = onshipping.create(cr,uid,res,context=context)
        for i in vals['move_ids']:
            res= {
                'product_id' : i['product_id'],
                'quantity': i['quantity'],
                'invoicing_qty': i['invoicing_qty'], 
                'product_uom': i['product_uom'],
                'move_id' : i['move_id'],
                'wizard_id' : new_id,
                'check_invoice':True,
                }
            onshipping_line.create(cr,uid,res)
        
        new_invoice_id = onshipping.create_invoice(cr, uid, [new_id], context=context)
        
        return new_invoice_id
    
    def action_done(self, cr, uid, ids, context=None):
        """Changes picking state to done.
        
        This method is called at the end of the workflow by the activity "done".
        @return: True
        """
        self.write(cr, uid, ids, {'state': 'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')})
        # kiet Create Asset 
        for pick in self.browse(cr,uid,ids):
            
            if pick.purchase_id and pick.purchase_id.purchase_type == 'asset':
                self.create_acount_asset(cr, uid, ids, pick, context)
                self.create_invoice(cr, uid, ids, context)
        
        return True
stock_picking()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
