# Embedded file name: D:\Working\Version_7.0\OpenERPV7\addons_hr\general_hr\hr_contract.py
import time
from datetime import date
from datetime import timedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import fields, osv
import netsvc
import pooler
import tools
import logging
import hashlib
import os
import re
from openerp import SUPERUSER_ID
from tools.translate import _
_logger = logging.getLogger(__name__)

class hr_grade_salary(osv.osv):
    _name = 'hr.grade.salary'
    _columns = {'code': fields.char('Code', 9, required=True),
     'name': fields.char('Name', 128, required=True),
     'ratio': fields.float('Ratio'),
     'active': fields.boolean('Active', help='If the active field is set to False, it will allow you to hide the record without removing it.')}
    _defaults = {'active': True,
     'ratio': lambda self, cr, uid, ctx = None: 1}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.code:
            code = self.search(cr, uid, [('code', '=', obj.code)])
            if code and len(code) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Grade Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        return super(hr_grade_salary, self).copy(cr, uid, id, default, context=context)


hr_grade_salary()

class hr_addendum_of_contract_category(osv.osv):
    _name = 'hr.addendum.of.contract.category'
    _columns = {'code': fields.char('Code', 9, required=True),
     'name': fields.char('Name', 128, required=True),
     'active': fields.boolean('Active', help='If the active field is set to False, it will allow you to hide the record without removing it.')}
    _defaults = {'active': True}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.code:
            code = self.search(cr, uid, [('code', '=', obj.code)])
            if code and len(code) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Grade Code must be unique !', ['code'])]


hr_addendum_of_contract_category()

class hr_contract(osv.osv):
    _inherit = 'hr.contract'

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
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'hr_contract.location')
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
            location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'hr_contract.location')
            file_size = len(value.decode('base64'))
            if location:
                attach = self.browse(cr, uid, id, context=context)
                if attach.store_fname:
                    self._file_delete(cr, uid, location, attach.store_fname)
                fname = self._file_write(cr, uid, location, value)
                super(hr_contract, self).write(cr, SUPERUSER_ID, [id], {'store_fname': fname,
                 'file_size': file_size}, context=context)
            else:
                super(hr_contract, self).write(cr, SUPERUSER_ID, [id], {'db_datas': value,
                 'file_size': file_size}, context=context)
            return True

    _columns = {'contract_signing_date': fields.date('Contract Signing Date'),
     'office_id': fields.many2one('hr.employee.office', 'Employee Title'),
     'grade_id': fields.many2one('hr.grade.salary', 'Salary Grade'),
     'signer': fields.char('Signer', size=256),
     'base_on_the_number': fields.char('Base On The Number', size=256),
     'job_id': fields.many2one('hr.job', 'Job'),
     'insurance_wage': fields.float('Insurance Wage', digits=(16, 2)),
     'qualification_id': fields.many2one('hr.qualification', 'Qualification'),
     'form_of_payment': fields.char('Method of Payment', size=256),
     'datas_fname': fields.char('File Name', size=256),
     'datas': fields.function(_data_get, fnct_inv=_data_set, string='Attachment File', type='binary', nodrop=True),
     'store_fname': fields.char('Stored Filename', size=256),
     'db_datas': fields.binary('Attachment File'),
     'file_size': fields.integer('File Size'),
     'addendum_of_contract': fields.one2many('hr.addendum.of.contract', 'contract_id', 'Appendix Of Contract')}


hr_contract()

class hr_addendum_of_contract(osv.osv):
    _name = 'hr.addendum.of.contract'
    _columns = {'efficiency_date': fields.date('Efficiency Date'),
     'sign_date': fields.date('Sign Date'),
     'category_id': fields.many2one('hr.addendum.of.contract.category', 'Appendix Of Contract Category'),
     'code': fields.char('Code', size=16),
     'money': fields.float('Money', digits=(16, 2)),
     'contract_id': fields.many2one('hr.contract', 'Contract', ondelete='cascade')}


hr_addendum_of_contract()