# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################

{
        "name" : "HR",
        "version" : "1.0",
        "author" : "",
        "website" : "",
        "category" : "Modules",
        "description" : """HR Standard""",
        "depends" : ["hr","hr_contract","hr_holidays"],
        "init_xml" : [],
        "demo_xml" : [],
        "update_xml" : [
                        "hr_config_view.xml",  
                        "hr_employee_view.xml",
                        "hr_contract_view.xml",
                        "hr_overtime_view.xml",
                        "hr_holidays_view.xml",
                        "wizard/hr_report_view.xml",
                        "report/list_employee_slog_report.xml",
                        "report/list_employee_birthday_report.xml",
                        "report/list_employee_vehicles_report.xml",
                        "report/list_employee_felicitation_report.xml",
                        "report/list_employee_discipline_report.xml",
                        "report/list_employee_accident_report.xml",
                        "report/list_employee_qualification_report.xml",
                        ],
        "installable": True
}
