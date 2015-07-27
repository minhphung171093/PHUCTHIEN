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
from openerp import SUPERUSER_ID

class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    
    _columns = {
        'description': fields.text('Description'),
        'ngay_gui':fields.date('Ngày gửi'),
        'ngay_nhan':fields.date('Ngày nhận lại'),
        'daidien_khachhang':fields.char('Đại diện khách hàng nhận'),
        'nguoi_giao_hang':fields.char('Người giao hàng'),
        'state_receive':fields.selection([('draft','Tạo mới'),('da_gui','Đã gửi'),('da_nhan','Đã nhận')],'Trạng thái',required=True),
    }
    _defaults = {
                 'state_receive':'draft',
                 }
    
    def status_send(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'ngay_gui':datetime.now().strftime('%Y-%m-%d'),'state_receive':'da_gui'})
    
    def status_receive(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'ngay_nhan':datetime.now().strftime('%Y-%m-%d'),'state_receive':'da_nhan'})
    
    def status_refresh(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state_receive':'draft'})
     
    def print_report(self, cr, uid, ids, context=None):
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'phieu_xuat_kho_report',
            }
        
stock_picking_out()

class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'
    
    _columns = {
        'description': fields.text('Description'),
        'nhiet_do':fields.char('Nhiệt độ'),
        'so_luong_thung':fields.char('Số lượng thùng'),
        'time_nhan':fields.datetime('Thời gian nhận'),
        'time_ketthuc':fields.datetime('Thời gian kết thúc'),
        'sampham_lanh':fields.boolean('Sản phẩm lạnh'),
    }
     
        
stock_picking_in()


class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    
    _columns = {
        'picking_packaging_line': fields.one2many('stock.picking.packaging','picking_id','Đóng gói'),
        'description': fields.text('Description'),
        'ngay_gui':fields.date('Ngày gửi'),
        'ngay_nhan':fields.date('Ngày nhận lại'),
        'daidien_khachhang':fields.char('Đại diện khách hàng nhận'),
        'nguoi_giao_hang':fields.char('Người giao hàng'),
        'state_receive':fields.selection([('draft','Tạo mới'),('da_gui','Đã gửi'),('da_nhan','Đã nhận')],'Trạng thái',required=True),
        'nhiet_do':fields.char('Nhiệt độ'),
        'so_luong_thung':fields.char('Số lượng thùng'),
        'time_nhan':fields.datetime('Thời gian nhận'),
        'time_ketthuc':fields.datetime('Thời gian kết thúc'),
        'sampham_lanh':fields.boolean('Sản phẩm lạnh'),
        
    }
    _defaults = {
                 'state_receive':'draft',
                 }
    
    def onchange_journal(self, cr, uid, ids, stock_journal_id):
        value ={}
        domain = {}
        if not stock_journal_id:
            value.update({'location_id':False,
                           'location_dest_id':False})
            domain.update({'location_id':[('id','=',False)],
                           'location_dest_id':[('id','=',False)]})
        else:
            journal = self.pool.get('stock.journal').browse(cr, uid, stock_journal_id)
            from_location_ids = [x.id for x in journal.from_location_id]
            to_location_ids = [x.id for x in journal.to_location_id]
            domain.update({'location_id':[('id','=',from_location_ids)],
                           'location_dest_id':[('id','=',to_location_ids)]})
            location_choxuly_ids = self.pool.get('stock.location').search(cr, 1, [('name','=','Kho Chờ Xử Lý')])
            location_id = False
            for loca_id in from_location_ids:
                if loca_id not in location_choxuly_ids:
                     location_id = loca_id
                     break
            location_dest_id = False
            if to_location_ids and to_location_ids[0] != location_id:
                location_dest_id = to_location_ids[0]
            value.update({'location_id':location_id,
                          'location_dest_id': location_dest_id})
        return {'value': value,'domain':domain}
    
    def status_send(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'ngay_gui':datetime.now().strftime('%Y-%m-%d'),'state_receive':'da_gui'})
    
    def status_receive(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'ngay_nhan':datetime.now().strftime('%Y-%m-%d'),'state_receive':'da_nhan'})
    
    def status_refresh(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state_receive':'draft'})
    
    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        """ Builds the dict containing the values for the invoice
            @param picking: picking object
            @param partner: object of the partner to invoice
            @param inv_type: type of the invoice ('out_invoice', 'in_invoice', ...)
            @param journal_id: ID of the accounting journal
            @return: dict that will be used to create the invoice object
        """
        
        payment_mode_id = False
        if isinstance(partner, int):
            partner = self.pool.get('res.partner').browse(cr, uid, partner, context=context)
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable.id
            payment_term = partner.property_payment_term.id or False
            payment_mode_id = picking.sale_id and picking.sale_id.payment_mode_id and picking.sale_id.payment_mode_id.id or False
        else:
            account_id = partner.property_account_payable.id
            payment_term = partner.property_supplier_payment_term.id or False
        comment = self._get_comment_invoice(cr, uid, picking)
        warehouse_id = picking.location_id.warehouse_id.id or False
        if not warehouse_id:
            warehouse_id = picking.location_dest_id.warehouse_id.id or False
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('warehouse_id','=',warehouse_id)])
        invoice_vals = {
            'name': picking.name,
            'origin': (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
            'type': inv_type,
            'account_id': account_id,
            'partner_id': partner.id,
            'comment': comment,
            'payment_term': payment_term,
            'fiscal_position': partner.property_account_position.id,
            'date_invoice': context.get('date_inv', False),
            'company_id': picking.company_id.id,
            'user_id': uid,
            'user_id': uid,
            'hop_dong_nt_id': picking.sale_id and picking.sale_id.hop_dong_nt_id and picking.sale_id.hop_dong_nt_id.id or False,
            'hop_dong_t_id': picking.sale_id and picking.sale_id.hop_dong_t_id and picking.sale_id.hop_dong_t_id.id or False,
            'payment_mode_id':payment_mode_id,
            'shop_id': shop_ids and shop_ids[0] or False,
        }
        cur_id = self.get_currency_id(cr, uid, picking)
        if cur_id:
            invoice_vals['currency_id'] = cur_id
        if journal_id:
            invoice_vals['journal_id'] = journal_id
        return invoice_vals
    
        
stock_picking()

class stock_picking_packaging(osv.osv):
    _name = 'stock.picking.packaging'
    
    _columns = {
        'picking_id':fields.many2one('stock.picking', string='Đóng gói'),
        'loai_thung_id': fields.many2one('loai.thung', string='Loại thùng'),
        'sl_thung': fields.integer('Số lượng thùng'),
        'sl_da': fields.float('Số lượng đá'),
        'chi_phi_da': fields.float('Chi phí đá'),
        'employee_id': fields.many2one('hr.employee','Nhân viên đóng gói'),
    }
    
stock_picking_packaging()

class loai_thung(osv.osv):
    _name = 'loai.thung'
    
    _columns = {
        'name': fields.char('Tên lại thùng',required=True),
        'the_tich': fields.float('Thể tích',required=True),
        'kich_thuoc':fields.float('Kích thước thùng'),
        'sl_da':fields.float('Số lượng đá'),
        'chi_phi_da':fields.float('Chi phí đá'),
        
    }
    
    
loai_thung()

class dulieu_donghang(osv.osv):
    _name = 'dulieu.donghang'
    
    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            seq_obj_name =  self._name
            vals['name'] = self.pool.get('ir.sequence').get(cr, user, seq_obj_name)
        new_id = super(dulieu_donghang, self).create(cr, user, vals, context)
        return new_id
    
    def status_send(self, cr, uid, ids, context=None):
        for id in self.browse(cr,uid,ids):
            for line in id.dulieu_donghang_line:
                self.pool.get('stock.picking.packaging').create(cr, uid,{'picking_id':id.picking_id.id,'loai_thung_id':line.loai_thung_id.id,'sl_thung':line.sl_thung,'sl_da':line.sl_da,'chi_phi_da':line.chi_phi_da,'employee_id':uid}, context=context)
        return self.write(cr, uid, ids, {'ngay_gui':datetime.now().strftime('%Y-%m-%d'),'state':'da_gui'})
    
    def status_receive(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'ngay_nhan':datetime.now().strftime('%Y-%m-%d'),'state':'da_nhan'})
    
    _columns = {
        'name':fields.char('Số',required= True),
        'picking_id':fields.many2one('stock.picking.out','Phiếu xuất hàng',domain="['&',('type','=','out'),('state','=','done')]",required= True),
        'partner_id': fields.many2one('res.partner', string='Khách hàng',required= True),
        'saleperson_id':fields.many2one('res.users', 'Nhân viên kinh doanh',required= True),
        'daidien_khachhang':fields.char('Đại diện khách hàng nhận'),
        'dulieu_donghang_line':fields.one2many('dulieu.donghang.line','dulieu_donghang_id','Quy cách đóng gói'),
        'sl_nhietke': fields.integer('Số lượng nhiệt kế'),
        'chi_phi_nhiet_ke': fields.float('Chi phí nhiệt kế'),
        'chi_phi_gui_hang': fields.float('Chi phí gửi hàng'),
        'ngay_gui':fields.date('Ngày gửi'),
        'ngay_nhan':fields.date('Ngày nhận lại'),
        'state':fields.selection([('draft','Tạo mới'),('da_gui','Đã gửi'),('da_nhan','Đã nhận')],'Trạng thái',required=True),
        'shipper_id':fields.many2one('res.users', 'Nhân viên giao hàng'),
        'so_phap_ly':fields.boolean('Sổ pháp lý'),
    }
    _defaults = {
                 'name':lambda self, cr, uid, context: '/',
                 'state':'draft',
                 }
    
    def onchange_picking_id(self, cr, uid, ids,picking_id=False, context=None):
        res = {'value':{
                        'partner_id':False,
                        'saleperson_id':False,
                        'dulieu_donghang_line':[],
                      }
               }
        if picking_id:
            picking = self.pool.get('stock.picking').browse(cr, uid, picking_id)
            sale_ids = self.pool.get('sale.order').search(cr,uid,[('name','=',picking.origin)], context=context)
            sale_id = self.pool.get('sale.order').browse(cr, uid, sale_ids[0])
            res['value'].update({
                                'partner_id':sale_id.partner_id.id or False,
                                'saleperson_id':sale_id.user_id.id or False,
                                })
            dulieu_donghang_line =[]
            the_tich = 0
            chi_phi_da = 0
            loai_thung_id = False
            for move in picking.move_lines:
                the_tich += move.product_id.volume*move.product_qty
            loai_thung_obj = self.pool.get('loai.thung')
            sql_1 = '''
                select max(the_tich) from loai_thung
            '''
            cr.execute(sql_1)
            max_thetich = [row[0] for row in cr.fetchall()]
            so_thung = int(the_tich/max_thetich[0])
            sql_2 = '''
                select id from loai_thung where the_tich = %s
            '''%(max_thetich[0])
            cr.execute(sql_2)
            thung_max_id = [row[0] for row in cr.fetchall()]
            for thung_max_id in loai_thung_obj.browse(cr,uid,thung_max_id):
                if so_thung >=1:
                    dulieu_donghang_line.append({
                                                'loai_thung_id':thung_max_id.id or False,
                                                'sl_thung':so_thung or 0,
                                                'sl_da':so_thung*thung_max_id.sl_da or 0,
                                                'chi_phi_da':so_thung*thung_max_id.chi_phi_da or 0,
                                                })
            so_du = the_tich % max_thetich[0]
            sql_chon_thung = '''
                select id,the_tich from loai_thung
            '''
            cr.execute(sql_chon_thung)
            kq = cr.fetchall()        
            for data in kq:
                if so_du <= data[1]:
                    loai_thung_id = data[0]
                    loai_thung_id = loai_thung_obj.browse(cr,uid,loai_thung_id)
                    chi_phi_da = so_thung*loai_thung_id.chi_phi_da
                    dulieu_donghang_line.append({
                                            'loai_thung_id':loai_thung_id.id or False,
                                            'sl_thung':1,
                                            'sl_da':loai_thung_id.sl_da or 0,
                                            'chi_phi_da':1*loai_thung_id.chi_phi_da or 0,
                                            })
                    break
            res['value'].update({
                        'dulieu_donghang_line': dulieu_donghang_line,
            })
            
        return res
    
dulieu_donghang()

class dulieu_donghang_line(osv.osv):
    _name = 'dulieu.donghang.line'
    
    _columns = {
        'dulieu_donghang_id':fields.many2one('dulieu.donghang', string='Dữ liệu đóng hàng'),
        'loai_thung_id': fields.many2one('loai.thung', string='Loại thùng'),
        'sl_thung': fields.integer('Số lượng thùng'),
        'sl_da': fields.float('Số lượng đá'),
        'chi_phi_da': fields.float('Chi phí đá'),
        
    }
    
    
dulieu_donghang_line()

class stock_location(osv.osv):
    _inherit = "stock.location"
     
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context=context)
     
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if not args:
            args = []
        stock_journal_pool = self.pool.get('stock.journal')
        if context.has_key('stock_journal_id') and context.get('phucthien_search_khochoxuly_formanager',False):
            if not context['stock_journal_id']:
                #args += [('id', 'in', [])] 
                return super(stock_location, self).search(cr, uid, args, offset, limit, order, context=context, count=count)
            else:
                group_obj = self.pool.get('res.groups')
                group_manager_model, group_manager_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'group_stock_manager')
                group_manger = group_obj.browse(cr, uid, group_manager_id)
                group_user_model, group_user_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'group_stock_user')
                group_user = group_obj.browse(cr, uid, group_user_id)
                location_choxuly_ids = self.search(cr, 1, [('name','=','Kho Chờ Xử Lý')])
                location_ids = []
                stock_journal_obj = stock_journal_pool.browse(cr, uid, context['stock_journal_id'])
                manger_user_ids = [user.id for user in group_manger.users]
                if context.get('location_id') and context['location_id'] =='location':
                    for location in stock_journal_obj.from_location_id:
                        if location_choxuly_ids and location_choxuly_ids[0] == location.id and uid in manger_user_ids:
                            location_ids.append(location.id)
                        if not location_choxuly_ids:
                            location_ids.append(location.id)
                        if location_choxuly_ids and location_choxuly_ids[0] != location.id:
                            location_ids.append(location.id)
                if context.get('location_dest_id') and context['location_dest_id'] =='location_dest':
                    for location in stock_journal_obj.to_location_id:
                        location_ids.append(location.id) 
                #l ocation_ids = super(stock_location, self).search(cr, uid, [('id','child_of',warehouse_obj.lot_stock_id.location_id.id),('inventory_type','=','SubInventory')])
                args += [('id', 'in', location_ids)]
        return super(stock_location, self).search(cr, uid, args, offset, limit, order, context=context, count=count)
stock_location()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
