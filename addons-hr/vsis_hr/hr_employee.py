# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################

from osv import fields, osv
import time
import netsvc
import pooler
import tools
from tools.translate import _
import datetime
import decimal_precision as dp
from tools import config
import logging
_logger = logging.getLogger(__name__)

class hr_maternity_detail(osv.osv):
    _name = "hr.maternity.detail"
    _rec_name = "maternity_id"
    _order = "maternity_id,employee_id"
    _columns = {
        'maternity_id': fields.many2one('hr.maternity','Manernity'),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
        'date_start': fields.date('Date Start', required=True),
        'date_stop': fields.date('Date Stop'),       
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
     
    _constraints = [
        (_check_date_start_stop, 'Stop date must be greater than start date', ['date_start', 'date_stop']),
    ]
    _sql_constraints = [
        ('employee_date_uniq', 'unique (employee_id, date_start)', 'The record must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_maternity_detail, self).copy(cr, uid, id, default, context=context)
hr_maternity_detail()

class hr_uniform(osv.osv):
    _name = "hr.uniform"
    _rec_name = "employee_id"
    _order = "date,employee_id"
    _columns = {      
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'date': fields.date('Date', required=True),
        'note': fields.text('Notes'),
        }
    _sql_constraints = [
        ('date_uniq', 'unique (employee_id, date)', 'The date must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_uniform, self).copy(cr, uid, id, default, context=context)
hr_uniform()

#===============================================================================
# Thong tin gia dinh cua nhan vien 
#===============================================================================
class hr_family(osv.osv):
    _name = "hr.family"
    _description = "Family"
    _order = "employee_id,name"
    _columns = {
        'name' : fields.char("Name", size=64, required=True),
        'id_no' : fields.char("ID", size=64),
        'tax_code' : fields.char("Tax Code", size=64),
        'birthday' : fields.date('Birthday'),
        'email' : fields.char('Email', size=64),
        'phone' : fields.char('Phone', size=32),
        'address_id': fields.many2one('res.partner', 'Working Address'),
        'address_home_id': fields.many2one('res.partner', 'Home Address'),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'function_id': fields.many2one('hr.function', 'Function'),
        'rel_id': fields.many2one('hr.relation', 'Relation'),  
        'note' : fields.text('Notes'),
        'depend': fields.boolean('Depend'),
    } 
    _sql_constraints = [
        ('family_uniq', 'unique (employee_id, name)', 'The record must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['name'] = (record['name'] or '') + '(copy)'
        default['depend'] = False
        return super(hr_family, self).copy(cr, uid, id, default, context=context)
hr_family()

#===============================================================================
# Qua trinh cong tac  
#===============================================================================
class hr_work(osv.osv):
    _name = "hr.work"
    _description = "Work Process"
    _order = "employee_id,name,start_date"
    _columns = {
        'name' : fields.selection([('past', 'Past'),('current', 'Current')],'Type', required=1),
        'start_date' : fields.date('Start Date', required=1),
        'end_date' : fields.date('End Date'),
        'address_id': fields.many2one('res.partner', 'Address', required=1),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'job_id' : fields.many2one("hr.job", "Job", required=1),
        'notes' : fields.text('Other Info'),
    }
    def _check_date_start_stop(self,cr,uid,ids,context=None):
        if context == None:
            context = {}
        obj= self.browse(cr, uid, ids[0], context=context)
        date_start = obj.start_date
        date_stop = obj.end_date
        if date_stop and date_start > date_stop:       
            return False
        return True
     
    _constraints = [
        (_check_date_start_stop, 'Stop date must be greater than start date', ['start_date', 'end_date']),
    ]
    _sql_constraints = [
        ('name_uniq', 'unique (employee_id, start_date, job_id)', 'The record must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['date_start'] = None
        default['date_end'] = None
        default['job_id'] = False
        return super(hr_work, self).copy(cr, uid, id, default, context=context)
hr_work()


#===============================================================================
# Qua trinh dao tao 
#===============================================================================
class hr_training(osv.osv):
    _name = "hr.training"
    _description = "Training Process"
    _order = "employee_id,name,start_date"
    _columns = {
        'name' : fields.selection([('past', 'Past'),('current', 'Current')],'Type', required=1),
        'start_date' : fields.date('Start Date', required=1),
        'end_date' : fields.date('End Date'),
        'address_id': fields.many2one('res.partner', 'Address', required=1),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'certification_id' : fields.many2one("hr.major", "Certification", required=1),
        'notes' : fields.text('Other Info'),
        'file' : fields.binary('File'),
    }
    def _check_date_start_stop(self,cr,uid,ids,context=None):
        if context == None:
            context = {}
        obj= self.browse(cr, uid, ids[0], context=context)
        date_start = obj.start_date
        date_stop = obj.end_date
        if date_stop and date_start > date_stop:       
            return False
        return True
     
    _constraints = [
        (_check_date_start_stop, 'Stop date must be greater than start date', ['start_date', 'end_date']),
    ]
    _sql_constraints = [
        ('name_uniq', 'unique (employee_id, start_date, certification_id)', 'The record must be unique !'),
    ]
    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['date_start'] = None
        default['date_end'] = None
        default['certification_id'] = False
        return super(hr_training, self).copy(cr, uid, id, default, context=context)
hr_training()

#===============================================================================
# inherit employee
#===============================================================================
class hr_employee(osv.osv):
    _inherit = "hr.employee"
    _order = "count asc"
    def format_count(self, count):
        if count < 10:
            return '000' + str(count)
        elif count < 100:
            return '00' + str(count)
        elif count < 1000:
            return '0' + str(count)   
        else:
            return str(count)
        
    def default_count(self, cr, uid, context): 
        sql = """SELECT max(count) as count_hr
                from hr_employee hr_em  """ 
        cr.execute(sql)
        dic = cr.dictfetchone()
        if dic and dic['count_hr']:
            count_emplo = dic['count_hr'] + 1
            return count_emplo    
        return 1
    
    def _get_date(self, cr, uid, ids, field_names, arg, context):   
        res = {}
        date_contract = {'date_start':'', 'date_end': ''}
        if not ids:
            return 
        contract_pool = self.pool.get('hr.contract')   
        sql = """SELECT id, create_date
                    from hr_employee"""
        cr.execute(sql)
            
        for id, date in cr.fetchall():
            line = self.browse(cr, uid, id)
            contract_temp_id = contract_pool.search(cr, uid, [('employee_id','=',line.id),('contract_type','=','hdtv')], order='date_start')
            contract_id = contract_pool.search(cr, uid, [('employee_id','=',line.id),('contract_type','!=','hdtv')], order='date_start')
            contract_temp = contract_temp_id and contract_pool.read(cr, uid, contract_temp_id[0], ['date_start','date_end']) or date_contract
            contract = contract_id and contract_pool.read(cr, uid, contract_id[0], ['date_start']) or date_contract 
            str_date = contract_temp['date_start'] and contract_temp['date_start'] or contract['date_start']
            if not line.code and not line.create_code_date and str_date: 
                self.write(cr, uid,[line.id],{'create_code_date':str_date})

            record ={   
                     'start_working_date' : contract['date_start'],
                     'stop_trying_date' : contract_temp['date_end'],
                     'start_trying_date' : contract_temp['date_start'],
                    }
            res[line.id] = record
        return res   
    
    def _emp_code(self, cr, uid, ids, field_names, arg, context):   
        res = {} 
        if not ids:
            return 
        sql = """SELECT id, create_code_date
                    from hr_employee"""
        cr.execute(sql)
        count = 0    
        for id, create_code_date in cr.fetchall():   
            sql = """SELECT count
                from hr_employee where id = %s"""%(id) 
            cr.execute(sql)
            count_res = cr.fetchone()
            if count_res:                
                count = count_res[0] 
            else:
                count = self.default_count(cr, uid, context)
            count_emplo = self.format_count(count)
            str_date = create_code_date
            code = str_date and ('1' + str_date[2:4] + str_date[5:7] + count_emplo) or ''
            res[id] = code
        return res  
  
    def _get_depend_qty(self, cr, uid, ids, field_names, arg, context):
        res = {}
        if not ids:
            return
        family_pool = self.pool.get('hr.family')         
        for line in self.browse(cr, uid, ids):
            depend_ids = family_pool.search(cr, uid, [('employee_id','=',line.id),('depend','=',True)])
            depend_qty = len(depend_ids) 
            res[line.id] = depend_qty
        return res

    def _get_depend(self, cr, uid, ids, context):
        result = {}
        for line in self.pool.get('hr.family').browse(cr, uid, ids):
            result[line.employee_id.id] = True
        return result.keys()
    
    def _get_deduct(self, cr, uid, ids, context):
        return self.pool.get('hr.employee').search(cr, uid,[])
    
    def _get_create_code_date(self, cr, uid, ids, context):
        result = {}
        for line in self.browse(cr, uid, ids):
            result[line.id] = True 
        return result.keys()
    
    _columns = {
        'company_basic_id': fields.many2one('hr.basic.company','Company Basic Salary'),
        'code': fields.function(_emp_code,                                         
                                string='Code', method=True, type='char', size=9,
                                store={'hr.employee': (_get_create_code_date, ['create_code_date'], 20),} ),
        'count' : fields.integer('Count'),       
        'last_name' : fields.char('Last Name', size=32),                
        'native_place' : fields.many2one('res.country.state','Home Town'),
        'place_of_birth' : fields.many2one('res.country.state','POB'),                               
        'religion_id': fields.many2one('hr.religion', 'Religion'),
        'ethnic_id': fields.many2one('hr.ethnic', 'Ethnic'),
        'level_id': fields.many2one('hr.recruitment.degree', 'Level'),        
        'depend_qty': fields.function(_get_depend_qty,
                                      store={'hr.family': (_get_depend, ['depend'], 20),}, 
                                      method=True, type='integer', string='Depend Qty', readonly=True),       
        'family_ids': fields.one2many('hr.family', 'employee_id','Family'),
        'major_ids' : fields.many2many('hr.certification','cer_emmp_rel', 'cer_id','employee_id', 'Major'),
        'certification_ids' : fields.many2many('hr.major','maj_emmp_rel', 'maj_id','employee_id', 'Certification'),
        'work_ids' : fields.one2many('hr.work', 'employee_id', 'Work'),
        'training_ids' : fields.one2many('hr.training', 'employee_id', 'Training'),
        'maternity_ids' : fields.one2many('hr.maternity.detail', 'employee_id', 'Maternity info'),
        
        #==========================================================
        # thong tin lien he
        #==========================================================        
        'address_temp_id': fields.many2one('res.partner', 'Current Address'),
        'address_home_id': fields.many2one('res.partner', 'Resident Address'),        
        #==========================================================
        #Ngay nhan viec, Ngay bat dau lam veic, ngay thoi viec, ly do thoi viec
        #==========================================================
        'create_code_date' : fields.date('Create Code date'), 
        'stop_working_date' : fields.date('Stop Working Date'),
#        'start_working_date' : fields.function(_get_date, multi='date', method=True, type='date', string='Start Working Date'),   
#        'start_trying_date' : fields.function(_get_date, multi='date', method=True, type='date', string='Start Trying Date'),
#        'stop_trying_date' : fields.function(_get_date, multi='date', method=True, type='date', string='Stop Trying Date'),
        'reason_id' : fields.many2one('hr.reason','Reason stop working'),
        #==========================================================
        # Cac ma so
        #==========================================================
        'code_new': fields.char('Attendance Code',12), # Ma NV
        'identification_id_date': fields.date('ID Date'),
        'identification_id_place': fields.many2one('res.country.state','ID Place'),
        # BHXH
        'sinid_place': fields.many2one('res.country.state','SIN Place'),
        'sinid_date': fields.date('SIN Date'),                 
        #BHTNghiep 
        'ssnid': fields.char('UIN', 32, help='Unemployment Insurance No', required=False),
        'ssnid_date': fields.date('UIN Date'),  
        'ssnid_stop_date': fields.date('UIN Stop Date'),
        # BHTNan
        'accident_code': fields.char('AIN', 32, help='Accident Insurance Number', required=False),
        'accident_code_date': fields.date('AIN Date'),
        'accident_code_stop_date': fields.date('AIN Stop Date'),
        'accident_code_type': fields.many2one('hr.accident.type','Accident Insurance Hospital'),
        #MST
        'emp_code': fields.char('Tax Code',12),
        'user_manager_id': fields.related('parent_id', 'user_id', type='many2one', string='User Manager', readonly=True, relation="res.users", store=True),         
        'remaining_leaves': fields.float(string='Remaining Legal Leaves',type='float',readonly=True),  
        'union_date': fields.date('Union Date'),
    } 
    def chuan_hoa(self, st):
            st = st.lower()
            st = st.rstrip(' ')
            st = st.lstrip(' ')
            return st
        
    def onchange_emp_code(self, cr, uid, ids, emp_code, context=None):
        res = {'warning': True}
        if not emp_code:
            return True   
        emp_ids = self.search(cr, uid, [('id','not in',ids),('emp_code','ilike',emp_code)])     
        for line in self.browse(cr, uid, emp_ids):
            emp_code_vs = self.chuan_hoa(line.emp_code)
            if emp_code_vs == emp_code:
                warning = {
                           'title': _('Warning!'),
                           'message': _('Tax code of employee is already existed')}
                res['warning'] = warning
        return res     
    
    def onchange_sinid(self, cr, uid, ids, sinid, context=None):
        res = {'warning': True}
        if not sinid:
            return True   
        emp_ids = self.search(cr, uid, [('id','not in',ids),('sinid','ilike',sinid)])     
        for line in self.browse(cr, uid, emp_ids):
            sinid_vs = self.chuan_hoa(line.sinid)
            if sinid_vs == sinid:
                warning = {
                           'title': _('Warning!'),
                           'message': _('Social insurance No of employee is already existed')}
                res['warning'] = warning
        return res 
            
    def onchange_ssnid(self, cr, uid, ids, ssnid, context=None):
        res = {'warning': True}
        if not ssnid:
            return res   
        emp_ids = self.search(cr, uid, [('id','not in',ids),('ssnid','ilike',ssnid)])     
        for line in self.browse(cr, uid, emp_ids):
            ssnid_vs = self.chuan_hoa(line.ssnid)
            if ssnid_vs == ssnid:
                warning = {
                           'title': _('Warning!'),
                           'message': _('Unemployment insurance No of employee is already existed')}
                res['warning'] = warning
        return res 
            
    def onchange_accident_code(self, cr, uid, ids, accident_code, context=None):
        res = {'warning': True}
        if not accident_code:
            return res
        emp_ids = self.search(cr, uid, [('id','not in',ids),('accident_code','ilike',accident_code)])     
        for line in self.browse(cr, uid, emp_ids):
            accident_code_vs = self.chuan_hoa(line.accident_code)
            if accident_code_vs == accident_code:
                warning = {
                           'title': _('Warning!'),
                           'message': _('Accident code of employee is already existed')}
                res['warning'] = warning
        return res 
            
    def onchange_identification_id(self, cr, uid, ids, identification_id, context=None):
        res = {'warning': True}
        emp_ids = self.search(cr, uid, [('id','not in',ids),('identification_id','ilike',identification_id)])     
        for line in self.browse(cr, uid, emp_ids):
            identification_id_vs = self.chuan_hoa(line.identification_id)
            if identification_id_vs == identification_id:
                warning = {
                           'title': _('Warning!'),
                           'message': _('ID no. of employee is already existed')}
                res['warning'] = warning
        return res
        
    def onchange_name_birthday(self, cr, uid, ids, name, last_name, birthday, context=None):                     
        res = {'warning': True}
        if not name or not birthday:
            return res
        emp_ids = self.search(cr, uid, [('id','not in',ids),('name','ilike',name), ('birthday','=',birthday)])     
        for line in self.browse(cr, uid, emp_ids):
            name_vs = self.chuan_hoa(line.name)
            last_name_vs = line.last_name and self.chuan_hoa(line.last_name) or ''
            birthday_vs = line.birthday
            name = self.chuan_hoa(line.name)
            last_name = last_name and self.chuan_hoa(last_name) or ''           
            if name_vs == name and last_name_vs == last_name and birthday_vs == birthday:
                warning = {
                           'title': _('Warning!'),
                           'message': _('Employee is already existed')}
                res['warning'] = warning
        return res
    
    def _check_birthday(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        obj= self.browse(cr, uid, ids[0], context=context)
        date = obj.birthday
        if date and date >= time.strftime('%Y-%m-%d'):       
            return False
        return True   
    
    def _check_identification_id_date(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        obj= self.browse(cr, uid, ids[0], context=context)
        date = obj.identification_id_date
        if date and date > time.strftime('%Y-%m-%d'):       
            return False
        return True
    
    def _check_sinid_date(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        obj= self.browse(cr, uid, ids[0], context=context)
        date = obj.sinid_date
        if date and date > time.strftime('%Y-%m-%d'):       
            return False
        return True
    
    def _check_ssnid_date(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        obj= self.browse(cr, uid, ids[0], context=context)
        date = obj.ssnid_date
        if date and date > time.strftime('%Y-%m-%d'):       
            return False
        return True
    
    def _check_accident_code_date(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        obj= self.browse(cr, uid, ids[0], context=context)
        date = obj.accident_code_date
        if date and date > time.strftime('%Y-%m-%d'):       
            return False
        return True
    
    _constraints = [
        (_check_birthday, 'Error ! Date error', ['birthday']),
        (_check_identification_id_date, 'Error ! Date error', ['identification_id_date']),
        (_check_sinid_date, 'Error ! Date error', ['sinid_date']),
        (_check_ssnid_date, 'Error ! Date error', ['ssnid_date']),
        (_check_accident_code_date, 'Error ! Date error', ['accident_code_date']),
    ]
    _sql_constraints = [     
        ('att_code_uniq', 'unique (code_new)',
            'The attendance code of the employee must be unique !'),               
        ('tax_code_uniq', 'unique (emp_code)',
            'The Tax code of the employee must be unique !'),                        
        ('social_insurance_code_uniq', 'unique (sinid)',
            'The social insurance number of the employee must be unique !'),
        ('unemployee_insurance_code_uniq', 'unique (snnid)',
            'The unemployment insurance number of the employee must be unique !'), 
        ('accident_code_uniq', 'unique (accident_code)',
            'The accident code of the employee must be unique !'),                                                    
    ]
    _defaults = { 
        'count' : default_count,
    }  
    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','last_name','code_new'], context=context)
        res = []
        for record in reads:
            name = (record['code_new'] and '[' + record['code_new'] +']' or '') + (record['last_name'] and record['last_name'] + ' ' or'')  + record['name'] 
#            _logger.warning("EMPLOYEE NAME %s",name)
            res.append((record['id'], name))
        return res
  
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        args = args[:] 
        ids = []
        
        if name:
            ids = self.search(cr, user, ['|',('code_new', operator, name),'|',('last_name', operator, name),'|', ('name', operator, name), ('code_new', operator, name)]+ args, limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)     
        return self.name_get(cr, user, ids, context=context)
hr_employee()  

class hr_holidays(osv.osv):
    _inherit = "hr.holidays"
    
    _columns = {
                'remaining_holiday': fields.float('Remaining Holiday', readonly=True, states={'draft':[('readonly',False)], 'confirm':[('readonly',False)]}),
                }
    
    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        from_dt = datetime.datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt = datetime.datetime.strptime(date_to, DATETIME_FORMAT)
        timedelta = to_dt - from_dt
        diff_day = timedelta.days*24 + float(timedelta.seconds) / 3600
        return diff_day
    
    def onchange_date_from(self, cr, uid, ids, date_to, date_from):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8)
            result['value']['date_to'] = str(date_to_with_delta)

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['number_of_days_temp'] = diff_day
        else:
            result['value']['number_of_days_temp'] = 0

        return result

    def onchange_date_to(self, cr, uid, ids, date_to, date_from):
        """
        Update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['number_of_days_temp'] = diff_day
        else:
            result['value']['number_of_days_temp'] = 0

        return result
    
    def check_holidays(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):            
            sql =   '''               
                    SELECT
                    sum(h.number_of_days) as days
                    FROM
                    hr_holidays h
                    JOIN hr_holidays_status s ON (s.id=h.holiday_status_id)
                    WHERE
                    h.state='validate' AND 
                    s.limit=False AND employee_id = %s
                    AND h.holiday_status_id = 1
                    ''' % (record.employee_id.id)
            cr.execute(sql)
            kq = cr.fetchall()
            self.write(cr, uid, ids, {'remaining_holiday': kq[0][0]})
        return super(hr_holidays,self).check_holidays(cr, uid, ids, context=context)
    
hr_holidays()   



#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
