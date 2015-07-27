# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

import time

import openerp
from openerp.osv import osv, fields
from openerp.tools.translate import _

class ir_sequence(osv.osv):
    _inherit = 'ir.sequence'
    _order = 'code'
    _columns = {
        'date_get': fields.selection([('1', 'System Date'), 
                                       ('2', 'Transact Date')], 'Date Get', size=16),
        'split_number': fields.boolean('Split number'),
        'rollback_rule': fields.selection(
                                          [('None', 'None'), 
                                           ('Daily', 'Daily'),
                                           ('Monthly', 'Monthly'),
                                           ('Yearly', 'Yearly'),],
                                          'Rollback Rule', size=16),
        'barcode_seq': fields.boolean('Create Barcode'),
        'sequence_his': fields.one2many('ir.sequence.his', 'seq_id', 'Sequence Histories', readonly=True),
    }
    _defaults = {
        'date_get': '1',
        'split_number': False,
        'rollback_rule': 'Yearly',
    }
    
    #Thanh: Add more Fields to sequence
    def _interpolation_dict_extend(self, cr, uid, obj_ids):
        def get_shop_code(id):
            if (id is None):
                return ''
            
            try:
                cr.execute("Select code from sale_shop where id = %s"%(id))
                res = cr.fetchone()
                return res and res[0] or ''
            except:
                return ''
        
        def get_pos_code(id):
            if (id is None):
                return ''
                
            try:
                cr.execute("Select code from pos_config where id = %s"%(id))
                res = cr.fetchone()
                return res and res[0] or ''
            except:
                return None
        
        def get_warehouse_code(id):
            if (id is None):
                return ''
                
            try:
                cr.execute("Select code from stock_warehouse where id = %s"%(id))
                res = cr.fetchone()
                return res and res[0] or ''
            except:
                return None
        
        def get_analytic_code(id):
            if (id is None):
                return ''
                
            try:
                cr.execute("Select code from account_analytic_account where id = %s"%(id))
                res = cr.fetchone()
                return res and res[0] or ''
            except:
                return None
            
        res = {'shop': '',
               'warehouse': '',
               'analis': '',
               'pos': ''}
        for obj_id in obj_ids:
            if obj_id[0] == 'shop':
                res['shop'] = get_shop_code(obj_id[1])
            if obj_id[0] == 'warehouse':
                res['warehouse'] = get_warehouse_code(obj_id[1])
            if obj_id[0] == 'analis':
                res['analis'] = get_analytic_code(obj_id[1])
            if obj_id[0] == 'pos':
                res['pos'] = get_pos_code(obj_id[1])
        return res
    #Thanh: Add more Fields
    
    def _next(self, cr, uid, seq_ids, context=None):
        if not seq_ids:
            return False
        if context is None:
            context = {}
        force_company = context.get('force_company')
        if not force_company:
            force_company = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        #Thanh: read more fields
#         sequences = self.read(cr, uid, seq_ids, ['name','company_id','implementation','number_next','prefix','suffix','padding'])
        sequences = self.read(cr, uid, seq_ids, ['name','company_id','implementation','number_next','prefix','suffix','padding',
                                                 'date_get','split_number','rollback_rule','number_increment'])
        #Thanh: read more fields
        preferred_sequences = [s for s in sequences if s['company_id'] and s['company_id'][0] == force_company ]
        seq = preferred_sequences[0] if preferred_sequences else sequences[0]
        if seq['implementation'] == 'standard':
            #Thanh: remove postgres sequence, get next number from History
#             cr.execute("SELECT nextval('ir_sequence_%03d')" % seq['id'])
#             seq['number_next'] = cr.fetchone()
            day = int(time.strftime('%d'))
            m = int(time.strftime('%m'))
            y = int(time.strftime('%Y'))
            sql = "select coalesce(max(his.number_current),0) from ir_sequence_his his where his.seq_id = %s"%(seq['id'])
            if seq['rollback_rule'] == 'Yearly':
                sql += " and his.year = %s"%(y)
            if seq['rollback_rule'] == 'Monthly':
                sql += " and his.year = %s"%(y) + " and his.month = %s"%(m)
            if seq['rollback_rule'] == 'Daily':
                sql += ' and his.year = %s'%(y) + ' and his.month = %s'%(m) + ' and his.day = %s'%(day)
            cr.execute(sql)
            result = cr.fetchone()
            number_current = 0
            if result:
                number_current = result[0]
            cr.execute("UPDATE ir_sequence SET number_next=%s+number_increment WHERE id=%s ", (number_current,seq['id']))
            seq['number_next'] = number_current + seq['number_increment']
            #Thanh: remove postgres sequence, get next number from History
        else:
            cr.execute("SELECT number_next FROM ir_sequence WHERE id=%s FOR UPDATE NOWAIT", (seq['id'],))
            cr.execute("UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s ", (seq['id'],))
        d = self._interpolation_dict()
        
        #Thanh: Get more _interpolation_dict
        d.update(self._interpolation_dict_extend(cr, uid, context.get('sequence_obj_ids',[])))
        #Thanh: Get more _interpolation_dict
        
        try:
            interpolated_prefix = self._interpolate(seq['prefix'], d)
            interpolated_suffix = self._interpolate(seq['suffix'], d)
        except ValueError:
            raise osv.except_osv(_('Warning'), _('Invalid prefix or suffix for sequence \'%s\'') % (seq.get('name')))
        
        sequence = interpolated_prefix + '%%0%sd' % seq['padding'] % seq['number_next'] + interpolated_suffix
        #Thanh: Insert into History
        if seq['implementation'] == 'standard': 
            cr.execute('''INSERT INTO ir_sequence_his (create_uid,create_date,write_uid,write_date,
                        seq_id,generate_code,company_id,number_current,
                        day,month,year)
                        values (%s,current_timestamp,%s,current_timestamp,
                                %s,'%s',%s,%s,
                                %s,%s,%s) 
            '''%(uid,uid,seq['id'],sequence,force_company,seq['number_next'],day,m,y))
        #Thanh: Insert into History
        return sequence
    
ir_sequence()

class ir_sequence_his(osv.osv):
    _name = 'ir.sequence.his'
    _order = 'generate_code desc'
    _columns = {
        'seq_id': fields.many2one('ir.sequence', 'Sequence', required=False),
        'generate_code': fields.char('Generate Code', size=64, required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'number_current': fields.integer('Number Current', required=True),
        'day': fields.integer('Day', help="Day of a month (1..31)"),
        'month': fields.integer('Month', help="Month of a year (1..12)"),
        'year': fields.integer('Year'),
#         'f_key': fields.integer('F Key', required=False),
#         'f_table': fields.char('F Table', size=64, required=False),
        
    }
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'ex.sequence.his', context=c),
    }

ir_sequence_his()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
