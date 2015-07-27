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

class depreciation_asset(osv.osv_memory):
    _name = "depreciation.asset"    
            
    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False
    
    _columns = {
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
        }
    
    def print_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'depreciation.asset'
        datas['form'] = self.read(cr, uid, ids)[0]        
        report_name = context['type_report']             
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
    
depreciation_asset()

class list_of_asset(osv.osv_memory):
    _name = "list.of.asset"    
            
    _columns = {
        'date_start': fields.date('Date Start'),
        'date_end':   fields.date('Date end'),
        'asset_type':fields.selection([
                                ('asset', 'Asset'),
                                ('prepaid', 'Prepaid Expense'),
                                ], 'Asset Type',size=32, required=True),
     }
        
    _defaults = {
        'date_start': time.strftime('%Y-%m-%d'),
        'date_end': time.strftime('%Y-%m-%d'),
        
        'asset_type': 'asset', 
        }
    
    def print_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'list.of.asset'
        datas['form'] = self.read(cr, uid, ids)[0]        
        report_name = context['type_report']             
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
    
list_of_asset()

class expense_allocation(osv.osv_memory):
    _name = "expense.allocation"    
    
    
    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False

    _columns = {
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
        'type':fields.selection([
                                ('short term', 'Short term'),
                                ('long term', 'Long term'),
                                ], 'Type',size=32, required=True),
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
        'type':'short term'
        }
    
    def print_report(self, cr, uid, ids, context=None): 
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'expense.allocation'
        datas['form'] = self.read(cr, uid, ids)[0]        
        report_name = context['type_report']             
        return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
expense_allocation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
