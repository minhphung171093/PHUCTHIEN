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

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    _columns={
              'basic': fields.float('Basic', digits=(16,2), required=True, help="Basic Salary of the employee"),
              'responsibility': fields.float('Responsibility', digits=(16,2), required=True, help="Responsibility Salary of the employee"),
              'travel_allowance': fields.float('Travel Allowance', digits=(16,2), required=True, help="Travel Allowance of the employee"),
              'phone_allowance': fields.float('Phone Allowance', digits=(16,2), required=True, help="Phone Allowance of the employee"),
              'loai_hd_id':fields.many2one('loai.hd','Loại HĐ'),
              }
hr_contract()

class loai_hd(osv.osv):
    _name = "loai.hd"    
    _columns = {
        'name' : fields.char('Loại HĐ', 128, required=True),
        }         
    
loai_hd()
    
