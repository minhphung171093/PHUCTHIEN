# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

import time
from datetime import datetime
from osv import fields, osv
from tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import decimal_precision as dp
from tools.translate import _

class general_ledger_report(osv.osv_memory):
    _name = "general.ledger.report"
    
    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False
            
    _columns = {
        'shop_ids': fields.many2many('sale.shop', 'general_ledger_report_shop_rel', 'wizard_id', 'shop_id', 'Shops', required=True),
        
        'times': fields.selection([
            ('dates','Date'),
            ('periods', 'Periods'),
            ('quarter','Quarter'),
            ('years','Years')], 'Periods Type', required=True ),
        'period_id_start': fields.many2one('account.period', 'Period',  domain=[('state','=','draft')],),
        'period_id_end': fields.many2one('account.period', 'End Period',  domain=[('state','=','draft')],),
        'fiscalyear_start': fields.many2one('account.fiscalyear', 'Fiscalyear', domain=[('state','=','draft')],),
        'fiscalyear_stop': fields.many2one('account.fiscalyear', 'Stop Fiscalyear',  domain=[('state','=','draft')],),
        'date_start': fields.date('Date Start'),
        'date_end':   fields.date('Date end'),
        'quarter':fields.selection([
            ('1', '1'),
            ('2','2'),
            ('3','3'),
            ('4','4')], 'Quarter'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
     }
    
    def _get_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
        
    def _get_shop_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid)
        return [x.id for x in user.shop_ids]
    
    _defaults = {
        'shop_ids': _get_shop_ids,
        'times': 'periods',
        'date_start': time.strftime('%Y-%m-%d'),
        'date_end': time.strftime('%Y-%m-%d'),        
        'period_id_start': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'period_id_end': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],        
        'fiscalyear_start': _get_fiscalyear,
        'fiscalyear_stop': _get_fiscalyear,
        'quarter': '1',
        'company_id': _get_company,
        }
    
    def finance_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'general.ledger.report'
        datas['form'] = self.read(cr, uid, ids)[0]        
        report_name = context['type_report']             
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
    
general_ledger_report()

class account_ledger_report(osv.osv_memory):
    _name = "account.ledger.report"    
    
    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False
            
    _columns = {
        'shop_ids': fields.many2many('sale.shop', 'account_ledger_report_shop_rel', 'wizard_id', 'shop_id', 'Shops', required=True),
        
        'times': fields.selection([
            ('dates','Date'),
            ('periods', 'Periods'),
            ('quarter','Quarter'),
            ('years','Years')], 'Periods Type', required=True ),
        'period_id_start': fields.many2one('account.period', 'Period',  domain=[('state','=','draft')],),
        'period_id_end': fields.many2one('account.period', 'End Period',  domain=[('state','=','draft')],),
        'fiscalyear_start': fields.many2one('account.fiscalyear', 'From Fiscalyear', domain=[('state','=','draft')],),
        'fiscalyear_stop': fields.many2one('account.fiscalyear', 'To Fiscalyear',  domain=[('state','=','draft')],),
        'date_start': fields.date('Date start'),
        'date_end':   fields.date('Date end'),
        'quarter':fields.selection([
            ('1', '1'),
            ('2','2'),
            ('3','3'),
            ('4','4')], 'Quarter'),
        'showdetails':fields.boolean('Get Detail'),
        'account_id': fields.many2one('account.account', 'Account', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
     }
    
    def _get_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    def _get_shop_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid)
        return [x.id for x in user.shop_ids]
    
    _defaults = {
        'shop_ids': _get_shop_ids,
        'times': 'periods',
        'date_start': time.strftime('%Y-%m-%d'),
        'date_end': time.strftime('%Y-%m-%d'),        
        'period_id_start': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'period_id_end': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],        
        'fiscalyear_start': _get_fiscalyear,
        'fiscalyear_stop': _get_fiscalyear,
        'quarter': '1',
        'company_id': _get_company,
        'showdetails':True
        }
    
    def finance_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'account.ledger.report'
        datas['form'] = self.read(cr, uid, ids)[0]    
        this = self.browse(cr,uid,ids[0])
        if this.showdetails:
            report_name = 'account_detail_ledger_report'
        else:
            report_name = 'account_ledger_report'
            
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
    
account_ledger_report()

class report_account_in_out_tax(osv.osv_memory):
    _name = "report.account.in.out.tax"
    
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
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'shop_ids': fields.many2many('sale.shop', 'report_in_out_tax_shop_rel', 'product_id', 'shop_id', 'Shop'),
        'filter_type': fields.selection([
            ('1', 'Hợp lệ'),
            ('2','Tất cả')], 'Hiển thị', required=True ),
     }
    
    def _get_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    _defaults = {
        'filter_type':'1',
        'times': 'periods',
        'date_start': time.strftime('%Y-%m-%d'),
        'date_end': time.strftime('%Y-%m-%d'),
        
        'period_id_start': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'period_id_end': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        
        'fiscalyear_start': _get_fiscalyear,
        'fiscalyear_stop': _get_fiscalyear,
        
        'company_id': _get_company,
        }
    
    
    def finance_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'report.accounting'
        datas['form'] = self.read(cr, uid, ids)[0]
        
        report_name = context['type_report'] 
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
report_account_in_out_tax()

class general_trial_balance(osv.osv_memory):
    _name = "general.trial.balance"    
    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False
    
    def _get_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
     
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
        
        'company_id': fields.many2one('res.company', 'Company', required=True),
     }
        
    _defaults = {
        'times': 'periods',
        'date_start': time.strftime('%Y-%m-%d'),
        'date_end': time.strftime('%Y-%m-%d'),        
        'period_id_start': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'period_id_end': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],        
        'fiscalyear_start': _get_fiscalyear,
        'fiscalyear_stop': _get_fiscalyear,
        
        'company_id': _get_company,
        }
    
    def finance_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'report.accounting'
        datas['form'] = self.read(cr, uid, ids)[0]        
        report_name = context['type_report']             
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
    
general_trial_balance()

class general_balance_sheet(osv.osv_memory):
    _name = "general.balance.sheet"    
    
    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False
    
    def _get_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    _columns = {
        'times': fields.selection([
            ('periods', 'Periods'),
            ('quarter','Quarter'),
            ('years','Years')], 'Periods Type', required=True ),
        'period_id_start': fields.many2one('account.period', 'Period',  domain=[('state','=','draft')],),
        'period_id_end': fields.many2one('account.period', 'End Perirod',  domain=[('state','=','draft')],),
        'fiscalyear_start': fields.many2one('account.fiscalyear', 'Fiscalyear', domain=[('state','=','draft')],),
        'fiscalyear_stop': fields.many2one('account.fiscalyear', 'Stop Fiscalyear',  domain=[('state','=','draft')],),
        'date_start': fields.date('Date Start'),
        'date_end':   fields.date('Date end'),
        'quarter':fields.selection([
            ('1', '1'),
            ('2','2'),
            ('3','3'),
            ('4','4')], 'Quarter'),
                
        'company_id': fields.many2one('res.company', 'Company', required=True),
     }
        
    _defaults = {
        'times': 'periods',
        'date_start': time.strftime('%Y-%m-%d'),
        'date_end': time.strftime('%Y-%m-%d'),        
        'period_id_start': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'period_id_end': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],        
        'fiscalyear_start': _get_fiscalyear,
        'fiscalyear_stop': _get_fiscalyear,
        'quarter': '1',
        
        'company_id': _get_company,
        }
    
    def finance_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'general.balance.sheet'
        datas['form'] = self.read(cr, uid, ids)[0]        
        report_name = context['type_report']             
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
    
general_balance_sheet()

class general_account_profit_loss(osv.osv_memory):
    _name = "general.account.profit.loss"    
    
    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False
    
    def _get_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False
    
    _columns = {
        'times': fields.selection([
            ('periods', 'Periods'),
            ('quarter','Quarter'),
            ('years','Years')], 'Periods Type', required=True ),
        'period_id_start': fields.many2one('account.period', 'Start Period',  domain=[('state','=','draft')],),
        'period_id_end': fields.many2one('account.period', 'End Period',  domain=[('state','=','draft')],),
        'fiscalyear_start': fields.many2one('account.fiscalyear', 'Start Fiscalyear', domain=[('state','=','draft')],),
        'fiscalyear_stop': fields.many2one('account.fiscalyear', 'Stop Fiscalyear',  domain=[('state','=','draft')],),
        'date_start': fields.date('Date Start'),
        'date_end':   fields.date('Date end'),
        'quarter':fields.selection([
            ('1', '1'),
            ('2','2'),
            ('3','3'),
            ('4','4')], 'Quarter'),
        
        'company_id': fields.many2one('res.company', 'Company', required=True),
     }
        
    _defaults = {
        'times': 'periods',
        'date_start': time.strftime('%Y-%m-%d'),
        'date_end': time.strftime('%Y-%m-%d'),        
        'period_id_start': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
        'period_id_end': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],        
        'fiscalyear_start': _get_fiscalyear,
        'fiscalyear_stop': _get_fiscalyear,
        'quarter': '1',
        
        'company_id': _get_company,
        }
    
    def finance_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'general.account.profit.loss'
        datas['form'] = self.read(cr, uid, ids)[0]        
        report_name = context['type_report']             
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
    
general_account_profit_loss()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
