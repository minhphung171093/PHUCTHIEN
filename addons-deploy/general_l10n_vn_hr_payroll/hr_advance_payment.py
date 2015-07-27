import datetime
import time
from itertools import groupby
from operator import itemgetter

import math
from openerp import netsvc
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare

class hr_advance_payment(osv.osv):
    _name = "hr.advance.payment"
    
    def _get_user_department(self, cr, uid, ids, field_name, arg, context=None):
        employee_pool = self.pool.get('hr.employee')
        res = {}
        for attendance in self.browse(cr, uid, ids, context=context):
            res[attendance.id] = attendance.employee_id.department_id and attendance.employee_id.department_id.id or False
        return res
    
    _columns ={
               'name':fields.char('Description',size=128),            
               'employee_id':fields.many2one('hr.employee','Employee',required=True, readonly=True, states={'draft': [('readonly', False)]}),
               'date':fields.date('Date',required=True, readonly=True, states={'draft': [('readonly', False)]}),
               'amount':fields.float('Amount', digits=(16,2), required=True, readonly=True, states={'draft': [('readonly', False)]}),
               'currency_id': fields.many2one('res.currency', 'Currency', required=True, readonly=True, states={'draft': [('readonly', False)]}),
               'exchange_rate':fields.float('Exchange Rate', digits=(16,2), required=True, readonly=True, states={'draft': [('readonly', False)]}),
               'user_id': fields.many2one('res.users', 'Created by', required=True, readonly=True, states={'draft': [('readonly', False)]}),
               'approved_by': fields.many2one('res.users', 'Approved by', readonly=True),
               
               'department_id': fields.function(_get_user_department, type='many2one', relation='hr.department', string='Department',
                store={
                    'hr.advance.payment': (lambda self, cr, uid, ids, c={}: ids, ['employee_id'], 10),
                }, readonly=True),
               
               'state': fields.selection([('draft','Draft'),('confirmed','Confirmed'),('cancel','Cancelled')], 'State', readonly=True)
               }
    
    def _get_currency(self, cr, uid, context=None):
        res_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id or False
        return res_id
    
    _defaults = {
        'date': time.strftime(DEFAULT_SERVER_DATE_FORMAT),
        'user_id': lambda obj, cr, uid, context: uid,
        'currency_id': _get_currency,
        'exchange_rate': 1.0,
        'state': 'draft'
    }
    def _check_amount(self, cr, uid, ids,context=None):
        for payment in self.browse(cr, uid, ids, context=context):
            if payment.amount <= 0:
                return False
        return True
    _constraints = [
        (_check_amount,"Amount must be greater than 0",['amount']),
    ]
    
    def action_confirm(self, cr, uid, ids, context=None):
        payslip_pool = self.pool.get('hr.payslip')
        for line in self.browse(cr, uid, ids):
            cr.execute('''
            SELECT id, number, state
            FROM hr_payslip
            WHERE employee_id=%s AND date_to >= '%s' AND date_from <='%s' 
            '''%(line.employee_id.id, line.date, line.date))
            res = cr.fetchall()
            for payslip in res:
                if payslip[2] == 'done':
                    raise osv.except_osv(_('Warning!'),_("Payslip number '%s' has been paid!\n You are not able to confirm this Payment!")%(payslip[1]))
#                 elif payslip[2] != 'cancel':
#                     cr.execute('''
#                     INSERT INTO hr_advance_payment_payslip_rel(payslip_id,payment_id) VALUES(%s,%s)
#                     '''%(payslip[0],line.id))
                    #Thanh: Recompute Related Payslip to update Advanced Amount
            self.write(cr, uid, [line.id], {'state':'confirmed','approved_by':uid})
            if res:
                payslip_pool.compute_sheet(cr, uid, [x[0] for x in res], context)
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        payslip_pool = self.pool.get('hr.payslip')
        for line in self.browse(cr, uid, ids):
            cr.execute('''
            SELECT hp.id, hp.number, hp.state
            FROM hr_advance_payment_payslip_rel app join hr_payslip hp on app.payslip_id = hp.id
            WHERE app.payment_id = %s
            '''%(line.id))
            res = cr.fetchall()
            for payslip in res:
                if payslip[2] == 'done':
                    raise osv.except_osv(_('Warning!'),_("Payslip number '%s' has been paid!\n You are not able to cancel this Payment!")%(res[0][0]))
                elif payslip[2] != 'cancel':
                    cr.execute('''
                    DELETE FROM hr_advance_payment_payslip_rel WHERE payment_id=%s
                    '''%(line.id))
                    #Thanh: Recompute Related Payslip to update Advanced Amount
            self.write(cr, uid, [line.id], {'state':'cancel'})
            if res:
                payslip_pool.compute_sheet(cr, uid, [x[0] for x in res], context)
        return True
    
    def set_to_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft','user_id':uid,'approved_by':False})
        return True
    
    def write(self, cr, uid, ids, vals, context=None):
        comp_currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id or False
        if vals.get('currency_id', False) and vals['currency_id'] == comp_currency_id:
            vals['exchange_rate'] = 1.0
        return super(hr_advance_payment, self).write(cr, uid, ids, vals, context)
    
    def create(self, cr, uid, vals, context=None):
        comp_currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id or False
        if vals.get('currency_id', False) and vals['currency_id'] == comp_currency_id:
            vals['exchange_rate'] = 1.0
        return super(hr_advance_payment, self).create(cr, uid, vals, context)
    
hr_advance_payment()