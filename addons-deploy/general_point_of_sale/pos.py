# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

import time

import openerp
from openerp import netsvc
from openerp.osv import osv, fields
from openerp.tools.translate import _

class pos_session(osv.osv):
    _inherit = 'pos.session'
    
    def create(self, cr, uid, values, context=None):
        context = context or {}
        config_id = values.get('config_id', False) or context.get('default_config_id', False)
        if not config_id:
            raise osv.except_osv( _('Error!'),
                _("You should assign a Point of Sale to your session."))

        # journal_id is not required on the pos_config because it does not
        # exists at the installation. If nothing is configured at the
        # installation we do the minimal configuration. Impossible to do in
        # the .xml files as the CoA is not yet installed.
        jobj = self.pool.get('pos.config')
        pos_config = jobj.browse(cr, uid, config_id, context=context)
        context.update({'company_id': pos_config.shop_id.company_id.id})
        if not pos_config.journal_id:
            jid = jobj.default_get(cr, uid, ['journal_id'], context=context)['journal_id']
            if jid:
                jobj.write(cr, uid, [pos_config.id], {'journal_id': jid}, context=context)
            else:
                raise osv.except_osv( _('error!'),
                    _("Unable to open the session. You have to assign a sale journal to your point of sale."))

        # define some cash journal if no payment method exists
        if not pos_config.journal_ids:
            journal_proxy = self.pool.get('account.journal')
            cashids = journal_proxy.search(cr, uid, [('journal_user', '=', True), ('type','=','cash')], context=context)
            if not cashids:
                cashids = journal_proxy.search(cr, uid, [('type', '=', 'cash')], context=context)
                if not cashids:
                    cashids = journal_proxy.search(cr, uid, [('journal_user','=',True)], context=context)

            jobj.write(cr, uid, [pos_config.id], {'journal_ids': [(6,0, cashids)]})


        pos_config = jobj.browse(cr, uid, config_id, context=context)
        bank_statement_ids = []
        for journal in pos_config.journal_ids:
            bank_values = {
                'journal_id' : journal.id,
                'user_id' : uid,
                'company_id' : pos_config.shop_id.company_id.id
            }
            statement_id = self.pool.get('account.bank.statement').create(cr, uid, bank_values, context=context)
            bank_statement_ids.append(statement_id)
        
        #Thanh: Create Sequence
        context.update({'sequence_obj_ids':[]})
        context['sequence_obj_ids'].append(['shop',pos_config.shop_id.id])
        context['sequence_obj_ids'].append(['pos',pos_config.code])
        name = self.pool.get('ir.sequence').get_id(cr, uid, pos_config.sequence_id.id, code_or_id='id', context=context)
        values.update({
#             'name' : pos_config.sequence_id._next(),
            'name': name,
            'statement_ids' : [(6, 0, bank_statement_ids)],
            'config_id': config_id
        })

        return super(pos_session, self).create(cr, uid, values, context=context)
    
    def open_frontend_cb(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if not ids:
            return {}
        for session in self.browse(cr, uid, ids, context=context):
            if session.user_id.id != uid:
                raise osv.except_osv(
                        _('Error!'),
                        _("You cannot use the session of another users. This session is owned by %s. Please first close this one to use this point of sale." % session.user_id.name))
#         context.update({'active_id': ids[0]})
#         return {
#             'type' : 'ir.actions.client',
#             'name' : _('Start Point Of Sale'),
#             'tag' : 'pos.ui',
#             'context' : context,
#         }
        
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'point_of_sale', 'view_pos_pos_form')
        res_id = res and res[1] or False
        context['default_type_pos'] = 'delivery'
        context['default_session_id'] = ids[0]
        return {
            'name': _('Point of Sale Orders'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'pos.order',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
        }
        
pos_session()

class pos_config(osv.osv):
    _inherit = 'pos.config'
    _columns = {
        'code' : fields.char('Code', size=5, select=1, required=True),
    }
    _defaults = {
    }
pos_config()

class pos_order(osv.osv):
    _inherit = 'pos.order'
    _columns = {
        #Thanh: Ten cua khach hang
        'partner_reference': fields.char('Partner Ref', size=250),
        'partner_id': fields.many2one('res.partner', 'Customer', 
                                      #Thanh filter just pos partner only
#                                       domain="[('customer_type','=',True)]",
                                      #Thanh filter just pos partner only
                                      change_default=True, select=1, 
                                      states={'draft': [('readonly', False)], 'paid': [('readonly', False)]}),
#         'section_id': fields.related('user_id', 'default_section_id',type='many2one',relation='crm.case.section',string='POS Team', store=True, readonly=True),
        'section_id': fields.many2one('crm.case.section', 'POS Team', states={'draft': [('readonly', False)], 'paid': [('readonly', False)]}),
    }
    
    def _default_customer(self, cr, uid, context=None):
        res = self.pool.get('res.partner').search(cr, uid, [('customer_type','=',True)])
        return res and res[0] or False
    
    _defaults = {
         'partner_id': _default_customer,
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        d = {
            'state': 'draft',
            'invoice_id': False,
            'account_move': False,
            'picking_id': False,
            'statement_ids': [],
            'nb_print': 0,
#             'name': self.pool.get('ir.sequence').get(cr, uid, 'pos.order'),
            'name':'/'
        }
        d.update(default)
        return super(osv.osv, self).copy(cr, uid, id, d, context=context)
    
    #Thanh: Pass obj_name and id to generate Sequence
    def create(self, cr, uid, values, context=None):
        context = context or {}
        context.update({'sequence_obj_ids':[]})
        if values.get('session_id',False):
            cr.execute('SELECT config_id FROM pos_session WHERE id=%s'%(values['session_id']))
            config_id = cr.fetchone()
            if config_id and config_id[0]:
                context['sequence_obj_ids'].append(['pos',config_id[0]])
                cr.execute('SELECT shop_id FROM pos_config WHERE id=%s'%(config_id[0]))
                shop_id = cr.fetchone()
                if shop_id and shop_id[0]:
                    context['sequence_obj_ids'].append(['shop',shop_id[0]])
                    cr.execute('SELECT warehouse_id FROM sale_shop WHERE id=%s'%(config_id[0]))
                    warehouse_id = cr.fetchone()
                    if warehouse_id and warehouse_id[0]:
                        context['sequence_obj_ids'].append(['warehouse',warehouse_id[0]])
        values['name'] = self.pool.get('ir.sequence').get(cr, uid, 'pos.order', context=context)
        
        new_id = super(osv.osv, self).create(cr, uid, values, context=context)
        
        cr.execute('''
        UPDATE pos_order_line
        SET section_id=(select section_id from pos_order where id=%s limit 1)
        WHERE order_id=%s and section_id is null
        '''%(new_id,new_id))
        
        cr.execute('''
        UPDATE pos_order
        SET section_id=(select default_section_id from res_users where id=%s limit 1)
        WHERE id=%s
        '''%(values['user_id'],new_id))
        
        return new_id
    #Thanh: Pass obj_name and id to generate Sequence
    
pos_order()

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def button_proforma_voucher(self, cr, uid, ids, context=None):
        context = context or {}
        payment_obj = self.pool.get('pos.make.payment')
        order_obj = self.pool.get('pos.order')
        wf_service = netsvc.LocalService("workflow")
        inv_amount = 0.0
        journal_id = False
        for obj in self.browse(cr,uid,ids):
            journal_id = obj.journal_id.id
            inv_amount = obj.amount
        for vid in ids:
            wf_service.trg_validate(uid, 'account.voucher', vid, 'proforma_voucher', cr)
        if context.get('invoice_id',False):
            statement_id = False
            fields_list =['payment_date', 'amount', 'payment_name', 'journal_id','statement_id']
            line_tm_ids =[]
            line_ck_ids= []
            for line in self.pool.get('account.invoice').browse(cr,uid,[context['invoice_id']]):
                for i in line.pos_order_ids:
                    if i.amount_total - i.amount_paid == 0:
                        continue
                    
                    context={'active_id':i.id}
                    vals = payment_obj.default_get(cr, uid, fields_list, context=context)
                    vals.update({'journal':journal_id})
                    
                    if  vals['amount']> inv_amount:
                        vals['amount'] = inv_amount
                        statement_id = order_obj.add_payment(cr, uid, i.id, vals, context=context)
                        if order_obj.test_paid(cr, uid, [i.id]):
                            wf_service = netsvc.LocalService("workflow")
                            wf_service.trg_validate(uid, 'pos.order', i.id, 'paid', cr)
                        
                        if statement_id:
                            sql ='''
                                SELECT type
                                FROM
                                    account_journal
                                WHERE
                                    id = %s
                            '''%(journal_id)
                            cr.execute(sql)
                            for j in cr.dictfetchall():
                                if j['type'] =='cash':
                                    self.pool.get('account.invoice').write(cr,uid,[line.id],{'statement_line_tm_ids':[(4, statement_id)]})
                                    line_tm_ids.append(statement_id)
                                else:
                                    self.pool.get('account.invoice').write(cr,uid,[line.id],{
                                            'statement_line_ck_ids':[(4, statement_id)]})
                                    line_ck_ids.append(statement_id)
                        sql ='''
                                UPDATE pos_order 
                                SET state = '%s'
                                WHERE id = %s
                            '''%('invoiced',i.id)
                        cr.execute(sql)
                        break
                    else:
                        inv_amount = inv_amount - vals['amount']
                        vals['amount'] = vals['amount']
                        statement_id = order_obj.add_payment(cr, uid, i.id, vals, context=context)
                        if order_obj.test_paid(cr, uid, [i.id]):
                            wf_service = netsvc.LocalService("workflow")
                            wf_service.trg_validate(uid, 'pos.order', i.id, 'paid', cr)
                        if statement_id:
                            sql ='''
                                SELECT type
                                FROM
                                    account_journal
                                WHERE
                                    id = %s
                            '''%(journal_id)
                            cr.execute(sql)
                            for j in cr.dictfetchall():
                                if j['type'] =='cash':
                                    self.pool.get('account.invoice').write(cr,uid,[line.id],{'statement_line_tm_ids':[(4, statement_id)]})
                                    line_tm_ids.append(statement_id)
                                else:
                                    self.pool.get('account.invoice').write(cr,uid,[line.id],{
                                            'statement_line_ck_ids':[(4, statement_id)]})
                                    line_ck_ids.append(statement_id)
                        sql ='''
                            UPDATE pos_order 
                            SET state = '%s'
                            WHERE id = %s
                        '''%('invoiced',i.id)
                        cr.execute(sql)
        return {'type': 'ir.actions.act_window_close'}
account_voucher()
 
class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'pos_order_ids':fields.many2many('pos.order',
            'pos_invoice_res', 'pos_id','invoice_id','Pos'),
        'statement_line_tm_ids':fields.many2many('account.bank.statement.line',
            'statement_line_tm_rel', 'statement_line_id','invoice_id','Moves'),
        'statement_line_ck_ids':fields.many2many('account.bank.statement.line',
            'statement_line_ck_rel', 'statement_line_id','invoice_id','Moves'),
    }
       
account_invoice()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
