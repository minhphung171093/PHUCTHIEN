# -*- encoding: utf-8 -*-
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
from lxml import etree

from osv import osv, fields

class asset_modify(osv.osv_memory):
    _inherit = 'asset.modify'
    _description = 'Modify Asset'

    _columns = {
#         'analytics_id': fields.many2one('account.analytic.plan.instance', 'Analytic Distribution'),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic account'),
    }

    def default_get(self, cr, uid, fields, context=None):
        """ To get default values for the object.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for which we want default values 
        @param context: A standard dictionary 
        @return: A dictionary which of fields with values. 
        """ 
        if not context:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        res = super(asset_modify, self).default_get(cr, uid, fields, context=context)
        asset_id = context.get('active_id', False)
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        if 'name' in fields:
            res.update({'name': asset.name})
        if 'method_number' in fields and asset.method_time == 'number':
            res.update({'method_number': asset.method_number})
        if 'method_period' in fields:
            res.update({'method_period': asset.method_period})
        if 'method_end' in fields and asset.method_time == 'end':
            res.update({'method_end': asset.method_end})
#         if 'analytics_id' in fields and asset.analytics_id:
#             res.update({'analytics_id': asset.analytics_id.id})
        if 'account_analytic_id' in fields and asset.account_analytic_id:
            res.update({'account_analytic_id': asset.account_analytic_id.id})
        return res
    
    def modify(self, cr, uid, ids, context=None):
        """ Modifies the duration of asset for calculating depreciation
        and maintains the history of old values.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of Ids 
        @param context: A standard dictionary 
        @return: Close the wizard. 
        """ 
        if not context:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        history_obj = self.pool.get('account.asset.history')
        asset_id = context.get('active_id', False)
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        data = self.browse(cr, uid, ids[0], context=context)
        if data.method_number != asset.method_number or data.method_period != asset.method_period or data.method_end != asset.method_end:
            history_vals = {
                'asset_id': asset_id,
                'name': data.name,
                'method_time': asset.method_time,
                'method_number': asset.method_number,
                'method_period': asset.method_period,
                'method_end': asset.method_end,
                'user_id': uid,
                'date': time.strftime('%Y-%m-%d'),
                'note': data.note,
            }
            history_obj.create(cr, uid, history_vals, context=context)
            asset_vals = {
                'method_number': data.method_number,
                'method_period': data.method_period,
                'method_end': data.method_end,
            }
            asset_obj.write(cr, uid, [asset_id], asset_vals, context=context)
            asset_obj.compute_depreciation_board(cr, uid, [asset_id], context=context)
        if (data.analytics_id and data.analytics_id != asset.analytics_id) or (data.account_analytic_id and data.account_analytic_id != asset.account_analytic_id):
            asset_vals = {
                'analytics_id': data.analytics_id.id,
                'account_analytic_id': data.account_analytic_id.id,
            }
            asset_obj.write(cr, uid, [asset_id], asset_vals, context=context)
        return {'type': 'ir.actions.act_window_close'}

asset_modify()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
