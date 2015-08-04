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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import base64
import tools
from tempfile import TemporaryFile
import xlrd
from xlrd import open_workbook,xldate_as_tuple

from osv import fields, osv

class stock_inventory(osv.osv):
    _inherit = "stock.inventory"
    _columns = {
        'name': fields.char('Reference', size=128, readonly=True),
        'description': fields.char('Description', size=128),
        'freeze_date': fields.datetime('Freeze Date',required=True),
        'user_request_id': fields.many2one('res.users', 'User Request', readonly=True, states={'draft': [('readonly', False)]}),
        'stock_journal_id': fields.many2one('stock.journal', 'Stock Journal', domain="[('source_type','=','phys_adj')]", required=True),
        'total_adjustment_value': fields.float('Total Adjustment Value',digits=(16,2), readonly=True),
        'search_product_ean':fields.char('Search Product/EAN', size=300),
        'file': fields.binary('File', help='Choose file Excel'),
        'file_name':  fields.char('Filename', 100, readonly=True),
        'ini_flag':fields.boolean('Ini Flag'),
    }
    _defaults = {
        'user_request_id': lambda s, c, u, ctx: u,
        'ini_flag':False
    }
    def create(self, cr, user, vals, context=None):
        context = context or {}
        context.update({'sequence_obj_ids':[]})
        if vals.get('stock_journal_id',False):
            journal = self.pool.get('stock.journal').browse(cr, user, vals['stock_journal_id'])
            vals['name'] = self.pool.get('ir.sequence').get_id(cr, user, journal.sequence_id.id, code_or_id='id', context=context)
        new_id = super(osv.osv, self).create(cr, user, vals, context)
        return new_id
    
    def onchange_group_type(self,cr,uid,ids,group_type):
        value ={}
        if group_type == False or group_type !='cat':
            value.update({'categ_id':False})
        return {'value': value}
    
    def read_file(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0])
#         sql = '''
#             delete from stock_inventory where inventory_line_id = %s
#         '''%(this.id)
#         cr.execute(sql)
        try:
            recordlist = base64.decodestring(this.file)
            excel = xlrd.open_workbook(file_contents = recordlist)
            sh = excel.sheet_by_index(0)
        except Exception, e:
            raise osv.except_osv(_('Warning!'), str(e))
        if sh:
            for row in range(7,sh.nrows):
                print sh.cell(row,3).value, sh.cell(row,4).value
                product_id = self.pool.get('product.product').search(cr, uid, [('name_template','=',sh.cell(row,3).value),('uom_id','=',sh.cell(row,4).value)])
                product_uom_id = self.pool.get('product.uom').search(cr, uid, [('name','=',sh.cell(row,4).value)])
                line = self.pool.get('stock.inventory.line').search(cr, uid, [('inventory_id','in',ids),('product_id','in',product_id),('product_uom','in',product_uom_id)])
                if not line:
                    raise osv.except_osv(_('Warning!'),_("You cannot change the quantity of product %s from 'Closed' to any other quantity!")%(sh.cell(row,3).value))
                vals = {
                    'count_quantity': sh.cell(row,5).value
                    }
                self.pool.get('stock.inventory.line').write(cr, uid, line ,vals)
        return True
    
    def action_done(self, cr, uid, ids, context=None):
        """ Finish the inventory
        @return: True
        """
        picking_id = False
        if context is None:
            context = {}
        
        move_obj = self.pool.get('stock.move')
        for inv in self.browse(cr, uid, ids, context=context):
            #move_obj.action_done(cr, uid, [x.id for x in inv.move_ids], context=context)
            context.update({'date_done':inv.freeze_date})
            self.write(cr, uid, [inv.id], {'state':'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
            for line in inv.move_ids:
                move_obj.action_done(cr,uid,[line.id],context=context)
                self.pool.get('stock.move').write(cr,uid,line.id,{'date':inv.freeze_date,'state':'done'})
                picking_id = line.picking_id or False
            if picking_id:
                self.pool.get('stock.picking').write(cr,uid,picking_id.id,{'state':'done','date_done':inv.freeze_date})
                
        return True
    
    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirm the inventory and writes its finished datlinee
        @return: True
        """
        count = 1
        if context is None:
            context = {}
        # to perform the correct inventory corrections we need analyze stock location by
        # location, never recursively, so we use a special context
        product_context = dict(context, compute_child=False)

        for inv in self.browse(cr, uid, ids, context=context):
            move_ids = []
            for line in inv.inventory_line_id:
                product_context.update(uom=line.product_uom.id, to_date=inv.date, date=inv.date, prodlot_id=line.prod_lot_id.id)
                #amount = location_obj._product_get(cr, uid, line.location_id.id, [pid], product_context)[pid]
                change = line.count_quantity - line.product_qty
                lot_id = line.prod_lot_id.id
                if change:
                    location_id = line.product_id.property_stock_inventory.id or False
                    location_dest_id = line.location_id.id or False
                    value = {
                        'name': line.product_id.name or False,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'prodlot_id': lot_id,
                        'tracking_id': line.tracking_id and line.tracking_id.id or False,
                        'date': inv.date,
                        'state':'draft',
                        'date':inv.freeze_date,
                        'price_unit': inv.ini_flag and line.freeze_cost or 0.0,
                        'ini_flag':inv.ini_flag or False
                    }

                    if change > 0:
                        value.update( {
                            'product_qty': change,
                            'location_id': location_id,
                            'location_dest_id': location_dest_id,
                        })
                    else:
                        value.update( {
                            'product_qty': -change,
                            'location_id': location_dest_id,
                            'location_dest_id': location_id,
                        })
                    if count:
                        new_id = self.create_picking(cr,uid,ids,inv.freeze_date,location_id,location_dest_id,inv.name)
                        count =0
                    if new_id:
                        value.update({'picking_id':new_id,'date':inv.freeze_date})
                    move_id = self._inventory_line_hook(cr, uid, line, value)
                    self.pool.get('stock.inventory.line').write(cr,uid,line.id,{'move_id':move_id})
                    move_ids.append(move_id)
            self.write(cr, uid, [inv.id], {'state': 'confirm', 'move_ids': [(6, 0, move_ids)]})
            self.pool.get('stock.move').action_confirm(cr, uid, move_ids, context=context)
        return True
    
    def create_picking(self,cr,uid,ids,date_done,location_id,location_dest_id,origin,context=None):
        
        journal_ids = self.pool.get('stock.journal').search(cr,uid,[('source_type','=','phys_adj')])
        if not journal_ids:
            raise osv.except_osv(_('Warning!'), _('Please define Stock Journal for Incomming Order.'))
        var = {
            'name':origin,
            'origin': origin,
            'date': date_done,
            'invoice_state': 'none',
            'type': 'internal',
#             'company_id': 1,
            'move_lines' : [],
            
            #Thanh: Add more fields
            'return':'none',
            'stock_journal_id':journal_ids and journal_ids[0] or False,
            'location_id': location_dest_id,
            'location_dest_id': location_id,
        }
        return self.pool.get('stock.picking').create(cr,uid,var)
    
    def report_inventory_accuracy_analysis(self,cr,uid,ids,context=None):
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'inventory_accuracy_analysis',
            }
        
stock_inventory()

class stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line"
    
    def _get_adjust_qty(self,cr,uid,ids, field_name, arg, context=None):
        res ={}
        cost_item = 0
        for line in self.browse(cr,uid,ids,context=context):
            adjust = line.product_qty - line.count_quantity
            res[line.id] = {
                            'adjust_quantity': 0,
                            'adjust_value': 0,
                            }
            if adjust == 0.0:
                continue
            cost_item = line.freeze_cost
            if adjust >0:
                res[line.id]['adjust_quantity'] =adjust
                res[line.id]['adjust_value'] = round(adjust * cost_item,0)
            else:
                res[line.id]['adjust_quantity'] =adjust 
                res[line.id]['adjust_value'] = round(adjust *(-1) * cost_item,0)
        return res
    
    def _get_product_info(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        uom_obj = self.pool.get('product.uom')
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                            'uom_conversion': 0.0,
                            'primary_qty': 0.0,
                            }
            if line.product_id and line.product_uom:
                res[line.id]['uom_conversion'] = 1
                res[line.id]['primary_qty'] = line.product_qty
        return res
    
    _columns = {
        'move_id':fields.many2one('stock.move','Move id'),
        'line_no': fields.integer('Line NO'),
        'product_ean': fields.char('Barcode', size=20),
        #'sys_uom': fields.many2one('product.uom', 'Primary UoM', required=True),
        'count_quantity': fields.float('Count Qty',digits=(16,3)),
        'freeze_cost': fields.float('Freeze Cost', readonly=False, digits=(16,2)),
#         'freeze_cost': fields.related('move_id','price_unit', type="float", string="freeze_cost", store=True, readonly=True),
        'adjust_quantity': fields.function(_get_adjust_qty, string='Adjust Quantity',type ='float',multi='pro_info'), #adjust = count - sysonhand
        'adjust_value':    fields.function(_get_adjust_qty, string='Adjust Value',type ='float',multi='pro_info'),
        #'adjust_quantity': fields.float('Sys Onhand',digits=(16,3),readonly=True), #adjust = count - sysonhand
        #'adjust_value':    fields.float('Adjust Value', digits=(16,2),readonly=True),
        
        'uom_conversion': fields.function(_get_product_info, string='Factor',type='float',digits= (16,4),
            store={
                "stock.inventory.line": (lambda self, cr, uid, ids, c={}: ids, ['product_id','product_uom','product_qty'], 10),
            }, readonly=True, multi='pro_info'),
        #'uom_conversion': fields.float('Factor', digits=(16,4), help="From product_barcode.", readonly=True),
        
        'primary_qty': fields.function(_get_product_info, string='Primary Qty',digits= (16,4),type='float',
            store={
                'stock.inventory.line': (lambda self, cr, uid, ids, c={}: ids, ['product_id','product_uom','product_qty'], 10),
            }, readonly=True, multi='pro_info'),
        'description': fields.char('Ghi chú', size=64),
        'tracking_id': fields.many2one('stock.tracking', 'Kệ'),
            }
    
    def onchange_product_ean(self, cr, uid, ids, product_id, product_uom_id, product_ean= False, context=None):
        
        if not product_ean:
            return {'value': {'product_ean' : product_ean or False}}
        
        cr.execute("SELECT product_id,uom_id FROM product_barcode WHERE barcode='%s'"%(product_ean,))
        res = cr.dictfetchall()
        if res:
            product_id = res[0]['product_id']
            product_uom_id = res[0]['uom_id']
        else:
            product_id = False
            product_uom_id = False
            
        res = self.onchange_product_id(cr, uid, ids, product_id, product_uom_id, product_ean= False, context=None)
        res.update({'product_id':product_id,'product_uom':product_uom_id})
        return {'value':res}
        
    
stock_inventory_line()

class stock_move(osv.osv):
    _inherit = 'stock.move'
    _columns = {
        'ini_flag':fields.boolean('Ini Flag'),
    }
stock_move() 
    
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
