
#-*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

import time
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class make_invoice_line_ids(osv.osv_memory):
    _name = "make.invoice.line.ids"
    
    def _amount_line_all(self, cr, uid, ids, field_names, arg, context=None):
        res = dict([(i, {}) for i in ids])
        account_tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids, context=context):
            taxes_ids = [ tax for tax in line.pos_line_id.product_id.taxes_id if tax.company_id.id == line.pos_line_id.order_id.company_id.id ]
            price = line.price_unit
            taxes = account_tax_obj.compute_all(cr, uid, taxes_ids, price, line.invoice_qty, product=line.pos_line_id.product_id, partner=line.pos_line_id.order_id.partner_id or False)

            cur = line.pos_line_id.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal_incl'] = cur_obj.round(cr, uid, cur, taxes['total_included'])
        return res
    
    _columns = {
        'price_unit':fields.float(string='Unit Price', digits=(16, 2)),
        'line_id':fields.many2one('make.invoice.line','Line'),
        'flag':fields.boolean('Check'),
        'product_id':fields.many2one('product.product','Product',required=True),
        'qty':fields.float('Qty'),
        'invoice_qty':fields.float('Invoiced Qty'),
        'pos_id':fields.many2one('pos.order','Pos'),
        'pos_line_id':fields.many2one('pos.order.line','Pos'),
        'price_total':fields.float('Price Total'),
        'price_subtotal_incl':fields.float('price_subtotal_incl'),
        }
    
    def onchange_qty(self,cr,uid,ids,price_uint,qty,qty_invoiced):
        if qty <qty_invoiced:
            subtotal = price_uint * qty
            vals ={
               'invoice_qty':qty,
               'price_subtotal_incl':subtotal
               }
            
            raise osv.except_osv(_('Warning!'), _('Số lượng tạo qty invoiced không được lớn hơn số lượng bill'))
            return {'value': vals}
        
        subtotal = price_uint * qty_invoiced
        vals ={
               'price_subtotal_incl':subtotal
               }
        return {'value': vals}
make_invoice_line_ids()

class make_invoice_line(osv.osv_memory):
    _name = "make.invoice.line"
    def _get_default_shop(self, cr, uid, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id','=',company_id)], context=context)
        if not shop_ids:
            raise osv.except_osv(_('Error!'), _('There is no default shop for the current user\'s company!'))
        return shop_ids[0]
    _columns = {
        'date_invoice': fields.date('Date Invoice',required=True),
        'partner_id':fields.many2one('res.partner','Customer',required=True),
        'shop_id':fields.many2one('sale.shop','Shop',required=True),
        'company_id': fields.many2one('res.company','Company'),
        'make_orders_line': fields.many2many('pos.order.line','pos_line_ref', 'make_invoice_line_id', 'line_id','Pos Order Line'),
        'sohodon':fields.char('Số hoá đơn',size =128,required=True),
        'orders_line':fields.one2many('make.invoice.line.ids','line_id','Line'),
        'note':fields.char('Note',size=128,required=True)
    }
    _defaults = {
        'date_invoice': fields.date.context_today,
        'shop_id': _get_default_shop, 
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'make.orders', context=c),
    }
    
    
    
    def default_get(self, cr, uid, fields, context=None):
        pos_line_ids = []
        res = super(make_invoice_line, self).default_get(cr, uid, fields, context=context)
        if context.get('active_ids',False):
            for pos in self.pool.get('pos.order').browse(cr,uid,context['active_ids']):
                if pos.state =='invoiced':
                    raise osv.except_osv(_('Error!'), _('Bill đã tạo invoiced'))
                for line_obj in pos.lines:
                    if line_obj.qty - line_obj.invoice_qty >0:
                        pos_line_ids.append({
                            'flag':True,
                            'product_id':line_obj.product_id.id,
                            'qty':line_obj.qty,
                            'invoice_qty':line_obj.qty - line_obj.invoice_qty,
                            'pos_id':pos.id,
                            'pos_line_id':line_obj.id,
                            'price_unit':line_obj.price_unit,
                            'price_total':line_obj.price_subtotal_incl,
                            'price_subtotal_incl':line_obj.price_subtotal_incl
                            })
            res.update({'orders_line':pos_line_ids}) 
        return res

    def _get_taxes_invoice(self, cr, uid, move_line, type):
        if type in ('in_invoice', 'in_refund'):
            taxes = move_line.product_id.supplier_taxes_id
        else:
            taxes = move_line.product_id.taxes_id
        return map(lambda x: x.id, taxes)
    
    def prepare_invoice(self,cr,uid,ids,groub_obj,inv_type):
        account_journal_id = False
        name = ''
        invoice_obj = self.pool.get('account.invoice')
        payment_term = groub_obj.partner_id.property_payment_term and groub_obj.partner_id.property_payment_term.id or False
        if inv_type == 'out_invoice':
            name = groub_obj.note
            account_journal_id = self.pool.get('account.journal').search(cr,uid,[('type','=','sale')])
        if inv_type == 'out_refund':
            name = groub_obj.note
            account_journal_id = self.pool.get('account.journal').search(cr,uid,[('type','=','sale_refund')])
        
        if not account_journal_id:
            raise osv.except_osv(_('Error!'), _('You much define ACcount Journal'))
            
        if inv_type in ('out_invoice', 'out_refund'):
            if groub_obj.partner_id:
                account_id = groub_obj.partner_id.property_account_receivable.id
            else:
                account_id = self.pool.get('account.account').search(cr,uid,[('code','=','13112')])
                account_id = account_id and account_id[0]
        else:
            if groub_obj.partner_id:
                account_id = groub_obj.partner_id.property_account_payable.id
            else:
                account_id = self.pool.get('account.account').search(cr,uid,[('code','=','33111')])
                account_id = account_id and account_id[0]
        invoice_vals = {
            'comment': groub_obj.note,
            'reference_number':groub_obj.sohodon or False,
            'origin': '',
            'type': inv_type,
            'account_id': account_id,
            'partner_id': groub_obj.partner_id.id,
            'shop_id': groub_obj.shop_id.id,
            #'address_invoice_id': address_invoice_id,
            #'address_contact_id': address_contact_id,
            'comment': '',
            'payment_term': payment_term,
            'fiscal_position': groub_obj.partner_id.property_account_position.id,
            'date_invoice': groub_obj.date_invoice,
            'company_id': groub_obj.company_id and groub_obj.company_id.id or False,
            'user_id': uid,
            #'reference_type': 'none',
            'invoice_type':'vat_invoice',
            #'reference': groub_obj.reference + str(ids) or False,
            #'payment_method': payment_method,
            'date_document': groub_obj.date_invoice or False,
            'group_invoice':True,
            'journal_id':account_journal_id and account_journal_id[0]
        }
        return invoice_obj.create(cr,uid,invoice_vals)
    
    def prepare_invoice_combine_line(self, cr, uid, ids, line, invoice_id, type):
        invoice_line = self.pool.get('account.invoice.line')
        
        for i in line:
            account_id = False
            if type == 'out_invoice':
                account_id = i.pos_line_id.product_id.product_tmpl_id.property_account_income.id
            else:
                account_id = i.pos_line_id.product_id.categ_id and i.pos_line_id.product_id.categ_id.property_account_refund_categ.id or False
                    
    #             account_id = line.product_id.product_tmpl_id.\
    #                 property_account_income.id
                
            if not account_id and type == 'out_invoice':
                account_id = i.pos_line_id.product_id.categ_id.\
                        property_account_income_categ.id
            
            if not account_id:
                raise osv.except_osv(_('Error!'), _('You must Define Account '))
            tax_id = self._get_taxes_invoice(cr, uid, i.pos_line_id, type)
                
            name =  i.pos_line_id.product_id.name
            res = {
                    'name': name,
                    'origin': i.pos_line_id.order_id.name,
                    'invoice_id': invoice_id,
                    'uos_id': i.pos_line_id.product_id and i.pos_line_id.product_id.uom_id.id,
                    'product_id': i.pos_line_id.product_id.id,
                    'account_id': account_id,
                    'price_unit': i.pos_line_id.price_unit,
                    'discount': i.pos_line_id.discount,
                    'quantity': i.invoice_qty,
                    'invoice_line_tax_id': tax_id and [(6, 0, tax_id)] or [],
                    #'account_analytic_id': account_analytic_id,
                    #'source_obj': 'pos.order.line',
                    #'source_id': line.id,
                   }
            
            invoive_line_id = invoice_line.create(cr,uid,res)
            invoice_qty = i.pos_line_id.invoice_qty or 0.0
            invoice_qty = invoice_qty + i.invoice_qty
            self.pool.get('pos.order.line').write(cr,uid,[i.pos_line_id.id],{'invoice_qty':invoice_qty})
        ## Update lai line invoice_line_id tren pos_order_line
#         sql = '''
#             Update pos_order_line set invoice_line_id = %s where id = %s
#         '''%(invoive_line_id,line.id)
#         cr.execute(sql)
        return True
    
    def group_invoice_by_tax(self, cr, uid, old_invoice_ids, context=None):
        context = context or {}
        invoice_pool = self.pool.get('account.invoice')
        invoice_ids = []
        date_invoice = context.get('date_invoice',False)
        
        for old_invoice_id in old_invoice_ids:
            tax_ids = []
            cr.execute('''
                SELECT distinct alt.tax_id
                FROM account_invoice_line al left join account_invoice_line_tax alt on al.id=alt.invoice_line_id
                WHERE al.invoice_id = %s
                '''%(old_invoice_id,))
            tax_ids = cr.fetchall()
            if tax_ids and len(tax_ids) > 1:
                for tax_id in tax_ids:
                    tax_id = tax_id[0]
                    cr.execute('''
                            SELECT al.id
                            FROM account_invoice_line al inner join account_invoice ai on ai.id=al.invoice_id
                            WHERE al.invoice_id = %s
                            '''%(old_invoice_id,))
                    invoice_line_ids = cr.fetchall()
                    if invoice_line_ids:
                        new_invoice_id = invoice_pool.copy(cr, uid, old_invoice_id, {'invoice_line':[],'date_invoice':date_invoice})
                        invoice_ids.append(new_invoice_id)
                        #stt=1
                        for invoice_line_id in invoice_line_ids:
                            invoice_line_id = invoice_line_id[0]
                            if tax_id:
                                cr.execute('''
                                        SELECT al.id
                                        FROM account_invoice_line al inner join account_invoice_line_tax alt on al.id=alt.invoice_line_id
                                        WHERE al.id = %s and alt.tax_id = %s
                                        '''%(invoice_line_id,tax_id,))
                                if cr.fetchall():
                                    cr.execute("UPDATE account_invoice_line SET invoice_id=%s WHERE id=%s"%(new_invoice_id,  invoice_line_id,))
                            else:
                                cr.execute('''
                                        SELECT id
                                        FROM account_invoice_line 
                                        WHERE id = %s and id not in(select invoice_line_id from account_invoice_line_tax)
                                        '''%(invoice_line_id))
                                if cr.fetchall():
                                    cr.execute("UPDATE account_invoice_line SET invoice_id=%s WHERE id=%s"%(new_invoice_id,  invoice_line_id,))
                invoice_pool.unlink(cr, uid, [old_invoice_id])
            else:
                invoice_ids.append(old_invoice_id)
        return invoice_ids
    
    def delete_noline_invoice(self, cr, uid, invoice_id):
        if invoice_id:
            sql = '''
            select id
            FROM account_invoice_line
            WHERE 
                invoice_id = %s
            ''' %(invoice_id)
            cr.execute(sql)
            data = cr.dictfetchone()
            if not data:
                cr.execute("DELETE FROM account_invoice where id = %s"%(invoice_id))
                return False
        return invoice_id
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)        
        return date.strftime('%d/%m/%Y')
    
    def get_sum_qty(self,cr,uid,invoice_ids,inv_type,groub_obj,context=None):
        invoice = self.pool.get('account.invoice')
        invoice_line = self.pool.get('account.invoice.line')
        date = self.get_vietname_date(groub_obj.date_invoice)
        context = context or {}
        name = groub_obj.note +' ngay: ' + str(date)
        self.pool.get('account.invoice').button_compute(cr, uid, invoice_ids, context=context, set_total=inv_type)
        for invoice_id in invoice_ids:
            line_ids = []
            sql = '''
                SELECT type ,date_document from account_invoice where id = %s 
            '''%(invoice_id)
            cr.execute(sql)
                
            
            
            sql = '''
                SELECT product_id,uos_id,price_unit,sum(quantity) total_qty , discount ,sum(price_subtotal) price_subtotal
                FROM account_invoice_line 
                WHERE 
                        invoice_id = %s                    
                GROUP by product_id,uos_id,price_unit,discount
            '''%(invoice_id)
            cr.execute(sql)
            
            data = cr.dictfetchall()
            for line in data:
                invoice_line_ids = invoice_line.search(cr,uid,[('product_id','=',line['product_id']),
                                                               ('uos_id','=',line['uos_id']),
                                                               ('price_unit','=',line['price_unit']),
                                                               ('discount','=',line['discount']),
                                                               ('invoice_id','=',invoice_id)])
                if invoice_line_ids:
                    line_ids.append(invoice_line_ids[0]) 
                    invoice_line.write(cr,uid,invoice_line_ids[0],{'quantity':line['total_qty'],'price_subtotal':line['price_subtotal']})
                    
            if line_ids:
                sql ='''
                    DELETE FROM account_invoice_line where invoice_id = %s and id not in (%s)
                '''%(invoice_id,','.join(map(str,line_ids)))
                cr.execute(sql)
                
            invoice.write(cr,uid,[invoice_id],{'comment':name})
            
            self.pool.get('account.invoice').button_reset_taxes(cr, uid, [invoice_id], context)
        return True
    
    def update_state_bill(self,cr,uid,ids):
        for i in ids:
            sql='''
                SELECT count(id) count
                FROM pos_order_line line 
                     where qty != coalesce(invoice_qty,0) 
                    and order_id =%s
            '''%(i)
            cr.execute(sql)
            for line in cr.dictfetchall():
                if line['count'] ==0:
                    sql ='''
                        Update pos_order set state = 'invoiced'
                        where id =%s
                    '''%(i)
                    cr.execute(sql)
        return True
                    
                    
        
    def make_orders(self, cr, uid, ids, context=None):
        group_invoice_ids = []
        invoice_ids =[]
        banks_statement_ids =[]
        line_tm_ids =[]
        line_ck_ids =[]
        groub_obj = self.browse(cr,uid,ids[0])
        pos_line_obj = self.pool.get('pos.order.line')
        invoice_obj = self.pool.get('account.invoice')
        pos_total_ids =[]
        pos_line_ids = []
        orders_line_obj  =False
        inv_type ='out_invoice'

        for i in self.browse(cr,uid,ids):
            if i.orders_line:
                orders_line_obj = i.orders_line
            for j in i.orders_line:
                if j.pos_id.id not in pos_total_ids:
                    pos_total_ids.append(j.pos_id.id)
                pos_line_ids.append(j.pos_line_id.id)
        if not pos_total_ids:
            raise osv.except_osv(_('Error!'), _('Khong co bill'))
        if not pos_line_ids:
            raise osv.except_osv(_('Error!'), _('Khong co bill'))
        if pos_total_ids:
            self.pool.get('pos.order').write(cr,uid,pos_total_ids,{'partner_id':groub_obj.partner_id.id})
        
        sql='''
            SELECT count(id) count
            FROM 
                pos_order
            WHERE
                state = 'invoiced'
                and id in (%s)
        '''%(','.join(map(str,pos_total_ids)))
        cr.execute(sql)
        for i in cr.dictfetchall():
            if i['count'] !=0:
                raise osv.except_osv(_('Error!'), _('Invoice Đã được tạo'))
        
        invoice_id = self.prepare_invoice(cr, uid, ids, groub_obj, inv_type)
        #for line in pos_line_obj.browse(cr, uid, pos_line_ids):
        self.prepare_invoice_combine_line(cr, uid, ids, orders_line_obj, invoice_id, inv_type)
        res = self.delete_noline_invoice(cr, uid, invoice_id)
        group_invoice_ids += res and [res] or []
        context['date_invoice'] = groub_obj.date_invoice
        context['combine'] = True
        if group_invoice_ids:     
            group_by_tax = True
            if group_by_tax:
                group_invoice_ids = self.group_invoice_by_tax(cr, uid, group_invoice_ids, context)
            for group_invoice_id in group_invoice_ids:
                res = self.delete_noline_invoice(cr, uid, group_invoice_id)
                invoice_ids += res and [res] or []
            self.get_sum_qty(cr, uid, invoice_ids,  inv_type,groub_obj,context)
        
        self.update_state_bill(cr, uid, pos_total_ids)
        if pos_total_ids:
            invoice_obj.write(cr,uid,invoice_ids,{'pos_order_ids':[(6, 0, pos_total_ids)]})
            
        return self.return_form(cr, uid, ids, invoice_ids)
    
    def return_form(self,cr,uid,ids,invoice_ids):
        if invoice_ids:
            if invoice_ids:
                domain_invoice_ids = []
                header = u"Hóa đơn khách hàng"
                sql ='''
                    SELECT id
                    FROM
                        account_invoice 
                    WHERE 
                            id in (%s) 
                        AND type ='out_invoice'
                    '''%(','.join(map(str,invoice_ids)))
                cr.execute(sql)
                domain_invoice_ids += [x['id'] for x in cr.dictfetchall()]
                if not domain_invoice_ids:
                    header = "Customer Refunds"
                    sql ='''
                    SELECT id
                    FROM
                        account_invoice 
                    WHERE 
                            id in (%s) 
                        AND type ='out_refund'
                    '''%(','.join(map(str,invoice_ids)))
                    cr.execute(sql)
                    domain_invoice_ids += [x['id'] for x in cr.dictfetchall()]
                    
                data_pool = self.pool.get('ir.model.data')
                #action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree")
                form_id = data_pool.get_object_reference(cr, uid, 'account', 'invoice_form')
                form_res = form_id and form_id[1] or False
                tree_id = data_pool.get_object_reference(cr, uid, 'account', 'invoice_tree')
                tree_res = tree_id and tree_id[1] or False
                
                if tree_res and form_res:
                    return {
                        'name':_(header),
                        'view_mode': 'tree, form',
                        'view_id': False,
                        'view_type': 'form',
                        'res_model': 'account.invoice',
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'current',
                        'domain': "[('id', 'in', %s)]" % domain_invoice_ids,
                        'views': [(tree_res, 'tree'), (form_res, 'form')],
                        'context': {}
                    }
        else:
            return {'type': 'ir.actions.act_window_close'}
        
make_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
