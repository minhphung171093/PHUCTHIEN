# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################

from osv import osv, fields

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    _columns = {
    }
    def asset_create(self, cr, uid, lines, context=None):
        context = context or {}
        asset_obj = self.pool.get('account.asset.asset')
        for line in lines:
            if line.asset_category_id:
                vals = {
                    'name': line.name,
                    'code': line.invoice_id.number or False,
                    'category_id': line.asset_category_id.id,
                    'analytic_account_id': line.asset_category_id.account_analytic_id and line.asset_category_id.account_analytic_id.id or False,
#                     'analytics_id': line.asset_category_id.analytics_id and line.asset_category_id.analytics_id.id or False,
#                     'warehouse_id': line.invoice_id.warehouse_id and line.invoice_id.warehouse_id.id or False,
                    'purchase_value': line.price_subtotal,
                    'period_id': line.invoice_id.period_id.id,
                    'partner_id': line.invoice_id.partner_id.id,
                    'company_id': line.invoice_id.company_id.id,
                    'currency_id': line.invoice_id.currency_id.id,
                }
                changed_vals = asset_obj.onchange_category_id(cr, uid, [], vals['category_id'], context=context)
                vals.update(changed_vals['value'])
                asset_id = asset_obj.create(cr, uid, vals, context=context)
                if line.asset_category_id.open_asset:
                    asset_obj.validate(cr, uid, [asset_id], context=context)
        return True

account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
