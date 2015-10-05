# # -*- coding: utf-8 -*-
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
import httplib

class users(osv.osv):
    _inherit = 'res.users'
    _columns = {
        'location_ids':fields.many2many('stock.location', 'stock_location_users_rel', 'user_id', 'location_id', 'Locations'),
    }
users()

class stock_return_reason(osv.osv):
    _name = 'stock.return.reason'
    _description = 'Stock Return Reason'
    _rec_name = "code"
    _order = 'code'
    
    _columns = {
        'code': fields.char('Code', size=12),
        'name': fields.char('Name', size=64),
        'active':fields.boolean('Active ?'),
    }
    _defaults = {
       'active':True,
    }
stock_return_reason()

class stock_location(osv.osv):
    _inherit = "stock.location"
    
    def _complete_name(self, cr, uid, ids, name, args, context=None):
        """ Forms complete name of location from parent location to child location.
        @return: Dictionary of values
        """
        res = {}
        for m in self.browse(cr, uid, ids, context=context):
#            names = [m.name]
#            parent = m.location_id
#            while parent:
#                names.append(parent.name)
#                parent = parent.location_id
#            res[m.id] = ' / '.join(reversed(names))
            res[m.id] = m.name
        return res
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context=context)
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if not args:
            args = []
        stock_journal_pool = self.pool.get('stock.journal')
        if context.has_key('stock_journal_id'):
            if not context['stock_journal_id']:
                #args += [('id', 'in', [])] 
                return super(stock_location, self).search(cr, uid, args, offset, limit, order, context=context, count=count)
            else:
                location_ids = []
                stock_journal_obj = stock_journal_pool.browse(cr, uid, context['stock_journal_id'])
                if context.get('location_id') and context['location_id'] =='location':
                    for location in stock_journal_obj.from_location_id:
                        location_ids.append(location.id) 
                if context.get('location_dest_id') and context['location_dest_id'] =='location_dest':
                    for location in stock_journal_obj.to_location_id:
                        location_ids.append(location.id) 
                #l ocation_ids = super(stock_location, self).search(cr, uid, [('id','child_of',warehouse_obj.lot_stock_id.location_id.id),('inventory_type','=','SubInventory')])
                args += [('id', 'in', location_ids)]
        return super(stock_location, self).search(cr, uid, args, offset, limit, order, context=context, count=count)
    
    _columns = {
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse'),
        'location_return': fields.boolean(_('For Return ?'), help=_('This location is for return goods?')),
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('warehouse_id',False):
            lo_child_ids = self.search(cr, uid, [('id','child_of',ids)])
            if lo_child_ids:
                cr.execute('UPDATE stock_location SET warehouse_id=%s WHERE id in (%s)'%(vals['warehouse_id'],','.join(map(str, ids))))
        return super(stock_location, self).write(cr, uid, ids, vals, context=context)
    
    def _product_get_all_report(self, cr, uid, ids, product_ids=False, context=None):
        return self._product_get_report(cr, uid, ids, product_ids, context, recursive=True)


    def _product_get_report(self, cr, uid, ids, product_ids=False,
            context=None, recursive=False):
        """ Finds the product quantity and price for particular location.
        @param product_ids: Ids of product
        @param recursive: True or False
        @return: Dictionary of values
        """
        if context is None:
            context = {}
            user = self.pool.get("res.users").browse(cr, uid, uid)
            context.update({"lang":user.partner_id and user.partner_id.lang or "en_US"})
        product_obj = self.pool.get('product.product')
        move_obj = self.pool.get('stock.move')
        # Take the user company and pricetype
        context['currency_id'] = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id

        # To be able to offer recursive or non-recursive reports we need to prevent recursive quantities by default
        context['compute_child'] = False

        if not product_ids:
            #product_ids = product_obj.search(cr, uid, [], context={'active_test': False})
            cr.execute("select distinct product_id from stock_move where state = 'done' and ( location_id IN %s or location_dest_id IN %s )", (tuple(ids), tuple(ids),))
            product_ids = filter(None, map(lambda x:x[0], cr.fetchall()))

        products = product_obj.browse(cr, uid, product_ids, context=context)
        products_by_uom = {}
        products_by_id = {}
        for product in products:
            products_by_uom.setdefault(product.uom_id.id, [])
            products_by_uom[product.uom_id.id].append(product)
            products_by_id.setdefault(product.id, [])
            products_by_id[product.id] = product

        result = {}
        result['product'] = []
        for id in ids:
            quantity_total = 0.0
            total_price = 0.0
            for uom_id in products_by_uom.keys():
                fnc = self._product_get
                if recursive:
                    fnc = self._product_all_get
                ctx = context.copy()
                ctx['uom'] = uom_id
                qty = fnc(cr, uid, id, [x.id for x in products_by_uom[uom_id]],
                        context=ctx)
                for product_id in qty.keys():
                    if not qty[product_id]:
                        continue
                    prod_p_qty = 0
                    product = products_by_id[product_id]
                    quantity_total += qty[product_id]

                    # Compute based on pricetype
                    # Choose the right filed standard_price to read
                    amount_unit = product.price_get('standard_price', context=context)[product.id]
                    price = qty[product_id] * amount_unit

                    prod_p_qty = (qty[product_id] / product.uom_id.factor * product.uom_po_id.factor)

                    total_price += price
                    result['product'].append({
                        'price': amount_unit,
                        'prod_name': product.name,
                        'code': product.default_code, # used by lot_overview_all report!
                        'variants': product.variants or '',
                        'uom': product.uom_id.name,
                        'p_uom': product.uom_po_id.name,
                        'prod_qty': qty[product_id],
                        'prod_p_qty': prod_p_qty,
                        'price_value': price,
                    })
        result['total'] = quantity_total
        result['total_price'] = total_price
        return result   
    
    def _product_reserve_tracking(self, cr, uid, ids,prodlot_id,tracking_id, product_id, product_qty, context=None, lock=False):
        """
        Attempt to find a quantity ``product_qty`` (in the product's default uom or the uom passed in ``context``) of product ``product_id``
        in locations with id ``ids`` and their child locations. If ``lock`` is True, the stock.move lines
        of product with id ``product_id`` in the searched location will be write-locked using Postgres's
        "FOR UPDATE NOWAIT" option until the transaction is committed or rolled back, to prevent reservin
        twice the same products.
        If ``lock`` is True and the lock cannot be obtained (because another transaction has locked some of
        the same stock.move lines), a log line will be output and False will be returned, as if there was
        not enough stock.

        :param product_id: Id of product to reserve
        :param product_qty: Quantity of product to reserve (in the product's default uom or the uom passed in ``context``)
        :param lock: if True, the stock.move lines of product with id ``product_id`` in all locations (and children locations) with ``ids`` will
                     be write-locked using postgres's "FOR UPDATE NOWAIT" option until the transaction is committed or rolled back. This is
                     to prevent reserving twice the same products.
        :param context: optional context dictionary: if a 'uom' key is present it will be used instead of the default product uom to
                        compute the ``product_qty`` and in the return value.
        :return: List of tuples in the form (qty, location_id) with the (partial) quantities that can be taken in each location to
                 reach the requested product_qty (``qty`` is expressed in the default uom of the product), of False if enough
                 products could not be found, or the lock could not be obtained (and ``lock`` was True).
        """
        result = []
        amount = 0.0
        if context is None:
            context = {}
        uom_obj = self.pool.get('product.uom')
        uom_rounding = self.pool.get('product.product').browse(cr, uid, product_id, context=context).uom_id.rounding
        if context.get('uom'):
            uom_rounding = uom_obj.browse(cr, uid, context.get('uom'), context=context).rounding

        locations_ids = self.search(cr, uid, [('location_id', 'child_of', ids)])
        if locations_ids:
            # Fetch only the locations in which this product has ever been processed (in or out)
            cr.execute("""SELECT l.id FROM stock_location l WHERE l.id in %s AND
                        EXISTS (SELECT 1 FROM stock_move m WHERE m.product_id = %s AND m.prodlot_id = %s AND m.tracking_id = %s
                                AND ((state = 'done' AND m.location_dest_id = l.id)
                                    OR (state in ('done','assigned') AND m.location_id = l.id)))
                       """, (tuple(locations_ids), product_id,prodlot_id,tracking_id))
            locations_ids = [i for (i,) in cr.fetchall()]
        for id in locations_ids:
            if lock:
                try:
                    # Must lock with a separate select query because FOR UPDATE can't be used with
                    # aggregation/group by's (when individual rows aren't identifiable).
                    # We use a SAVEPOINT to be able to rollback this part of the transaction without
                    # failing the whole transaction in case the LOCK cannot be acquired.
                    cr.execute("SAVEPOINT stock_location_product_reserve")
                    cr.execute("""SELECT id FROM stock_move
                                  WHERE product_id=%s AND prodlot_id = %s AND tracking_id = %s AND
                                          (
                                            (location_dest_id=%s AND
                                             location_id<>%s AND
                                             state='done')
                                            OR
                                            (location_id=%s AND
                                             location_dest_id<>%s AND
                                             state in ('done', 'assigned'))
                                          )
                                  FOR UPDATE of stock_move NOWAIT""", (product_id,prodlot_id,tracking_id, id, id, id, id), log_exceptions=False)
                except Exception:
                    # Here it's likely that the FOR UPDATE NOWAIT failed to get the LOCK,
                    # so we ROLLBACK to the SAVEPOINT to restore the transaction to its earlier
                    # state, we return False as if the products were not available, and log it:
                    cr.execute("ROLLBACK TO stock_location_product_reserve")
                    _logger.warning("Failed attempt to reserve %s x product %s, likely due to another transaction already in progress. Next attempt is likely to work. Detailed error available at DEBUG level.", product_qty, product_id)
                    _logger.debug("Trace of the failed product reservation attempt: ", exc_info=True)
                    return False

            # XXX TODO: rewrite this with one single query, possibly even the quantity conversion
            cr.execute("""SELECT product_uom, sum(product_qty) AS product_qty
                          FROM stock_move
                          WHERE location_dest_id=%s AND
                                location_id<>%s AND
                                product_id=%s AND prodlot_id = %s AND tracking_id = %s AND 
                                state='done'
                          GROUP BY product_uom
                       """,
                       (id, id, product_id,prodlot_id,tracking_id))
            results = cr.dictfetchall()
            cr.execute("""SELECT product_uom,-sum(product_qty) AS product_qty
                          FROM stock_move
                          WHERE location_id=%s AND
                                location_dest_id<>%s AND
                                product_id=%s AND prodlot_id = %s AND tracking_id = %s AND
                                state in ('done', 'assigned')
                          GROUP BY product_uom
                       """,
                       (id, id, product_id,prodlot_id,tracking_id))
            results += cr.dictfetchall()
            total = 0.0
            results2 = 0.0
            for r in results:
                amount = uom_obj._compute_qty(cr, uid, r['product_uom'], r['product_qty'], context.get('uom', False))
                results2 += amount
                total += amount
            if total <= 0.0:
                continue

            amount = results2
            compare_qty = float_compare(amount, 0, precision_rounding=uom_rounding)
            if compare_qty == 1:
                if amount > min(total, product_qty):
                    amount = min(product_qty, total)
                result.append((amount, id))
                product_qty -= amount
                total -= amount
                if product_qty <= 0.0:
                    return result
                if total <= 0.0:
                    continue
        return False
    
    def _product_reserve(self, cr, uid, ids,prodlot_id, product_id, product_qty, context=None, lock=False):
        """
        Attempt to find a quantity ``product_qty`` (in the product's default uom or the uom passed in ``context``) of product ``product_id``
        in locations with id ``ids`` and their child locations. If ``lock`` is True, the stock.move lines
        of product with id ``product_id`` in the searched location will be write-locked using Postgres's
        "FOR UPDATE NOWAIT" option until the transaction is committed or rolled back, to prevent reservin
        twice the same products.
        If ``lock`` is True and the lock cannot be obtained (because another transaction has locked some of
        the same stock.move lines), a log line will be output and False will be returned, as if there was
        not enough stock.

        :param product_id: Id of product to reserve
        :param product_qty: Quantity of product to reserve (in the product's default uom or the uom passed in ``context``)
        :param lock: if True, the stock.move lines of product with id ``product_id`` in all locations (and children locations) with ``ids`` will
                     be write-locked using postgres's "FOR UPDATE NOWAIT" option until the transaction is committed or rolled back. This is
                     to prevent reserving twice the same products.
        :param context: optional context dictionary: if a 'uom' key is present it will be used instead of the default product uom to
                        compute the ``product_qty`` and in the return value.
        :return: List of tuples in the form (qty, location_id) with the (partial) quantities that can be taken in each location to
                 reach the requested product_qty (``qty`` is expressed in the default uom of the product), of False if enough
                 products could not be found, or the lock could not be obtained (and ``lock`` was True).
        """
        result = []
        amount = 0.0
        if context is None:
            context = {}
        uom_obj = self.pool.get('product.uom')
        uom_rounding = self.pool.get('product.product').browse(cr, uid, product_id, context=context).uom_id.rounding
        if context.get('uom'):
            uom_rounding = uom_obj.browse(cr, uid, context.get('uom'), context=context).rounding

        locations_ids = self.search(cr, uid, [('location_id', 'child_of', ids)])
        if locations_ids:
            # Fetch only the locations in which this product has ever been processed (in or out)
            cr.execute("""SELECT l.id FROM stock_location l WHERE l.id in %s AND
                        EXISTS (SELECT 1 FROM stock_move m WHERE m.product_id = %s AND m.prodlot_id = %s
                                AND ((state = 'done' AND m.location_dest_id = l.id)
                                    OR (state in ('done','assigned') AND m.location_id = l.id)))
                       """, (tuple(locations_ids), product_id,prodlot_id))
            locations_ids = [i for (i,) in cr.fetchall()]
        for id in locations_ids:
            if lock:
                try:
                    # Must lock with a separate select query because FOR UPDATE can't be used with
                    # aggregation/group by's (when individual rows aren't identifiable).
                    # We use a SAVEPOINT to be able to rollback this part of the transaction without
                    # failing the whole transaction in case the LOCK cannot be acquired.
                    cr.execute("SAVEPOINT stock_location_product_reserve")
                    cr.execute("""SELECT id FROM stock_move
                                  WHERE product_id=%s AND prodlot_id = %s AND
                                          (
                                            (location_dest_id=%s AND
                                             location_id<>%s AND
                                             state='done')
                                            OR
                                            (location_id=%s AND
                                             location_dest_id<>%s AND
                                             state in ('done', 'assigned'))
                                          )
                                  FOR UPDATE of stock_move NOWAIT""", (product_id,prodlot_id, id, id, id, id), log_exceptions=False)
                except Exception:
                    # Here it's likely that the FOR UPDATE NOWAIT failed to get the LOCK,
                    # so we ROLLBACK to the SAVEPOINT to restore the transaction to its earlier
                    # state, we return False as if the products were not available, and log it:
                    cr.execute("ROLLBACK TO stock_location_product_reserve")
                    _logger.warning("Failed attempt to reserve %s x product %s, likely due to another transaction already in progress. Next attempt is likely to work. Detailed error available at DEBUG level.", product_qty, product_id)
                    _logger.debug("Trace of the failed product reservation attempt: ", exc_info=True)
                    return False

            # XXX TODO: rewrite this with one single query, possibly even the quantity conversion
            cr.execute("""SELECT product_uom, sum(product_qty) AS product_qty
                          FROM stock_move
                          WHERE location_dest_id=%s AND
                                location_id<>%s AND
                                product_id=%s AND prodlot_id = %s AND
                                state='done'
                          GROUP BY product_uom
                       """,
                       (id, id, product_id,prodlot_id))
            results = cr.dictfetchall()
            cr.execute("""SELECT product_uom,-sum(product_qty) AS product_qty
                          FROM stock_move
                          WHERE location_id=%s AND
                                location_dest_id<>%s AND
                                product_id=%s AND prodlot_id = %s AND
                                state in ('done', 'assigned')
                          GROUP BY product_uom
                       """,
                       (id, id, product_id,prodlot_id))
            results += cr.dictfetchall()
            total = 0.0
            results2 = 0.0
            for r in results:
                amount = uom_obj._compute_qty(cr, uid, r['product_uom'], r['product_qty'], context.get('uom', False))
                results2 += amount
                total += amount
            if total <= 0.0:
                continue

            amount = results2
            compare_qty = float_compare(amount, 0, precision_rounding=uom_rounding)
            if compare_qty == 1:
                if amount > min(total, product_qty):
                    amount = min(product_qty, total)
                result.append((amount, id))
                product_qty -= amount
                total -= amount
                if product_qty <= 0.0:
                    return result
                if total <= 0.0:
                    continue
        return False
    
stock_location()

class stock_warehouse(osv.osv):
    _inherit = "stock.warehouse"
    _columns = {
        'code': fields.char('Code', size=5, required=True),
        'lot_return_id': fields.many2one('stock.location', 'Location For Return', domain=[('location_return', '=', 'True')]),
        'journal_production_in_id':fields.many2one('stock.journal', 'Nhập kho TP/BTP',),
        'journal_production_out_id':fields.many2one('stock.journal', 'Xuất kho NVL',),
    }
stock_warehouse()

class stock_journal(osv.osv):
    _inherit = "stock.journal"
    _columns = {
        'name': fields.char('Stock Journal', size=32, required=True),
        'user_id': fields.many2one('res.users', 'Responsible'),
        'source_type': fields.selection([
                                        ('in', 'Getting Goods'), 
                                        ('out', 'Sending Goods'),
                                        ('return_customer', 'Return from customer'), 
                                        ('return_supplier', 'Return to supplier'), 
                                        ('internal', 'Internal'),
                                        ('production', 'Production'),
                                        ('phys_adj', 'Physical Adjustment'),], 'Source Type', size=16, required=True),
        'sequence_id': fields.many2one('ir.sequence', 'Sequence', required=True),
        
        'from_location_id':fields.many2many('stock.location','stock_journal_from_location_ref', 
                                                 'journal_id','location_id','From Location',required = True), 
        'to_location_id':fields.many2many('stock.location','stock_journal_to_location_ref', 
                                                 'journal_id','location_id','From Location',required = True), 
    }
    _defaults = {
        'user_id': lambda s, c, u, ctx: u
    }
    
stock_journal()
    
class stock_move(osv.osv):
    _inherit = 'stock.move'
    
    
    def _get_accounting_data_for_valuation(self, cr, uid, move, context=None):
        """
        Return the accounts and journal to use to post Journal Entries for the real-time
        valuation of the move.

        :param context: context dictionary that can explicitly mention the company to consider via the 'force_company' key
        :raise: osv.except_osv() is any mandatory account or journal is not defined.
        """
        acc_src = False
        product_obj=self.pool.get('product.product')
        accounts = product_obj.get_product_accounts(cr, uid, move.product_id.id, context)
        if move.stock_journal_id.source_type == 'internal':
            if move.location_id.usage =='internal' and move.location_dest_id.usage !='internal':
                for location in move.stock_journal_id.to_location_id:
                    if location.usage != 'internal':
                        acc_src = location.valuation_in_account_id.id
            if move.location_id.usage !='internal' and move.location_dest_id.usage =='internal':
                for location in move.stock_journal_id.to_location_id:
                    if location.usage != 'internal':
                        acc_dest = location.valuation_out_account_id.id
                        
        if move.stock_journal_id.source_type == 'out':
            if move.location_id.valuation_out_account_id:
                acc_src = move.location_id.valuation_out_account_id.id
            else:
                acc_src = accounts['stock_account_input']
            if move.location_dest_id.valuation_in_account_id:
                acc_dest = move.location_dest_id.valuation_in_account_id.id
            else:
                acc_dest = accounts['stock_account_output']
        
        if move.stock_journal_id.source_type == 'phys_adj':
            if move.location_id.usage =='internal' and move.location_dest_id.usage !='internal':
                for location in move.stock_journal_id.to_location_id:
                    if location.usage != 'internal':
                        acc_dest = location.valuation_in_account_id.id 
                        acc_src = location.valuation_out_account_id.id
            if move.location_id.usage !='internal' and move.location_dest_id.usage =='internal':
                for location in move.stock_journal_id.to_location_id:
                    if location.usage != 'internal':
                         acc_dest = location.valuation_in_account_id.id 
                         acc_src = location.valuation_out_account_id.id
#         
#         if context and context.get('inventory') =='phys_adj':
#             acc_src = accounts['property_stock_account_loss_categ']

        acc_valuation = accounts.get('property_stock_valuation_account_id', False)
        journal_id = accounts['stock_journal']

#         if acc_dest == acc_valuation:
#             raise osv.except_osv(_('Error!'),  _('Cannot create Journal Entry, Output Account of this product and Valuation account on category of this product are same.'))
# 
#         if acc_src == acc_valuation:
#             raise osv.except_osv(_('Error!'),  _('Cannot create Journal Entry, Input Account of this product and Valuation account on category of this product are same.'))
# 
#         if not acc_src:
#             raise osv.except_osv(_('Error!'),  _('Please define stock input account for this product or its category: "%s" (id: %d)') % \
#                                     (move.product_id.name, move.product_id.id,))
#         if not acc_dest:
#             raise osv.except_osv(_('Error!'),  _('Please define stock output account for this product or its category: "%s" (id: %d)') % \
#                                     (move.product_id.name, move.product_id.id,))
        if not journal_id:
            raise osv.except_osv(_('Error!'), _('Please define journal on the product category: "%s" (id: %d)') % \
                                    (move.product_id.categ_id.name, move.product_id.categ_id.id,))
        if not acc_valuation:
            raise osv.except_osv(_('Error!'), _('Please define inventory valuation account on the product category: "%s" (id: %d)') % \
                                    (move.product_id.categ_id.name, move.product_id.categ_id.id,))
        return journal_id, acc_src, acc_dest, acc_valuation
    
    
    def _create_account_move_line(self, cr, uid, move, src_account_id, dest_account_id, reference_amount, reference_currency_id, context=None):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given stock move.
        """
        # prepare default values considering that the destination accounts have the reference_currency_id as their main currency
        #kiet get _account_analytic_id
        date =move.date or time.strftime('%Y-%m-%d')
        partner_id = (move.picking_id.partner_id and self.pool.get('res.partner')._find_accounting_partner(move.picking_id.partner_id).id) or False
        rec = self.pool.get('account.analytic.default').account_get(cr, uid, move.product_id.id, partner_id, uid, date, context=context)
        debit_line_vals = {
                    'name': move.name,
                    'product_id': move.product_id and move.product_id.id or False,
                    'quantity': move.product_qty,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': date,
                    'partner_id': partner_id,
                    'debit': reference_amount,
                    'account_id': dest_account_id,
#                     'analytic_account_id':rec.analytic_id.id or False
        }
        credit_line_vals = {
                    'name': move.name,
                    'product_id': move.product_id and move.product_id.id or False,
                    'quantity': move.product_qty,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': date,
                    'partner_id': partner_id,
                    'credit': reference_amount,
                    'account_id': src_account_id,
#                     'analytic_account_id':rec.analytic_id.id or False
        }

        # if we are posting to accounts in a different currency, provide correct values in both currencies correctly
        # when compatible with the optional secondary currency on the account.
        # Financial Accounts only accept amounts in secondary currencies if there's no secondary currency on the account
        # or if it's the same as that of the secondary amount being posted.
        account_obj = self.pool.get('account.account')
        src_acct, dest_acct = account_obj.browse(cr, uid, [src_account_id, dest_account_id], context=context)
        src_main_currency_id = src_acct.company_id.currency_id.id
        dest_main_currency_id = dest_acct.company_id.currency_id.id
        cur_obj = self.pool.get('res.currency')
        if reference_currency_id != src_main_currency_id:
            # fix credit line:
            credit_line_vals['credit'] = cur_obj.compute(cr, uid, reference_currency_id, src_main_currency_id, reference_amount, context=context)
            if (not src_acct.currency_id) or src_acct.currency_id.id == reference_currency_id:
                credit_line_vals.update(currency_id=reference_currency_id, amount_currency=-reference_amount)
        if reference_currency_id != dest_main_currency_id:
            # fix debit line:
            debit_line_vals['debit'] = cur_obj.compute(cr, uid, reference_currency_id, dest_main_currency_id, reference_amount, context=context)
            if (not dest_acct.currency_id) or dest_acct.currency_id.id == reference_currency_id:
                debit_line_vals.update(currency_id=reference_currency_id, amount_currency=reference_amount)

        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
    
    
    def _create_product_valuation_moves(self, cr, uid, move, context=None):
        """
        Generate the appropriate accounting moves if the product being moves is subject
        to real_time valuation tracking, and the source or destination location is
        a transit location or is outside of the company.
        """
        #Thanh: Remove check Real-time
#         if move.product_id.valuation == 'real_time': # FIXME: product valuation should perhaps be a property?
        if context is None:
            context = {}
        src_company_ctx = dict(context,force_company=move.location_id.company_id.id)
        dest_company_ctx = dict(context,force_company=move.location_dest_id.company_id.id)
        account_moves = []
        # Outgoing moves (or cross-company output part)
        if move.location_id.company_id \
            and (move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal'\
                 or move.location_id.company_id != move.location_dest_id.company_id):
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, src_company_ctx)
            reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
            #returning goods to supplier
            if move.location_dest_id.usage == 'supplier':
                account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_valuation, acc_src, reference_amount, reference_currency_id, context))]
            else:
                account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_valuation, acc_dest, reference_amount, reference_currency_id, context))]

        # Incoming moves (or cross-company input part)
        if move.location_dest_id.company_id \
            and (move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal'\
                 or move.location_id.company_id != move.location_dest_id.company_id):
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, dest_company_ctx)
            reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, move, src_company_ctx)
            #goods return from customer
            if move.location_id.usage == 'customer':
                account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_dest, acc_valuation, reference_amount, reference_currency_id, context))]
            else:
                account_moves += [(journal_id, self._create_account_move_line(cr, uid, move, acc_src, acc_valuation, reference_amount, reference_currency_id, context))]

        move_obj = self.pool.get('account.move')
        for j_id, move_lines in account_moves:
            new_id = move_obj.create(cr, uid,
                    {
                     'date':move.date or False,
                     'shop_id':move.picking_id and move.picking_id.shop_id and move.picking_id.shop_id.id or False,
                     'journal_id': j_id,
                     'line_id': move_lines,
                     'ref': move.picking_id and move.picking_id.name}, context=context)
            move_obj.post(cr, uid, [new_id], context)
                
    
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        cur = False
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            taxes = []
            price = 0.0
            product_uom_qty = line.product_qty
            cur = False
            if line.sale_line_id:
                price = line.sale_line_id.price_unit * (1 - (line.sale_line_id.discount or 0.0) / 100.0)
                taxes = line.sale_line_id.tax_id
                cur = line.sale_line_id.order_id.pricelist_id.currency_id
            
            if line.purchase_line_id:
                price = line.price_unit 
                taxes = line.purchase_line_id.taxes_id
                cur = line.purchase_line_id.order_id.pricelist_id.currency_id
            
#             if line.pos_line_id:
#                 price = line.price_unit 
#                 taxes = line.pos_line_id.product_id and line.pos_line_id.product_id.taxes_id or False
                
            taxes = tax_obj.compute_all(cr, uid, taxes, price, product_uom_qty, line.product_id, line.picking_id.partner_id)
            if cur:
                taxes['total'] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id] = taxes['total']
        return res
    
    def _get_product_code(self, cr, uid, ids, fields, args, context=None):
        result = {}
        for move in self.browse(cr, uid, ids, context=context):
            result[move.id] = move.product_id and move.product_id.default_code or 'No ref'
        return result
    
    def _move_to_update_after_product_change(self, cr, uid, ids, fields=None, arg=None, context=None):
        if type(ids) != type([]):
            ids = [ids]
        return self.pool.get('stock.move').search(cr, uid, [('product_id', 'in', ids)]) or []
    
    _store_product_code = {
        'stock.move': (lambda self, cr, uid, ids, context: ids, ['product_id'], 10),
#         'product.product': (_move_to_update_after_product_change, ['default_code'], 10),
    }
    
    def _get_product_info(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        uom_obj = self.pool.get('product.uom')
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                            'uom_conversion': 0.0,
                            'primary_qty': 0.0,
                            }
            if line.product_id and line.product_uom:
                if line.product_uom.id != line.product_id.uom_id.id:
                    if line.product_id.__hasattr__('uom_ids'):
                        res[line.id]['primary_qty'] = uom_obj._compute_qty(cr, uid, line.product_uom.id, line.product_qty, line.product_id.uom_id.id, product_id=line.product_id.id)
                    else:
                        res[line.id]['primary_qty'] = uom_obj._compute_qty(cr, uid, line.product_uom.id, line.product_qty, line.product_id.uom_id.id)
                else:
                    res[line.id]['primary_qty'] = line.product_qty
                res[line.id]['uom_conversion'] = line.product_qty and round(res[line.id]['primary_qty']/line.product_qty,3) or 0.0
        return res
    
    _columns = {
#         'cost_unit': fields.float('Unit Cost', digits_compute= dp.get_precision('Product Price')),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
        
        'product_code':  fields.function(_get_product_code, method=True, type='char', size=128, store=_store_product_code, string='Product Code', readonly=True),
        'partner_ref':  fields.related('partner_id', 'ref', string='Partner Ref', type='char', size=16),
        'picking_return':  fields.related('picking_id', 'return', string='Picking Return', type='char', size=12, readonly=1),
        'product_categ_id':  fields.related('product_id', 'categ_id', string='Product Category', type='many2one', relation='product.category',size=12, readonly=1),
        'return_reason_id': fields.many2one('stock.return.reason', 'Return Reason'),
        
        'stock_journal_id':  fields.related('picking_id', 'stock_journal_id', type='many2one', relation='stock.journal', string='Stock Journal', store=True, readonly=1),
        'uom_conversion': fields.function(_get_product_info, string='Factor', digits= (16,4),type='float',
            store={
                'stock.move': (lambda self, cr, uid, ids, c={}: ids, ['product_id','product_uom','product_qty'], 10),
            }, readonly=True, multi='pro_info'),
        'primary_qty': fields.function(_get_product_info, string='Primary Qty', digits_compute= dp.get_precision('Product Unit of Measure'), type='float',
            store={
                'stock.move': (lambda self, cr, uid, ids, c={}: ids, ['product_id','product_uom','product_qty'], 10),
            }, readonly=True, multi='pro_info'),
        'ini_flag':fields.boolean('Ini Flag'),
        'costed':fields.boolean('Costed'),
        'invoiced_qty':fields.float('Invoiced Qty'),
        'sale_price':  fields.related('sale_line_id', 'price_unit', string='Gía bán', type='float', relation='sale.order.line', readonly=1),
        'purchase_price':  fields.related('purchase_line_id', 'price_unit', string='Giá mua', type='float', relation='purchase.order.line', readonly=1),
    }
    _defaults = {
        'ini_flag':False,
        'costed':False
    }
    
    # Kiet: Tao lo tu dong
    def update_lot(self, cr, uid, ids, context=None):
        lot_obj = self.pool.get('stock.production.lot')
        for move in self.browse(cr, uid, ids):
            if move.prodlot_id:
                raise osv.except_osv(unicode('Tạo Lô', 'utf8'), unicode('Số lô đã tồn tại', 'utf8'))
            lot_id = lot_obj.create(cr, uid, {
                'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.lot.serial'),
                'product_id': move.product_id.id,
            })
            cr.execute('update stock_move set prodlot_id = %s where id = %s',(lot_id,move.id))
        return True
    
    
    def check_assign(self, cr, uid, ids, context=None):
        """ Checks the product type and accordingly writes the state.
        @return: No. of moves done
        """
        done = []
        count = 0
        pickings = {}
        if context is None:
            context = {}
        for move in self.browse(cr, uid, ids, context=context):
            if move.product_id.type == 'consu' or move.location_id.usage == 'supplier':
                if move.state in ('confirmed', 'waiting'):
                    done.append(move.id)
                pickings[move.picking_id.id] = 1
                continue
            if move.state in ('confirmed', 'waiting'):
                # Important: we must pass lock=True to _product_reserve() to avoid race conditions and double reservations
                if not move.prodlot_id:
                    raise osv.except_osv(_('Warning!'),_("Please input Prodlot"))
                if not move.tracking_id:
                    res = self.pool.get('stock.location')._product_reserve(cr, uid, [move.location_id.id],move.prodlot_id.id, move.product_id.id, move.product_qty, {'uom': move.product_uom.id}, lock=True)
                else:
                    res = self.pool.get('stock.location')._product_reserve_tracking(cr, uid, [move.location_id.id],move.prodlot_id.id,move.tracking_id.id, move.product_id.id, move.product_qty, {'uom': move.product_uom.id}, lock=True)
                if res:
                    #_product_available_test depends on the next status for correct functioning
                    #the test does not work correctly if the same product occurs multiple times
                    #in the same order. This is e.g. the case when using the button 'split in two' of
                    #the stock outgoing form
                    self.write(cr, uid, [move.id], {'state':'assigned'})
                    done.append(move.id)
                    pickings[move.picking_id.id] = 1
                    r = res.pop(0)
                    product_uos_qty = self.pool.get('stock.move').onchange_quantity(cr, uid, ids, move.product_id.id, r[0], move.product_id.uom_id.id, move.product_id.uos_id.id)['value']['product_uos_qty']
                    cr.execute('update stock_move set location_id=%s, product_qty=%s, product_uos_qty=%s where id=%s', (r[1], r[0],product_uos_qty, move.id))

                    while res:
                        r = res.pop(0)
                        product_uos_qty = self.pool.get('stock.move').onchange_quantity(cr, uid, ids, move.product_id.id, r[0], move.product_id.uom_id.id, move.product_id.uos_id.id)['value']['product_uos_qty']
                        move_id = self.copy(cr, uid, move.id, {'product_uos_qty': product_uos_qty, 'product_qty': r[0], 'location_id': r[1]})
                        done.append(move_id)
                #Thanh: Raise Error if not enough Stock, inactive temporary
                else:
                    raise osv.except_osv(_('Warning!'),_("Not enough stock for Product '%s'.\nPlease ask for an Internal Moves to Location '%s' and Prodlot '%s'")%(move.product_id.name,move.location_id.name,move.prodlot_id.name))
        if done:
            count += len(done)
            self.write(cr, uid, done, {'state': 'assigned'})

        if count:
            for pick_id in pickings:
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_write(uid, 'stock.picking', pick_id, cr)
        return count
    
    def action_assign(self, cr, uid, ids, *args):
        #Overwritten to use .read() instead of .browse() which is slower
        """ Changes state to confirmed or waiting.
        @return: List of values
        """
        todo = []
        for move in self.read(cr, uid, ids, ['state']):
            if move['state'] in ('confirmed', 'waiting'):
                todo.append(move['id'])
            #THANH concurrent udpate
            res = self.check_assign(cr, uid, todo)
            cr.commit()
            #END
        return res
    
    def product_id_change(self, cr, uid, ids, product, location_id, location_dest_id, context=None):
        context = context or {}
        result = {}
        
        product_obj = self.pool.get('product.product').browse(cr, uid, product, context=context)
        if product_obj and product_obj.uom_id:
            result['product_uom'] = product_obj.uom_id.id
        result['name'] = product_obj.name
        result['location_id'] = location_id
        result['location_dest_id'] = location_dest_id
        return {'value': result}
    
    def action_done(self, cr, uid, ids, context=None):
        """ Makes the move done and if all moves are done, it will finish the picking.
        @return:
        """
        picking_ids = []
        move_ids = []
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}

        todo = []
        for move in self.browse(cr, uid, ids, context=context):
            if move.state=="draft":
                todo.append(move.id)
        if todo:
            self.action_confirm(cr, uid, todo, context=context)
            todo = []

        for move in self.browse(cr, uid, ids, context=context):
            if move.state in ['done','cancel']:
                continue
            move_ids.append(move.id)

            if move.picking_id:
                picking_ids.append(move.picking_id.id)
            if move.move_dest_id.id and (move.state != 'done'):
                # Downstream move should only be triggered if this move is the last pending upstream move
                other_upstream_move_ids = self.search(cr, uid, [('id','!=',move.id),('state','not in',['done','cancel']),
                                            ('move_dest_id','=',move.move_dest_id.id)], context=context)
                if not other_upstream_move_ids:
                    self.write(cr, uid, [move.id], {'move_history_ids': [(4, move.move_dest_id.id)]})
                    if move.move_dest_id.state in ('waiting', 'confirmed'):
                        self.force_assign(cr, uid, [move.move_dest_id.id], context=context)
                        if move.move_dest_id.picking_id:
                            wf_service.trg_write(uid, 'stock.picking', move.move_dest_id.picking_id.id, cr)
                        if move.move_dest_id.auto_validate:
                            self.action_done(cr, uid, [move.move_dest_id.id], context=context)
            
            #Thanh: Remove generating St_create_product_valuation_movesock Journal Entry from stock
#             self._create_product_valuation_moves(cr, uid, move, context=context)
            #Thanh: Remove generating Stock Journal Entry from stock
            
            if move.state not in ('confirmed','done','assigned'):
                todo.append(move.id)
            
            #Thanh" Update date done for move from Picking
#             if move.type == 'in' or (move.type=='out' and move.picking_return == 'supplier'):
            if context.get('prodlot_flag'):
                if move.prodlot_id.id:
                    self.write(cr, uid, [move.id],{'state': 'done', 'date':move.picking_id.date or time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
            else:
                self.write(cr, uid, [move.id],{'state': 'done', 'date':move.picking_id.date or time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
            #Thanh" Update date done for move from Picking
                
        if todo:
            self.action_confirm(cr, uid, todo, context=context)
        
        #Thanh: remove get date done for move from current date
#         self.write(cr, uid, move_ids, {'state': 'done', 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}, context=context)
        #Thanh: remove get date done for move from current date
        
        for id in move_ids:
            wf_service.trg_trigger(uid, 'stock.move', id, cr)

        for pick_id in picking_ids:
            wf_service.trg_write(uid, 'stock.picking', pick_id, cr)

        return True
    
    
    
    def action_scrap(self, cr, uid, ids, quantity, location_id, context=None):
        """ Move the scrap/damaged product into scrap location
        @param cr: the database cursor
        @param uid: the user id
        @param ids: ids of stock move object to be scrapped
        @param quantity : specify scrap qty
        @param location_id : specify scrap location
        @param context: context arguments
        @return: Scraped lines
        """
        #quantity should in MOVE UOM
        if quantity <= 0:
            raise osv.except_osv(_('Warning!'), _('Please provide a positive quantity to scrap.'))
        res = []
        for move in self.browse(cr, uid, ids, context=context):
            move_qty = move.product_qty
            uos_qty = quantity / move_qty * move.product_uos_qty
            default_val = {
                'product_qty': quantity,
                'product_uos_qty': uos_qty,
                'state': move.state,
                'scrapped' : True,
                'location_dest_id': location_id,
                'tracking_id': move.tracking_id.id,
                'prodlot_id': move.prodlot_id.id,
                'note': context and context.get('note', ''),
            }
            new_move = self.copy(cr, uid, move.id, default_val)

            res += [new_move]
            product_obj = self.pool.get('product.product')
            for product in product_obj.browse(cr, uid, [move.product_id.id], context=context):
                if move.picking_id:
                    uom = product.uom_id.name if product.uom_id else ''
                    message = _("%s %s %s has been <b>moved to</b> scrap.") % (quantity, uom, product.name)
                    move.picking_id.message_post(body=message)

        self.action_done(cr, uid, res, context=context)
        return res

#     def action_confirm(self, cr, uid, ids, context=None):
#         """ Confirms stock move.
#         @return: List of ids.
#         """
#         moves = self.browse(cr, uid, ids, context=context)
#         self.write(cr, uid, ids, {'state': 'confirmed'})
#         
#         new_moves=[]
#         for move in moves:
#             if move.location_id.usage == 'production' or move.location_id.usage == 'supplier' or move.location_dest_id.id == 11 or move.location_dest_id.id == 30: 
# #TODO: temporary fix to be remove with different handling of push flows.
#                 new_moves.append(move)
#         self.create_chained_picking(cr, uid, new_moves, context)
#         return []
    
    def theo_ngay_nhap(self, cr, uid, ids, context=None):
        locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')], context=None)
        for move in self.browse(cr, uid, ids):
            lot_ids = []
            sql='''
             SELECT prodlot_id, sum(qty)
                FROM 
                    stock_report_prodlots srp inner join 
                    stock_production_lot spl on spl.id = srp.prodlot_id
                WHERE 
                    spl.product_id = %s                        
                    and srp.location_id IN %s
                group by prodlot_id,date
                having sum(qty)>0
                order by date
            '''%(move.product_id.id,tuple(locations),)
            cr.execute(sql)
            for line in cr.dictfetchall():
                lot_ids.append(line['prodlot_id'])
            if lot_ids:
                self.write(cr, uid, [move.id], {'prodlot_id':lot_ids[0]})
            else:
                self.write(cr, uid, [move.id], {'prodlot_id':False})
        return True
    
    def theo_han_su_dung(self, cr, uid, ids, context=None):
        locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')], context=None)
        for move in self.browse(cr, uid, ids):
            lot_ids = []
            sql='''
             SELECT prodlot_id, sum(qty)
                FROM 
                    stock_report_prodlots srp inner join 
                    stock_production_lot spl on spl.id = srp.prodlot_id
                WHERE 
                    spl.product_id = %s
                    and life_date is not null
                    and life_date > '%s'  
                    and srp.location_id IN %s
                group by prodlot_id,life_date
                having sum(qty)>0
                order by life_date
            '''%(move.product_id.id,move.date_expected,tuple(locations),)
            cr.execute(sql)
            for line in cr.dictfetchall():
                lot_ids.append(line['prodlot_id'])
            if lot_ids:
                self.write(cr, uid, [move.id], {'prodlot_id':lot_ids[0]})
            else:
                self.write(cr, uid, [move.id], {'prodlot_id':False})
        return True
    
stock_move()

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    
    #Thanh: Change the way to get Sequence
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default = default.copy()
        picking_obj = self.browse(cr, uid, id, context=context)
        if picking_obj.type == 'internal':
#             if ('name' not in default) or (picking_obj.name == '/'):
#                 seq_obj_name = 'stock.picking.' + picking_obj.type
#                 default['name'] = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
#                 default['origin'] = ''
#                 default['backorder_id'] = False
            default['name'] = '/'
            if 'invoice_state' not in default and picking_obj.invoice_state == 'invoiced':
                default['invoice_state'] = '2binvoiced'
            res = super(osv.osv, self).copy(cr, uid, id, default, context)
            return res
        elif picking_obj.type =='in':
            default['name'] = '/'
            if 'invoice_state' not in default and picking_obj.invoice_state == 'invoiced':
                default['invoice_state'] = '2binvoiced'
            res = super(osv.osv, self).copy(cr, uid, id, default, context)
            return res
        elif picking_obj.type =='out':
            default['name'] = '/'
            if 'invoice_state' not in default and picking_obj.invoice_state == 'invoiced':
                default['invoice_state'] = '2binvoiced'
            res = super(osv.osv, self).copy(cr, uid, id, default, context)
            return res
        else:
            raise osv.except_osv(_('Warning!'), _('You are not able to Duplicate Incomming or Delivery Order.'))
    
    
    def allow_cancel(self, cr, uid, ids, context=None):
        for pick in self.browse(cr, uid, ids, context=context):
            if not pick.move_lines:
                return True
            for move in pick.move_lines:
                if move.state == 'done':
                    self.pool.get('stock.move').action_cancel(cr, uid,[move.id], context=context)
                    #raise osv.except_osv(_('Error!'), _('You cannot cancel the picking as some moves have been done. You should cancel the picking lines.'))
        return True
        
    def print_inphieu(self, cr, uid, ids, context=None): 
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'order_inphieu',
            }
    
    def create(self, cr, user, vals, context=None):
        context = context or {}
        context.update({'sequence_obj_ids':[]})
        if ('name' not in vals) or (vals.get('name')=='/'):
#             seq_obj_name =  self._name
            if vals.get('stock_journal_id',False):
                journal = self.pool.get('stock.journal').browse(cr, user, vals['stock_journal_id'])
                if not journal.sequence_id:
                    raise osv.except_osv(_('Warning!'), _('Please define Sequence for Stock Journal.'))
                
                if journal.source_type in ['in','return_customer']:
                    cr.execute('SELECT warehouse_id FROM stock_location WHERE id=%s'%(vals['location_dest_id']))
                    warehouse_id = cr.fetchone()
                    if warehouse_id and warehouse_id[0]:
                        context['sequence_obj_ids'].append(['warehouse',warehouse_id[0]])
                if journal.source_type in ['out','return_supplier','internal']:
                    cr.execute('SELECT warehouse_id FROM stock_location WHERE id=%s'%(vals['location_id']))
                    warehouse_id = cr.fetchone()
                    if warehouse_id and warehouse_id[0]:
                        context['sequence_obj_ids'].append(['warehouse',warehouse_id[0]])
                        
                vals['name'] = self.pool.get('ir.sequence').get_id(cr, user, journal.sequence_id.id, code_or_id='id', context=context)
                
        new_id = super(osv.osv, self).create(cr, user, vals, context)
        return new_id
    
    #Thanh: Change the way to get Sequence
    
    #Thanh: Re-open Picking
    def has_valuation_moves(self, cr, uid, move):
        return self.pool.get('account.move').search(cr, uid, [
            ('ref', '=', move.picking_id.name),
            ])

    def action_revert_done(self, cr, uid, ids, context=None):
        move_ids = []
        invoice_ids = []
        if not len(ids):
            return False
        
        sql ='''
            Select id 
            FROM
                stock_move where picking_id = %s
        '''%(ids[0])
        cr.execute(sql)
        for line in cr.dictfetchall():
            move_ids.append(line['id'])
        if move_ids:
            sql='''
                SELECT state ,id
                FROM account_invoice 
                WHERE id IN (
                     SELECT distinct invoice_id 
                     FROM account_invoice_line 
                     WHERE source_id in(%s))
            '''%(','.join(map(str,move_ids)))
            cr.execute(sql)
            for line in cr.dictfetchall():
                if line['state'] not in ('draft','cancel'):
                    raise osv.except_osv(
                        _('Error'),
                        _('You must first cancel all Invoice order(s) attached to this sales order.'))
                else:
                    invoice_ids.append(line['id'])
            if invoice_ids:
                self.pool.get('account.invoice').unlink(cr,uid,invoice_ids)
                
        for picking in self.browse(cr, uid, ids, context):
            for line in picking.move_lines:
                if self.has_valuation_moves(cr, uid, line):
                    raise osv.except_osv(
                        _('Error'),
                        _('Line %s has valuation moves (%s). \
                            Remove them first') % (line.name,
                                                   line.picking_id.name))
                line.write({'state': 'draft','invoiced_qty':0})
            self.write(cr, uid, [picking.id], {'state': 'draft'})
            if picking.invoice_state == 'invoiced':# and not picking.invoice_id:
                self.write(cr, uid, [picking.id],
                           {'invoice_state': '2binvoiced'})
            wf_service = netsvc.LocalService("workflow")
            # Deleting the existing instance of workflow
            wf_service.trg_delete(uid, 'stock.picking', picking.id, cr)
            wf_service.trg_create(uid, 'stock.picking', picking.id, cr)
        for (id, name) in self.name_get(cr, uid, ids):
            message = _(
                "The stock picking '%s' has been set in draft state."
                ) % (name,)
            self.log(cr, uid, id, message)
        return True
    #Thanh: Re-open Picking
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        account_tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'untax_amount': 0.0,
                'tax_amount':0.0,
                'total_amount':0.0,
            }
            cur = False
            if order.sale_id:
                cur = order.sale_id.pricelist_id.currency_id
            if order.purchase_id:
                cur = order.purchase_id.pricelist_id.currency_id
#             if order.pos_id:
#                 cur = order.pos_id.pricelist_id.currency_id
            
            val = val1 = 0.0
            for line in order.move_lines:
               val1 += line.price_subtotal
               taxes = line.product_id.taxes_id
               price = line.price_unit
                
               if line.sale_line_id:
                   price = line.sale_line_id.price_unit * (1 - (line.sale_line_id.discount or 0.0) / 100.0)
                   taxes = line.sale_line_id.tax_id
            
               if line.purchase_line_id:
                   price = line.price_unit
                   taxes = line.purchase_line_id.taxes_id
                   
#                if line.pos_line_id:
#                    price = line.price_unit
#                    taxes = line.pos_line_id.product_id and line.pos_line_id.product_id.taxes_id or False
                
               for c in account_tax_obj.compute_all(cr, uid, taxes, price, line.product_qty, product=line.product_id, partner=line.picking_id.partner_id or False)['taxes']:
                    val += c.get('amount', 0.0)
            
            if cur:
                val = cur_obj.round(cr, uid, cur, val)
                val1 = cur_obj.round(cr, uid, cur, val1)
                
            res[order.id]['tax_amount']= val
            res[order.id]['untax_amount']= val1
            res[order.id]['total_amount']=res[order.id]['untax_amount'] + res[order.id]['tax_amount']
            
        return res
    
    def _get_stock_move(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()
    
    def _get_location_info(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        shop_id = False
        warehouse_id = False
        for pick in self.browse(cr, uid, ids, context=context):
            
            res[pick.id] = {
                            'shop_id': False,
                            'warehouse_id': False,
                            }
            
            if pick.location_id.usage =='internal':
                warehouse_id = pick.location_id and pick.location_id.warehouse_id.id or False
            if not warehouse_id:
                if pick.location_dest_id.usage =='internal':
                    warehouse_id = pick.location_dest_id and pick.location_dest_id.warehouse_id.id or False
                
            
            if warehouse_id:
                res[pick.id]['warehouse_id'] = warehouse_id
                sql='''
                    SELECT id FROM sale_shop WHERE warehouse_id = %s
                '''%(warehouse_id)
                cr.execute(sql)
                shop_res = cr.fetchone()
                shop_id = shop_res and shop_res[0] or False
            if shop_id:
                res[pick.id]['shop_id'] = shop_id
        return res
    
    def _compute_date_user_tz(self, cr, uid, ids, fieldnames, args, context=None):  
        user_pool = self.pool.get('res.users')
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'date_done_user_tz': False,
                'day_done_user_tz': False,
            }
            
            if obj.date_done:
                date_user_tz = user_pool._convert_user_datetime(cr, uid, obj.date_done)
                res[obj.id]['date_done_user_tz'] = date_user_tz.strftime('%Y-%m-%d')
                res[obj.id]['day_done_user_tz'] = date_user_tz.strftime('%d-%m-%Y')
        return res
    
    # Ham kiem ke kho trung chuyen 
    def _get_check_flag(self, cr, uid, ids, fieldnames, args, context=None):  
        res = {}
        check_flag= False
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.type =='out' and obj.sale_id:
                res[obj.id] = check_flag
                for line in obj.move_lines:
                    if line.location_dest_id.usage=='inventory':
                        check_flag= True,
                        res[obj.id] = check_flag
        return res
    
    def update_flag(self,cr,uid,pik,context=None):
        pick_obj = self.pool.get('stock.picking').browse(cr,uid,pik)
        flag= False
        for move in pick_obj.move_lines:
            if move.location_dest_id.usage == 'inventory':
                flag = True
        sql='''
            update stock_picking set check_flag = %s where id = %s
        '''%(flag,pick_obj.id)
        cr.execute(sql)
        
    _columns = {
        # kiet: Add fields warehouse theo location
        'shop_id': fields.function(_get_location_info, type='many2one', relation='sale.shop', string='Shop',
            store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['location_id','location_dest_id'], 10),
            }, readonly=True, multi='lo_info'),
        'warehouse_id': fields.function(_get_location_info, type='many2one', relation='stock.warehouse', string='Warehouse',
            store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['location_id','location_dest_id'], 10),
            }, readonly=True, multi='lo_info'),
        
        #Thanh: Add these field to help searching datas easily
        'date_done_user_tz': fields.function(_compute_date_user_tz, type='date', method=True, string='Date Done', store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['date_done'], 10),
                }, multi='tz'),
        
        'day_done_user_tz': fields.function(_compute_date_user_tz, type='char', method=True, string='Day Done', store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['date_done'], 10),
            }, multi='tz'),
                
        #Thanh: Add field Receipt User for menu Internal Moves
        'receipt_user': fields.char('Receipt User', size=300),
        
        'untax_amount': fields.function(_amount_all, string='Untaxed Amount', digit=(16,2), multi='all',
          store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                'stock.move': (_get_stock_move, ['price_unit','product_qty','picking_id'], 20),
            }),
        'tax_amount': fields.function(_amount_all, string='Tax Amount', digit=(16,2), multi='all',
          store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                'stock.move': (_get_stock_move, ['price_unit','product_qty','picking_id'], 20),
            }),
        'total_amount': fields.function(_amount_all, string='Total Amount', digit=(16,2), multi='all',
          store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                'stock.move': (_get_stock_move, ['price_unit','product_qty','picking_id'], 20),
            }),
                
        # kiet.
        
        'check_flag': fields.function(_get_check_flag, type='boolean',  string='check_domain',
            store={
                'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 10),
                'stock.move': (_get_stock_move, ['state','location_dest_id'], 20),
            }, readonly=True),
                
        #Thanh: Set Journal always required
        'stock_journal_id': fields.many2one('stock.journal','Stock Journal', required=True, select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}, track_visibility='onchange'),
        
        'return': fields.selection([('none', 'Normal'), ('customer', 'Return from Customer'),('internal','Return Internal'), ('supplier', 'Return to Supplier')], 'Type', required=True, select=True, help="Type specifies whether the Picking has been returned or not."),
        'write_date':  fields.datetime('Last Modification', readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'write_uid':  fields.many2one('res.users', 'Updated by', readonly=True),
        'create_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'return_reason_id': fields.many2one('stock.return.reason', 'Return Reason', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
        'nhietdo_di':fields.char('Nhiệt độ khi đi'),
        'nhietdo_den':fields.char('Nhiệt độ khi đến'),
    }
    
    def _get_journal(self, cr, uid, context=None):
        journal_domain = []
        if context.get('default_type',False) and context.get('default_return',False):
            default_type = context['default_type']
            default_return = context['default_return']
            if default_type == 'in':
                journal_domain = [('source_type', '=', 'in')]
                if default_return == 'customer':
                    journal_domain = [('source_type', '=', 'return_customer')]
            if default_type == 'out':
                journal_domain = [('source_type', '=', 'out')]
                if default_return == 'supplier':
                    journal_domain = [('source_type', '=', 'return_supplier')]
        else:
            journal_domain = [('source_type', '=', 'internal')]
        journal_ids = self.pool.get('stock.journal').search(cr, uid, journal_domain)
        return journal_ids and journal_ids[0] or False
    
    _defaults = {    
        'return': 'none',
        'type':   'internal',
        
        'stock_journal_id': _get_journal,
    }
    
    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        """ Builds the dict containing the values for the invoice
            @param picking: picking object
            @param partner: object of the partner to invoice
            @param inv_type: type of the invoice ('out_invoice', 'in_invoice', ...)
            @param journal_id: ID of the accounting journal
            @return: dict that will be used to create the invoice object
        """
        if isinstance(partner, int):
            partner = self.pool.get('res.partner').browse(cr, uid, partner, context=context)
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable.id
            payment_term = partner.property_payment_term.id or False
        else:
            account_id = partner.property_account_payable.id
            payment_term = partner.property_supplier_payment_term.id or False
        comment = self._get_comment_invoice(cr, uid, picking)
        
        #Thanh: Get Shop where Warehouse belonging to
        warehouse_id = picking.location_id.warehouse_id.id or False
        if not warehouse_id:
            warehouse_id = picking.location_dest_id.warehouse_id.id or False
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('warehouse_id','=',warehouse_id)])
        invoice_vals = {
            'name': picking.name,
            'origin': (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
            'type': inv_type,
            'account_id': account_id,
            'partner_id': partner.id,
            'comment': comment,
            'payment_term': payment_term,
            'fiscal_position': partner.property_account_position.id,
            'date_invoice': context.get('date_inv', False),
            'company_id': picking.company_id.id,
            'user_id': uid,
            # kiet them cai mau hoa don
            'number_register':partner and partner.number_register or False,
            
            #Thanh: add more fields
            'shop_id': shop_ids and shop_ids[0] or False,
        }
        cur_id = self.get_currency_id(cr, uid, picking)
        if cur_id:
            invoice_vals['currency_id'] = cur_id
        if journal_id:
            invoice_vals['journal_id'] = journal_id
        return invoice_vals
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        journal_obj = self.pool.get('stock.journal')
        if context is None:
            context = {}
        res = super(stock_picking,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        
        if view_type == 'form':
            journal_ids = []
            if context.get('default_type',False):
                journal_domain = []
                if context.get('default_return',False):
                    default_type = context['default_type']
                    default_return = context['default_return']
                    if default_type == 'in':
                        journal_domain = [('source_type', '=', 'in')]
                        if default_return == 'customer':
                            journal_domain = [('source_type', '=', 'return_customer')]
                    if default_type == 'out':
                        journal_domain = [('source_type', '=', 'out')]
                        if default_return == 'supplier':
                            journal_domain = [('source_type', '=', 'return_supplier')]
                
                if context['default_type'] == 'internal':
                    journal_domain = [('source_type', '=', 'internal')]
                if context.get('search_source_type',False) and context['search_source_type'] == 'production':
                    journal_domain = [('source_type', '=', 'production')]
                if context.get('search_source_type',False) and context['search_source_type'] == 'phys_adj':
                    journal_domain = [('source_type', '=', 'phys_adj')]
                    
                journal_ids = journal_obj._name_search(cr, uid, '', journal_domain, context=context, limit=None, name_get_uid=1)
            if journal_ids != []:
                for field in res['fields']:
                    if field == 'stock_journal_id':
                        res['fields'][field]['selection'] = journal_ids
        return res
    
    def onchange_journal(self, cr, uid, ids, stock_journal_id):
        value ={}
        domain = {}
        if not stock_journal_id:
            value.update({'location_id':False,
                           'location_dest_id':False})
            domain.update({'location_id':[('id','=',False)],
                           'location_dest_id':[('id','=',False)]})
        else:
            journal = self.pool.get('stock.journal').browse(cr, uid, stock_journal_id)
            from_location_ids = [x.id for x in journal.from_location_id]
            to_location_ids = [x.id for x in journal.to_location_id]
            domain.update({'location_id':[('id','=',from_location_ids)],
                           'location_dest_id':[('id','=',to_location_ids)]})
            location_id = from_location_ids and from_location_ids[0] or False
            location_dest_id = False
            if to_location_ids and to_location_ids[0] != location_id:
                location_dest_id = to_location_ids[0]
            value.update({'location_id':location_id,
                          'location_dest_id': location_dest_id})
        return {'value': value,'domain':domain} 
    
    def onchange_location(self,cr,uid,ids,location_id,location_dest_id,move_lines):
        if location_id and location_dest_id and location_id == location_dest_id:
            value ={}
            value.update({'location_dest_id':False})
            warning = {
            'title': _('Location Warning!'),
            'message' : _('Location = Location Dest')
            }
            return {'value': value, 'warning': warning} 
        if location_id:
            i = 0
            for line in move_lines:
                if not line[2]:
                    move_lines[i][0] = 1
                    move_lines[i][2] = {'location_id':location_id}
                else:
                    move_lines[i][2]['location_id'] = location_id
                i+= 1
        if location_dest_id:
            i = 0
            for line in move_lines:
                if not line[2]:
                    move_lines[i][0] = 1
                    move_lines[i][2] = {'location_dest_id':location_dest_id}
                else:
                    move_lines[i][2]['location_dest_id'] = location_dest_id
                i+= 1
        
        result ={
                 'move_lines': move_lines,
                 'location_id': location_id,
                 }
        
        return  {'value': result}
    
    def _get_price_unit_invoice(self, cr, uid, move_line, type, context=None):
        """ Gets price unit for invoice
        @param move_line: Stock move lines
        @param type: Type of invoice
        @return: The price unit for the move line
        """
#         if context is None:
#             context = {}
# 
#         if type in ('in_invoice', 'in_refund'):
#             # Take the user company and pricetype
#             context['currency_id'] = move_line.company_id.currency_id.id
#             amount_unit = move_line.product_id.price_get('standard_price', context=context)[move_line.product_id.id]
#             
#             return amount_unit
#         else:
#             return move_line.product_id.list_price
#         
        # kiet sua gia
        price =0.0
        if move_line.sale_line_id:
            if move_line.sale_line_id.price_unit:
                price = move_line.sale_line_id.price_unit
                
        if move_line.purchase_line_id:
            price = move_line.purchase_line_id.price_unit
            
        return price or 0.0
    
    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
        invoice_vals, context=None):
        """ Builds the dict containing the values for the invoice line
            @param group: True or False
            @param picking: picking object
            @param: move_line: move_line object
            @param: invoice_id: ID of the related invoice
            @param: invoice_vals: dict used to created the invoice
            @return: dict that will be used to create the invoice line
        """
        if group:
            name = (picking.name or '') + '-' + move_line.name
        else:
            name = move_line.name
        origin = move_line.picking_id.name or ''
        if move_line.picking_id.origin:
            origin += ':' + move_line.picking_id.origin

        if invoice_vals['type'] in ('out_invoice', 'out_refund'):
            account_id = move_line.product_id.property_account_income.id
            if not account_id:
                account_id = move_line.product_id.categ_id.\
                        property_account_income_categ.id
        else:
            account_id = move_line.product_id.property_account_expense.id
            if not account_id:
                account_id = move_line.product_id.categ_id.\
                        property_account_expense_categ.id
        if invoice_vals['fiscal_position']:
            fp_obj = self.pool.get('account.fiscal.position')
            fiscal_position = fp_obj.browse(cr, uid, invoice_vals['fiscal_position'], context=context)
            account_id = fp_obj.map_account(cr, uid, fiscal_position, account_id)
        # set UoS if it's a sale and the picking doesn't have one
        uos_id = move_line.product_uos and move_line.product_uos.id or False
        if not uos_id and invoice_vals['type'] in ('out_invoice', 'out_refund'):
            uos_id = move_line.product_uom.id
            
        quantity =  move_line.product_uos_qty or move_line.product_qty
        if context.get('invoicing_list',False):
            quantity = 0
            for line in context['invoicing_list']:
                if move_line.id == line.move_id.id and line.check_invoice:
                    quantity = line.quantity
                    self.pool.get('stock.move').write(cr,uid,move_line.id,{'invoiced_qty':move_line.invoiced_qty + quantity})
                    break
        if quantity:
            return {
                'name': name,
                'origin': origin,
                'invoice_id': invoice_id,
                'uos_id': uos_id,
                'product_id': move_line.product_id.id,
                'account_id': account_id,
                'price_unit': self._get_price_unit_invoice(cr, uid, move_line, invoice_vals['type']),
                'discount': self._get_discount_invoice(cr, uid, move_line),
                'quantity': quantity,
                'invoice_line_tax_id': [(6, 0, self._get_taxes_invoice(cr, uid, move_line, invoice_vals['type']))],
                'account_analytic_id': self._get_account_analytic_invoice(cr, uid, picking, move_line),
                'source_obj':'stock.move',
                'source_id':move_line.id,
                #Hung moi them so lo vao invoice line
                'prodlot_id':move_line.prodlot_id.id,
                'adjust_price':move_line.purchase_line_id and move_line.purchase_line_id.adjust_price or 0.0, 
            }

        else:
            return {}
    
    def action_invoice_create(self, cr, uid, ids, journal_id=False,group=False, type='out_invoice', context=None):
        """ Creates invoice based on the invoice state selected for picking.
        @param journal_id: Id of journal
        @param group: Whether to create a group invoice or not
        @param type: Type invoice to be created
        @return: Ids of created invoices for the pickings
        """
        if context is None:
            context = {}

        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        partner_obj = self.pool.get('res.partner')
        invoices_group = {}
        res = {}
        inv_type = type
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.invoice_state != '2binvoiced':
                continue
            partner = self._get_partner_to_invoice(cr, uid, picking, context=context)
            if isinstance(partner, int):
                partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
            if not partner:
                raise osv.except_osv(_('Error, no partner!'),
                    _('Please put a partner on the picking list if you want to generate invoice.'))

            if not inv_type:
                inv_type = self._get_invoice_type(picking)

            if group and partner.id in invoices_group:
                invoice_id = invoices_group[partner.id]
                invoice = invoice_obj.browse(cr, uid, invoice_id)
                invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
                invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
            else:
                invoice_vals = self._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
                invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
                invoices_group[partner.id] = invoice_id
            res[picking.id] = invoice_id
            for move_line in picking.move_lines:
                if move_line.state == 'cancel':
                    continue
                if move_line.scrapped:
                    # do no invoice scrapped products
                    continue
                vals = self._prepare_invoice_line(cr, uid, group, picking, move_line,
                                invoice_id, invoice_vals, context=context)
                if vals:
                    invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
                    self._invoice_line_hook(cr, uid, move_line, invoice_line_id)
                    
            invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
                    set_total=(inv_type in ('in_invoice', 'in_refund')))
            
            
        for picking in self.browse(cr, uid, res.keys(), context=context):
            invoiced=True
            for line in picking.move_lines:
                return_qty = self.pool.get('stock.invoice.onshipping').get_returned_qty(cr,uid,line)
                invoicing_qty = line.product_qty - return_qty 
                if invoicing_qty != line.invoiced_qty:
                    invoiced = False
                    break
            if invoiced:
                self.write(cr, uid, [picking.id], {
                'invoice_state': 'invoiced',
                }, context=context)    
            
        return res
    
    def action_done(self, cr, uid, ids, context=None):
        """Changes picking state to done.
        
        This method is called at the end of the workflow by the activity "done".
        @return: True
        """
        self.write(cr, uid, ids, {'state': 'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')})
        
        return True
    
    
        
        return True
    
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        """ Makes partial picking and moves done.
        @param partial_datas : Dictionary containing details of partial picking
                          like partner_id, partner_id, delivery_date,
                          delivery moves with product_id, product_qty, uom
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        else:
            context = dict(context)
        res = {}
        location={}
         
        #Thanh: Declare Object
#         cost_detail_pool = self.pool.get("stock.actual.cost.details")
#         cost_layer_pool = self.pool.get("stock.item.cost.layers")
        #end: Thanh
         
        move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        sequence_obj = self.pool.get('ir.sequence')
        wf_service = netsvc.LocalService("workflow")
        date_done = partial_datas.get('delivery_date',False)
        for pick in self.browse(cr, uid, ids, context=context):
            new_picking = None
            complete, too_many, too_few = [], [], []
            move_product_qty, prodlot_ids, product_avail, partial_qty, product_uoms = {}, {}, {}, {}, {}
            for move in pick.move_lines:
                if move.state in ('done', 'cancel'):
                    continue
                partial_data = partial_datas.get('move%s'%(move.id), {})
                product_qty = partial_data.get('product_qty',0.0)
                move_product_qty[move.id] = product_qty
                product_uom = partial_data.get('product_uom',False)
                product_price = partial_data.get('product_price',0.0)
                product_currency = partial_data.get('product_currency',False)
                prodlot_id = partial_data.get('prodlot_id')
                prodlot_ids[move.id] = prodlot_id
                product_uoms[move.id] = product_uom
                partial_qty[move.id] = uom_obj._compute_qty(cr, uid, product_uoms[move.id], product_qty, move.product_uom.id)
                
                # Kiet add location 
                location[move.id] = partial_data.get('location_dest_id',False)
                if move.product_qty == partial_qty[move.id]:
                    complete.append(move)
                elif move.product_qty > partial_qty[move.id]:
                    too_few.append(move)
                else:
                    too_many.append(move)
                
                    
            for move in too_few:
                product_qty = move_product_qty[move.id]
                if not new_picking:
                    new_picking_name = pick.name
                    self.write(cr, uid, [pick.id], 
                               {'name': sequence_obj.get(cr, uid,
                                            'stock.picking.%s'%(pick.type)),
                               })
                    new_picking = self.copy(cr, uid, pick.id,
                            {
                                'name': new_picking_name,
                                'move_lines' : [],
                                'state':'draft',
                            })
                if product_qty != 0:
                    defaults = {
                            'product_qty' : product_qty,
                            'product_uos_qty': product_qty, #TODO: put correct uos_qty
                            'picking_id' : new_picking,
                            'state': 'assigned',
                            'move_dest_id': False,
                            'price_unit': move.price_unit,
                            'product_uom': product_uoms[move.id],
                            'location_dest_id':location[move.id]
                    }
                    prodlot_id = prodlot_ids[move.id]
                    if prodlot_id:
                        defaults.update(prodlot_id=prodlot_id)
                    move_obj.copy(cr, uid, move.id, defaults)
                move_obj.write(cr, uid, [move.id],
                        {
                            'product_qty': move.product_qty - partial_qty[move.id],
                            'product_uos_qty': move.product_qty - partial_qty[move.id], #TODO: put correct uos_qty
                            'prodlot_id': False,
                            'tracking_id': False,
                        })
 
            if new_picking:
                move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
            for move in complete:
                defaults = {'location_dest_id':location[move.id],'product_uom': product_uoms[move.id], 'product_qty': move_product_qty[move.id]}
                if prodlot_ids.get(move.id):
                    defaults.update({'prodlot_id': prodlot_ids[move.id]})
                move_obj.write(cr, uid, [move.id], defaults)
            for move in too_many:
                product_qty = move_product_qty[move.id]
                defaults = {
                    'product_qty' : product_qty,
                    'product_uos_qty': product_qty, #TODO: put correct uos_qty
                    'product_uom': product_uoms[move.id],
                    'location_dest_id':location[move.id]
                }
                prodlot_id = prodlot_ids.get(move.id)
                if prodlot_ids.get(move.id):
                    defaults.update(prodlot_id=prodlot_id)
                if new_picking:
                    defaults.update(picking_id=new_picking)
                move_obj.write(cr, uid, [move.id], defaults)
 
            # At first we confirm the new picking (if necessary)
            if new_picking:
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                # Then we finish the good picking
                self.write(cr, uid, [pick.id], {'backorder_id': new_picking})
                self.action_move(cr, uid, [new_picking], context={'date_done':date_done})
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
                wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
                delivered_pack_id = pick.id
                back_order_name = self.browse(cr, uid, delivered_pack_id, context=context).name
                self.message_post(cr, uid, new_picking, body=_("Back order <em>%s</em> has been <b>created</b>.") % (back_order_name), context=context)
                self.write(cr, uid, [new_picking], {'date_done':date_done})
            else:
                self.action_move(cr, uid, [pick.id], context={'date_done':date_done})
                self.write(cr, uid, [pick.id], {'date_done':date_done})
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
                delivered_pack_id = pick.id
 
            delivered_pack = self.browse(cr, uid, delivered_pack_id, context=context)
            res[pick.id] = {'delivered_picking': delivered_pack.id or False}
 
        return res
    
class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'
    
    def _get_location_info(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        shop_id = False
        warehouse_id = False
        for pick in self.browse(cr, uid, ids, context=context):
            
            res[pick.id] = {
                            'shop_id': False,
                            'warehouse_id': False,
                            }
            
            if pick.location_id.usage =='internal':
                warehouse_id = pick.location_id and pick.location_id.warehouse_id and pick.location_id.warehouse_id.id or False
            if not warehouse_id:
                if pick.location_dest_id.usage =='internal':
                    warehouse_id = pick.location_dest_id and pick.location_dest_id.warehouse_id and pick.location_dest_id.warehouse_id.id or False
                
            
            if warehouse_id:
                res[pick.id]['warehouse_id'] = warehouse_id
                sql='''
                    SELECT id FROM sale_shop WHERE warehouse_id = %s
                '''%(warehouse_id)
                cr.execute(sql)
                shop_res = cr.fetchone()
                shop_id = shop_res and shop_res[0] or False
            if shop_id:
                res[pick.id]['shop_id'] = shop_id
        return res
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        return self.pool.get('stock.picking').fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
    
    def copy(self, cr, uid, id, default=None, context=None):
        return self.pool.get('stock.picking').copy(cr, uid, id, default, context)
        
    def action_revert_done(self, cr, uid, ids, context=None):
        #override in order to redirect to stock.picking object
        return self.pool.get('stock.picking').action_revert_done(
            cr, uid, ids, context=context)
        
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        account_tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'untax_amount': 0.0,
                'tax_amount':0.0,
                'total_amount':0.0,
            }
            cur = False
            if order.purchase_id:
                cur = order.purchase_id.pricelist_id.currency_id
            
            val = val1 = 0.0
            for line in order.move_lines:
               val1 += line.price_subtotal
               taxes = line.product_id.taxes_id
               price = line.price_unit
                
               if line.purchase_line_id:
                   price = line.price_unit
                   taxes = line.purchase_line_id.taxes_id
                   
               for c in account_tax_obj.compute_all(cr, uid, taxes, price, line.product_qty, product=line.product_id, partner=line.picking_id.partner_id or False)['taxes']:
                    val += c.get('amount', 0.0)
            
            if cur:
                val = cur_obj.round(cr, uid, cur, val)
                val1 = cur_obj.round(cr, uid, cur, val1)
                
            res[order.id]['tax_amount']= val
            res[order.id]['untax_amount']= val1
            res[order.id]['total_amount']=res[order.id]['untax_amount'] + res[order.id]['tax_amount']
            
        return res
    
    def _get_stock_move(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()
    
    def _partial_picking_change(self,cr,uid,ids,context=None):
        result = []
        for partial in self.browse(cr, uid, ids, context=context):
            result.append(partial.picking_id.id)
        result = list(set(result))
        return result
    
    def _compute_date_user_tz(self, cr, uid, ids, fieldnames, args, context=None):  
        user_pool = self.pool.get('res.users')
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'date_done_user_tz': False,
                'day_done_user_tz': False,
            }
            
            if obj.date_done:
                date_user_tz = user_pool._convert_user_datetime(cr, uid, obj.date_done)
                res[obj.id]['date_done_user_tz'] = date_user_tz.strftime('%Y-%m-%d')
                res[obj.id]['day_done_user_tz'] = date_user_tz.strftime('%d-%m-%Y')
        return res
    
    _columns = {
        # kiet: Add fields warehouse theo location
        'shop_id': fields.function(_get_location_info, type='many2one', relation='sale.shop', string='Shop',
            store={
                'stock.picking.in': (lambda self, cr, uid, ids, c={}: ids, ['location_id','location_dest_id'], 10),
            }, readonly=True, multi='pro_info'),
        'warehouse_id': fields.function(_get_location_info, type='many2one', relation='stock.warehouse', string='Warehouse',
            store={
                'stock.picking.in': (lambda self, cr, uid, ids, c={}: ids, ['location_id','location_dest_id'], 10),
            }, readonly=True, multi='pro_info'),
                
        'untax_amount': fields.function(_amount_all, string='Untaxed Amount', digit=(16,2), multi='all',
          store={
                'stock.picking.in': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                'stock.move': (_get_stock_move, ['price_unit','product_qty','picking_id'], 20),
            }, track_visibility='onchange'),
        'tax_amount': fields.function(_amount_all, string='Tax Amount', digit=(16,2), multi='all',
          store={
                'stock.picking.in': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                'stock.move': (_get_stock_move, ['price_unit','product_qty','picking_id'], 20),
            }, track_visibility='onchange'),
        'total_amount': fields.function(_amount_all, string='Total Amount', digit=(16,2), multi='all',
          store={
                'stock.picking.in': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                'stock.move': (_get_stock_move, ['price_unit','product_qty','picking_id'], 20),
            }, track_visibility='onchange'),
        
        #Thanh: Add these field to help searching datas easily
        'date_done_user_tz': fields.function(_compute_date_user_tz, type='date', method=True, string='Date Done', store={
                'stock.picking.in': (lambda self, cr, uid, ids, c={}: ids, ['date_done'], 10),
                }, multi='tz'),
        
        'day_done_user_tz': fields.function(_compute_date_user_tz, type='char', method=True, string='Day Done', store={
                'stock.picking.in': (lambda self, cr, uid, ids, c={}: ids, ['date_done'], 10),
            }, multi='tz'),
                
        'stock_journal_id': fields.many2one('stock.journal','Stock Journal', required=True, select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}, track_visibility='onchange'),
        'return': fields.selection([('none', 'Normal'), ('customer', 'Return from Customer'), ('supplier', 'Return to Supplier')], 'Type', required=True, select=True, help="Type specifies whether the Picking has been returned or not."),
        'write_date':  fields.datetime('Last Modification', readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'write_uid':  fields.many2one('res.users', 'Updated by', readonly=True),
        'create_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'return_reason_id': fields.many2one('stock.return.reason', 'Return Reason'),
    }
    
    _defaults = {    
        'return': 'none',
        'type':   'in',
    }
    
    def print_report(self, cr, uid, ids, context=None):
#         if context and context.get('report_type'):
#             if context['report_type'] =='receipt_order':
                return {
                        'type': 'ir.actions.report.xml',
                        'report_name': 'bienban_kiemkho_thanhpham_lanh',
                    }
    
    def print_report_template_2(self, cr, uid, ids, context=None):
#         if context and context.get('report_type'):
#             if context['report_type'] =='receipt_order':
                return {
                        'type': 'ir.actions.report.xml',
                        'report_name': 'bienban_kiemkho_thanhpham',
                    }
    
    def create(self, cr, user, vals, context=None):
        context = context or {}
        if context.get('no_create',False):
            raise osv.except_osv(_('Creation Error!'), _('You cannot create a Picking in this menu'))
        context.update({'sequence_obj_ids':[]})
        if ('name' not in vals) or (vals.get('name')=='/'):
#             seq_obj_name =  self._name
            if vals.get('stock_journal_id',False):
                journal = self.pool.get('stock.journal').browse(cr, user, vals['stock_journal_id'])
                if not journal.sequence_id:
                    raise osv.except_osv(_('Warning!'), _('Please define Sequence for Stock Journal.'))
                
                if journal.source_type in ['in','return_customer']:
                    cr.execute('SELECT warehouse_id FROM stock_location WHERE id=%s'%(vals['location_dest_id']))
                    warehouse_id = cr.fetchone()
                    if warehouse_id and warehouse_id[0]:
                        context['sequence_obj_ids'].append(['warehouse',warehouse_id[0]])
                if journal.source_type in ['out','return_supplier','internal']:
                    cr.execute('SELECT warehouse_id FROM stock_location WHERE id=%s'%(vals['location_id']))
                    warehouse_id = cr.fetchone()
                    if warehouse_id and warehouse_id[0]:
                        context['sequence_obj_ids'].append(['warehouse',warehouse_id[0]])
                        
                vals['name'] = self.pool.get('ir.sequence').get_id(cr, user, journal.sequence_id.id, code_or_id='id', context=context)
                
        new_id = super(osv.osv, self).create(cr, user, vals, context)
        return new_id
    
class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    
    def _get_location_info(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        shop_id = False
        warehouse_id = False
        for pick in self.browse(cr, uid, ids, context=context):
            res[pick.id] = {
                            'shop_id': False,
                            'warehouse_id': False,
                            }
            if pick.location_id.usage =='internal':
                warehouse_id = pick.location_id and pick.location_id.warehouse_id.id or False
            if not warehouse_id:
                if pick.location_dest_id.usage =='internal':
                    warehouse_id = pick.location_dest_id and pick.location_dest_id.warehouse_id.id or False
                
            
            if warehouse_id:
                res[pick.id]['warehouse_id'] = warehouse_id
                sql='''
                    SELECT id FROM sale_shop WHERE warehouse_id = %s
                '''%(warehouse_id)
                cr.execute(sql)
                shop_res = cr.fetchone()
                shop_id = shop_res and shop_res[0] or 0
            if shop_id:
                res[pick.id]['shop_id'] = shop_id
        return res
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        return self.pool.get('stock.picking').fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
    
    def copy(self, cr, uid, id, default=None, context=None):
        return self.pool.get('stock.picking').copy(cr, uid, id, default, context)
    
    def action_revert_done(self, cr, uid, ids, context=None):
        #override in order to redirect to stock.picking object
        return self.pool.get('stock.picking').action_revert_done(
            cr, uid, ids, context=context)
        
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        account_tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'untax_amount': 0.0,
                'tax_amount':0.0,
                'total_amount':0.0,
            }
            cur = False
            if order.sale_id:
                cur = order.sale_id.pricelist_id.currency_id
            
            val = val1 = 0.0
            for line in order.move_lines:
               val1 += line.price_subtotal
               taxes = line.product_id.taxes_id
               price = line.price_unit
                
               if line.sale_line_id:
                   price = line.sale_line_id.price_unit * (1 - (line.sale_line_id.discount or 0.0) / 100.0)
                   taxes = line.sale_line_id.tax_id
                   
               for c in account_tax_obj.compute_all(cr, uid, taxes, price, line.product_qty, product=line.product_id, partner=line.picking_id.partner_id or False)['taxes']:
                    val += c.get('amount', 0.0)
            
            if cur:
                val = cur_obj.round(cr, uid, cur, val)
                val1 = cur_obj.round(cr, uid, cur, val1)
                
            res[order.id]['tax_amount']= val
            res[order.id]['untax_amount']= val1
            res[order.id]['total_amount']=res[order.id]['untax_amount'] + res[order.id]['tax_amount']
            
        return res
    
    def _get_stock_move(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()
    
    def _partial_picking_change(self,cr,uid,ids,context=None):
        result = []
        for partial in self.browse(cr, uid, ids, context=context):
            result.append(partial.picking_id.id)
        result = list(set(result))
        return result
    
    def _compute_date_user_tz(self, cr, uid, ids, fieldnames, args, context=None):  
        user_pool = self.pool.get('res.users')
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = {
                'date_done_user_tz': False,
                'day_done_user_tz': False,
            }
            
            if obj.date_done:
                date_user_tz = user_pool._convert_user_datetime(cr, uid, obj.date_done)
                res[obj.id]['date_done_user_tz'] = date_user_tz.strftime('%Y-%m-%d')
                res[obj.id]['day_done_user_tz'] = date_user_tz.strftime('%d-%m-%Y')
        return res
    
    _columns = {
        # kiet: Add fields warehouse theo location
        'shop_id': fields.function(_get_location_info, type='many2one', relation='sale.shop', string='Shop',
            store={
                'stock.picking.out': (lambda self, cr, uid, ids, c={}: ids, ['location_id','location_dest_id'], 10),
            }, readonly=True, multi='pro_info'),
        'warehouse_id': fields.function(_get_location_info, type='many2one', relation='stock.warehouse', string='Warehouse',
            store={
                'stock.picking.out': (lambda self, cr, uid, ids, c={}: ids, ['location_id','location_dest_id'], 10),
            }, readonly=True, multi='pro_info'),
                
        'untax_amount': fields.function(_amount_all, string='Untaxed Amount', digit=(16,2), multi='all',
          store={
                'stock.picking.out': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                'stock.move': (_get_stock_move, ['price_unit','product_qty','picking_id'], 20),
            }),
        'tax_amount': fields.function(_amount_all, string='Tax Amount', digit=(16,2), multi='all',
          store={
                'stock.picking.out': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                'stock.move': (_get_stock_move, ['price_unit','product_qty','picking_id'], 20),
            }),
        'total_amount': fields.function(_amount_all, string='Total Amount', digit=(16,2), multi='all',
          store={
                'stock.picking.out': (lambda self, cr, uid, ids, c={}: ids, ['move_lines'], 20),
                'stock.move': (_get_stock_move, ['price_unit','product_qty','picking_id'], 20),
            }),
        
        #Thanh: Add these field to help searching datas easily
        'date_done_user_tz': fields.function(_compute_date_user_tz, type='date', method=True, string='Date Done', store={
                'stock.picking.out': (lambda self, cr, uid, ids, c={}: ids, ['date_done'], 10),
                }, multi='tz'),
        
        'day_done_user_tz': fields.function(_compute_date_user_tz, type='char', method=True, string='Day Done', store={
                'stock.picking.out': (lambda self, cr, uid, ids, c={}: ids, ['date_done'], 10),
            }, multi='tz'),
                
        'stock_journal_id': fields.many2one('stock.journal','Stock Journal', required=True, select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}, track_visibility='onchange'),
        'return': fields.selection([('none', 'Normal'), ('customer', 'Return from Customer'), ('supplier', 'Return to Supplier')], 'Type', required=True, select=True, help="Type specifies whether the Picking has been returned or not."),
        'write_date':  fields.datetime('Last Modification', readonly=True),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'write_uid':  fields.many2one('res.users', 'Updated by', readonly=True),
        'create_uid': fields.many2one('res.users', 'Created by', readonly=True),
        'return_reason_id': fields.many2one('stock.return.reason', 'Return Reason'),
        'nhietdo_di':fields.char('Nhiệt độ khi đi'),
        'nhietdo_den':fields.char('Nhiệt độ khi đến'),
    }
    
    _defaults = {    
        'return': 'none',
        'type':   'out',
    }
    
     
    def print_report(self, cr, uid, ids, context=None):
        return {
                'type': 'ir.actions.report.xml',
                'report_name': 'order',
            }
    
    
    def create(self, cr, user, vals, context=None):
        context = context or {}
        if context.get('no_create',False):
            raise osv.except_osv(_('Creation Error!'), _('You cannot create a Picking in this menu'))
        context.update({'sequence_obj_ids':[]})
        if ('name' not in vals) or (vals.get('name')=='/'):
#             seq_obj_name =  self._name
            if vals.get('stock_journal_id',False):
                journal = self.pool.get('stock.journal').browse(cr, user, vals['stock_journal_id'])
                if not journal.sequence_id:
                    raise osv.except_osv(_('Warning!'), _('Please define Sequence for Stock Journal.'))
                
                if journal.source_type in ['in','return_customer']:
                    cr.execute('SELECT warehouse_id FROM stock_location WHERE id=%s'%(vals['location_dest_id']))
                    warehouse_id = cr.fetchone()
                    if warehouse_id and warehouse_id[0]:
                        context['sequence_obj_ids'].append(['warehouse',warehouse_id[0]])
                if journal.source_type in ['out','return_supplier','internal']:
                    cr.execute('SELECT warehouse_id FROM stock_location WHERE id=%s'%(vals['location_id']))
                    warehouse_id = cr.fetchone()
                    if warehouse_id and warehouse_id[0]:
                        context['sequence_obj_ids'].append(['warehouse',warehouse_id[0]])
                        
                vals['name'] = self.pool.get('ir.sequence').get_id(cr, user, journal.sequence_id.id, code_or_id='id', context=context)
                
        new_id = super(osv.osv, self).create(cr, user, vals, context)
        return new_id
    
#Wizard
class stock_partial_picking_line(osv.TransientModel):
    _inherit = "stock.partial.picking.line"
    def _tracking(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for tracklot in self.browse(cursor, user, ids, context=context):
            tracking = False
            if (tracklot.wizard_id.picking_id.type == 'in' and tracklot.product_id.track_incoming == True) or \
                (tracklot.wizard_id.picking_id.type == 'out' and tracklot.product_id.track_outgoing == True):
                tracking = True
            res[tracklot.id] = tracking
        return res
    _columns = {
            'tracking': fields.function(_tracking, string='Tracking', type='boolean'),
    }
stock_partial_picking_line()

class stock_partial_picking(osv.osv_memory):
    _inherit = "stock.partial.picking"

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(stock_partial_picking, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('stock.picking', 'stock.picking.in', 'stock.picking.out'), 'Bad context propagation'
        picking_id, = picking_ids
        if 'picking_id' in fields:
            res.update(picking_id=picking_id)
        if 'move_ids' in fields:
            picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
            if 'only_available' in context:
                moves = [self._partial_move_for(cr, uid, m,context=context) for m in picking.move_lines if m.state in ('assigned')]
            else:
                moves = [self._partial_move_for(cr, uid, m,context=context) for m in picking.move_lines if m.state not in ('done', 'cancel')]
            #KIET: Fix lai cach lay Array tu ham _partial_move_for
            new_moves = []
            for lines in moves:
                for line in lines:
                    new_moves.append(line)
            res.update(move_ids=new_moves)
            #KIET: Fix lai cach lay Array tu ham _partial_move_for
        if 'date' in res:
            picking_obj = self.pool.get('stock.picking').browse(cr,uid,picking_ids[0])
            if picking_obj and picking_obj.date:
                res.update(date=picking_obj.date)
            else:
                res.update(date=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        return res
    
    #Thanh: Remove checking qty_in_line_uom vs wizard_line.quantity
    def do_partial(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        assert len(ids) == 1, 'Partial picking processing may only be done one at a time.'
        stock_picking = self.pool.get('stock.picking')
        stock_move = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        partial = self.browse(cr, uid, ids[0], context=context)
        partial_data = {
            'delivery_date' : partial.date
        }
        picking_type = partial.picking_id.type
        for wizard_line in partial.move_ids:
            line_uom = wizard_line.product_uom
            move_id = wizard_line.move_id.id

            #Quantiny must be Positive
            if wizard_line.quantity < 0:
                raise osv.except_osv(_('Warning!'), _('Please provide proper Quantity.'))

            if move_id:
                initial_uom = wizard_line.move_id.product_uom
                qty_in_initial_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, initial_uom.id)
                without_rounding_qty = (wizard_line.quantity / line_uom.factor) * initial_uom.factor
            else:
                seq_obj_name =  'stock.picking.' + picking_type
                move_id = stock_move.create(cr,uid,{'name' : self.pool.get('ir.sequence').get(cr, uid, seq_obj_name),
                                                    'product_id': wizard_line.product_id.id,
                                                    'product_qty': wizard_line.quantity,
                                                    'product_uom': wizard_line.product_uom.id,
                                                    'prodlot_id': wizard_line.prodlot_id.id,
                                                    'location_id' : wizard_line.location_id.id,
                                                    'location_dest_id' : wizard_line.location_dest_id.id,
                                                    'picking_id': partial.picking_id.id
                                                    },context=context)
                stock_move.action_confirm(cr, uid, [move_id], context)
            partial_data['move%s' % (move_id)] = {
                'product_id': wizard_line.product_id.id,
                'product_qty': wizard_line.quantity,
                'product_uom': wizard_line.product_uom.id,
                'prodlot_id': wizard_line.prodlot_id.id,
                #KIET: Update move_id cho truong hop phat sinh nhieu Lo or nhieu dong trong Wizard Xuat Nhap Kho
                'move_id': move_id,
            }
            
            if (picking_type == 'in') and (wizard_line.product_id.cost_method == 'average'):
                partial_data['move%s' % (move_id)].update(product_price=wizard_line.cost,
                                                                  product_currency=wizard_line.currency.id)
                 
            partial_data['move%s' % (move_id)].update(location_dest_id=wizard_line.location_dest_id.id)
            
        done = stock_picking.do_partial(cr, uid, [partial.picking_id.id], partial_data, context=context)
        
        if done[partial.picking_id.id]['delivered_picking'] == partial.picking_id.id:
            return {'type': 'ir.actions.act_window_close'}
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': context.get('active_model', 'stock.picking'),
            'name': _('Partial Delivery'),
            'res_id': done[partial.picking_id.id]['delivered_picking'],
            'view_type': 'form',
            'view_mode': 'form,tree,calendar',
            'context': context,
        }
    
    #KIET: Chinh sua lai, Tu dong lay Lo gan vao hang` Xuat Kho
    def _partial_move_for(self, cr, uid, move,context=None):
        partial_move_ids =[]
        lot_pool = self.pool.get('stock.production.lot')
        locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')], context=None)
        lot_ids = []
        check= True
        if move.picking_id.type == 'out':
            if move.product_id.track_outgoing:
                sql='''
                 SELECT prodlot_id, sum(qty)
                    FROM 
                        stock_report_prodlots srp inner join 
                        stock_production_lot spl on spl.id = srp.prodlot_id
                    WHERE 
                        spl.product_id = %s                        
                        and srp.location_id IN %s
                    group by prodlot_id,date
                    having sum(qty)>0
                    order by date
                '''%(move.product_id.id,tuple(locations),)
                cr.execute(sql)
                for line in cr.dictfetchall():
                    lot_ids.append(line['prodlot_id'])
                if lot_ids:
                    for line in lot_pool.browse(cr,uid,lot_ids):
                        if check ==True:
                            move_id = move.id
                            check = False
                        else:
                            move_id = False
                            
                        if  move.product_qty - line.stock_available > 0: 
                            partial_move = {
                            'product_id' : move.product_id.id,
                            'quantity' : line.stock_available,
                            'product_uom' : move.product_uom.id,
                            'prodlot_id' : line.id,
                            'move_id' : move_id,
                            'location_id' : move.location_id.id,
                            'location_dest_id' : move.location_dest_id.id,
                            'picking_id':move.picking_id.id
                                }
                            partial_move_ids.append(partial_move) 
                            move.product_qty = move.product_qty - line.stock_available
                        else:
                            partial_move = {
                            'product_id' : move.product_id.id,
                            'quantity' : move.product_qty,
                            'product_uom' : move.product_uom.id,
                            'prodlot_id' : line.id,
                            'move_id' : move_id,
                            'location_id' : move.location_id.id,
                            'location_dest_id' : move.location_dest_id.id,
                            'picking_id':move.picking_id.id
                            }
                            partial_move_ids.append(partial_move)
                            break
                else:
                    partial_move = {
                        'product_id' : move.product_id.id,
                        'quantity' : move.product_qty or 0,
                        'product_uom' : move.product_uom.id,
                        'prodlot_id' : move.prodlot_id.id,
                        'move_id' : move.id,
                        'location_id' : move.location_id.id,
                        'location_dest_id' : move.location_dest_id.id,
                        }
                    partial_move_ids.append(partial_move)
            else:
                partial_move = {
                'product_id' : move.product_id.id,
                'quantity' : move.product_qty or 0,
                'product_uom' : move.product_uom.id,
                'prodlot_id' : move.prodlot_id.id,
                'move_id' : move.id,
                'location_id' : move.location_id.id,
                'location_dest_id' : move.location_dest_id.id,
                }
                partial_move_ids.append(partial_move)
        else:
            partial_move = {
                'product_id' : move.product_id.id,
                'quantity' : move.product_qty or 0,
                'product_uom' : move.product_uom.id,
                'prodlot_id' : move.prodlot_id.id,
                'move_id' : move.id,
                'solo':move.prodlot_id.name or '/',
                'location_id' : move.location_id.id,
                'location_dest_id' : move.location_dest_id.id,
            }
            if move.picking_id.type == 'in' and move.product_id.cost_method == 'average':
                partial_move.update(update_cost=True, **self._product_cost_for_average_update(cr, uid, move))
            partial_move_ids.append(partial_move)
            
        return partial_move_ids
    
stock_partial_picking()


class stock_return_picking(osv.osv):
    _inherit = 'stock.return.picking'

    _columns = {
        'return_type': fields.selection([('none', 'Normal'), ('internal','Return Internal'), ('customer', 'Return from Customer'), ('supplier', 'Return to Supplier')], 'Type', required=True, readonly=True, help="Type specifies whether the Picking has been returned or not."),
        'note':        fields.text('Notes'),
        'location_id': fields.many2one('stock.location', 'Location', help='If a location is chosen the destination location for customer return (or origin for supplier return) is forced for all moves.'),
        'return_reason_id': fields.many2one('stock.return.reason', 'Return Reason'),
        'journal_id':fields.many2one('stock.journal', 'Stock Journal',required=True,),
        'option':fields.boolean('Tranfer Product'),
    }
    _defaults = {
#         'return_type': lambda self, cr, uid, context: self._get_return_type(cr, uid, context=context),
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(stock_return_picking, self).default_get(cr, uid, fields, context)
        record_id = context and context.get('active_id', False) or False
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        if pick and pick.sale_id and pick.sale_id:
            warehouse = pick.sale_id.shop_id and pick.sale_id.shop_id.warehouse_id
            res.update({'location_id': warehouse and warehouse.lot_return_id and warehouse.lot_return_id.id or False})
        
        if pick:
            if pick.type == 'in':
                journal_ids =  self.pool.get('stock.journal').search(cr,uid,[('source_type','=','return_supplier')])
                if pick['return'] == 'none':
                    res.update({'return_type': 'supplier','journal_id':journal_ids and journal_ids[0] or False})
            elif pick.type == 'out':
                journal_ids =  self.pool.get('stock.journal').search(cr,uid,[('source_type','=','return_customer')])
                if pick['return'] == 'none':
                    res.update({'return_type': 'customer','journal_id':journal_ids and journal_ids[0] or False})
            else:
                if pick['return'] == 'none':
                    res.update({'return_type': 'internal','journal_id':pick.stock_journal_id.id})
                    
            result1 = []
            return_history = self.get_return_history(cr, uid, record_id, context)       
            for line in pick.move_lines:
                if line.state in ('cancel') or line.scrapped:
                    continue
                qty = line.product_qty - return_history.get(line.id, 0)
                if qty > 0:
                    result1.append({'product_id': line.product_id.id, 'quantity': qty,'move_id':line.id, 'prodlot_id': line.prodlot_id and line.prodlot_id.id or False})
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': result1})
        return res
    
    def create_returns(self, cr, uid, ids, context=None):
        """ 
         Creates return picking.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: List of ids selected
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        if context is None:
            context = {} 
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        data_obj = self.pool.get('stock.return.picking.memory')
        act_obj = self.pool.get('ir.actions.act_window')
        model_obj = self.pool.get('ir.model.data')
        wf_service = netsvc.LocalService("workflow")
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        data = self.read(cr, uid, ids[0], context=context)
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
        set_invoice_state_to_none = False#True LY by default 
        returned_lines = 0
        location_id = False
        location_dest_id = False
        return_picking_obj = self.browse(cr,uid,ids[0])
        # Create new picking for returned products

        if pick.type == 'out':
            new_type = 'in'
            location_id = pick.location_id and pick.location_id.id or False
            location_dest_id = pick.location_dest_id and pick.location_dest_id.id or False
            # lay mat dinh stoc
            journal_id =  self.pool.get('stock.journal').search(cr,uid,[('source_type','=','return_customer')])
        elif pick.type == 'in':
            new_type = 'out'
            location_id = pick.location_id and pick.location_id.id or False
            location_dest_id = pick.location_dest_id and pick.location_dest_id.id or False
            journal_id =  self.pool.get('stock.journal').search(cr,uid,[('source_type','=','return_supplier')])
        else:
            new_type = 'internal'
            journal_id =  [pick.stock_journal_id.id] or False
            location_id = pick.location_id and pick.location_id.id or False
            location_dest_id = pick.location_dest_id and pick.location_dest_id.id or False
        
        seq_obj_name = 'stock.picking.' + new_type
        # SHOULD USE ir_sequence.next_by_code() or ir_sequence.next_by_id()
        new_pick_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
        new_picking_vals = {'name': _('%s-%s-return') % (new_pick_name, pick.name),
                            'move_lines': [],
                            'state':'draft',
                            'type': new_type,
                            'return': data['return_type'],
                            'note': data['note'],
                            'origin':pick.name or '',
                            'return_reason_id': data['return_reason_id'] and data['return_reason_id'][0],#data return (id,code) eg. (10, 'operation')
                            'date':date_cur,
                            'invoice_state': data['invoice_state'], 
                            'stock_journal_id':journal_id and journal_id[0] or False,
                            'location_id':location_dest_id,
                            'location_dest_id':location_id,}
        new_picking = pick_obj.copy(cr, uid, pick.id, new_picking_vals)
        #Hung them chuc nang doi san pham.
        if pick.type =='out' and pick.sale_id and return_picking_obj.option:
            new_id = pick_obj.copy(cr, uid, pick.id, {
                                        'name': pick.name + '-ship',
                                        'move_lines': [], 
                                        'state':'draft', 
                                        'type': 'out',
                                        'date':date_cur,
                                        'date_done':False, 
                                        'invoice_state': data['invoice_state'], })
            val_id = data['product_return_moves']
            for v in val_id:
                data_get = data_obj.browse(cr, uid, v, context=context)
                mov_id = data_get.move_id.id
                new_qty = data_get.quantity
                move = move_obj.browse(cr, uid, mov_id, context=context)
                if new_qty >move.product_qty:
                    error = 'Không vượt quá số lượng đơn hàng'
                    raise osv.except_osv(unicode('Lỗi', 'utf8'), unicode(error, 'utf8'))
                if move.state in ('cancel') or move.scrapped:
                    continue
                new_location = move.location_dest_id.id
                returned_qty = move.product_qty
                for rec in move.move_history_ids2:
                    returned_qty -= rec.product_qty
                if new_qty:
                    returned_lines += 1
                    new_move_vals = {'prodlot_id':move.prodlot_id and move.prodlot_id.id or False,
                                    'product_qty': new_qty,
                                    'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id, new_qty, move.product_uos.id),
                                    'picking_id': new_id,
                                    'state': 'draft',
                                    'location_id': new_location,
                                    'location_dest_id': move.location_id.id,
                                    'date': date_cur,
                                    'note': data['note'],
                                    'return_reason_id': data['return_reason_id'] and data['return_reason_id'][0], }#data return (id,code) eg. (10, 'operation')
                    if data['location_id']:
                        if data['return_type'] == 'customer':
                            new_move_vals.update({'location_dest_id': data['location_id'][0], })
                        else:
                            new_move_vals.update({'location_id': data['location_id'][0], })
                    
                    new_move = move_obj.copy(cr, uid, move.id, new_move_vals)
                    move_obj.write(cr, uid, [move.id], {'move_history_ids2':[(4, new_move)]}, context=context)
            if not returned_lines:
                raise osv.except_osv(_('Warning!'), _("Please specify at least one non-zero quantity."))

        val_id = data['product_return_moves']
        for v in val_id:
            data_get = data_obj.browse(cr, uid, v, context=context)
            mov_id = data_get.move_id.id
            new_qty = data_get.quantity
            move = move_obj.browse(cr, uid, mov_id, context=context)
            new_location = move.location_dest_id.id
            returned_qty = move.product_qty
            for rec in move.move_history_ids2:
                returned_qty -= rec.product_qty
    
            if returned_qty != new_qty:
                set_invoice_state_to_none = False
            if new_qty:
                returned_lines += 1
                new_move=move_obj.copy(cr, uid, move.id, {
                                            'prodlot_id':move.prodlot_id and move.prodlot_id.id or False,
                                            'product_qty': new_qty,
                                            'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id, new_qty, move.product_uos.id),
                                            'picking_id': new_picking, 
                                            'state': 'draft',
                                            'location_id': new_location, 
                                            'location_dest_id': move.location_id.id,
                                            'date': date_cur,
                })
                move_obj.write(cr, uid, [move.id], {'move_history_ids2':[(4,new_move)]}, context=context)
        if not returned_lines:
            raise osv.except_osv(_('Warning!'), _("Please specify at least one non-zero quantity."))
        #LY make it can be invoiced
        if data['invoice_state'] == 'none':#returned_qty == new_qty #!= new_qty:
            set_invoice_state_to_none = True#LY False
        if set_invoice_state_to_none:
            pick_obj.write(cr, uid, [pick.id], {'invoice_state':'none'}, context=context)
        wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
        pick_obj.force_assign(cr, uid, [new_picking], context)
        # Update view id in context, lp:702939
        model_list = {
                'out': 'stock.picking.out',
                'in': 'stock.picking.in',
                'internal': 'stock.picking',
        }
        return {
            'domain': "[('id', 'in', [" + str(new_picking) + "])]",
            'name': _('Returned Picking'),
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model': model_list.get(new_type, 'stock.picking'),
            'type':'ir.actions.act_window',
            'context':context,
        }

stock_return_picking()

class stock_move_scrap(osv.osv_memory):
    _inherit = "stock.move.scrap"
    _name = "stock.move.scrap"

    _columns = {
        'note': fields.text('Return reason'),
    }
    _defaults = {
        'location_id': lambda *x: False
    }

    
    def move_scrap(self, cr, uid, ids, context=None):
        """ To move scrapped products
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        move_ids = context['active_ids']
        for data in self.browse(cr, uid, ids):
            context.update({'note': data.note})
            move_obj.action_scrap(cr, uid, move_ids,
                             data.product_qty, data.location_id.id,
                             context=context)
        return {'type': 'ir.actions.act_window_close'}

stock_move_scrap()

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def write(self, cr, uid, ids, vals, context=None):
        super(account_invoice, self).write(cr, uid, ids, vals, context)
        for invoice_obj in self.browse(cr, uid, ids):
            if vals.get('invoice_line'):
                if invoice_obj.type == 'in_invoice':
                    for line in vals['invoice_line']:
                        if line[2] and 'price_unit' in line[2]:
                            if line[1]:
                                price_unit = line[2]['price_unit']
                                sql='''
                                    UPDATE stock_move SET price_unit = %s
                                    WHERE purchase_line_id = (
                                        select id from purchase_order_line where id in (
                                            select order_line_id from purchase_order_line_invoice_rel 
                                                where invoice_id in (%s)))
                                '''%(price_unit,line[1])
                                cr.execute(sql)
        return True
    
account_invoice()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
