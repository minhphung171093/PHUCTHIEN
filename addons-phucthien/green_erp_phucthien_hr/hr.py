# # -*- coding: utf-8 -*-

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

class tinhtrang_suckhoe(osv.osv):
    _name= 'tinhtrang.suckhoe'
    _columns={
              'name':fields.char('Tình trạng sức khỏe'),
              'date':fields.date('Ngày'),
              'employee_id':fields.many2one('hr.employee','Nhân viên')
              }
    _defaults = {
        'date': fields.datetime.now,
        
        }
tinhtrang_suckhoe()

class hr_family(osv.osv):
    _name = "hr.family"
    _description = "Family"
    _order = "employee_id,name"
    _columns = {
        'name' : fields.char("Tên", size=128, required=True),
        'id_no' : fields.char("ID", size=128),
        'birthday' : fields.date('Ngày sinh'),
        'email' : fields.char('Email', size=64),
        'phone' : fields.char('Số điện thoại', size=32),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'relation': fields.char('Mối quan hệ'),
        'note' : fields.text('Ghi chú'),
        'depend': fields.boolean('Phụ thuộc'),
    } 
hr_family()

class hr_employee(osv.osv):
    _inherit= 'hr.employee'
    
    def _get_depend(self, cr, uid, ids, context):
        result = {}
        for line in self.pool.get('hr.family').browse(cr, uid, ids):
            result[line.employee_id.id] = True
        return result.keys()
    
    def _get_depend_qty(self, cr, uid, ids, field_names, arg, context):
        res = {}
        if not ids:
            return
        family_pool = self.pool.get('hr.family')         
        for line in self.browse(cr, uid, ids):
            depend_ids = family_pool.search(cr, uid, [('employee_id','=',line.id),('depend','=',True)])
            depend_qty = len(depend_ids) 
            res[line.id] = depend_qty
        return res

    _columns={
              'tinhtrang_suckhoe_ids':fields.one2many('tinhtrang.suckhoe','employee_id','Tình trạng sức khỏe'),
              'family_ids': fields.one2many('hr.family', 'employee_id','Người phụ thuộc'),
              'depend_qty': fields.function(_get_depend_qty,
                                      store={'hr.family': (_get_depend, ['depend'], 20),}, 
                                      method=True, type='integer', string='Số người phụ thuộc', readonly=True),    
              'phuongtien_giaohang':fields.char('Phương tiện đi lại'),
              }
hr_employee()

class dinhmuc_congtacphi(osv.osv):
    _name= 'dinhmuc.congtacphi'
    _columns={
              'name':fields.many2one('hr.employee','Nhân viên',required=True),
              'year':fields.integer('Năm',required=True),
              'amount':fields.float('Giá trị',required=True)
              }
dinhmuc_congtacphi()

    
