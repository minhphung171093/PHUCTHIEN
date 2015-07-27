# -*- coding: utf-8 -*-

from osv import fields, osv
from tools.translate import _
import time
from datetime import datetime
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from openerp import netsvc


class bangke_point_of_sale(osv.osv_memory):
    _name = 'bangke.point.of.sale'
    _columns = {
         'from_date': fields.datetime('Từ ngày',required =True),
         'to_date': fields.datetime('Đến ngày',required =True),
         'company_id':fields.many2one('res.company','company'),
         'section_id': fields.many2one('crm.case.section', 'POS Team',),
    }
    
    def _get_default_section_id(self, cr, uid, context=None):
        """ Gives default section by checking if present in the context """
        section_id = self.pool.get('crm.lead')._resolve_section_id_from_context(cr, uid, context=context) or False
        if not section_id:
            section_id = self.pool.get('res.users').browse(cr, uid, uid, context).default_section_id.id or False
        return section_id
    
    _defaults = { 
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'bangke.point.of.sale', context=c),
        'from_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'to_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'section_id': _get_default_section_id,
    }
    def print_bangke(self,cr,uid,ids,context=None):
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'bangke.point.of.sale'
        datas['form'] = self.read(cr, uid, ids)[0]        
        return {'type': 'ir.actions.report.xml', 'report_name': 'bangke_point_of_sale_report' , 'datas': datas}
    
bangke_point_of_sale()



class daonhthu_point_of_sale(osv.osv_memory):
    _name = 'doanhthu.point.of.sale'
    _columns = {
         'from_date': fields.datetime('Từ ngày',required =True),
         'to_date': fields.datetime('Đến ngày',required =True),
         'company_id':fields.many2one('res.company','company'),
         'section_id': fields.many2one('crm.case.section', 'POS Team',required =True),
    }
    
    def _get_default_section_id(self, cr, uid, context=None):
        """ Gives default section by checking if present in the context """
        section_id = self.pool.get('crm.lead')._resolve_section_id_from_context(cr, uid, context=context) or False
        if not section_id:
            section_id = self.pool.get('res.users').browse(cr, uid, uid, context).default_section_id.id or False
        return section_id
    
    _defaults = { 
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'bangke.point.of.sale', context=c),
        'from_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'to_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'section_id': _get_default_section_id,
    }
    def print_bangke(self,cr,uid,ids,context=None):
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'doanhthu.point.of.sale'
        datas['form'] = self.read(cr, uid, ids)[0]        
        return {'type': 'ir.actions.report.xml', 'report_name': 'doanhthu_point_of_sale_report' , 'datas': datas}
    
daonhthu_point_of_sale()