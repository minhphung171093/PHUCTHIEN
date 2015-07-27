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

class print_report_account(osv.osv_memory):
    _name = "print.report.account"
    _columns = {
        'name': fields.selection([
            ('print_invoice', 'Print Invoice'),
            ('print_bangke_mua','Print bảng kê mua hàng')], 'Name', required=True ),
     }
    
    def print_report(self,cr,uid,ids,context=None):
        
        invoice_ids = False
        if context.get('active_ids'):
            invoice_ids = context['active_ids']
            
        report_name = self.browse(cr,uid,ids[0]).name
        context.update({'report_name':report_name})
        account_obj = self.pool.get('account.invoice')
        return account_obj.print_invoice( cr, uid, invoice_ids, context)
print_report_account()

class print_report_cus(osv.osv_memory):
    _name = "print.report.cus"
    _columns = {
        'name': fields.selection([
            ('print_invoice_cus', 'Print Invoice'),
            ('print_bangke_ban','Print bảng kê bán hàng'),
            ('print_with_set','Print With Sheet'),], 'Name', required=True ),
     }
    
    def print_report(self,cr,uid,ids,context=None):
        type = False
        invoice_ids = False
        account_obj = self.pool.get('account.invoice')
        if context.get('active_ids'):
            invoice_ids = context['active_ids']
        report_name = self.browse(cr,uid,ids[0]).name
        for line in account_obj.browse(cr,uid,invoice_ids):
            type = line.type
        
        
        if type =='out_refund' and report_name =='print_with_set':
            report_name = 'vt_with_seet_refund'
        context.update({'report_name':report_name})
        
        return account_obj.print_invoice( cr, uid, invoice_ids, context)
    
print_report_cus()

# # class report_accounting(osv.osv_memory):
# #     _name = "report.accounting"
# #     
# #     def _get_fiscalyear(self, cr, uid, context=None):
# #         now = time.strftime('%Y-%m-%d')
# #         fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
# #         return fiscalyears and fiscalyears[0] or False
# #     
# #     _columns = {
# #         'times': fields.selection([
# #             ('periods', 'Periods'),
# #             ('dates','Dates'),
# #             ('years','Years')], 'Time', required=True ),
# #         'language':fields.selection([
# #             ('vn', 'Vietnamese'),
# #             ('en','English')], 'Language', required=True ),
# #         'state_entries':fields.selection([
# #             ('post', 'All Posted Entries'),
# #             ('all','All Entries')], 'Target Moves', required=True ),
# #         'account_id': fields.many2one('account.account', 'Account',  domain=[('type','<>','view')]),
# #         'period_id_start': fields.many2one('account.period', 'Start Period',  domain=[('state','=','draft')],),
# #         'period_id_end': fields.many2one('account.period', 'End Period',  domain=[('state','=','draft')],),
# #         'fiscalyear_start': fields.many2one('account.fiscalyear', 'Start Fiscalyear', domain=[('state','=','draft')],),
# #         'fiscalyear_stop': fields.many2one('account.fiscalyear', 'Stop Fiscalyear',  domain=[('state','=','draft')],),
# #         'date_start': fields.date('Date Start'),
# #         'date_end':   fields.date('Date end'),
# #         'type':fields.selection([
# #             ('pdf', 'PDF'),
# #             ('nomal','Nomal')], 'Type Print', required=True ),
# #      }
# #     _defaults = {
# #         'times': 'periods',
# #         'language':'vn',
# #         'state_entries':'post',
# #         'type':'nomal',
# #         
# #         'date_start': time.strftime('%Y-%m-%d'),
# #         'date_end': time.strftime('%Y-%m-%d'),
# #         
# #         'period_id_start': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
# #         'period_id_end': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
# #         
# #         'fiscalyear_start': _get_fiscalyear,
# #         'fiscalyear_stop': _get_fiscalyear,
# #         }
# #     
# #     def finance_report(self, cr, uid, ids, context=None): 
# #         datas = {'ids': context.get('active_ids', [])}
# #         datas['model'] = 'report.accounting'
# #         datas['form'] = self.read(cr, uid, ids)[0]
# #         
# #         report_name = context['type_report'] 
# #         if datas['form']['language'] == 'en':
# #             report_name = report_name + '_en'
# #         if datas['form']['type'] == 'pdf':
# #             report_name = report_name + '_pdf'
# #             
# #         return {'type': 'ir.actions.report.xml', 'report_name': report_name , 'datas': datas}
#     
# report_accounting()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
