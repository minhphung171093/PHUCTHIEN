# -*- encoding: utf-8 -*-
##############################################################################
#
#    Viet Solution Infomation System, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://vietsolutionis.vn>). All Rights Reserved
#
##############################################################################
import time
from datetime import date
from datetime import timedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import fields, osv
import netsvc
import pooler
import tools
from tools.translate import _


#===============================================================================
# configuration contract
# contract type 
#===============================================================================
class hr_contract_duration(osv.osv):
    _name = "hr.contract.duration"
    _order = "code"
    _description = "Contract duration"
    _columns = {
        'code' : fields.char('Code', 16, required=True),
        'name' : fields.char('Name', 128, required=True),
        'month' : fields.integer('Number of Months', digits=(2,0), required=True),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
    ]
    def copy(self, cr, uid, ids, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, ids, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_contract_duration, self).copy(cr, uid, ids, default, context=context)
hr_contract_duration()

#===============================================================================
#basic salary company
#===============================================================================
class hr_basic_company(osv.osv):
    _name = "hr.basic.company"
    _order= "code, date_start"
    _columns = {
        'code': fields.char('Code', 9, required=True),
        'description': fields.char('Description', 256),
        'name': fields.float('Salary'),
        'date_start': fields.date('Date Start', required=True),
        'date_stop': fields.date('Date Stop'),
        'employee_ids': fields.one2many('hr.employee', 'company_basic_id','Employees'),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the basic salary of company  without removing it."),
    }
    _defaults = {
        'active': True,
    }
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
                name = '[' + record['code'] + '] ' + str(name)
            res.append((record['id'], name))
        return res
    
    def _check_date_start_stop(self,cr,uid,ids,context=None):
        if context == None:
            context = {}
        obj= self.browse(cr, uid, ids[0], context=context)
        date_start = obj.date_start
        date_stop = obj.date_stop
        if date_stop and date_start >= date_stop:       
            return False
        return True
     
    _constraints = [
        (_check_date_start_stop, 'Stop date must be greater than start date', ['date_start', 'date_stop']),
    ]
    
    _sql_constraints = [    
        ('code_uniq', 'unique (code)', 'The code must be unique !'),
        ('name_chk', 'CHECK (name>0)', 'Wrong ratio value !'),
    ]
         
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['date_start'] = time.strftime('%Y-%m-%d')
        default['date_stop'] = False
        return super(hr_basic_company, self).copy(cr, uid, id, default, context=context)
hr_basic_company()

#===============================================================================
# grade scale
#===============================================================================
class hr_grade(osv.osv):
    _name = "hr.grade"
    _order = "code"
    _columns = {
        'code': fields.char('Code', 9, required=True),
        'name': fields.char('Name', 128, required=True),
        'date_start': fields.date('Date Start', required=True),
        'date_stop': fields.date('Date Stop'),
        'grade_line': fields.one2many('hr.grade.line', 'grade_id', 'Grade Line'),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
    }
    def _check_date_start_stop(self,cr,uid,ids,context=None):
        if context == None:
            context = {}
        obj= self.browse(cr, uid, ids[0], context=context)
        date_start = obj.date_start
        date_stop = obj.date_stop
        if date_stop and date_start >= date_stop:       
            return False
        return True
       
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
#        default['date_start'] = time.strftime('%Y-%m-%d')
#        default['date_stop'] = False
        return super(hr_grade, self).copy(cr, uid, id, default, context=context)

hr_grade()

#===============================================================================
# grade line
#===============================================================================
class hr_grade_line(osv.osv):
    _name = "hr.grade.line"
    _columns = {
        'code': fields.char('Code', 9, required=True),
        'name': fields.char('Name', 128, required=True),
        'ratio': fields.float('Ratio'),
        'grade_id': fields.many2one('hr.grade', 'Salary Scale'),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the record without removing it."),
    }
    _defaults = {
        'active': True,
        'ratio': lambda self,cr,uid,ctx=None:1,
    }
    _sql_constraints = [    
        ('name_uniq', 'unique (grade_id, code)', 'The grade line must be unique !'),
        ('ratio_chk', 'CHECK (ratio>=0)',  'Wrong ratio value !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        return super(hr_grade_line, self).copy(cr, uid, id, default, context=context)
hr_grade_line()

#===============================================================================
# reward and discipline
#===============================================================================
class hr_reward_discipline(osv.osv):
    _name = "hr.reward.discipline"
    _columns = {
        'date': fields.date('Date'),
        'name': fields.char('Reference Document'),
        'description': fields.text('Description'),
        'type':fields.selection([
            ('reward','Reward'),
            ('discipline','Discipline'),                        
        ],'Type', required=True),
        'employee_id': fields.many2one('hr.employee', 'Employee'),        
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }
hr_reward_discipline()

#===============================================================================
# salary history
#===============================================================================
class hr_salary_history(osv.osv):
    _name = "hr.salary.history"
    _order = "employee_id, contract_id, date"
    
    def _get_salary(self, cr, uid, ids, field_name, arg, context=None):
        res = {}        
        if not ids:
            return True
        if isinstance(ids, (int, long)):
            ids = [ids]  
        
        for line in self.browse(cr, uid, ids): 
            if line.state == 'draft':           
                ratio = line.grade_id and self.pool.get('hr.grade.line').browse(cr, uid, line.grade_id.id).ratio or 0
                basic_wage = line.contract_id.employee_id.company_basic_id and line.contract_id.employee_id.company_basic_id.name * ratio or 0
                res[line.id] = {'basic_company_id': line.contract_id.employee_id.company_basic_id and line.contract_id.employee_id.company_basic_id.id or False, 
                                'basic_wage': basic_wage,
                                'incentive_wage': line.total_wage > basic_wage and line.total_wage - basic_wage or 0}
            else:
                res[line.id] = {}
        return res

    def _basic_get_ids(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        his_ids = []
        for record in self.browse(cr, uid, ids):
            his_pool = self.pool.get('hr.salary.history')
            his_ids = his_pool.search(cr, uid, [('date','>=',record.date_start)])                    
        return his_ids

    def _grade_get_ids(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        his_ids =[]
        for record in self.browse(cr, uid, ids):         
            his_pool = self.pool.get('hr.salary.history')
            his_ids = his_pool.search(cr, uid, [('grade_id','=',record.id)])
        return his_ids
    
    def _trial_wage(self, cr, uid, ids, field_names, arg, context):  
        res ={}       
        for line in self.browse(cr, uid, ids):
            res[line.id] = line.trial_type == 'percent' and line.total_wage * line.trial_percent/100 or line.trial_wage
        return res
    
    def _set_trial_wage(self, cr, uid, ids, name, value, arg, context=None):
        if not value:
            return False
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            sql_str = """update hr_salary_history set
                    trial_wage = %s
                where
                    id = %s """ % (value, id)
            cr.execute(sql_str)
        return True
    
    _rec_name = 'date'
    _columns = {
        'date' : fields.date('Date', required=True, states={'done':[('readonly',True)]}, ondelete='cascade'),
        'reason_id': fields.many2one('hr.reward.discipline', 'Reward/Discipline', states={'done':[('readonly',True)]}),
        'contract_id': fields.many2one('hr.contract', 'Contract', states={'done':[('readonly',True)]}, ondelete='cascade'),
        'employee_id': fields.related('contract_id', 'employee_id', string='Employee', type='many2one', relation='hr.employee', store=True),
        'scale_id': fields.many2one('hr.grade', 'Salary Scale', states={'done':[('readonly',True)]}),        
        'grade_id': fields.many2one('hr.grade.line', 'Employee Grade', states={'done':[('readonly',True)]}),
        'basic_company_id': fields.function(_get_salary,                                 
                                  method=True, 
                                  store={'hr.salary.history': (lambda self, cr, uid, ids, c={}: ids, ['state', 'date', 'grade_id'], 20),
                                         'hr.grade.line': (_grade_get_ids, ['ratio'], 20),
                                         'hr.basic.company': (_basic_get_ids, ['name','date_start','date_stop'], 20),}, 
                                  type='many2one', 
                                  relation='hr.basic.company', 
                                  string='Company Basic Wage',
                                  multi='wage',
                                  states={'done':[('readonly',True)]}),
#        'basic_wage': fields.function(_get_salary,                                 
#                                  method=True, 
#                                  store={'hr.salary.history': (lambda self, cr, uid, ids, c={}: ids, ['state', 'grade_id', 'date'], 20),
#                                         'hr.grade.line': (_grade_get_ids, ['ratio'], 20),
#                                         'hr.basic.company': (_basic_get_ids, ['name','date_start','date_stop'], 20),}, 
#                                  type='float', 
#                                  string='Basic Wage', 
#                                  multi='wage',
#                                  states={'done':[('readonly',True)]}),
        'basic_wage': fields.float('Basic Wage',states={'done':[('readonly',True)]}),
        'incentive_wage': fields.function(_get_salary,                                 
                                  method=True, 
                                  store={'hr.salary.history': (lambda self, cr, uid, ids, c={}: ids, ['state', 'grade_id', 'date'], 20),
                                         'hr.grade.line': (_grade_get_ids, ['ratio'], 20),
                                         'hr.basic.company': (_basic_get_ids, ['name','date_start','date_stop'], 20),}, 
                                  type='float', 
                                  string='Incentive Wage',
                                  multi='wage',
                                  states={'done':[('readonly',True)]}),
        'allowances_wage': fields.float('Allowances Wage',states={'done':[('readonly',True)]}),
        'mobile_allowances_wage': fields.float('Mobile Allowances Wage',states={'done':[('readonly',True)]}),        
        'incentive_wage': fields.function(_get_salary,                                 
                                  method=True, 
                                  store={'hr.salary.history': (lambda self, cr, uid, ids, c={}: ids, ['state', 'grade_id', 'date'], 20),
                                         'hr.grade.line': (_grade_get_ids, ['ratio'], 20),
                                         'hr.basic.company': (_basic_get_ids, ['name','date_start','date_stop'], 20),}, 
                                  type='float', 
                                  string='Incentive Wage',
                                  multi='wage',
                                  states={'done':[('readonly',True)]}),
        'total_wage': fields.float('Total Wage',states={'done':[('readonly',True)]}),
        'is_trial': fields.boolean('Trial'),
        'trial_wage': fields.function(_trial_wage, 
                                      fnct_inv=_set_trial_wage, 
                                      store={'hr.salary.history': (lambda self, cr, uid, ids, c={}: ids, ['trial_percent'], 20),},
                                      method=True,                                      
                                      string='Trial Wage'), 
        'trial_percent': fields.float('Trial Wage Percent',
                                      states={'done':[('readonly',True)]}),
        'trial_type': fields.selection([('percent', 'Percent'),
                                        ('fix', 'Fix Amount')], 
                                        'Trial Wage Type',
                                        states={'done':[('readonly',True)]}),
        'notes': fields.text('Notes', states={'done':[('readonly',True)]}), 
        'state': fields.selection([('draft','Draft'),
                                   ('done','Done'), 
                                   ('cancel','Cancel')],'State',readonly=True),        
    }
    _defaults = {
        'state': lambda self,cr,uid,ctx=None:'draft',
        'trial_type': lambda self,cr,uid,ctx=None:'percent',
    }
    
    _sql_constraints = [    
        ('history_uniq', 'unique (contract_id, name, state)', 'Record must be unique !'),
    ]
    
    def onchange_trial_type(self, cr, uid, ids, trial_type): 
        return {'value': {'trial_wage':0, 'trial_percent':0}}
    
    def onchange_trial_wage(self, cr, uid, ids, total_wage, trial_percent): 
        return {'value': {'trial_wage': total_wage * trial_percent/100}}
    
    #TODO: return trial wage after change total_wage
    def onchange_basic(self, cr, uid, ids, employee_id, scale_id, grade_id, date, total_wage, trial_date_start, trial_date_end):  
        res = {}
        if not date or not employee_id:
            return res
        emp_pool = self.pool.get('hr.employee')
        emp = emp_pool.browse(cr, uid, employee_id)
        company_basic_id = emp.company_basic_id  
        if not company_basic_id: 
            raise osv.except_osv(_('Warning !'), _("Cannot find company basic wage!"))        
        if company_basic_id.date_start <= date <= company_basic_id.date_stop:
            raise osv.except_osv(_('Warning !'), _("Company basic wage is not valid!"))
        ratio = grade_id and self.pool.get('hr.grade.line').browse(cr, uid, grade_id).ratio or 0
        basic_wage = company_basic_id.name * ratio or 0                    
        if total_wage > 0 and total_wage - basic_wage < 0: 
            raise osv.except_osv(_('Warning !'), _("The wage is invalid!"))
        #TOD0: return domain scale_id
        is_trial = False
        trial_date_start = trial_date_start and trial_date_start or  emp.contract_id.trial_date_start
        trial_date_end = trial_date_end and trial_date_end or  emp.contract_id.trial_date_end
        if trial_date_start <= date <= trial_date_end:
            is_trial = True
        res = {'value':{'is_trial': is_trial,
                        'basic_company_id':company_basic_id.id, 
                        'basic_wage': basic_wage, 
                        'incentive_wage': total_wage > basic_wage and total_wage - basic_wage or 0}}
        return res 
    
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
#        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['name'] = time.strftime('%Y-%m-%d')
        default['state'] = 'draft'  
        return super(hr_salary_history, self).copy(cr, uid, id, default, context=context)
       
    def unlink(self, cr, uid, ids, context=None):   
        for o in self.browse(cr, uid, ids):
            if o.state in ('done','error'):
                raise osv.except_osv(('Error !'), ('You cannot delete done adjust wage line.'))
        return super(hr_salary_history, self).unlink(cr, uid, ids, context=context)

    def action_confirm(self, cr, uid, ids, *args):
        if not ids:
            return False 
        self.write(cr, uid, ids, {'state': 'done'})
        return
    
    def action_cancel(self, cr, uid, ids, *args):
        if not ids:
            return False 
        #TODO: if exist confirm payslip can't cancel 
        self.write(cr, uid, ids, {'state': 'cancel'})
        return
    
    def action_set_draft(self, cr, uid, ids, *args):
        if not ids:
            return False   
        self.write(cr, uid, ids, {'state': 'draft'})
        return
hr_salary_history()

class hr_contract(osv.osv):
    _inherit = "hr.contract"
    
    def _get_wage(self, cr, uid, ids, name, arg, context=None):
        res = {}
        dict_res = {}
        history_pool = self.pool.get('hr.salary.history')
        if not ids: 
            return
        if isinstance(ids, (int, long)):
            ids = [ids]
        for contract in self.browse(cr, uid, ids, context=context):
            his_ids = history_pool.search(cr, uid, [('contract_id','=', contract.id), ('state','=', 'done')], order='date desc')
                        
            if his_ids: 
                his_line = history_pool.browse(cr, uid, his_ids[0])
#                basic = his_line.employee_id.company_basic_id.name * his_line.grade_id.ratio
                basic = his_line.basic_wage
                incentive = his_line.total_wage > basic and his_line.total_wage - basic or 0 
                dict_res = {'basic_company_id': his_line.employee_id.company_basic_id.id, 
                            'basic': basic , 
                            'wage': incentive, 
                            'scale_id': his_line.scale_id.id, 
                            'grade_id': his_line.grade_id.id,
                            'allowances_wage' :his_line.allowances_wage,
                            'mobile_allowances_wage' :his_line.mobile_allowances_wage,
                            'total_wage': his_line.total_wage,
                            'trial_wage': 0}
                
            trial_his_ids = history_pool.search(cr, uid, [('contract_id','=', contract.id), ('state','=', 'done'),('is_trial','=',True)], order='date desc')            
            if trial_his_ids:
                trial_his_line = history_pool.browse(cr, uid, trial_his_ids[0])
                #print 'trial_line', trial_his_line.is_trial, trial_his_line.date, trial_his_line.contract_id.name  
                dict_res.update({'trial_wage': trial_his_line.trial_wage})
            res[contract.id] = dict_res
        #print 'hop dong', res
        return res
    
    def _history_get_ids(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        contract_ids = []     
        for record in self.browse(cr, uid, ids):         
            contract_ids.append(record.contract_id.id)
        return contract_ids
    def _get_status_contract_end(self, cr, uid, ids, name, arg, context=None):        
        res = {}          
        for line in self.browse(cr, uid, ids):
            if line.trial_date_start:
                res[line.id] = 3
            else:
                if line.date_end:
                    result = 0     
                    b = datetime.now()
                    a = line.date_end
                    temp = datetime(int(a[0:4]),int(a[5:7]),int(a[8:10]))
                    kq = temp - b
                    if kq.days < 30:
                        result = 1
                    if kq.days > 30:
                        result = 0
                    if kq.days < 0: 
                        result = 2
                    res[line.id] = result
                else:
                    res[line.id] = 0            
        return res
    _columns = {        
        #=======================================================================
        # add new field
        #=======================================================================
        'department_id': fields.related('employee_id', 'department_id', type='many2one', relation='hr.department', string='Department', store=True, readonly=True),
        'history': fields.one2many('hr.salary.history','contract_id','History Salary'),
        'basic_company_id': fields.function(_get_wage, 
                                    multi='wage', 
                                    type='many2one',
                                    relation='hr.basic.company', 
                                    digits=(16,2), 
                                    string='Company Basic Wage'), 
        'scale_id': fields.function(_get_wage, 
                                    multi='wage',
                                    type='many2one',
                                    relation='hr.grade',
                                    digits=(16,2), 
                                    string='Scale'),        
        'grade_id': fields.function(_get_wage, 
                                    multi='wage', 
                                    type='many2one',
                                    relation='hr.grade.line', 
                                    digits=(16,2), 
                                    string='Grade'),
        'basic': fields.function(_get_wage, 
                                 multi='wage',
                                 store={'hr.salary.history': (_history_get_ids, ['grade_id', 'date', 'state'], 20),
                                        'hr.contract': (lambda self, cr, uid, ids, c={}: ids, ['history'], 20),}, 
                                 type='float', 
                                 digits=(16,2), 
                                 string='Basic Wage'),
        'wage': fields.function(_get_wage, 
                                multi='wage',
                                store={'hr.salary.history': (_history_get_ids, ['grade_id', 'date', 'state'], 20),
                                       'hr.contract': (lambda self, cr, uid, ids, c={}: ids, ['history'], 20),}, 
                                type='float', 
                                digits=(16,2), 
                                string='Incentive Wage'),
        'trial_wage': fields.function(_get_wage, 
                                multi='wage',
                                store={'hr.salary.history': (_history_get_ids, ['grade_id', 'date', 'state', 'trial_percent', 'trial_wage'], 20),
                                       'hr.contract': (lambda self, cr, uid, ids, c={}: ids, ['history'], 20),}, 
                                type='float', 
                                digits=(16,2), 
                                string='Trial Wage'),
        'allowances_wage': fields.function(_get_wage, 
                                      multi='wage',
                                      store={'hr.salary.history': (_history_get_ids, ['grade_id', 'date', 'state'], 20),
                                             'hr.contract': (lambda self, cr, uid, ids, c={}: ids, ['history'], 20),}, 
                                      type='float', 
                                      digits=(16,2), 
                                      string='Allowances Wage'), 
        'mobile_allowances_wage': fields.function(_get_wage, 
                                      multi='wage',
                                      store={'hr.salary.history': (_history_get_ids, ['grade_id', 'date', 'state'], 20),
                                             'hr.contract': (lambda self, cr, uid, ids, c={}: ids, ['history'], 20),}, 
                                      type='float', 
                                      digits=(16,2), 
                                      string='Mobile Allowances Wage'), 
        'total_wage': fields.function(_get_wage, 
                                      multi='wage',
                                      store={'hr.salary.history': (_history_get_ids, ['grade_id', 'date', 'state'], 20),
                                             'hr.contract': (lambda self, cr, uid, ids, c={}: ids, ['history'], 20),}, 
                                      type='float', 
                                      digits=(16,2), 
                                      string='Total Wage'),
        'duration_type': fields.many2one('hr.contract.duration','Contract Duration', required=1),
        'reversion':  fields.integer('Reversion'),
        'date_reversion': fields.date('Date Reversion'),
        'contract_mode': fields.selection([('hdtv', 'Probation'),
                                           ('hdct','Collaborators'),
                                           ('hdld','Official time'),
                                           ('hdhv','Apprenticeship')],
                                           'Contract Mode'),     
        'salary_type': fields.selection([('day', 'Day'),
                                   ('time', 'Time'),
                                   ('product', 'Product'),
                                   ('other', 'Other')], 'Salary Type',
                                   required=True),   
        #override field: not required, required
        'type_id': fields.many2one('hr.contract.type', "Contract Type"),
        'name': fields.char('Contract Reference', size=64, require=True),
        'status_contract_end': fields.function(_get_status_contract_end,type='integer', string='Status Contract End'),
    }
    _defaults = {              
        'reversion': lambda * a: 1,
        'date_reversion': lambda * a: time.strftime('%Y-%m-%d'),
    }
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Contract reference must be unique!'),
        ('employee_date_uniq', 'unique (employee_id, date_start, date_end)', 'Contract duration of employee must be unique!')
    ]  
    _order = 'employee_id desc';  
    
    def on_change_start_date(self, cr, uid, ids, date_start, duration_type):
        if not duration_type:
            return {}
        if not date_start:
            return {}
        date_start = datetime.strptime(date_start, "%Y-%m-%d")
        month = self.pool.get('hr.contract.duration').browse(cr, uid, duration_type).month
        end_date = month>0 and (date_start + relativedelta(months=month)).strftime('%Y-%m-%d') or False
        return {'value':{'date_end': end_date}}
    
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()        
        default['name'] = (record.name or '') + '(Copy)'   
        default['date_start'] = time.strftime('%Y-%m-%d')
        default['date_end'] = False
        return super(osv.osv, self).copy(cr, uid, id, default, context=context)
    
    #Auto create history line date = contract date
    def create(self, cr, uid, vals, context=None):        
        res = super(hr_contract, self).create(cr, uid, vals, context)
        if not 'history' in vals or ('history' in vals and vals['history'] == []):
            history_obj = self.pool.get('hr.salary.history')
            
            record = {'contract_id': res, 
                      'notes': 'name' in vals and vals['name'] or '',
                      'date': vals['date_start'],     
                      'state': 'draft'}
            history_obj.create(cr, uid, record)
        return res


               
hr_contract()

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
