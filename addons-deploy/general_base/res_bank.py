# -*- coding: utf-8 -*-
# #############################################################################
# 
# #############################################################################
from osv import fields, osv
from tools.translate import _

import xlrd
from openerp import SUPERUSER_ID

import os
from openerp import modules
base_path = os.path.dirname(modules.get_module_path('general_base'))

class res_bank(osv.osv):
    _inherit = 'res.bank'
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
            #Thanh: Search by BIC (Vietcombank,...)
            if not ids:
                ids = self.search(cr, uid, [('bic', operator, name)] + args, limit=limit, context=context)
            #Thanh: Search by BIC (Vietcombank,...)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)
    
    _columns = {
    }
    
    def _check_bic(self, cr, uid, ids, context=None):
        bank = self.browse(cr, uid, ids[0], context=context)
        if bank.bic:
            e_ids = self.search(cr, uid, [('id','!=',bank.id),('bic','=',bank.bic)])
            if e_ids:
                raise osv.except_osv(_('Duplicate Bank!'),_("BIC '%s' is already exist for Bank '%s'!")%(bank.bic,self.browse(cr, uid, e_ids[0], context=context).name))
        return True
 
    _constraints = [
        (_check_bic, "BIC is already exist", ['bic']),
    ]
    
    def init(self, cr):
        wb = xlrd.open_workbook(base_path + '/general_base/data/res_bank.xls')
        wb.sheet_names()
        sh = wb.sheet_by_index(0)
        
        i = -1
        for rownum in range(sh.nrows):
            i += 1
            row_values = sh.row_values(rownum)
            
            if i == 0:
                continue
            
            try:
                cr.execute('''
                INSERT INTO res_bank(name,bic,active)
                SELECT '%s','%s',True
                WHERE not exists (select id from res_bank where name='%s' or bic='%s')
                '''%(row_values[0],
                     row_values[1],
                     row_values[0],
                     row_values[1]))
                cr.execute('commit;')
            except Exception, e:
                continue
        return True
    
res_bank()

class res_partner_bank_type(osv.osv):
    _inherit = 'res.partner.bank.type'
    
    _columns = {
    }
    
#     def _check_bic(self, cr, uid, ids, context=None):
#         bank = self.browse(cr, uid, ids[0], context=context)
#         if bank.bic:
#             e_ids = self.search(cr, uid, [('id','!=',bank.id),('bic','=',bank.bic)])
#             if e_ids:
#                 raise osv.except_osv(_('Duplicate Bank!'),_("BIC '%s' is already exist for Bank '%s'!")%(bank.bic,self.browse(cr, uid, e_ids[0], context=context).name))
#         return True
#  
#     _constraints = [
#         (_check_bic, "BIC is already exist", ['bic']),
#     ]
    
    def init(self, cr):
        wb = xlrd.open_workbook(base_path + '/general_base/data/res_partner_bank_type.xls')
        wb.sheet_names()
        sh = wb.sheet_by_index(0)
        
        i = -1
        for rownum in range(sh.nrows):
            i += 1
            row_values = sh.row_values(rownum)
            
            if i == 0:
                continue
            
            try:
                cr.execute('''
                INSERT INTO res_partner_bank_type(name,code,format_layout)
                SELECT '%s','%s','%s'
                WHERE not exists (select id from res_partner_bank_type where name='%s' or code='%s')
                '''%(row_values[0],
                     row_values[1],
                     row_values[2],
                     row_values[0],
                     row_values[1]))
                cr.execute('commit;')
            except Exception, e:
                continue
        return True
    
res_partner_bank_type()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
