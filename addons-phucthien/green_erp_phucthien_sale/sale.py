# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
import time
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import time
from datetime import date
from datetime import timedelta
from datetime import datetime
import calendar
import amount_to_text_vn
import openerp.addons.decimal_precision as dp
import codecs
from openerp import netsvc

class sale_order_rule(osv.osv):
    _name = "sale.order.rule"
    
    _columns = {
        'partner_id': fields.many2one('res.partner','Customer'),
        'from_date': fields.date('From Date', required=True),
        'to_date': fields.date('To Date', required=True),
        'product_id': fields.many2one('product.product','Product', required=True),
        'uom_id': fields.many2one('product.uom','Units of Measure'),
        'condition': fields.selection([('quantity','Quantity'),('value','Value')],'Condition', required=True),
        'operator': fields.selection([('>=','>='),('<=','<=')],'Operator', required=True),
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
    
sale_order_rule()

class sale_order(osv.osv):
    _inherit = "sale.order"
    
    _columns = {
        'product_category_id': fields.many2one('product.category','Loại sản phẩm'),
        'nv_duyet_id': fields.many2one('res.users','Nhân viên duyệt',readonly=1),
        'tp_duyet_id': fields.many2one('res.users','Trưởng phòng duyệt',readonly=1),
        'hop_dong_nt_id': fields.many2one('hop.dong','Hợp đồng nguyên tắc',domain="['&',('partner_id','=',partner_id),('type','=','nguyen_tac')]"),
        'hop_dong_t_id': fields.many2one('hop.dong','Hợp đồng thầu',domain="['&',('partner_id','=',partner_id),('type','=','thau')]"),
        'payment_mode_id': fields.many2one('res.payment.mode', 'Payment mode'),
        'chiu_trach_nhiem_id': fields.many2one('res.users', 'Người chịu trách nhiệm',readonly=True),
        'remark':fields.text('Ghi chú'),
        'sale_reason_peding_id': fields.many2one('sale.reason.pending','Lý do không đươc duyệt'),
        'dia_chi_kh':fields.text('Địa chỉ Khách hàng',readonly=True)
    }
    
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        val=[]
        if not part:
            return {'value': {'partner_invoice_id': False, 'partner_shipping_id': False,  'payment_term': False, 'fiscal_position': False}}

        partner = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        addr = self.pool.get('res.partner').address_get(cr, uid, [partner.id], ['delivery', 'invoice', 'contact'])
        pricelist = partner.property_product_pricelist and partner.property_product_pricelist.id or False
        payment_term = partner.property_payment_term and partner.property_payment_term.id or False
        fiscal_position = partner.property_account_position and partner.property_account_position.id or False
        dedicated_salesman = partner.user_id and partner.user_id.id or uid
        val = {
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'payment_term': payment_term,
            'fiscal_position': fiscal_position,
#             'user_id': dedicated_salesman,
        }
        if pricelist:
            val['pricelist_id'] = pricelist
        if part:
#             if partner.street2:
#             country = part.country_id and country_id.name or False
            val['dia_chi_kh']= partner.street + '/' +(partner.street2 or '') + '/' + partner.country_id.name
#             else:
#                 val['dia_chi_kh']= partner.street + '/' + partner.country_id.name
        return {'value': val}
    def create(self, cr, uid, vals, context=None):
        if 'partner_id' in vals:
            part = self.pool.get('res.partner').browse(cr, uid, vals['partner_id'])
            vals.update({
                        'dia_chi_kh': part.street + '/' +(part.street2 or '') + '/' + part.country_id.name
                         })
        new_id = super(sale_order, self).create(cr, uid, vals, context)
        sale = self.browse(cr, uid, new_id)
        return new_id
    
    def write(self, cr, uid, ids, vals, context=None):
        if 'partner_id' in vals:
            part = self.pool.get('res.partner').browse(cr, uid, vals['partner_id'])
            vals.update({
                        'dia_chi_kh': part.street + '/' +(part.street2 or '') + '/' + part.country_id.name
                         })
        new_write = super(sale_order, self).write(cr, uid, ids, vals, context=context) 
        return new_write
    def action_button_confirm(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        sale_rule_obj = self.pool.get('sale.order.rule')
        product_uom_obj = self.pool.get('product.uom')
        sale_line_obj = self.pool.get('sale.order.line')
        product_obj = self.pool.get('product.product')
        for sale in self.browse(cr, uid, ids):
            #Kiem tra co hop dong hay khong va ngay het han hop dong
            if not sale.hop_dong_nt_id and not sale.hop_dong_t_id and sale.partner_id.is_hop_dong:
                raise osv.except_osv(_('Cảnh báo!'),_('Vui lòng chọn hợp đồng nguyên tắc hoặc hợp đồng thầu trước khi xác nhận bán hàng!'))
            if sale.hop_dong_nt_id and sale.partner_id.is_hop_dong:
                if sale.date_order < sale.hop_dong_nt_id.tu_ngay or (sale.hop_dong_nt_id.den_ngay and sale.date_order > sale.hop_dong_nt_id.den_ngay or False):
                    raise osv.except_osv(_('Cảnh báo!'),_('Ngày bán hàng không nằm trong thời hạn của hợp đồng nguyên tắc!'))
            if sale.hop_dong_t_id and sale.partner_id.is_hop_dong:
                if sale.date_order < sale.hop_dong_t_id.tu_ngay or (sale.hop_dong_t_id.den_ngay and sale.date_order > sale.hop_dong_t_id.den_ngay or False):
                    raise osv.except_osv(_('Cảnh báo!'),_('Ngày bán hàng không nằm trong thời hạn của hợp đồng thầu!'))
            #Kiem tra ngay het han cac giay phep
            kiemtra_ngayhethan = True
            if (sale.partner_id.gpkd and sale.partner_id.date_gpkd) and sale.partner_id.date_gpkd < sale.date_order:
                kiemtra_ngayhethan = False
            if (sale.partner_id.cchn and sale.partner_id.date_cchn) and sale.partner_id.date_cchn < sale.date_order:
                kiemtra_ngayhethan = False
            if (sale.partner_id.gptn and sale.partner_id.date_gptn) and sale.partner_id.date_gptn < sale.date_order:
                kiemtra_ngayhethan = False
            if (sale.partner_id.gpp and sale.partner_id.date_gpp) and sale.partner_id.date_gpp < sale.date_order:
                kiemtra_ngayhethan = False
            if (sale.partner_id.gdp and sale.partner_id.date_gdp) and sale.partner_id.date_gdp < sale.date_order:
                kiemtra_ngayhethan = False
            if (sale.partner_id.gsp and sale.partner_id.date_gsp) and sale.partner_id.date_gsp < sale.date_order:
                kiemtra_ngayhethan = False        
                
            if not kiemtra_ngayhethan:
                raise osv.except_osv(_('Cảnh báo!'),_('Kiểm tra lại ngày hết hạn của giấy phép!'))
            
                    
            sql = '''
                select product_id,sum(product_uom_qty) as product_uom_qty from sale_order_line where order_id = %s group by product_id
            '''%(sale.id)
            cr.execute(sql)
            sale_lines = cr.dictfetchall()
            #Kiem tra so luong, don gia so voi dieu kien ban hang
            for sale_line in sale_lines:
                #Kiem tra so ngay no cua khach hang
                if sale.partner_id.so_ngay_no_ids:
                    for list_ngay_no in sale.partner_id.so_ngay_no_ids:
                        if product_obj.browse(cr,uid,sale_line['product_id']).categ_id.id == list_ngay_no.product_category_id.id and product_obj.browse(cr,uid,sale_line['product_id']).manufacturer_product_id.id == list_ngay_no.manufacturer_product_id.id:
#                             if sale_line['product_id'] == list_ngay_no.product_id.id:
                            sql = '''
                                select id from account_invoice
                                    where date_invoice is not null
                                        and partner_id = %s
                                        and state='open'
                                        and date('%s')-date(date_invoice) > %s 
                                        order by date_invoice limit 1
                            '''%(sale.partner_id.id,sale.date_order,list_ngay_no.so_ngay)
                            cr.execute(sql)
                            invoice_ids = [row[0] for row in cr.fetchall()]
                            if invoice_ids:
                                if sale.partner_id.credit > sale.partner_id.credit_limit:
                                    raise osv.except_osv(_('Cảnh báo!'),_('Khách hàng %s vượt quá hạn mức tín dụng đối với sản phẩm %s %s ngày qui định!')%(sale.partner_id.name,product_obj.browse(cr,uid,sale_line['product_id']).name,list_ngay_no.so_ngay))
                sql = '''
                    select product_uom, sum(product_uom_qty) as product_uom_qty from sale_order_line where product_id = %s and order_id=%s group by product_uom 
                '''%(sale_line['product_id'],sale.id)
                cr.execute(sql)
                uom_lines = cr.dictfetchall()
                sql = '''
                    select id from sale_order_rule where  product_id = %s and '%s' between from_date and to_date and active = True
                '''%(sale_line['product_id'],time.strftime('%Y-%m-%d'))
                cr.execute(sql)
                sale_rule_ids = [r[0] for r in cr.fetchall()]
                for sale_rule in sale_rule_obj.browse(cr, uid, sale_rule_ids):
                    if sale_rule.partner_id.id and sale_rule.partner_id.id != sale.partner_id.id:
                        continue
                    uom_qty = 0
                    if sale_rule.condition=='quantity':
                        
                        for uom in uom_lines:
                            uom_qty += product_uom_obj._compute_qty(cr, uid, uom['product_uom'], uom['product_uom_qty'], sale_rule.uom_id.id)
                        
                        if sale_rule.operator=='>=':
                            if uom_qty < sale_rule.value:
                                if sale_rule.message:
                                    raise osv.except_osv(_('Warning!'),_(sale_rule.message))
                                else:
                                    raise osv.except_osv(_('Warning!'),_('Không thể duyệt sản phẩm với số lượng bé hơn số lượng tối thiểu: %s!')%(sale_rule.value))
                        if sale_rule.operator=='<=':
                            if uom_qty > sale_rule.value:
                                if sale_rule.message:
                                    raise osv.except_osv(_('Warning!'),_(sale_rule.message))
                                else:
                                    raise osv.except_osv(_('Warning!'),_('Không thể duyệt sản phẩm với số lượng lớn hơn số lượng tối đa: %s!')%(sale_rule.value))
                    if sale_rule.condition=='value':
                        sale_line_ids = sale_line_obj.search(cr, uid, [('order_id','=',sale.id),('product_id','=',sale_line['product_id'])])
                        price = sale_line_obj.browse(cr,uid,sale_line_ids[0]).price_unit
                        if sale_rule.operator=='>=':
                            if price < sale_rule.value:
                                if sale_rule.message:
                                    raise osv.except_osv(_('Warning!'),_(sale_rule.message))
                                else:
                                    raise osv.except_osv(_('Warning!'),_('Không thể duyệt sản phẩm với số lượng bé hơn giá trị tối thiểu: %s!')%(sale_rule.value))
                        if sale_rule.operator=='<=':
                            if price > sale_rule.value:
                                if sale_rule.message:
                                    raise osv.except_osv(_('Warning!'),_(sale_rule.message))
                                else:
                                    raise osv.except_osv(_('Warning!'),_('Không thể duyệt sản phẩm với số lượng lớn hơn giá trị tối đa: %s!')%(sale_rule.value))
            #Kiem tra so luong, don gia so voi hop dong thau
            if sale.hop_dong_t_id:
                for hd_line in sale.hop_dong_t_id.hopdong_line:
                    sql = '''
                        select product_id, sum(product_uom_qty) as total_qty
                        from sale_order_line l
                        inner join sale_order s on l.order_id = s.id
                        where s.hop_dong_t_id = %s and s.partner_id = %s and l.product_id = %s and s.state in ('done','progress')
                        group by product_id
                    '''%(sale.hop_dong_t_id.id,sale.partner_id.id,hd_line.product_id.id)
                    cr.execute(sql)
                    lines_qty = cr.dictfetchall()
                    product_uom_qty = 0
                    price_unit = 0
                    tax_amount = 0
                    sale_order_lines = sale_line_obj.search(cr,uid,[('order_id','=',sale.id),('product_id','=',hd_line.product_id.id)])
                    if sale_order_lines:
                        product_uom_qty = sale_line_obj.browse(cr,uid,sale_order_lines[0]).product_uom_qty
                        price_unit = sale_line_obj.browse(cr,uid,sale_order_lines[0]).price_unit
                        tax = sale_line_obj.browse(cr,uid,sale_order_lines[0]).tax_id
                        if tax:
                            for tax in tax:
                                tax_amount += tax.amount
                            price_unit = price_unit*(1+tax_amount)
                        value_price = hd_line.price_unit - price_unit
                        if abs(value_price) > 10:
                            raise osv.except_osv(_('Warning!'),_('Không thể duyệt sản phẩm với đơn giá khác đơn giá trong hợp đồng thầu: %s!')%(hd_line.price_unit))
                        for line_qty in lines_qty:
                            if line_qty['total_qty'] + product_uom_qty > hd_line.product_qty:
                                raise osv.except_osv(_('Warning!'),_('Không thể duyệt sản phẩm với số lượng lớn hơn số lượng trong hợp đồng thầu: %s!')%(hd_line.product_qty))
                    
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_confirm', cr)
        return self.write(cr, uid, ids, {'nv_duyet_id':uid})
    
    def duyet_khong_dieukien(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_confirm', cr)
        return self.write(cr, uid, ids, {'tp_duyet_id':uid})
    
    def chiu_trach_nhiem(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'chiu_trach_nhiem_id':uid})

    def print_sale_order(self, cr, uid, ids, context=None): 
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'denghixuatban_report',
            }
    
sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        context = context or {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        warning = {}
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        if not product:
            res['value'].update({'product_packaging': False})
            return res

        # set product uom in context to get virtual stock in current uom
        if res.get('value', {}).get('product_uom'):
            # use the uom changed by super call
            context.update({'uom': res['value']['product_uom']})
        elif uom:
            # fallback on selected
            context.update({'uom': uom})

        #update of result obtained in super function
        product_obj = product_obj.browse(cr, uid, product, context=context)
        res['value']['delay'] = (product_obj.sale_delay or 0.0)
        res['value']['type'] = product_obj.procure_method

        #check if product is available, and if not: raise an error
        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom, context=context)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if not uom2:
            uom2 = product_obj.uom_id

        # Calling product_packaging_change function after updating UoM
        res_packing = self.product_packaging_change(cr, uid, ids, pricelist, product, qty, uom, partner_id, packaging, context=context)
        res['value'].update(res_packing.get('value', {}))
        warning_msgs = res_packing.get('warning') and res_packing['warning']['message'] or ''
        #Hung chan ko canh bao khong du so luong o sale
#         compare_qty = float_compare(product_obj.virtual_available, qty, precision_rounding=uom2.rounding)
#         if (product_obj.type=='product') and int(compare_qty) == -1 \
#            and (product_obj.procure_method=='make_to_stock'):
#             warn_msg = _('You plan to sell %.2f %s but you only have %.2f %s available !\nThe real stock is %.2f %s. (without reservations)') % \
#                     (qty, uom2.name,
#                      max(0,product_obj.virtual_available), uom2.name,
#                      max(0,product_obj.qty_available), uom2.name)
#             warning_msgs += _("Not enough stock ! : ") + warn_msg + "\n\n"
# 
#         #update of warning messages
#         if warning_msgs:
#             warning = {
#                        'title': _('Configuration Error!'),
#                        'message' : warning_msgs
#                     }
        res.update({'warning': {}})
        return res
    
sale_order_line()
class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    _columns = {
        'product_category_id': fields.many2one('product.category','Loại sản phẩm'),
    }
stock_picking()

class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"
    
    _columns = {
        'product_category_id': fields.many2one('product.category','Loại sản phẩm'),
    }
stock_picking_out()

class res_partner(osv.osv):
    _inherit = "res.partner"
    
    def _get_gp_gan_hh(self, cr, uid, ids, name, arg, context=None):        
        res = {}          
        for line in self.browse(cr, uid, ids):
            result = False
            if line.date_gpkd:
                b = datetime.now()
                a = line.date_gpkd
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 15:
                    result = True
            if line.date_cchn:
                b = datetime.now()
                a = line.date_cchn
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 15:
                    result = True
            if line.date_gptn:
                b = datetime.now()
                a = line.date_gptn
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 15:
                    result = True
            if line.date_gdp:
                b = datetime.now()
                a = line.date_gdp
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 15:
                    result = True
            res[line.id] = result
            if line.date_gpp:
                b = datetime.now()
                a = line.date_gpp
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 15:
                    result = True
            res[line.id] = result
            if line.date_gsp:
                b = datetime.now()
                a = line.date_gsp
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 15:
                    result = True
            res[line.id] = result
        return res
    
    _columns = {
        'user_id': fields.many2one('res.users', 'Salesperson', track_visibility='onchange', help='The internal user that is in charge of communicating with this contact if any.'),
        'gpkd': fields.boolean('Giấy phép kinh doanh'),
        'date_gpkd': fields.date('Ngày hết hạn GPKD'),
        'cchn': fields.boolean('Chứng chỉ hành nghề'),
        'date_cchn': fields.date('Ngày hết hạn CCHN'),
        'gptn': fields.boolean('Giấy phép tiêm ngừa'),
        'date_gptn': fields.date('Ngày hết hạn GPTN'),
#Hung them giay GPP/GDP/GSP
        'gdp': fields.boolean('GDP'),
        'date_gdp': fields.date('Ngày hết hạn GDP'),
        'gpp': fields.boolean('GPP'),
        'date_gpp': fields.date('Ngày hết hạn GPP'),
        'gsp': fields.boolean('GSP'),
        'date_gsp': fields.date('Ngày hết hạn GSP'),
#         'so_ngay_no': fields.integer('Số ngày nợ'),
        'hop_dong_ids':fields.one2many('hop.dong','partner_id','Hợp Đồng',readonly =True),
        'so_cmnd': fields.integer('Số CMND'),
        'is_hop_dong': fields.boolean('Hợp đồng'),
        'gp_gan_hh': fields.function(_get_gp_gan_hh,type='boolean', string='Giấy phép gần hết hạn'),
        'so_ngay_no_ids':fields.one2many('so.ngay.no','partner_id','Số ngày nợ theo sản phẩm'),
        'danhsach_canhtranh_ids':fields.one2many('danhsach.canhtranh','partner_id','Danh sách sản phẩm cạnh tranh'),
    }
res_partner()
class so_ngay_no(osv.osv):
    _name = "so.ngay.no"
    _columns = {
                'product_category_id': fields.many2one('product.category', 'Product Category'),
                'manufacturer_product_id': fields.many2one('manufacturer.product','Hãng sản xuất'),
                'so_ngay':fields.integer('Số ngày'),
                'partner_id': fields.many2one('res.partner','Khách hàng',required = True),
                }
    
so_ngay_no()

class res_company(osv.osv):
    _inherit = "res.company"
    
    def _get_gp_gan_hh(self, cr, uid, ids, name, arg, context=None):        
        res = {}          
        for line in self.browse(cr, uid, ids):
            result = False
            if line.date_cchn_duoc:
                b = datetime.now()
                a = line.date_cchn_duoc
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 1800:
                    result = True
            if line.date_gpddk_kd_thuoc:
                b = datetime.now()
                a = line.date_gpddk_kd_thuoc
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 1800:
                    result = True
            if line.date_gdp:
                b = datetime.now()
                a = line.date_gdp
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 1800:
                    result = True
            if line.date_gpp:
                b = datetime.now()
                a = line.date_gpp
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 1800:
                    result = True
            res[line.id] = result
            if line.date_gsp:
                b = datetime.now()
                a = line.date_gsp
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 1800:
                    result = True
            res[line.id] = result
            if line.date_lhtp_daugoi_norinse:
                b = datetime.now()
                a = line.date_lhtp_daugoi_norinse
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 1800:
                    result = True
            res[line.id] = result
            if line.date_lhtp_suatam_norinse:
                b = datetime.now()
                a = line.date_lhtp_suatam_norinse
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 1800:
                    result = True
            res[line.id] = result
            if line.date_lhtp_rabipur:
                b = datetime.now()
                a = line.date_lhtp_rabipur
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 1800:
                    result = True
            res[line.id] = result
            if line.date_lhtp_hepavax_gene_10mcg:
                b = datetime.now()
                a = line.date_lhtp_hepavax_gene_10mcg
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 1800:
                    result = True
            res[line.id] = result
            if line.date_lhtp_hepavax_gene_20mcg:
                b = datetime.now()
                a = line.date_lhtp_hepavax_gene_20mcg
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 1800:
                    result = True
            res[line.id] = result
        return res
    
    _columns = {
                'cchn_duoc': fields.boolean('Chứng chỉ hành nghề dược'),
                'date_cchn_duoc': fields.date('Ngày hết hạn CCHN Dược'),
                'gpddk_kd_thuoc': fields.boolean('Giấy phép đủ điều kiện kinh doanh thuốc'),
                'date_gpddk_kd_thuoc': fields.date('Ngày hết hạn CCHN Dược'),
                'gdp': fields.boolean('GDP'),
                'date_gdp': fields.date('Ngày hết hạn GDP'),
                'gpp': fields.boolean('GPP'),
                'date_gpp': fields.date('Ngày hết hạn GPP'),
                'gsp': fields.boolean('GSP'),
                'date_gsp': fields.date('Ngày hết hạn GSP'),
                'lhtp_daugoi_norinse': fields.boolean('Lưu hành sản phẩm Dầu gội Norinse'),
                'date_lhtp_daugoi_norinse': fields.date('Ngày hết hạn'),
                'lhtp_suatam_norinse': fields.boolean('GP Lưu hành sản phẩm sửa tắm Norinse'),
                'date_lhtp_suatam_norinse': fields.date('Ngày hết hạn'),
                'lhtp_rabipur': fields.boolean('GP Lưu hành sản phẩm Rabipur'),
                'date_lhtp_rabipur': fields.date('Ngày hết hạn'),
                'lhtp_hepavax_gene_10mcg': fields.boolean('GP Lưu hành sản phẩm Hepavax Gene 10mcg'),
                'date_lhtp_hepavax_gene_10mcg': fields.date('Ngày hết hạn'),
                'lhtp_hepavax_gene_20mcg': fields.boolean('GP Lưu hành sản phẩm Hepavax Gene 20mcg'),
                'date_lhtp_hepavax_gene_20mcg': fields.date('Ngày hết hạn'),
                'gp_gan_hh': fields.function(_get_gp_gan_hh,type='boolean', string='Giấy phép gần hết hạn'),
                }
res_company()

class sale_reason_pending(osv.osv):
    _name = "sale.reason.pending"
    
    _columns = {
        'name': fields.char('Reason Name'),
    }
    
sale_reason_pending()

class remind_work_situation(osv.osv):
    _name = "remind.work.situation"
    
    _columns = {
        'name': fields.char('Name'),
    }
    
remind_work_situation()

class remind_work(osv.osv):
    _name = "remind.work"
    _inherit = ['mail.thread']
    _columns = {
        'name': fields.char('Chủ đề', required=True,readonly=True, states={'draft': [('readonly', False)]}),
        'date_start': fields.datetime('Thời gian bắt đầu',readonly=True, states={'draft': [('readonly', False)]}),
        'date_end': fields.datetime('Thời gian kết thúc',readonly=True, states={'draft': [('readonly', False)]}),
        'user_id': fields.many2one('res.users', 'Gán cho',required=True,readonly=True, states={'draft': [('readonly', False)]}),
        'situation_id': fields.many2one('remind.work.situation', 'Tình trạng công việc',readonly=True, states={'draft': [('readonly', False)]}),
        'note':fields.text('Nội dung',readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([ ('draft', 'Draft'),
                                    ('open', 'Open'),
                                    ('cancel', 'Cancelled'),
                                    ('done', 'Done'),],string='Status',readonly=True, states={'draft': [('readonly', False)]}),
    }
    _defaults = {
        'date_start': fields.datetime.now,
        'state':  'draft',
        'user_id': lambda self,cr,uid,ctx: uid,
    }
    
    def case_open(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'open'})
    def case_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'})
    def case_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'})
    
remind_work()
class sanpham_canhtranh(osv.osv):
    _name = "sanpham.canhtranh"
    _columns = {
                'name':fields.char('Tên sản phẩm',required = True),
                'description': fields.char('Ghi chú'),
                }
    
sanpham_canhtranh()
class danhsach_canhtranh(osv.osv):
    _name = "danhsach.canhtranh"
    _columns = {
                'name':fields.date('Ngày',required=True),
                'product_id': fields.many2one('product.product', 'Product'),
                'qty':fields.integer('SL'),
                'qty_con_lai':fields.integer('SL còn lại'),
                'sanpham_canhtranh1_id': fields.many2one('sanpham.canhtranh','SPCT1'),
                'soluong_canhtranh1':fields.integer('SLCT1'),
                'soluong_canhtranh1_conlai':fields.integer('SLCTCL1'),
                'sanpham_canhtranh2_id': fields.many2one('sanpham.canhtranh','SPCT2'),
                'soluong_canhtranh2':fields.integer('SLCT2'),
                'soluong_canhtranh2_conlai':fields.integer('SLCTCL2'),
                'sanpham_canhtranh3_id': fields.many2one('sanpham.canhtranh','SPCT3'),
                'soluong_canhtranh3':fields.integer('SLCT3'),
                'soluong_canhtranh3_conlai':fields.integer('SLCTCL3'),
                'partner_id': fields.many2one('res.partner','Khách hàng',required = True),
                }
    
danhsach_canhtranh()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
