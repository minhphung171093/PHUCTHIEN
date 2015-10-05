# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import fields, osv
from tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import decimal_precision as dp
from tools.translate import _

class general_aged_partner_balance(osv.osv_memory):
    
    def get_account_combo (self,cr,uid,context=None):  
        result = []
        sql ='''
            select id ,code || '-' || name from account_account where code in (
            select distinct code from fn_get_account_liability()) 
            order by code
        '''
        cr.execute(sql)
        vouchers = cr.fetchall()
        for line in vouchers:
            result.append((line[0], line[1]))   
        return result
    
    def _get_fiscalyear(self, cr, uid, context=None):
        
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False
    
    _name = "general.aged.partner.balance"
    _columns = {
        'times': fields.selection([
            ('periods', 'Periods'),
            ('dates','Dates'),
            ('years','Years')], 'Time', required=True ),
        'partner_id': fields.many2one('res.partner','Partner'),
        'date_start':fields.date('Start Date'),
        'date_end' :fields.date('End date'),
        'check':fields.boolean('Clearing'),
#         'warehouse_id':fields.many2one('stock.warehouse','Warehouse'),
        'period_id_start': fields.many2one('account.period', 'Start Period',  domain=[('state','=','draft')],),
        'period_id_end': fields.many2one('account.period', 'End Perirod',  domain=[('state','=','draft')],),
        'fiscalyear_start': fields.many2one('account.fiscalyear', 'Start Fiscalyear', domain=[('state','=','draft')],),
        'fiscalyear_stop': fields.many2one('account.fiscalyear', 'Stop Fiscalyear',  domain=[('state','=','draft')],),
        'type': fields.selection([
            ('open', 'Open'),
            ('paid','Paid')], 'Type'),
        'account_id': fields.selection(get_account_combo, 'Account',required=True),
        
        'period_length':fields.integer('Period Length (days)', required=True),
        'direction_selection': fields.selection([('Past','Past'),
                                                 ('Future','Future')],
                                                 'Direction', required=True),
                
        'company_id': fields.many2one('res.company', 'Company', required=True),
     }
    
    def _get_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    _defaults = {
        'period_length': 30,
        'direction_selection': 'Past',
        
        'date_start': time.strftime('%Y-%m-%d'),
        'date_end': time.strftime('%Y-%m-%d'),
        
        'period_id_start': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'period_id_end': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'fiscalyear_start': _get_fiscalyear,
        'fiscalyear_stop': _get_fiscalyear,
        'times': 'dates',
        'company_id': _get_company,
        }
    
    
    def print_report(self,cr,uid,ids,context=None):
        res = {}
        data = {'ids': context.get('active_ids', [])}
        data['model'] = 'general.aged.partner.balance'
        data['form'] = self.read(cr, uid, ids)[0]
        
        period_length = data['form']['period_length']
        if period_length<=0:
            raise osv.except_osv(_('User Error!'), _('You must set a period length greater than 0.'))
        if not data['form']['date_start']:
            raise osv.except_osv(_('User Error!'), _('You must set a start date.'))

        start = datetime.strptime(data['form']['date_start'], "%Y-%m-%d")

        if data['form']['direction_selection'] == 'past':
            for i in range(5)[::-1]:
                stop = start - relativedelta(days=period_length)
                res[str(i)] = {
                    'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
                start = stop - relativedelta(days=1)
        else:
            for i in range(5):
                stop = start + relativedelta(days=period_length)
                res[str(5-(i+1))] = {
                    'name': (i!=4 and str((i) * period_length)+'-' + str((i+1) * period_length) or ('+'+str(4 * period_length))),
                    'start': start.strftime('%Y-%m-%d'),
                    'stop': (i!=4 and stop.strftime('%Y-%m-%d') or False),
                }
                start = stop + relativedelta(days=1)
        data['form'].update(res)
        
        report_name = context['type_report'] 
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': data}
    
general_aged_partner_balance()

class general_report_partner_ledger(osv.osv_memory):
    _name = "general.report.partner.ledger"
    
    def get_account_combo (self,cr,uid,context=None):  
        result = []
        sql ='''
            select id ,code || '-' || name from account_account where code in (
            select distinct code from fn_get_account_liability()) 
            order by code
        '''
        cr.execute(sql)
        vouchers = cr.fetchall()
        for line in vouchers:
            result.append((line[0], line[1]))   
        return result
    
    
    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False
    
    _columns = {
        'times': fields.selection([
            ('periods', 'Periods'),
            ('dates','Dates'),
            ('years','Years')], 'Time', required=True ),
        'account_id': fields.many2one('account.account', 'Account',required=True, domain=[('type','in',('payable','receivable'))]),
        'period_id_start': fields.many2one('account.period', 'Start Period',  domain=[('state','=','draft')],),
        'period_id_end': fields.many2one('account.period', 'End Period',  domain=[('state','=','draft')],),
        'fiscalyear_start': fields.many2one('account.fiscalyear', 'Start Fiscalyear', domain=[('state','=','draft')],),
        'fiscalyear_stop': fields.many2one('account.fiscalyear', 'Stop Fiscalyear',  domain=[('state','=','draft')],),
        'date_start': fields.date('Date Start'),
        'date_end':   fields.date('Date end'),
        'partner_id':fields.many2one('res.partner','Partner',required=True, domain="[]"),
        #'account_id': fields.many2one('account.account', 'Account',required=True, domain=[('type','in',('payable','receivable'))]),
        'account_id': fields.selection(get_account_combo, 'Account',required=True),
        
        'company_id': fields.many2one('res.company', 'Company', required=True),
     }
    
    def _get_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    _defaults = {
        #'report_type':'payable',
        'times': 'periods',
        'date_start': time.strftime('%Y-%m-%d'),
        'date_end': time.strftime('%Y-%m-%d'),
        
        'period_id_start': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'period_id_end': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'fiscalyear_start': _get_fiscalyear,
        'fiscalyear_stop': _get_fiscalyear,
        'company_id': _get_company
        }
    
    def onchange_account(self,cr,uid,ids,report_type):
        dom = {}
        value = {}
        account_obj = self.pool.get('account.account')
        if report_type:
            acc_ids = account_obj.search(cr,uid,[('type','=',report_type)])
            if acc_ids:
                value ={'account_id':acc_ids}
                
        return {'value':value}
    def print_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'general.report.partner.ledger'
        datas['form'] = self.read(cr, uid, ids)[0]
        
        report_name = context['type_report'] 
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}

general_report_partner_ledger()

class general_report_partner_ledger_detail(osv.osv_memory):
    _name = "general.report.partner.ledger.detail"
    
    def get_account_combo (self,cr,uid,context=None):  
        result = []
        sql ='''
            select id ,code || '-' || name from account_account where code in (
            select distinct code from fn_get_account_liability()) 
            order by code
        '''
        cr.execute(sql)
        vouchers = cr.fetchall()
        for line in vouchers:
            result.append((line[0], line[1]))   
        return result
    
    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False
    
    _columns = {
        'times': fields.selection([
            ('periods', 'Periods'),
            ('dates','Dates'),
            ('years','Years')], 'Time', required=True ),
        
        'period_id_start': fields.many2one('account.period', 'Start Period',  domain=[('state','=','draft')],),
        'period_id_end': fields.many2one('account.period', 'End Period',  domain=[('state','=','draft')],),
        'fiscalyear_start': fields.many2one('account.fiscalyear', 'Start Fiscalyear', domain=[('state','=','draft')],),
        'fiscalyear_stop': fields.many2one('account.fiscalyear', 'Stop Fiscalyear',  domain=[('state','=','draft')],),
        'date_start': fields.date('Date Start'),
        'date_end':   fields.date('Date end'),
        #'account_id': fields.many2one('account.account', 'Account',domain=[('type','in',('receivable','payable'))],required=True),
        'account_id': fields.selection(get_account_combo, 'Account',required=True),
        
        'company_id': fields.many2one('res.company', 'Company', required=True),
     }
    
    def _get_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    _defaults = {
        'times': 'periods',
        'date_start': time.strftime('%Y-%m-%d'),
        'date_end': time.strftime('%Y-%m-%d'),
        
        'period_id_start': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'period_id_end': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        
        'fiscalyear_start': _get_fiscalyear,
        'fiscalyear_stop': _get_fiscalyear,
        
        'company_id': _get_company
        }
    
    
    def print_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'general.report.partner.ledger.detail'
        datas['form'] = self.read(cr, uid, ids)[0]
        
        report_name = context['type_report'] 
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}

general_report_partner_ledger_detail()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
