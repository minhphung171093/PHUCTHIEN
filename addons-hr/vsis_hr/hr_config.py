# -*- encoding: utf-8 -*-
##############################################################################
#
#    Viet Solution Infomation System, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://vietsolutionis.vn>). All Rights Reserved
#
##############################################################################

from osv import fields, osv
import time
import netsvc
import pooler
import tools
from tools.translate import _
import datetime
import decimal_precision as dp
from tools import config

#===============================================================================
# Employee category
#===============================================================================
class hr_employee_category(osv.osv):
    _inherit = "hr.employee.category"
    _order = "code"
    _columns = {
        'employee_ids': fields.many2many('hr.employee', 'employee_category_rel', 'category_id','emp_id', 'Employees'),
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),        
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_employee_category, self).copy(cr, uid, id, default, context=context)
hr_employee_category()

#===============================================================================
# department
#==============================================================================
class hr_department(osv.osv):
    _inherit = "hr.department"
    _order = "code"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
        'child_ids': fields.one2many('hr.department', 'parent_id', 'Contains'),        
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_department, self).copy(cr, uid, id, default, context=context)
hr_department()

#===============================================================================
# Danh muc qui dinh thai san 
#===============================================================================
class hr_maternity(osv.osv):
    _name = "hr.maternity"
    _order = "date_start desc"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'month': fields.float('Number of months'),
        'hour': fields.float('Working hours'),
        'date_start': fields.date('Date Start', required=True),
        'date_stop': fields.date('Date Stop'),    
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),    
        } 
    _defaults = {
        'active': True,
    }
    def _check_date_start_stop(self,cr,uid,ids,context=None):
        if context == None:
            context = {}
        obj= self.browse(cr, uid, ids[0], context=context)
        date_start = obj.date_start
        date_stop = obj.date_stop
        if date_stop and date_start > date_stop:       
            return False
        return True
     
    _constraints = [
        (_check_date_start_stop, 'Stop date must be greater than start date', ['date_start', 'date_stop']),
    ]
    _sql_constraints = [
        ('name_uniq', 'unique (code)', 'The name must be unique !'),
        ('date_uniq', 'unique (date_start)', 'The record must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        default['date_start'] = time.strftime('%Y-%m-%d')
        default['date_stop'] = False
        return super(hr_maternity, self).copy(cr, uid, id, default, context=context)
hr_maternity()

#===============================================================================
# Danh muc ly do nghi viec 
#===============================================================================
class hr_recruitment_degree(osv.osv):
    _inherit = "hr.recruitment.degree"
    _order = "code"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_recruitment_degree, self).copy(cr, uid, id, default, context=context)
hr_recruitment_degree()

#===============================================================================
# Danh muc ly do nghi viec 
#===============================================================================
class hr_reason(osv.osv):
    _name = "hr.reason"
    _order = "code"
    _description = "reason stop working"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'type': fields.selection([
            ('NH', 'Nghi huu'),
            ('HH', 'Het thoi han HDLD'),
            ('TV', 'Thoi viec truoc thoi han'),
            ('MV', 'Mat viec lam'),
            ('BV', 'Tu y bo viec'),
            ('ST', 'Sa thai do ky luat LD'),
            ('KH', 'Ly do khac'),
            ], 'Type', required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_reason, self).copy(cr, uid, id, default, context=context)
hr_reason()

#===============================================================================
# danh muc loai bhtn
#===============================================================================
class hr_accident_type(osv.osv):
    _name = "hr.accident.type"
    _order = "code"
    _description = "Accident Insurance Type"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [        
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_accident_type, self).copy(cr, uid, id, default, context=context)
hr_accident_type()

#===============================================================================
# danh muc nghe nghiep
#===============================================================================
class hr_function(osv.osv):
    _name = "hr.function"
    _order = "code"
    _description = "function"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [        
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_function, self).copy(cr, uid, id, default, context=context)
hr_function()
#===============================================================================
# danh muc ton giao
#===============================================================================
class hr_religion(osv.osv):
    _name = "hr.religion"
    _order = "code"
    _description = "Religion"
    _columns = {
        'name' : fields.char('Name', 64, required=True),
        'code' : fields.char('Code', 9, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_religion, self).copy(cr, uid, id, default, context=context)
hr_religion()

#===============================================================================
# danh muc dan toc 
#===============================================================================
class hr_ethnic(osv.osv):
    _name = "hr.ethnic"
    _order = "code"
    _description = "Ethnic or Nation"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_ethnic, self).copy(cr, uid, id, default, context=context)
hr_ethnic()

#===============================================================================
# danh muc loai bang cap, chung chi
#===============================================================================
class hr_certification(osv.osv):
    _name = "hr.certification"
    _order = "code"
    _description = "certification"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_certification, self).copy(cr, uid, id, default, context=context)
hr_certification()
#Tại vì trước đây làm major nhằm qua certification nên giờ Hưng làm ngược lại 
class hr_major(osv.osv):
    _name = "hr.major"
    _order = "code"
    _description = "major"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_major, self).copy(cr, uid, id, default, context=context)
hr_major()

#===============================================================================
#danh muc quan he gia dinh 
#===============================================================================
class hr_relation(osv.osv):
    _name = "hr.relation"
    _description = "Family Relationship"
    _order = "code"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_relation, self).copy(cr, uid, id, default, context=context)
hr_relation()
#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
