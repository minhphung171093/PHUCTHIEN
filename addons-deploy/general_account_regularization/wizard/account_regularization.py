# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################
from osv import osv, fields
from tools.translate import _
import time
from datetime import datetime

class wizard_regularize(osv.osv_memory):
	_name = "wizard.regularize"
	_columns = {
#		'fiscalyear': fields.many2one('account.fiscalyear', 'Fiscal year', help='Fiscal Year for the write move', required=True),
		'journal_id': fields.many2one('account.journal', 'Journal', help='Journal for the move', required=True),
		'period_id': fields.many2one('account.period', 'Period', help='Period for the move', required=True),
		'date_move': fields.date('Date', help='Date for the move', required=True),
		
		'balance_calc': fields.selection([('date','Date'),('period','Period')], 'Regularization time calculation', required=True),
# 		'periods': fields.many2many('account.period', 'wizard_regularize_period', 'wizard_regularize_id', 'period_id', 'Periods', help='Periods to regularize', required=False),
		'date_to': fields.date('Date To', help='Include movements up to this date', required=False),
	}
    
	_defaults = {
		'balance_calc': lambda *a: 'period',
		'date_move': time.strftime('%Y-%m-%d'),
		'period_id': lambda self, cr, uid, c: self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0],
    }
    
	def regularize(self, cr, uid, ids, context):
		this = self.browse(cr, uid, ids)[0]
		regu_objs = self.pool.get('account.regularization')
		regu_ids = regu_objs.search(cr, uid, [('balance_calc','=',this.balance_calc),('active','=',True)], order='sequence')
		if not regu_ids:
			raise osv.except_osv('Warning!', "There are no Regularization with type '%s'"%(this.balance_calc))
		date = this.date_move
		period = this.period_id.id or False
		journal = this.journal_id.id or False
		date_to = None
		period_ids = [period]
		if this.balance_calc == 'date':
			date_to = this.date_to
# 		else:
# 			period_ids = [x.id for x in this.periods]
		move_ids = regu_objs.regularize(cr, uid, regu_ids, context, date, period, journal, date_to, period_ids)
		return {
            'name': _('Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'domain': "[('id','in',["+','.join(map(str,move_ids))+"])]",
            'type': 'ir.actions.act_window',
        }


wizard_regularize()


