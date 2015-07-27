# Embedded file name: D:\Working\Version_7.0\OpenERPV7\addons_hr\general_hr\hr_config.py
from osv import fields, osv
import time
import netsvc
import pooler
import tools
from tools.translate import _
import datetime
import decimal_precision as dp
from tools import config

class hr_department(osv.osv):
    _inherit = 'hr.department'
    _columns = {'code': fields.char('Code', size=16, required=True)}


hr_department()

class hr_employee_office(osv.osv):
    _name = 'hr.employee.office'
    _order = 'code'
    _description = 'Office'
    _columns = {'name': fields.char('Name', 64, required=True),
     'code': fields.char('Code', 16, required=True),
     'active': fields.boolean('Active', help='If the active field is set to False, it will allow you to hide the record without removing it.')}
    _defaults = {'active': True}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.code:
            code = self.search(cr, uid, [('code', '=', obj.code)])
            if code and len(code) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Office Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_employee_office, self).copy(cr, uid, id, default, context=context)


hr_employee_office()

class hr_employee_kind(osv.osv):
    _name = 'hr.employee.kind'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Kind Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_employee_kind, self).copy(cr, uid, id, default, context=context)


hr_employee_kind()

class hr_employee_formality(osv.osv):
    _name = 'hr.employee.formality'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Formality Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_employee_formality, self).copy(cr, uid, id, default, context=context)


hr_employee_formality()

class hr_type_of_labor(osv.osv):
    _name = 'hr.type.of.labor'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Type of labor Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_type_of_labor, self).copy(cr, uid, id, default, context=context)


hr_type_of_labor()

class hr_payroll_category(osv.osv):
    _name = 'hr.payroll.category'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Payroll Category Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_payroll_category, self).copy(cr, uid, id, default, context=context)


hr_payroll_category()

class hr_cost_code(osv.osv):
    _name = 'hr.cost.code'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Cost Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_cost_code, self).copy(cr, uid, id, default, context=context)


hr_cost_code()

class hr_vehicles(osv.osv):
    _name = 'hr.vehicles'
    _order = 'code'
    _description = 'Vehicles'
    _columns = {'name': fields.char('Name', 64, required=True),
     'code': fields.char('Code', 16, required=True),
     'active': fields.boolean('Active', help='If the active field is set to False, it will allow you to hide the record without removing it.')}
    _defaults = {'active': True}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.code:
            code = self.search(cr, uid, [('code', '=', obj.code)])
            if code and len(code) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Vehicles Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_vehicles, self).copy(cr, uid, id, default, context=context)


hr_vehicles()

class hr_employee_level(osv.osv):
    _name = 'hr.employee.level'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Level Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_employee_level, self).copy(cr, uid, id, default, context=context)


hr_employee_level()

class hr_ethnic(osv.osv):
    _name = 'hr.ethnic'
    _order = 'code'
    _description = 'Ethnic or Nation'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Ethnic Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_ethnic, self).copy(cr, uid, id, default, context=context)


hr_ethnic()

class hr_religion(osv.osv):
    _name = 'hr.religion'
    _order = 'code'
    _description = 'Religion'
    _columns = {'name': fields.char('Name', 64, required=True),
     'code': fields.char('Code', 9, required=True),
     'active': fields.boolean('Active', help='If the active field is set to False, it will allow you to hide the record without removing it.')}
    _defaults = {'active': True}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.code:
            code = self.search(cr, uid, [('code', '=', obj.code)])
            if code and len(code) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Religion Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_religion, self).copy(cr, uid, id, default, context=context)


hr_religion()

class hr_closet(osv.osv):
    _name = 'hr.closet'
    _order = 'code'
    _description = 'Closet'
    _columns = {'name': fields.char('Name', 64, required=True),
     'code': fields.char('Code', 9, required=True),
     'active': fields.boolean('Active', help='If the active field is set to False, it will allow you to hide the record without removing it.')}
    _defaults = {'active': True}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.code:
            code = self.search(cr, uid, [('code', '=', obj.code)])
            if code and len(code) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Closet Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_closet, self).copy(cr, uid, id, default, context=context)


hr_closet()

class res_country_districts(osv.osv):
    _description = 'Country districts'
    _name = 'res.country.districts'
    _columns = {'state_id': fields.many2one('res.country.state', 'State', required=True),
     'name': fields.char('Districts Name', size=64, required=True, help='Administrative divisions of a country. E.g. Fed. State, Departement, Canton'),
     'code': fields.char('Districts Code', size=3, help='The area code in max. three chars.', required=True)}
    _order = 'code'

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.code:
            code = self.search(cr, uid, [('code', '=', obj.code)])
            if code and len(code) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Districts Code must be unique !', ['code'])]


res_country_districts()

class hr_work_permits(osv.osv):
    _name = 'hr.work.permits'
    _order = 'code'
    _description = 'Work Permits'
    _columns = {'name': fields.char('Name', 64, required=True),
     'code': fields.char('Code', 9, required=True),
     'active': fields.boolean('Active', help='If the active field is set to False, it will allow you to hide the record without removing it.')}
    _defaults = {'active': True}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.code:
            code = self.search(cr, uid, [('code', '=', obj.code)])
            if code and len(code) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Work Permits Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_work_permits, self).copy(cr, uid, id, default, context=context)


hr_work_permits()

class hr_reason(osv.osv):
    _name = 'hr.reason'
    _order = 'code'
    _description = 'reason stop working'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_reason, self).copy(cr, uid, id, default, context=context)


hr_reason()

class hr_relation(osv.osv):
    _name = 'hr.relation'
    _description = 'Family Relationship'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_relation, self).copy(cr, uid, id, default, context=context)


hr_relation()

class hr_qualification_grade(osv.osv):
    _name = 'hr.qualification.grade'
    _description = 'Qualification Grade'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Code must be unique !', ['code'])]

    def copy(self, cr, uid, id, default = {}, context = None, done_list = [], local = False):
        record = self.browse(cr, uid, id, context=context)
        if not default:
            default = {}
        default = default.copy()
        default['code'] = (record['code'] or '') + '(copy)'
        default['name'] = (record['name'] or '') + '(copy)'
        return super(hr_qualification_grade, self).copy(cr, uid, id, default, context=context)


hr_qualification_grade()

class hr_slog_priority(osv.osv):
    _name = 'hr.slog.priority'
    _order = 'id desc'
    _columns = {'name': fields.char('Name', 128, required=True)}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.name:
            name = self.search(cr, uid, [('name', '=', obj.name)])
            if name and len(name) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Slog priority name must be unique !', ['name'])]


hr_slog_priority()

class hr_slog_type(osv.osv):
    _name = 'hr.slog.type'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Slog type Code must be unique !', ['code'])]


hr_slog_type()

class hr_felicitation_title(osv.osv):
    _name = 'hr.felicitation.title'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Felicitation Title Code must be unique !', ['code'])]


hr_felicitation_title()

class hr_felicitation_phase(osv.osv):
    _name = 'hr.felicitation.phase'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Felicitation Phase Code must be unique !', ['code'])]


hr_felicitation_phase()

class hr_felicitation_type(osv.osv):
    _name = 'hr.felicitation.type'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Felicitation Type Code must be unique !', ['code'])]


hr_felicitation_type()

class hr_discipline_formality(osv.osv):
    _name = 'hr.discipline.formality'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Discipline Formality Code must be unique !', ['code'])]


hr_discipline_formality()

class hr_accident_type(osv.osv):
    _name = 'hr.accident.type'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Code must be unique !', ['code'])]


hr_accident_type()

class hr_mission_type(osv.osv):
    _name = 'hr.mission.type'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Code must be unique !', ['code'])]


hr_mission_type()

class hr_mission_purposes(osv.osv):
    _name = 'hr.mission.purposes'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
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

    _constraints = [(_check_name, 'The Code must be unique !', ['code'])]


hr_mission_purposes()

class hr_overtime_type(osv.osv):
    _name = 'hr.overtime.type'
    _order = 'code'
    _columns = {'code': fields.char('Code', 16, required=True),
     'name': fields.char('Name', 128, required=True),
     'ratio': fields.float('Ratio')}
    _defaults = {'ratio': 0.0}

    def _check_name(self, cr, uid, ids):
        obj = self.browse(cr, uid, ids[0])
        if obj and obj.code:
            code = self.search(cr, uid, [('code', '=', obj.code)])
            if code and len(code) > 1:
                return False
        return True

    _constraints = [(_check_name, 'The Code must be unique !', ['code'])]


hr_overtime_type()