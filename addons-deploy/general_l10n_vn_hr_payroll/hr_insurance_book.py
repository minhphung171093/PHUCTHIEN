
import datetime
import time
from itertools import groupby
from operator import itemgetter

import math
from openerp import netsvc
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_insurance_book(osv.osv):
    _name = "hr.insurance.book"
    _columns = {
                'name': fields.char('Number', size=128, required=True),
                'issue_date': fields.date('Issue Date', required=True),
                'issue_place': fields.char('Issue Place', size=500, required=True),
                'joining_date': fields.date('Joining Date', required=True),
                'joining_date_at_company': fields.date('Joining Date At Company', required=True),
                'finished_date': fields.date('Finished Date', required=False),
                'state': fields.selection([('draft','Draft')], 'State', required=True),
                'employee_id':fields.many2one('hr.employee', 'Employee', required=True),
                'note': fields.text('Note')
                }
    _defaults = {
        'state': 'draft',
    }
    
hr_insurance_book()