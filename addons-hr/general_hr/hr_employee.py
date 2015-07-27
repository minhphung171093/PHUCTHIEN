# Embedded file name: D:\Working\Version_7.0\OpenERPV7\addons_hr\general_hr\hr_employee.py
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
import hashlib
import os
import re
from openerp import SUPERUSER_ID
_logger = logging.getLogger(__name__)

class hr_employee(osv.osv):
    _inherit = 'hr.employee'
    _order = 'id desc'

    def _full_path(self, cr, uid, location, path):
        raise location.startswith('file:') or AssertionError('Unhandled filestore location %s' % location)
        location = location[5:]
        location = re.sub('[.]', '', location)
        location = location.strip('/\\')
        path = re.sub('[.]', '', path)
        path = path.strip('/\\')
        return os.path.join(tools.config['root_path'], location, cr.dbname, path)

    def _file_read(self, cr, uid, location, fname, bin_size = False):
        full_path = self._full_path(cr, uid, location, fname)
        r = ''
        try:
            if bin_size:
                r = os.path.getsize(full_path)
            else:
                r = open(full_path, 'rb').read().encode('base64')
        except IOError:
            _logger.error('_read_file reading %s', full_path)

        return r

    def _file_write(self, cr, uid, location, value):
        bin_value = value.decode('base64')
        fname = hashlib.sha1(bin_value).hexdigest()
        fname = fname[:3] + '/' + fname
        full_path = self._full_path(cr, uid, location, fname)
        try:
            dirname = os.path.dirname(full_path)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            open(full_path, 'wb').write(bin_value)
        except IOError:
            _logger.error('_file_write writing %s', full_path)

        return fname

    def _file_delete(self, cr, uid, location, fname):
        count = self.search(cr, 1, [('store_fname', '=', fname)], count=True)
        if count <= 1:
            full_path = self._full_path(cr, uid, location, fname)
            try:
                os.unlink(full_path)
            except OSError:
                _logger.error('_file_delete could not unlink %s', full_path)
            except IOError:
                _logger.error('_file_delete could not unlink %s', full_path)

    def _data_get(self, cr, uid, ids, name, arg, context = None):
        if context is None:
            context = {}
        result = {}
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'hr_employee.location')
        bin_size = context.get('bin_size')
        for attach in self.browse(cr, uid, ids, context=context):
            if location and attach.store_fname:
                result[attach.id] = self._file_read(cr, uid, location, attach.store_fname, bin_size)
            else:
                result[attach.id] = attach.db_datas

        return result

    def _data_set(self, cr, uid, id, name, value, arg, context = None):
        if not value:
            return True
        else:
            if context is None:
                context = {}
            location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'hr_employee.location')
            file_size = len(value.decode('base64'))
            if location:
                attach = self.browse(cr, uid, id, context=context)
                if attach.store_fname:
                    self._file_delete(cr, uid, location, attach.store_fname)
                fname = self._file_write(cr, uid, location, value)
                super(hr_employee, self).write(cr, SUPERUSER_ID, [id], {'store_fname': fname,
                 'file_size': file_size}, context=context)
            else:
                super(hr_employee, self).write(cr, SUPERUSER_ID, [id], {'db_datas': value,
                 'file_size': file_size}, context=context)
            return True

    _columns = {'last_name': fields.char('Last Name', size=32),
     'attendance_code': fields.char('Attendance Code', size=16, required=True),
     'code': fields.char('Employee Code', size=16),
     'attendance_code_start': fields.date('Attendance Code Start', required=True),
     'date_start': fields.date('Start Date', required=True),
     'trial_date_start': fields.date('Probationary Start Date'),
     'trial_date_end': fields.date('Probationary End Date'),
     'trial_extension_start_date': fields.date('Probationary Extension Date'),
     'trial_extension_end_date': fields.date('Probationary Extension End Date'),
     'tax_code': fields.char('Tax Code', size=16),
     'tax_code_date': fields.date('Tax Code Date'),
     'activation_date': fields.date('Effective Date'),
     'office_id': fields.many2one('hr.employee.office', 'Employee Title'),
     'kind_id': fields.many2one('hr.employee.kind', 'Employee Type'),
     'formality_id': fields.many2one('hr.employee.formality', 'Employee Formality'),
     'type_of_labor_id': fields.many2one('hr.type.of.labor', 'Type of labor'),
     'skilled_workmanship': fields.char('Competency', size=128),
     'payroll_category_id': fields.many2one('hr.payroll.category', 'Payroll Category'),
     'cost_code_id': fields.many2one('hr.cost.code', 'Expense Code'),
     'english_name': fields.char('English Name', size=32),
     'place_of_birth': fields.many2one('res.country.state', 'Place of Birth'),
     'identification_id_date': fields.date('ID Date'),
     'identification_id_place': fields.many2one('res.country.state', 'ID Place'),
     'native_land': fields.char('Native Place', size=32),
     'is_car': fields.boolean('Is Car'),
     'driver_license_number': fields.char('Driver license number', size=32),
     'vehicles_id': fields.many2one('hr.vehicles', 'Vehicles'),
     'payslip_password': fields.char('Payslip Password', size=16),
     'level_id': fields.many2one('hr.employee.level', 'Education Level'),
     'ethnic_id': fields.many2one('hr.ethnic', 'Ethnic'),
     'religion_id': fields.many2one('hr.religion', 'Religion'),
     'height': fields.float('Height'),
     'weight': fields.float('Weight'),
     'blood_group': fields.selection([('O+', 'O+'),
                     ('O-', 'O-'),
                     ('A+', 'A+'),
                     ('A-', 'A-'),
                     ('B+', 'B+'),
                     ('B-', 'B-'),
                     ('AB+', 'AB+'),
                     ('AB-', 'AB-')], 'Blood Group'),
     'passport_date': fields.date('Passport Date'),
     'passport_place': fields.many2one('res.country.state', 'Passport Place'),
     'passport_expiration_date': fields.date('Passport expiration date'),
     'is_smoking': fields.boolean('Is Smoking'),
     'closet_id': fields.many2one('hr.closet', 'Closet'),
     'out_sourced': fields.char('Outsourcing', size=64),
     'scheduled_to_work': fields.text('Scheduled to work'),
     'description': fields.text('Description'),
     'datas_fname': fields.char('File Name', size=256),
     'datas': fields.function(_data_get, fnct_inv=_data_set, string='Attachment File', type='binary', nodrop=True),
     'store_fname': fields.char('Stored Filename', size=256),
     'db_datas': fields.binary('Database Data'),
     'file_size': fields.integer('File Size'),
     'email': fields.char('Email', size=240),
     'home_phone': fields.char('Home Phone', size=32, readonly=False),
     'permanent_address_state_id': fields.many2one('res.country.state', 'Permanent Address Provinces'),
     'permanent_address_districts_id': fields.many2one('res.country.districts', 'Permanent Address Districts'),
     'permanent_address': fields.char('Permanent Address', size=240),
     'residence_address_state_id': fields.many2one('res.country.state', 'Residence Address Provinces'),
     'residence_address_districts_id': fields.many2one('res.country.districts', 'Residence Address Districts'),
     'residence_address': fields.char('Residence Address', size=240),
     'emergency_address': fields.char('Emergency Address', size=240),
     'hi_no': fields.char('Health Insurance Number', size=32, help='Health Insurance Number'),
     'hi_date': fields.date('Health Insurance Date'),
     'hi_expired_date': fields.date('Health Insurance Expired Date'),
     'registered_medical': fields.char('Register Hospital', size=32),
     'registered_medical_province': fields.many2one('res.country.state', 'Province'),
     'hospitals_code': fields.char('Hospital Code', size=32),
     'labor_records_number': fields.char('Labor Book number', size=32),
     'labor_records_date': fields.date('Labor Book Date'),
     'unemployment_nsurance_date': fields.date('Unemployment Insurance Date'),
     'time_of_unemployment': fields.integer('Time of Unemployment Insurance', size=32),
     'file_save': fields.char('File Save', size=32),
     'work_permits_id': fields.many2one('hr.work.permits', 'Work Permit(Foreigner)'),
     'work_permits_date': fields.date('Work Permit Date(Foreigner)'),
     'sinid_old': fields.char('SIN Old No', size=32, help='Social Insurance Old Number'),
     'sinid_date': fields.date('SIN Date'),
     'sinid_joining_date': fields.date('SIN Joining Date'),
     'sinid_place': fields.many2one('res.country.state', 'SIN Place'),
     'got_insurance_reserves': fields.boolean('Got Insurance Reserves'),
     'insurance_reserves_date': fields.date('Insurance Reserves Date'),
     'sin_submitted_date': fields.date('Social Insurance Submitted Date'),
     'track_marked': fields.boolean('Track Marked'),
     'work_permits_number': fields.char('Work Permits Number', size=32),
     'work_permits_expired_date': fields.date('Work Permits Expired Date'),
     'note_insurance': fields.text('Note'),
     'submitted_stop_working_date': fields.date('Resign Date'),
     'reason_id': fields.many2one('hr.reason', 'Resign Reason'),
     'stop_working_request_date': fields.date('Resign Request Date'),
     'stop_working_number': fields.char('Resign Number', size=32),
     'is_return_health_insurance': fields.boolean('Is Return Health Insurance'),
     'stop_working_date': fields.date('Leave Date'),
     'black_list': fields.boolean('Black List'),
     'stop_working_approve_date': fields.date('Resign Approve Date'),
     'representative': fields.char('Representative', size=32),
     'return_health_insurance_date': fields.date('Heath Insurance Return Date'),
     'reason_black_list': fields.text('Reason Black List'),
     'coach_id': fields.many2one('hr.employee', 'Leader'),
     'calendar_id': fields.many2one('resource.calendar', 'Working Time', select=True, required=True)}
    _defaults = {}

    def _check_code(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.code:
            code = self.search(cr, uid, [('code', '=', obj.code)])
            if code and len(code) > 1:
                return False
        return True

    def _check_attendance_code(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.attendance_code:
            attendance_code = self.search(cr, uid, [('attendance_code', '=', obj.attendance_code)])
            if attendance_code and len(attendance_code) > 1:
                return False
        return True

    _constraints = [(_check_code, 'The Employee Code must be unique !', ['attendance_code']), (_check_attendance_code, 'The Attendance Code must be unique !', ['attendance_code'])]

    def name_get(self, cr, uid, ids, context = None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'last_name'], context=context)
        res = []
        for record in reads:
            name = record['name'] + ' ' + (record['last_name'] and record['last_name'] or '')
            res.append((record['id'], name))

        return res

    def name_search(self, cr, user, name, args = None, operator = 'ilike', context = None, limit = 100):
        if not args:
            args = []
        args = args[:]
        ids = []
        if name:
            ids = self.search(cr, user, ['|',
             '|',
             ('name', operator, name),
             ('last_name', operator, name),
             ('code', operator, name)] + args, limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)


hr_employee()

class hr_family(osv.osv):
    _name = 'hr.family'
    _description = 'Family'
    _order = 'employee_id,name'
    _columns = {'name': fields.char('Name', size=64, required=True),
     'birthday': fields.date('D.O.B'),
     'phone': fields.char('Phone', size=32),
     'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
     'rel_id': fields.many2one('hr.relation', 'Relationship'),
     'note': fields.text('Notes'),
     'depend': fields.boolean('Depend'),
     'agency_work': fields.char('Agency Work', size=64),
     'nationality_id': fields.many2one('res.country', 'Nationality'),
     'gender': fields.selection([('male', 'Male'), ('female', 'Female')], 'Gender'),
     'career': fields.char('Career', size=64),
     'permanent_address': fields.char('Permanent Address', size=240),
     'date_of_death': fields.date('Date of death')}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.name:
            name = self.search(cr, uid, [('name', '=', obj.name), ('employee_id', '=', obj.employee_id.id)])
            if name and len(name) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Name must be unique !', ['name'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['name'] = (record['name'] or '') + '(copy)'
        default['depend'] = False
        return super(hr_family, self).copy(cr, uid, id, default, context=context)


hr_family()

class hr_uniform(osv.osv):
    _name = 'hr.uniform'
    _rec_name = 'employee_id'
    _order = 'effective_date,employee_id'
    _columns = {'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
     'effective_date': fields.date('Effective Date', required=True),
     'expiration_date': fields.date('Expiration Date'),
     'reissued_date': fields.date('Reissued Date'),
     'size': fields.float('Size'),
     'description': fields.text('Description')}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.employee_id:
            name = self.search(cr, uid, [('effective_date', '=', obj.effective_date), ('employee_id', '=', obj.employee_id.id)])
            if name and len(name) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Employee must be unique !', ['name'])]


hr_uniform()

class hr_qualification(osv.osv):
    _name = 'hr.qualification'
    _rec_name = 'name'
    _order = 'employee_id'
    _columns = {'name': fields.char('Professional', size=240, required=True),
     'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
     'level_id': fields.many2one('hr.employee.level', 'Education Level'),
     'training_address': fields.char('Training Address', size=240),
     'date_start': fields.date('Date Start'),
     'graduate_year': fields.integer('Graduate Year'),
     'training_unit': fields.char('Training Course', size=240),
     'date_end': fields.date('Date End'),
     'grade_id': fields.many2one('hr.qualification.grade', 'Grade'),
     'certificate': fields.char('Certificate'),
     'note': fields.text('Notes')}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.employee_id:
            name = self.search(cr, uid, [('employee_id', '=', obj.employee_id.id)])
            if name and len(name) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Employee must be unique !', ['name'])]


hr_qualification()

class hr_slog(osv.osv):
    _name = 'hr.slog'
    _rec_name = 'employee_id'
    _order = 'id desc'
    _columns = {'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
     'from_date': fields.date('From Date'),
     'end_date': fields.date('To Date'),
     'priority_id': fields.many2one('hr.slog.priority', 'Priority'),
     'type_id': fields.many2one('hr.slog.type', 'Type'),
     'description': fields.text('Description'),
     'note': fields.text('Notes')}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.employee_id:
            name = self.search(cr, uid, [('employee_id', '=', obj.employee_id.id)])
            if name and len(name) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Employee must be unique !', ['name'])]


hr_slog()

class hr_felicitation(osv.osv):
    _name = 'hr.felicitation'
    _rec_name = 'employee_id'
    _order = 'id desc'

    def _full_path(self, cr, uid, location, path):
        raise location.startswith('file:') or AssertionError('Unhandled filestore location %s' % location)
        location = location[5:]
        location = re.sub('[.]', '', location)
        location = location.strip('/\\')
        path = re.sub('[.]', '', path)
        path = path.strip('/\\')
        return os.path.join(tools.config['root_path'], location, cr.dbname, path)

    def _file_read(self, cr, uid, location, fname, bin_size = False):
        full_path = self._full_path(cr, uid, location, fname)
        r = ''
        try:
            if bin_size:
                r = os.path.getsize(full_path)
            else:
                r = open(full_path, 'rb').read().encode('base64')
        except IOError:
            _logger.error('_read_file reading %s', full_path)

        return r

    def _file_write(self, cr, uid, location, value):
        bin_value = value.decode('base64')
        fname = hashlib.sha1(bin_value).hexdigest()
        fname = fname[:3] + '/' + fname
        full_path = self._full_path(cr, uid, location, fname)
        try:
            dirname = os.path.dirname(full_path)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            open(full_path, 'wb').write(bin_value)
        except IOError:
            _logger.error('_file_write writing %s', full_path)

        return fname

    def _file_delete(self, cr, uid, location, fname):
        count = self.search(cr, 1, [('store_fname', '=', fname)], count=True)
        if count <= 1:
            full_path = self._full_path(cr, uid, location, fname)
            try:
                os.unlink(full_path)
            except OSError:
                _logger.error('_file_delete could not unlink %s', full_path)
            except IOError:
                _logger.error('_file_delete could not unlink %s', full_path)

    def _data_get(self, cr, uid, ids, name, arg, context = None):
        if context is None:
            context = {}
        result = {}
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'hr_felicitation.location')
        bin_size = context.get('bin_size')
        for attach in self.browse(cr, uid, ids, context=context):
            if location and attach.store_fname:
                result[attach.id] = self._file_read(cr, uid, location, attach.store_fname, bin_size)
            else:
                result[attach.id] = attach.db_datas

        return result

    def _data_set(self, cr, uid, id, name, value, arg, context = None):
        if not value:
            return True
        else:
            if context is None:
                context = {}
            location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'hr_felicitation.location')
            file_size = len(value.decode('base64'))
            if location:
                attach = self.browse(cr, uid, id, context=context)
                if attach.store_fname:
                    self._file_delete(cr, uid, location, attach.store_fname)
                fname = self._file_write(cr, uid, location, value)
                super(hr_employee, self).write(cr, SUPERUSER_ID, [id], {'store_fname': fname,
                 'file_size': file_size}, context=context)
            else:
                super(hr_employee, self).write(cr, SUPERUSER_ID, [id], {'db_datas': value,
                 'file_size': file_size}, context=context)
            return True

    _columns = {'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
     'grade_date': fields.date('Grade Date'),
     'efficiency_date': fields.date('Efficiency Date'),
     'proposer_id': fields.many2one('hr.employee', 'Proposer'),
     'title_id': fields.many2one('hr.felicitation.title', 'Title'),
     'approved_grade_felicitation': fields.char('Approved Grade Felicitation'),
     'felicitation_phase_id': fields.many2one('hr.felicitation.phase', 'Felicitation Phase'),
     'felicitation_number': fields.integer('Felicitation Number'),
     'type_id': fields.many2one('hr.felicitation.type', 'Type'),
     'felicitation_amount': fields.float('Felicitation Amount'),
     'reason': fields.text('Reason'),
     'description': fields.text('Description'),
     'datas_fname': fields.char('File Name', size=256),
     'datas': fields.function(_data_get, fnct_inv=_data_set, string='Attachment File', type='binary', nodrop=True),
     'store_fname': fields.char('Stored Filename', size=256),
     'db_datas': fields.binary('Attachment File'),
     'file_size': fields.integer('File Size')}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.employee_id:
            name = self.search(cr, uid, [('employee_id', '=', obj.employee_id.id)])
            if name and len(name) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Employee must be unique !', ['name'])]


hr_felicitation()

class hr_discipline(osv.osv):
    _name = 'hr.discipline'
    _rec_name = 'employee_id'
    _order = 'id desc'
    _columns = {'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
     'departmant_manager': fields.char('Department Manager'),
     'violation_date': fields.date('Violation Date'),
     'decided_number': fields.char('Decided Number'),
     'discipline_date': fields.date('Discipline Date'),
     'approver': fields.char('Approver'),
     'date_to': fields.date('Date To'),
     'deponent': fields.char('Deponent'),
     'formality_discipline_id': fields.many2one('hr.discipline.formality', 'Formality Discipline'),
     'efficiency_date': fields.date('Efficiency Date'),
     'expired_date': fields.date('Expired Date'),
     'regulation_content': fields.text('Regulation Content'),
     'description': fields.text('Description Discipline')}


hr_discipline()

class hr_accident(osv.osv):
    _name = 'hr.accident'
    _rec_name = 'employee_id'
    _order = 'id desc'
    _columns = {'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
     'accident_location': fields.char('Accident Location'),
     'date': fields.date('Date'),
     'degree_of_disability': fields.char('Degree Of Disability'),
     'accident_type_id': fields.many2one('hr.accident.type', 'Accident Type'),
     'advance_amount': fields.float('Advance Amount'),
     'actually_paid': fields.float('Actually Paid'),
     'company_paid': fields.float('Company Paid'),
     'insurance_paid': fields.float('Insurance Paid'),
     'note': fields.text('Note')}


hr_accident()

class hr_cost_line(osv.osv):
    _name = 'hr.cost.line'
    _columns = {'mission_id': fields.many2one('hr.mission', 'Mission'),
     'name': fields.char('Cost Name', 128, required=True),
     'amount': fields.float('Amount', required=True)}
    _defaults = {'amount': 0.0}


hr_cost_line()

class hr_mission(osv.osv):
    _name = 'hr.mission'
    _rec_name = 'name'
    _order = 'id desc'

    def _total_cost(self, cr, uid, ids, field_name, arg, context = None):
        res = {}
        for mission in self.browse(cr, uid, ids, context=context):
            res[mission.id] = {'amount_total': 0.0}
            val = 0.0
            for line in mission.cost_line:
                val += line.amount

            res[mission.id] = val

        return res

    _columns = {'name': fields.char('Name', require=True),
     'mission_type_id': fields.many2one('hr.mission.type', 'Mission Type', require=True),
     'state': fields.selection([('draft', 'Draft'),
               ('approve', 'Approve'),
               ('paid', 'Paid'),
               ('done', 'Done')], string='State', size=128, readonly=True),
     'mission_purposes': fields.many2one('hr.mission.purposes', 'Mission Purposes'),
     'code': fields.char('Code', size=16),
     'street': fields.char('Street', size=128),
     'city': fields.char('City', size=128),
     'state_id': fields.many2one('res.country.state', 'State'),
     'country_id': fields.many2one('res.country', 'Country'),
     'date_from': fields.date('Date From'),
     'date_to': fields.date('Date To'),
     'reality_date_from': fields.date('Reality Date From'),
     'reality_date_to': fields.date('Reality Date To'),
     'total_leave': fields.float('Total Leave'),
     'actual_number_of_days': fields.float('Actual Number Of Days'),
     'description': fields.text('Description'),
     'approver_id': fields.many2one('hr.employee', 'Approver'),
     'employee_ids': fields.many2many('hr.employee', 'mission_employee_ref', 'mission_id', 'employee_id', 'Employees', require=True, readonly=True, states={'draft': [('readonly', False)]}),
     'cost_line': fields.one2many('hr.cost.line', 'mission_id', 'Cost Line', readonly=True, states={'draft': [('readonly', False)]}),
     'amount_total': fields.function(_total_cost, string='Total Cost', type='float')}
    _defaults = {'state': 'draft'}

    def to_approve(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'approve'})

    def to_paid(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'paid'})

    def to_done(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'done'})

    def to_refuse(self, cr, uid, ids, context = None):
        return self.write(cr, uid, ids, {'state': 'draft'})


hr_mission()