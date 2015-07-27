# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################

from osv import fields, osv
import time
from tools import config
from openerp import SUPERUSER_ID

class account_account(osv.osv):
	_name = 'account.account'
	_inherit = 'account.account'

	def balance_calculation(self, cr, uid, ids, context, date=time.strftime('%Y-%m-%d'), periods=[]):
		acc_set = ",".join(map(str, ids))
		query = self.pool.get('account.move.line')._query_get(cr, uid,
				context=context)

		if not periods:
			cr.execute(("SELECT a.id, " \
					"COALESCE(SUM(l.debit - l.credit), 0) " \
				"FROM account_account a " \
					"LEFT JOIN account_move_line l " \
					"ON (a.id=l.account_id) " \
				"WHERE a.type != 'view' " \
					"AND a.id IN (%s) " \
					"AND " + query + " " \
					"AND a.active " \
					"AND l.date <= '%s' "
				"GROUP BY a.id") % (acc_set, date))
		else:
			cr.execute(("SELECT a.id, " \
					"COALESCE(SUM(l.debit - l.credit), 0) " \
				"FROM account_account a " \
					"LEFT JOIN account_move_line l " \
					"ON (a.id=l.account_id) " \
				"WHERE a.type != 'view' " \
					"AND a.id IN (%s) " \
					"AND " + query + " " \
					"AND a.active " \
					"AND l.period_id in (%s) " \
				"GROUP BY a.id") % (acc_set, ",".join(map(str, periods))))

		res = {}
		for account_id, sum in cr.fetchall():
			res[account_id] = round(sum,2)
		for id in ids:
			res[id] = round(res.get(id,0.0), 2)
		return res

account_account()

class account_regularization(osv.osv):
	_name = 'account.regularization'
	_description = 'Account Regularization Model'
	_order = 'sequence'
	_columns ={
		'name': fields.char('Name', size=64, required=True),
		'account_ids': fields.many2many('account.account', 'account_regularization_rel', 'regularization_id', 'account_id', 'Accounts to balance', required=True, domain=[('type','!=','view')]),
		'debit_account_id': fields.many2one('account.account', 'Result account, debit', required=True),
		'credit_account_id': fields.many2one('account.account', 'Result account, credit', required=True),
		'balance_calc': fields.selection([('date','Date'),('period','Periods')], 'Regularization time calculation', required=True),
		#'journal_id': fields.many2one('account.journal', 'Journal', required=True),
		'move_ids': fields.one2many('account.move', 'regularization_id', 'Regularization Moves'),
		
		#Thanh: Add somes fields
		'company_id': fields.many2one('res.company', 'Company', required=True),
		'sequence': fields.integer('Sequence', required=True),
		'journal_id': fields.many2one('account.journal', 'Journal', required=False),
		'active': fields.boolean('Active'),
	}

	_defaults = {
		'active': True,
		'balance_calc': lambda *a: 'period',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.regularization', context=c),
    }
	
	#Thanh: Allow modify deactivated records
	def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
		if context and 'active_test' not in context: context['active_test'] = False
		return super(account_regularization, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order, context=context, count=count)
       
	def regularize(self, cr, uid, ids, context, date=time.strftime('%Y-%m-%d'), period=None, journal=None, date_to=None, period_ids=[]):
		""" This method will calculate all the balances from all the child accounts of the regularization
		and create the corresponding move."""
		#Thanh: check Journal
		move_ids = []
		move_obj = self.pool.get('account.move')
		move_line_obj = self.pool.get('account.move.line')
		if not period or not journal:
			raise osv.except_osv('No period or journal defined')
		
		for regularization in self.browse(cr,uid, ids):
			if regularization.journal_id:
				journal = regularization.journal_id.id
			# Find all children accounts
			account_ids = self.pool.get('account.account')._get_children_and_consol(cr, uid, [x.id for x in regularization.account_ids], context)
			if date_to:
				balance_results = self.pool.get('account.account').balance_calculation(cr, uid, account_ids, context, date=date_to)
			else:
				balance_results = self.pool.get('account.account').balance_calculation(cr, uid, account_ids, context, periods=period_ids)
			if balance_results.keys().__len__() == balance_results.values().count(0.0):
				continue
#				raise osv.except_osv('Warning!', 'Nothing to regularize')
			move = move_obj.create(cr, uid, {'journal_id': journal, 
																'period_id': period, 
																'regularization_id': regularization.id,
																'company_id': regularization.company_id.id,}, context=context)
			sum = 0.0
			for item in balance_results.keys():
				if balance_results[item] <> 0.0:
					val = {
						'name': regularization.name,
						'date': date,
						'move_id': move,
						'account_id':item,
						'credit': ((balance_results[item]>0.0) and balance_results[item]) or 0.0,
						'debit': ((balance_results[item]<0.0) and -balance_results[item]) or 0.0,
						'journal_id': journal,
						'period_id': period,
					}
					sum += balance_results[item]
					move_line_obj.create(cr, uid, val, context=context)
			diff_line = {
						'name': regularization.name,
						'date': date,
						'move_id': move,
						'account_id': (sum>0) and regularization.debit_account_id.id or regularization.credit_account_id.id,
						'credit': ((sum<0.0) and -sum) or 0.0,
						'debit': ((sum>0.0) and sum) or 0.0,
						'journal_id': journal,
						'period_id': period,
			}
			move_line_obj.create(cr, uid, diff_line, context=context)
			if move:
				move_obj.post(cr,uid,[move],context)
				move_ids.append(move)
		return move_ids

account_regularization()


class account_move(osv.osv):
	_name = 'account.move'
	_inherit = 'account.move'
	_columns = {
		'regularization_id': fields.many2one('account.regularization', 'Regularization'),
	}
account_move()


