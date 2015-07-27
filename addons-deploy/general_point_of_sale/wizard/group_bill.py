# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

from osv import fields, osv
from tools.translate import _
import time
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from openerp import netsvc

class group_bill(osv.osv_memory):
    _name = 'group.bill'
    _columns = {
#         'warehouse_id':fields.many2one('sale.shop', 'Shop',required =True),
        'shop_id':fields.many2one('sale.shop', 'Shop',required =True),
        'date_invoice': fields.date('Date Invoice',required =True ),
        'group_general':fields.boolean('Group General'),
        'group_bill_point': fields.many2many('pos.order','group_bill_ref', 'group_bill_id', 'pos_order_id','Bill',domain="[('state', '=', ('paid'))]"),
        'partner_id':fields.many2one('res.partner','Customer',required =True),
        'company_id':fields.many2one('res.company','company'),
        'from_date': fields.date('Từ ngày'),
        'to_date': fields.date('Đến ngày'),
        'account_journal_id':fields.many2one('account.journal','Phương thức thanh toán',required =True,domain=[('type', '=', 'cash')])
    }
    _defaults = { 
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'group.bill', context=c),
        'group_general':True,
    }
    
    def onchange_get_bill(self,cr,uid,ids,partner_id,from_date,to_date):
        if not partner_id or not from_date:
            return {}
        to_date = to_date or time.strftime(DATE_FORMAT)
        sql ='''
            SELECT id 
            FROM pos_order
            WHERE
                state = '%s'
                --and (invoiced_flag = False or invoiced_flag is null)
                and timezone('UTC',date_order::timestamp)::date between '%s' and '%s'
                and partner_id = %s
        ''' %('paid',from_date,to_date,partner_id)
        cr.execute(sql)
        pos_ids = [x[0] for x in cr.fetchall()]
        vals ={
               'group_bill_point':pos_ids
           }
        return {'value': vals}

    def onchange_date_invoice(self,cr,uid,ids,date_invoice):
        res = {}
        if date_invoice:
            sql ='''
                SELECT id 
                FROM pos_order
                WHERE
                    state = '%s'
                    and (invoiced_flag = False or invoiced_flag is null)
                    and timezone('UTC',date_order::timestamp)::date = '%s'
            ''' %('paid',date_invoice)
            cr.execute(sql)
            pos_ids = [x[0] for x in cr.fetchall()]
        else:
            sql ='''
                SELECT id 
                FROM pos_order
                WHERE
                    state = '%s'
                    and (invoiced_flag = False or invoiced_flag is null)
            ''' %('paid')
            cr.execute(sql)
            pos_ids = [x[0] for x in cr.fetchall()]

        domain = {'group_bill_point':
                        [('id', 'in', pos_ids)]}
        return {'value': res, 'domain': domain}
    
    def get_vietname_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)        
        return date.strftime('%d/%m/%Y')
    
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
    
    def get_sum_qty(self,cr,uid,invoice_ids,inv_type,groub_obj,context=None):
        invoice = self.pool.get('account.invoice')
        invoice_line = self.pool.get('account.invoice.line')
        date = False
        name =False
        context = context or {}
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
                
            if inv_type == 'out_invoice':
                #if tax_name:
                name = '''POS ngay %s  ''' %(date)
            else:
                name = '''Dieu chinh doanh thu ngay %s ''' %(date)
            
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
            if 'combine' in context and context['combine'] == True:
                sql ='''
                    DELETE FROM account_invoice_line where invoice_id = %s and quantity <= 0
                '''%(invoice_id)
                cr.execute(sql)
            #invoice.write(cr,uid,invoice_id,{'name':name})
            self.pool.get('account.invoice').button_reset_taxes(cr, uid, [invoice_id], context)
            #viet hàm thanh toán ở dây luôn
            if invoice_id:
                self.pay_invoice(cr, uid,  invoice_id,groub_obj)
        return True
    
    def pay_invoice(self, cr, uid, invoice_id,groub_obj,context=None):
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
            'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
            'default_reference': inv.name,
            'close_after_process': True,
            'invoice_type': inv.type,
            'invoice_id': inv.id,
            'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
            'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
        }
        vals = voucher.default_get(cr, uid, fields_list, context=voucher_context)
        res = voucher.onchange_journal(cr, uid, [], groub_obj.account_journal_id.id, 
                                       False, False, inv.partner_id.id, 
                                       inv.date_invoice, 
                                       inv.residual, 
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
        vals.update({'journal_id':groub_obj.account_journal_id.id,
                     'shop_id':inv.shop_id.id})
        voucher_id = voucher.create(cr, uid, vals)
        if voucher_id:
            wf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
        else:
            raise osv.except_osv(_('Lỗi!'), _('Không thể tạo thanh toán!'))
        return True
    
    
    def group_bill_invoice(self,cr, uid, ids, context=None):
        sql = False
        pos_line_obj = self.pool.get('pos.order.line')
        groub_obj = self.browse(cr,uid,ids[0])
        group_general = groub_obj.group_general
        group_invoice_ids = []
        invoice_ids = []
        shop_ids = []
        shop_id = ','.join(map(str,[groub_obj.shop_id.id]))
        
        if group_general:
            sql='''
                SELECT id
                FROM pos_order pos
                WHERE 
                    (invoiced_flag = False or invoiced_flag is null)
                    and state='paid'
                    and shop_id in (%s) 
                    and timezone('UTC',date_order::timestamp)::date between '%s' and '%s'
                '''%(shop_id,groub_obj.from_date,groub_obj.to_date)
            (groub_obj.date_invoice,shop_ids)
            cr.execute(sql)
            pos_total_ids = [x[0] for x in cr.fetchall()]
            if not pos_total_ids:
                raise osv.except_osv(_('Error!'), _('Bill unavalible'))
            sql ='''
                    UPDATE pos_order 
                    SET invoiced_flag = True ,state = '%s',date_invoice = '%s',private_inv_flag = False
                    WHERE id in (%s)
                '''%('invoiced',groub_obj.date_invoice,','.join(map(str,pos_total_ids)))
            cr.execute(sql)
        else:
            sql='''
                SELECT id
                FROM pos_order where id in 
                    (SELECT pos_order_id 
                    FROM group_bill_ref 
                    WHERE group_bill_id =%s)
                '''%(ids[0])
            cr.execute(sql)
            pos_total_ids = [x[0] for x in cr.fetchall()]
            
            sql ='''
                UPDATE pos_order 
                SET invoiced_flag = True ,state = '%s',date_invoice = '%s',private_inv_flag = True
                WHERE id in (%s)
            '''%('invoiced',groub_obj.date_invoice,','.join(map(str,pos_total_ids)))
            cr.execute(sql)
        
        if not pos_total_ids:
            raise osv.except_osv(_('Error!'), _('Khong co bill'))
        # lay bill ban hang`
        type_bill = ['receipt','delivery']
        for i in type_bill:
            if i in ['','delivery']:
                inv_type ='out_invoice'
                sql ='''
                SELECT pol.id
                FROM pos_order po inner join pos_order_line pol on po.id = pol.order_id
                WHERE
                    po.id in (%s)
                    and po.type_pos is null
                '''%(','.join(map(str,pos_total_ids)))
            else:
                inv_type ='out_refund'
                sql ='''
                    SELECT pol.id
                    FROM pos_order po inner join pos_order_line pol on po.id = pol.order_id
                    WHERE
                        po.id in (%s)
                        and po.type_pos ='%s'
                '''%(','.join(map(str,pos_total_ids)),i)
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
            
        return self.return_form(cr, uid, ids, invoice_ids)
    
    def return_form(self,cr,uid,ids,invoice_ids):
        if invoice_ids:
            if invoice_ids:
                domain_invoice_ids = []
                header = "Hóa đơn khách hàng"
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
    
    _defualt = {
                }
group_bill()
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
