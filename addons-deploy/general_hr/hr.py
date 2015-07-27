# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime

class hr_employee(osv.osv):
    _inherit = "hr.employee"
    
    _columns = {
        'code': fields.char('Code', size=128),
        'scanner_code': fields.char('Scanner Code', size=128),
        
        'identification_date_issue': fields.date('Identification Date Issue'),
        'identification_place_issue': fields.char('Identification Place Issue', size=128),
        
        # kiet them add danh sach ban hang cho nhan vien
        'emp_sale_ids':fields.many2many('sale.order', 'emp_sale_rel', 'employee_id', 'sale_id', 'List Sale'),
        'times': fields.selection([
            ('dates','Date'),
            ('periods', 'Periods'),
            ('quarter','Quarter'),
            ('years','Years')], 'Periods Type',),
        'period_id': fields.many2one('account.period', 'Period',  domain=[('state','=','draft')],),
        'fiscalyear': fields.many2one('account.fiscalyear', 'Fiscalyear', domain=[('state','=','draft')],),
        'date_start': fields.date('Date Start'),
        'date_end':   fields.date('Date end'),
        'quarter':fields.selection([
            ('1', '1'),
            ('2','2'),
            ('3','3'),
            ('4','4')], 'Quarter'),
         ###########################################################################
    }
    _defaults ={
        'times':'date'
    }
    
    def get_quarter_date(self,year,quarter):
        self.start_date = False
        self.end_date  = False
        if quarter == '1':
            self.start_date = '''%s-01-01'''%(year)
            self.end_date = year + '-03-31'
        elif quarter == '2':
            self.start_date = year+'-04-01'
            self.end_date =year+'-06-30'
        elif quarter == '3':
            self.start_date = year+'-07-01'
            self.end_date = year+'-09-30'
        else:
            self.start_date = year+'-10-01'
            self.end_date = year+'-12-31'
            
    def add_sale_order(self,cr,uid,ids,context=None):
        this = self.browse(cr,uid,ids[0])
        start_date = False
        end_date  = False
        if not this.user_id:
            raise
        if this.times =='periods':
            start_date = this.period_id.date_start
            end_date   = this.period_id.date_stop
        elif this.times == 'years':
            start_date = this.fiscalyear.date_start
            end_date   = this.fiscalyear.date_stop
        elif this.times =='quarter':
            year = this.fiscalyear.name
            if this.quarter == '1':
                start_date = '''%s-01-01'''%(year)
                end_date = year + '-03-31'
            elif this.quarter == '2':
                start_date = year+'-04-01'
                end_date =year+'-06-30'
            elif this.quarter == '3':
                start_date = year+'-07-01'
                end_date = year+'-09-30'
            else:
                start_date = year+'-10-01'
                end_date = year+'-12-31'
        else:
            start_date = this.date_start
            end_date   = this.date_end
            
        sql='''
            SELECT * from sale_order 
                WHERE date_order between '%s' and '%s'
                    and user_id = %s
                    and state not in ('draft','cancel')
                Order by date_order
        '''%(start_date,end_date,this.user_id.id)
        cr.execute(sql)
        sale_ids = [x[0] for x in cr.fetchall()]
        self.write(cr, uid, ids, {'emp_sale_ids': [[6,0,sale_ids]]})
        return 1
    
    def _check_code(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        if obj.code:
            pids = self.search(cr, uid, [('code','=',obj.code),('id','<>',obj.id)])
            if pids:
                raise osv.except_osv(_('Trùng lắp dữ liệu!'), _('Trùng mã nhân viên: %s')%(obj.code))
        if obj.scanner_code:
            pids = self.search(cr, uid, [('scanner_code','=',obj.scanner_code),('id','<>',obj.id)])
            if pids:
                raise osv.except_osv(_('Trùng lắp dữ liệu!'), _('Trùng mã vân tay: %s')%(obj.scanner_code))
        if obj.identification_id:
            pids = self.search(cr, uid, [('identification_id','=',obj.identification_id),('id','<>',obj.id)])
            if pids:
                raise osv.except_osv(_('Trùng lắp dữ liệu!'), _('Trùng Số CMND: %s')%(obj.identification_id))
        return True
 
    _constraints = [
        (_check_code, 'Mã nhân viên bị trùng', ['code']),
    ]
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        ids = []
        if name:
            ids = self.search(cr, user, [('code', operator, name)], limit=limit)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name)], limit=limit)
        if not ids:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = record['code'] + ' ' + name
            res.append((record['id'], name))
        return res
    
hr_employee()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
