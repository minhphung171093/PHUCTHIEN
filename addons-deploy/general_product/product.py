# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

from osv import osv, fields
import decimal_precision as dp
from tools.translate import _
import time
DATE_FORMAT = "%Y-%m-%d"
from openerp import SUPERUSER_ID
import xlrd
from lxml import etree

import os
from openerp import modules
base_path = os.path.dirname(modules.get_module_path('general_product'))

class product_uom(osv.osv):
    _inherit = "product.uom"
    
#     def name_get(self, cursor, user, ids, context=None):
#         if isinstance(ids, (int, long)):
#             ids = [ids]
#         if not ids:
#             return []
#         res = []
#         data_move = self.pool.get('account.move').browse(cursor, user, ids, context=context)
#         for uom in data_move:
#             name = uom.name
#             if uom.category_id.name:
#                 name += "[" + 
#             res.append((move.id, name))
#         return res
    
    def write(self, cr, uid, ids, vals, context=None):
#             if 'category_id' in vals:
#                 for uom in self.browse(cr, uid, ids, context=context):
#                     if uom.category_id.id != vals['category_id']:
#                         raise osv.except_osv(_('Warning!'),_("Cannot change the category of existing Unit of Measure '%s'.") % (uom.name,))
        return super(osv.osv, self).write(cr, uid, ids, vals, context=context)

product_uom()

class product_category(osv.osv):
    _inherit = "product.category"
    _columns = {
        'code': fields.char('Code', size=64),
        
        'property_account_refund_categ': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Refund Account",
            view_load=True,
            help="This account will be used for invoices return to value sales for the current product category"),
        'property_stock_account_loss_categ': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Stock Account Loss",
            view_load=True,
            help="This account will hold the current value of the loss products for the current product category"),
        'property_stock_account_scrap_categ': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Stock Account Scrap",
            view_load=True,
            help="This account will hold the current value of the scrap products for the current product category"),
    }
    
    def copy(self, cr, uid, id, default=None, context=None, done_list=None, local=False):
        default = {} if default is None else default.copy()
        default.update({'code': '/'})
        return super(product_category, self).copy(cr, uid, id, default, context=context)
    
    
    def is_code_uniq(self,cr,uid,ids):
        for i in self.browse(cr,uid,ids):
            if i.code!='/':
                category_ids = self.search(cr, uid, [('code','=',i.code),
                                                  ('id','<>',i.id)])
                if category_ids:
                    return False
        return True
    
    _constraints = [(is_code_uniq, 'Lỗi: Mã phân loại đã tồn tại !!!', [''])]
    
    def onchange_parent_id(self, cr, uid, ids, parent_id):
        value = {'value': {}}
        if parent_id:
            parent_obj = self.browse(cr, uid, parent_id)
            value['value'].update({'property_account_refund_categ': parent_obj.property_account_refund_categ.id or False,
                                   'property_stock_account_loss_categ': parent_obj.property_stock_account_loss_categ.id or False,
                                   'property_stock_account_scrap_categ': parent_obj.property_stock_account_scrap_categ.id or False,
                                   'property_stock_valuation_account_id': parent_obj.property_stock_valuation_account_id.id or False,
                                   'property_account_income_categ': parent_obj.property_account_income_categ.id or False,
                                   'property_account_expense_categ': parent_obj.property_account_expense_categ.id or False,})
        return value
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(product_category,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            
            if context.has_key('search_finished_goods'):
                categ_ids = self.search(cr, uid, [('code','=','TP')])
                for node in doc.xpath("//field[@name='parent_id']"):
                    node.set('domain', "[('parent_id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
                    
                    res['arch'] = etree.tostring(doc)
            
            if context.has_key('search_product'):
                categ_ids = self.search(cr, uid, [('code','=','HB')])
                for node in doc.xpath("//field[@name='parent_id']"):
                    node.set('domain', "[('parent_id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
                    
                    res['arch'] = etree.tostring(doc)
                    
            if context.has_key('search_materials'):
                categ_ids = self.search(cr, uid, [('code','=','NVL')])
                for node in doc.xpath("//field[@name='parent_id']"):
                    node.set('domain', "[('parent_id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
                    
                res['arch'] = etree.tostring(doc)
                
            if context.has_key('search_semi_finished_goods'):
                categ_ids = self.search(cr, uid, [('code','=','BTP')])
                for node in doc.xpath("//field[@name='parent_id']"):
                    node.set('domain', "[('parent_id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
                    
                res['arch'] = etree.tostring(doc)
            
            if context.has_key('search_congcudungcu'):
                categ_ids = self.search(cr, uid, [('code','=','CCDC')])
                for node in doc.xpath("//field[@name='parent_id']"):
                    node.set('domain', "[('parent_id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
                    
                res['arch'] = etree.tostring(doc)
            
            if context.has_key('search_nguyenlieutieuhao'):
                categ_ids = self.search(cr, uid, [('code','=','NLTH')])
                for node in doc.xpath("//field[@name='parent_id']"):
                    node.set('domain', "[('parent_id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
                    
                res['arch'] = etree.tostring(doc)
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        
        if context.has_key('search_finished_goods'):
            categ_ids = self.search(cr, uid, [('code','=','TP')])
            if len(categ_ids):
                args.append(('id','child_of',categ_ids))
        
        if context.has_key('search_product'):
            categ_ids = self.search(cr, uid, [('code','=','HB')])
            if len(categ_ids):
                args.append(('id','child_of',categ_ids))
                
        if context.has_key('search_materials'):
            categ_ids = self.search(cr, uid, [('code','=','NVL')])
            if len(categ_ids):
                args.append(('id','child_of',categ_ids))
        
        if context.has_key('search_semi_finished_goods'):
            categ_ids = self.search(cr, uid, [('code','=','BTP')])
            if len(categ_ids):
                args.append(('id','child_of',categ_ids))
        
        if context.has_key('search_congcudungcu'):
            categ_ids = self.search(cr, uid, [('code','=','CCDC')])
            if len(categ_ids):
                args.append(('id','child_of',categ_ids))
        
        if context.has_key('search_nguyenlieutieuhao'):
            categ_ids = self.search(cr, uid, [('code','=','NLTH')])
            if len(categ_ids):
                args.append(('id','child_of',categ_ids))
                
        return super(product_category, self).search(cr, uid, args, offset, limit, order, context=context, count=count)
    
    def init(self, cr):
        wb = xlrd.open_workbook(base_path + '/general_product/data/product_category.xls')
        wb.sheet_names()
        sh = wb.sheet_by_index(0)
        account_pool = self.pool.get('account.account')
        i = -1
        for rownum in range(sh.nrows):
            i += 1
            row_values = sh.row_values(rownum)
            
            if i == 0:
                continue
            
            try:
                exist_ids = self.search(cr, SUPERUSER_ID, [('code','=',row_values[7])])
                if not len(exist_ids):
                    vals = {'name': row_values[0], 'code':row_values[7]}
                    
                    if row_values[8]:
                        parent_ids = self.search(cr, SUPERUSER_ID, [('code','=',row_values[8])])
                        vals.update({'parent_id': parent_ids and parent_ids[0] or False})
                        
                    account_ids = account_pool.search(cr, SUPERUSER_ID, [('code','=',row_values[1])])
                    if len(account_ids):
                        vals.update({'property_account_income_categ': account_ids[0]})
                    
                    account_ids = account_pool.search(cr, SUPERUSER_ID, [('code','=',row_values[2])])
                    if len(account_ids):
                        vals.update({'property_account_refund_categ': account_ids[0]})
                    
                    account_ids = account_pool.search(cr, SUPERUSER_ID, [('code','=',row_values[3])])
                    if len(account_ids):
                        vals.update({'property_account_expense_categ': account_ids[0]})
                    
                    account_ids = account_pool.search(cr, SUPERUSER_ID, [('code','=',row_values[4])])
                    if len(account_ids):
                        vals.update({'property_stock_valuation_account_id': account_ids[0]})
                    
                    account_ids = account_pool.search(cr, SUPERUSER_ID, [('code','=',row_values[5])])
                    if len(account_ids):
                        vals.update({'property_stock_account_loss_categ': account_ids[0]})
                    
                    account_ids = account_pool.search(cr, SUPERUSER_ID, [('code','=',row_values[6])])
                    if len(account_ids):
                        vals.update({'property_stock_account_scrap_categ': account_ids[0]})
                    
                    self.create(cr, SUPERUSER_ID, vals)
            except Exception, e:
                continue
        
        #Thanh: Fix parent left and parent right
        def browse_rec(root, pos=0):
            cr.execute("SELECT id FROM product_category WHERE parent_id=%s order by sequence"%(root))
            pos2 = pos + 1
            for id in cr.fetchall():
                pos2 = browse_rec(id[0], pos2)
            cr.execute('update product_category set parent_left=%s, parent_right=%s where id=%s', (pos, pos2, root))
            return pos2 + 1  
        query = "SELECT id FROM product_category WHERE parent_id IS NULL order by sequence"
        pos = 0
        cr.execute(query)
        for (root,) in cr.fetchall():
            pos = browse_rec(root, pos)
        return True
    
product_category()

class product_template(osv.osv):
    _inherit = "product.template"
    
    _columns = {
        'name': fields.char('Name', size=128, required=True, translate=False, select=True),
    }
    
product_template()

class product_product(osv.osv):
    _inherit = "product.product"
    
    _columns = {
        #Thanh: required for Code
        'default_code' : fields.char('Internal Reference', size=64, select=True, required=True),
        'shop_ids': fields.many2many('sale.shop', 'product_shop_rel', 'product_id', 'shop_id', 'Product Shop'),
    }
    
    def copy(self, cr, uid, id, default=None, context=None, done_list=None, local=False):
        default = {} if default is None else default.copy()
        default.update({'default_code': '/'})
        return super(product_product, self).copy(cr, uid, id, default, context=context)
#     
    
    def is_default_uniq(self,cr,uid,ids):
        for product in self.browse(cr,uid,ids):
            if product.default_code and product.default_code != '/':
                product_obj_ids = self.search(cr, uid, [('default_code','=',product.default_code),
                                                  ('id','<>',product.id),('active','=',True)])
                if product_obj_ids:
                    return False
        return True
    
    _constraints = [(is_default_uniq, 'Lỗi: Mã sản phẩm đã tồn tại!!!', ['default_code'])]
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        
        categ_pool = self.pool.get('product.category')
        new_args = []
#         if context.has_key('partner_id'):
#             args.append(('partner_id','=',context['partner_id']))
            
        if context.has_key('search_finished_goods'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','TP')])
            if len(categ_ids):
                new_args.append(('categ_id','child_of',categ_ids))
        
        if context.has_key('search_product'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','HB')])
            if len(categ_ids):
                new_args.append(('categ_id','child_of',categ_ids))
                
        if context.has_key('search_materials'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','NVL')])
            if len(categ_ids):
                new_args.append(('categ_id','child_of',categ_ids))
        
        if context.has_key('search_semi_finished_goods'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','BTP')])
            if len(categ_ids):
                new_args.append(('categ_id','child_of',categ_ids))
        
        if context.has_key('search_congcudungcu'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','CCDC')])
            if len(categ_ids):
                new_args.append(('categ_id','child_of',categ_ids))
        
        if context.has_key('search_nguyenlieutieuhao'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','NLTH')])
            if len(categ_ids):
                new_args.append(('categ_id','child_of',categ_ids))
                
        if len(new_args):
            if len(new_args) > 1:
                for i in range(0,len(new_args)-1):
                    args.append('|')
            args += new_args
        return super(product_product, self).search(cr, uid, args, offset, limit, order, context=context, count=count)
    
    def default_get(self, cr, uid, fields, context=None):
        res = super(product_product, self).default_get(cr, uid, fields, context=context)
        
        categ_pool = self.pool.get('product.category')
        categ_ids = []
        if context.has_key('search_finished_goods'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','TP')])
        
        if context.has_key('search_product'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','HB')])
            
        if context.has_key('search_materials'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','NVL')])
        
        if context.has_key('search_semi_finished_goods'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','BTP')])
        
        if context.has_key('search_congcudungcu'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','CCDC')])
        
        if context.has_key('search_nguyenlieutieuhao'):
            categ_ids = categ_pool.search(cr, uid, [('code','=','NLTH')])
            
        if len(categ_ids):
            res.update({'categ_id':categ_ids[0]})
        return res
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if context is None:
            context = {}
        res = super(product_product,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            categ_pool = self.pool.get('product.category')
            
            if context.has_key('search_finished_goods'):
                categ_ids = categ_pool.search(cr, uid, [('code','=','TP')])
                for node in doc.xpath("//field[@name='categ_id']"):
                    node.set('domain', "[('id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
            
            if context.has_key('search_product'):
                categ_ids = categ_pool.search(cr, uid, [('code','=','HB')])
                for node in doc.xpath("//field[@name='categ_id']"):
                    node.set('domain', "[('id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
                        
            if context.has_key('search_materials'):
                categ_ids = categ_pool.search(cr, uid, [('code','=','NVL')])
                for node in doc.xpath("//field[@name='categ_id']"):
                    node.set('domain', "[('id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
                    
            if context.has_key('search_semi_finished_goods'):
                categ_ids = categ_pool.search(cr, uid, [('code','=','BTP')])
                for node in doc.xpath("//field[@name='categ_id']"):
                    node.set('domain', "[('id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
                    
            if context.has_key('search_congcudungcu'):
                categ_ids = categ_pool.search(cr, uid, [('code','=','CCDC')])
                for node in doc.xpath("//field[@name='categ_id']"):
                    node.set('domain', "[('id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
            
            if context.has_key('search_nguyenlieutieuhao'):
                categ_ids = categ_pool.search(cr, uid, [('code','=','NLTH')])
                for node in doc.xpath("//field[@name='categ_id']"):
                    node.set('domain', "[('id', 'child_of', [%s])]"%(','.join(map(str, categ_ids))))
                    
            xarch, xfields = self._view_look_dom_arch(cr, uid, doc, view_id, context=context)
            res['arch'] = xarch
            res['fields'] = xfields
                
        return res
product_product()
