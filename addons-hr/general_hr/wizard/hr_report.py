# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.tools
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare

class list_employee_slog_report(osv.osv_memory):
    _name = "list.employee.slog.report"
    
    _columns = {
                'from_date':fields.date('From Date'),
                'to_date':fields.date('To Date'),
                'department_id':fields.many2one('hr.department','Department'),
                }
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'list.employee.slog.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['form'].update({'active_id':context.get('active_ids',False)})
        return {'type': 'ir.actions.report.xml', 'report_name': 'list_employee_slog_report', 'datas': datas}
        
list_employee_slog_report()

class list_employee_birthday_report(osv.osv_memory):
    _name = "list.employee.birthday.report"
    
    _columns = {
                'from_birthday':fields.date('From Birthday'),
                'to_birthday':fields.date('To Birthday'),
                'department_id':fields.many2one('hr.department','Department'),
                }
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'list.employee.birthday.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['form'].update({'active_id':context.get('active_ids',False)})
        return {'type': 'ir.actions.report.xml', 'report_name': 'list_employee_birthday_report', 'datas': datas}
        
list_employee_birthday_report()
class list_employee_vehicles_report(osv.osv_memory):
    _name = "list.employee.vehicles.report"
    
    _columns = {
                'department_id':fields.many2one('hr.department','Department'),
                }
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'list.employee.vehicles.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['form'].update({'active_id':context.get('active_ids',False)})
        return {'type': 'ir.actions.report.xml', 'report_name': 'list_employee_vehicles_report', 'datas': datas}
        
list_employee_vehicles_report()
class list_employee_felicitation_report(osv.osv_memory):
    _name = "list.employee.felicitation.report"
    
    _columns = {
                'from_efficiency_date':fields.date('Efficiency Date From'),
                'to_efficiency_date':fields.date('Efficiency Date To'),
                'department_id':fields.many2one('hr.department','Department'),
                }
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'list.employee.felicitation.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['form'].update({'active_id':context.get('active_ids',False)})
        return {'type': 'ir.actions.report.xml', 'report_name': 'list_employee_felicitation_report', 'datas': datas}
        
list_employee_felicitation_report()
class list_employee_discipline_report(osv.osv_memory):
    _name = "list.employee.discipline.report"
    
    _columns = {
                'efficiency_date_from':fields.date('Efficiency Date From'),
                'efficiency_date_to':fields.date('Efficiency Date To'),
                'violation_date_from':fields.date('Violation Date From'),
                'violation_date_to':fields.date('Violation Date To'),
                'discipline_date_from':fields.date('Discipline Date From'),
                'discipline_date_to':fields.date('Discipline Date To'),
                'department_id':fields.many2one('hr.department','Department'),
                }
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'list.employee.discipline.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['form'].update({'active_id':context.get('active_ids',False)})
        return {'type': 'ir.actions.report.xml', 'report_name': 'list_employee_discipline_report', 'datas': datas}
        
list_employee_discipline_report()

class list_employee_accident_report(osv.osv_memory):
    _name = "list.employee.accident.report"
    _columns = {
                'from_date':fields.date('From Date'),
                'to_date':fields.date('To Date'),
                'accident_type_id': fields.many2one('hr.accident.type', 'Accident Type'),
                'department_id':fields.many2one('hr.department','Department'),
                }
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'list.employee.accident.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['form'].update({'active_id':context.get('active_ids',False)})
        return {'type': 'ir.actions.report.xml', 'report_name': 'list_employee_accident_report', 'datas': datas}
        
list_employee_accident_report()

class list_employee_qualification_report(osv.osv_memory):
    _name = "list.employee.qualification.report"
    _columns = {
                'from_date':fields.date('From Date'),
                'to_date':fields.date('To Date'),
                'department_id':fields.many2one('hr.department','Department'),
                }
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'list.employee.qualification.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        datas['form'].update({'active_id':context.get('active_ids',False)})
        return {'type': 'ir.actions.report.xml', 'report_name': 'list_employee_qualification_report', 'datas': datas}
        
list_employee_qualification_report()


