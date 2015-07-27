# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
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

class hr_holidays_status(osv.osv):
    _inherit = "hr.holidays.status"
    _columns = {
        'des': fields.char('Description', size=64, required=True),
    }
hr_holidays_status()    
#===============================================================================
# department
#==============================================================================
class hr_department(osv.osv):
    _inherit = "hr.department"
    _columns = {
        'rule_cate_ids': fields.many2many('hr.salary.rule.category',
            'department_rule_cate_rel', 'cate_id','department_id',
            ' Rule Categories'),
                
    }
hr_department()
#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
