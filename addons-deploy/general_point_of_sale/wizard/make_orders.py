
#-*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

import time
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class make_orders(osv.osv_memory):
    _name = "make.orders"
    
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
        'make_orders_line': fields.many2many('pos.order','pos_ref', 'make_order_id', 'order_id','Pos Order'),
        'sohodon':fields.char('Số hoá đơn',size =128,required=True),
        'note':fields.char('Note',size=128,required=True)
        
    }
    _defaults = {
        'date_invoice': fields.date.context_today,
        'shop_id': _get_default_shop, 
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'make.orders', context=c),

    }

    
    def default_get(self, cr, uid, fields, context=None):
        res = {}
        sale_ids = []
        res = super(make_orders, self).default_get(cr, uid, fields, context=context)
        if context.get('active_ids',False):
            for sale in self.pool.get('pos.order').browse(cr,uid,context['active_ids']):
                sale_ids.append(sale.id)
            res.update({'make_orders_line':sale_ids}) 
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
#         address_contact_id, address_invoice_id = \
#                 self.pool.get('res.partner').address_get(cr, uid, [groub_obj.partner_id.id], ['delivery']).values()
                        
        payment_term = groub_obj.partner_id.property_payment_term and groub_obj.partner_id.property_payment_term.id or False
        #payment_method = groub_obj.partner_id.payment_method_id and groub_obj.partner_id.payment_method_id.id or False
        
        if inv_type == 'out_invoice':
            name = ''
            account_journal_id = self.pool.get('account.journal').search(cr,uid,[('type','=','sale')])
        if inv_type == 'out_refund':
            name = ''
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
            #'name': name,
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
        
        account_id = False
        if type == 'out_invoice':
            account_id = line.product_id.product_tmpl_id.property_account_income.id
        else:
            account_id = line.product_id.categ_id and line.product_id.categ_id.property_account_refund_categ.id or False
                
#             account_id = line.product_id.product_tmpl_id.\
#                 property_account_income.id
            
        if not account_id and type == 'out_invoice':
            account_id = line.product_id.categ_id.\
                    property_account_income_categ.id
        
        if not account_id:
            raise osv.except_osv(_('Error!'), _('You must Define Account '))
        
        tax_id = self._get_taxes_invoice(cr, uid, line, type)
            
        name =  line.product_id.name
        res = {
                'name': name,
                'origin': line.order_id.name,
                'invoice_id': invoice_id,
                'uos_id': line.product_id and line.product_id.uom_id.id,
                'product_id': line.product_id.id,
                'account_id': account_id,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'quantity': line.qty,
                'invoice_line_tax_id': tax_id and [(6, 0, tax_id)] or [],
                #'account_analytic_id': account_analytic_id,
                #'source_obj': 'pos.order.line',
                #'source_id': line.id,
               }
        
        invoive_line_id = invoice_line.create(cr,uid,res)
        ## Update lai line invoice_line_id tren pos_order_line
#         sql = '''
#             Update pos_order_line set invoice_line_id = %s where id = %s
#         '''%(invoive_line_id,line.id)
#         cr.execute(sql)
        return True
    
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
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)        
        return date.strftime('%d/%m/%Y')
    
    def get_sum_qty(self,cr,uid,invoice_ids,inv_type,groub_obj,context=None):
        invoice = self.pool.get('account.invoice')
        invoice_line = self.pool.get('account.invoice.line')
        context = context or {}
        
        date = self.get_vietname_date(groub_obj.date_invoice)
        name = groub_obj.note + str(date)
        #name = '''POS ngay %s  ''' %(date)
        self.pool.get('account.invoice').button_compute(cr, uid, invoice_ids, context=context, set_total=inv_type)
        for invoice_id in invoice_ids:
            line_ids = []
            sql = '''
                SELECT type ,date_document from account_invoice where id = %s 
            '''%(invoice_id)
            cr.execute(sql)
            for line in cr.dictfetchall():
                date = self.get_vietname_date(line['date_document'])
                inv_type = line['type']
                
               
            
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
    
    def add_lamtronso(self,cr,uid,invoice_id,price_unit):
        account_ids =self.pool.get('account.account').search(cr,uid,[('code','=','6329001')])
        tax_ids = self.pool.get('account.tax').search(cr,uid,[('description','=','VAT OUT 10% (BGTG)')])
        res={
                'discount_type':'1',
                'account_id':account_ids and account_ids[0]  or False,
                'quantity':1,
                'name':'Chi phi lam tron',
                'invoice_line_tax_id':[(6,0,tax_ids)],
                'invoice_id':invoice_id,
                'price_unit':price_unit
             }
        self.pool.get('account.invoice.line').create(cr,uid,res)
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

        pos_total_ids = context and context.get('active_ids', False)
        
        if not pos_total_ids:
            raise osv.except_osv(_('Error!'), _('Khong co bill'))
        
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
            
        sql ='''
            UPDATE pos_order 
            SET invoiced_flag = True ,state = '%s',date_invoice = '%s',private_inv_flag = True
            WHERE id in (%s)
        '''%('invoiced',groub_obj.date_invoice,','.join(map(str,pos_total_ids)))
        cr.execute(sql)
        
        inv_type ='out_invoice'
        sql ='''
            SELECT pol.id
            FROM pos_order po inner join pos_order_line pol on po.id = pol.order_id
            WHERE
                po.id in (%s)
                and (po.type_pos is null or po.type_pos ='delivery')
        '''%(','.join(map(str,pos_total_ids)))
        cr.execute(sql)
        pos_line_ids = [x[0] for x in cr.fetchall()]
        invoice_id = self.prepare_invoice(cr, uid, ids, groub_obj, inv_type)
        for line in pos_line_obj.browse(cr, uid, pos_line_ids):
            self.prepare_invoice_combine_line(cr, uid, ids, line, invoice_id, inv_type)
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
        total_amount = 0
        for i in self.pool.get('pos.order').browse(cr,uid,pos_total_ids):
            for line in i.statement_ids:
                banks_statement_ids.append(line.id)
            total_amount = total_amount + i.amount_total
        if pos_total_ids:
            invoice_obj.write(cr,uid,invoice_ids,{'pos_order_ids':[(6, 0, pos_total_ids)]})
        if total_amount:
            for i in invoice_obj.browse(cr,uid,invoice_ids):
                if total_amount != i.amount_total:
                    self.add_lamtronso(cr, uid, invoice_id, total_amount - i.amount_total)
                    
        if banks_statement_ids:
            sql ='''
                SELECT journal_id,sum(amount) thanhtoan
                FROM account_bank_statement_line
                WHERE id in (%s)
                GROUP BY journal_id
                
            '''%(','.join(map(str,banks_statement_ids)))
            cr.execute(sql)
            for i in cr.dictfetchall():
                self.pay_invoice(cr, uid,  invoice_ids[0],i['journal_id'],i['thanhtoan'])
                sql ='''
                    SELECT abs.id ,aj.type
                    FROM
                        account_bank_statement_line abs inner join account_journal aj on abs.journal_id = aj.id
                    WHERE
                        journal_id = %s
                        and abs.id in (%s)
                '''%(i['journal_id'],','.join(map(str,banks_statement_ids)))
                cr.execute(sql)
                for j in cr.dictfetchall():
                    if j['type'] =='cash':
                        line_tm_ids.append(j['id'])
                    else:
                        line_ck_ids.append(j['id'])
                        
            invoice_obj.write(cr,uid,invoice_ids,{'statement_line_tm_ids':[(6, 0, line_tm_ids)],
                                                    'statement_line_ck_ids':[(6, 0, line_ck_ids)],})
                
        return self.return_form(cr, uid, ids, invoice_ids)
    
    def pay_invoice(self, cr, uid, invoice_id,journal_id,amount,context=None):
        wf_service = netsvc.LocalService("workflow")
        voucher = self.pool.get('account.voucher')
        if invoice_id:
            wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)
            
        fields_list = ['comment', 'line_cr_ids', 'is_multi_currency', 'reference', 'line_dr_ids', 'company_id', 'currency_id', 
                         'shop_id', 'narration', 'partner_id', 'payment_rate_currency_id', 'paid_amount_in_company_currency', 
                         'writeoff_acc_id', 'state', 'pre_line', 'type', 'payment_option', 'account_id', 'period_id', 'date', 
                         'reference_number', 'payment_rate', 'name', 'writeoff_amount', 'analytic_id', 'journal_id', 'amount']
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        voucher_context = {
            'payment_expected_currency': inv.currency_id.id,
            'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
            'default_amount': inv.type in ('out_refund', 'in_refund') and -amount or amount,
            'default_reference': inv.name,
            'close_after_process': True,
            'invoice_type': inv.type,
            'invoice_id': inv.id,
            'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
            'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
        }
        vals = voucher.default_get(cr, uid, fields_list, context=voucher_context)
        res = voucher.onchange_journal(cr, uid, [], journal_id, 
                                       False, False, inv.partner_id.id, 
                                       inv.date_invoice, 
                                       amount, 
                                       vals['type'], vals['company_id'], context=voucher_context)
        vals = dict(vals.items() + res['value'].items())
        line_cr_ids = []
        line_dr_ids = []
        for line in vals['line_cr_ids']:
            line_cr_ids.append((0,0,line))
        for line in vals['line_dr_ids']:
            line_dr_ids.append((0,0,line))
        vals['line_cr_ids'] = line_cr_ids
        vals['line_dr_ids'] = line_dr_ids
        vals.update({'journal_id':journal_id,
                     'shop_id':inv.shop_id.id})
        voucher_id = voucher.create(cr, uid, vals)
        if voucher_id:
            wf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
        else:
            raise osv.except_osv(_('Lỗi!'), _('Không thể tạo thanh toán!'))
        return True
    
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
    

make_orders()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
