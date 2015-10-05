# -*- coding: utf-8 -*-
from openerp import tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from datetime import datetime
import time
from datetime import date
from datetime import timedelta
from datetime import datetime
import calendar
import amount_to_text_vn
import openerp.addons.decimal_precision as dp
import codecs

class hop_dong(osv.osv):
    _name = "hop.dong"
    
    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit, line.product_qty, line.product_id, line.hopdong_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.company_id.currency_id
            for line in order.hopdong_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('hopdong.line').browse(cr, uid, ids, context=context):
            result[line.hopdong_id.id] = True
        return result.keys()
    
    def _get_hd_gan_hh(self, cr, uid, ids, name, arg, context=None):        
        res = {}          
        for line in self.browse(cr, uid, ids):
            if line.den_ngay:
                result = False     
                b = datetime.now()
                a = line.den_ngay
                temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                kq = temp - b
                if kq.days <= 15:
                    result = True
                res[line.id] = result
            else:
                res[line.id] = False            
        return res
    
    _columns = {
        'name':fields.char('Số', size = 1024,required = True),
        'type':fields.selection([('kinh_te','Hợp đồng kinh tế'),('thau','Hợp đồng thầu'),('nguyen_tac','Hợp đồng nguyên tắc')
                                 ,('mua','Hợp đồng mua'),('ky_gui','Hợp đồng ký gửi'),('tai_tro','Hợp đồng tài trợ')
                                 ,('khac','Hợp đồng khác')],'Loại hợp đồng' ,required=True,readonly=True, states={'moi_tao': [('readonly', False)]}),
        'tu_ngay':fields.date('Từ ngày',required = True,readonly=True, states={'moi_tao': [('readonly', False)]}),
        'den_ngay':fields.date('Ngày hết hạn'),
        'company_id': fields.many2one('res.company','Công ty',required = True,readonly=True, states={'moi_tao': [('readonly', False)]}),
        'partner_id': fields.many2one('res.partner','Khách hàng',required = True,domain="['&',('customer','=',True),('is_hop_dong','=',True)]",readonly=True, states={'moi_tao': [('readonly', False)]}),
        'phuc_luc_hd_thau':fields.text('Phụ lục hợp đồng thầu',readonly=True, states={'moi_tao': [('readonly', False)]}),
        'hopdong_line': fields.one2many('hopdong.line','hopdong_id','Line',readonly=True, states={'moi_tao': [('readonly', False)]}),
        
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Cộng',
            store={
                'hop.dong': (lambda self, cr, uid, ids, c={}: ids, ['hopdong_line'], 10),
                'hopdong.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Thuế GTGT',
            store={
                'hop.dong': (lambda self, cr, uid, ids, c={}: ids, ['hopdong_line'], 10),
                'hopdong.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tổng cộng',
            store={
                'hop.dong': (lambda self, cr, uid, ids, c={}: ids, ['hopdong_line'], 10),
                'hopdong.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        'state': fields.selection([
            ('moi_tao', 'Mới tạo'),
            ('da_duyet', 'Đã duyệt'),
            ('da_gui', 'Đã gửi'),
            ('da_nhan', 'Đã nhận'),
            ('het_han', 'Hết hạn'),
            ('huy_bo', 'Hủy bỏ'),
            ], 'Trạng thái',readonly=True, states={'moi_tao': [('readonly', False)]}),
        'ngay_gui':fields.date('Ngày gửi'),
        'ngay_nhan':fields.date('Ngày nhận'),
        'nguoi_nhan':fields.char('Người nhận', size = 1024,),
        'thanh_ly_hd':fields.boolean('Thanh lý hợp đồng'),
        'hd_gan_hh': fields.function(_get_hd_gan_hh,type='boolean', string='Hợp đồng gần hết hạn'),
    }
    
    _defaults = {
        'type': 'thau',
        'tu_ngay': time.strftime('%Y-%m-%d'),
        'state': 'moi_tao',
    }
    
    def print_hopdong(self, cr, uid, ids, context=None):
        hopdong = self.browse(cr, uid, ids[0])
        datas = {
             'ids': ids,
             'model': 'hop.dong',
             'form': self.read(cr, uid, ids[0], context=context)
        }
        if hopdong.type == 'kinh_te':
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hopdong_report',
                'datas': datas,
                'nodestroy' : True
                }
        elif hopdong.type == 'thau':
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hop_dong_thau_report',
                'datas': datas,
                'nodestroy' : True
            }
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hop_dong_nguyen_tac_report',
                'datas': datas,
                'nodestroy' : True
            }
    
    def duyet(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'da_duyet'})
    def da_gui(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'da_gui'})
    def da_nhan(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'da_nhan'})
    
    def het_han(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'het_han'})
    
    def huy_bo(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'huy_bo'})
    
    def set_to_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'moi_tao'})
    
hop_dong()

class hopdong_line(osv.osv):
    _name = 'hopdong.line'
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_qty, line.product_id, line.hopdong_id.partner_id)
            cur = line.hopdong_id.company_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res
    _columns = {
        'hopdong_id': fields.many2one('hop.dong', 'Hợp đồng', required=True, ondelete='cascade', select=True),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True,),
        'name':fields.char('Name',size=1024,required=True),
        'nongdo_hamluong':fields.char('Nồng độ, hàm lượng',size=64,),
        'product_uom': fields.many2one('product.uom', 'Đơn vị tính'),
        'quycach_donggoi':fields.char('Quy cách đóng gói', size = 64,),
        'manufacturer_product_id': fields.many2one('manufacturer.product','Hãng sản xuất',),
        'product_country_id': fields.many2one('res.country', 'Nước sản xuất'),
        'sodangky_gpnk':fields.char('Số đăng ký, giấy phép nhập khẩu',size=64),
        'product_qty': fields.float('Số lượng', digits_compute= dp.get_precision('Product UoS')),
        'price_unit': fields.float('Đơn giá', digits_compute= dp.get_precision('Product Price')),
        'tax_id': fields.many2many('account.tax', 'hopdong_order_tax', 'hopdong_id', 'tax_id', 'Taxes'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
        'handung_tuoitho':fields.char('Hạn dùng, tuổi thọ', size = 64),
        
        
    }
    
    def onchange_product_id(self, cr, uid, ids,product_id=False, context=None):
        vals = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            vals = {
                    'product_uom':product.uom_id.id or False,
                    'name':product.name,
                    'manufacturer_product_id':product.manufacturer_product_id.id or False,
                    'product_country_id':product.product_country_id.id or False
                    }
        return {'value': vals}
hopdong_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
