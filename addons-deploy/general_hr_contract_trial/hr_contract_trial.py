#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

from openerp import netsvc
from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    _description = 'Contract'
    
    _columns = {
        'state': fields.selection([
            ('trial', 'Trial'),
            ('official', 'Official'),
            ('finished', 'Finished'),
            ], 'State', readonly=True),
    }
    
    _defaults ={
        'state': 'official',
    }
    
    def action_official(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'official'})
        return True
    
    def action_finished(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'finished'})
        return True
    
    def write(self, cr, uid, ids, vals, context=None):
        this = self.browse(cr, uid, ids[0])
        if this.state == 'finished':
            vals = {}
        return super(hr_contract, self).write(cr, uid, ids, vals, context)
    
hr_contract()