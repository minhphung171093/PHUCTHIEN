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
        'contract_history': fields.one2many('hr.contract.history','contract_id', 'History', readonly=True),
    }
    
    _defaults ={
                }
    
    def write(self, cr, uid, ids, vals, context=None):
        contract_history_pool = self.pool.get('hr.contract.history')
        for line in self.browse(cr, uid, ids):
            contract_history_vals = {}
            if vals.get('name',False) and line.name:
                contract_history_vals.update({'name':line.name or False})
            if vals.get('wage',False) and line.wage:
                contract_history_vals.update({'wage':line.wage or False})
            if vals.get('date_start',False) and line.date_start:
                contract_history_vals.update({'date_start':line.date_start or False})
            if vals.get('date_end',False) and line.date_end:
                contract_history_vals.update({'date_end':line.date_end  or False})
            
            if vals.get('trial_date_start',False) and line.trial_date_start:
                contract_history_vals.update({'trial_date_start':line.trial_date_start or False})
            if vals.get('trial_date_end',False) and line.trial_date_end:
                contract_history_vals.update({'trial_date_end':line.trial_date_end or False})
            
            if contract_history_vals:
                contract_history_vals.update({'contract_id':line.id})
                contract_history_pool.create(cr, uid, contract_history_vals)
        return super(hr_contract, self).write(cr, uid, ids, vals, context)
    
hr_contract()

class hr_contract_history(osv.osv):
    _name = 'hr.contract.history'
    _order = 'create_date desc'
    _columns = {
        'create_date': fields.datetime('Create Date', readonly=True),
        'create_uid': fields.many2one('res.users','Create User', readonly=True),
        
        'name': fields.char('Contract Reference', size=64),
        'wage': fields.float('Wage', digits=(16,2)),
        'date_start': fields.date('Start From'),
        'date_end': fields.date('End To'),
        'trial_date_start': fields.date('Trial From'),
        'trial_date_end': fields.date('Trial To'),
        
        'contract_id': fields.many2one('hr.contract', 'Contract', required=True, ondelete='cascade', select=True),
    }
    
    _defaults = {
    }
    
hr_contract_history()