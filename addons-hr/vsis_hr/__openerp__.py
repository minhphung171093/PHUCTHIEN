# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################

{
        "name" : "VSIS HR",
        "version" : "1.0",
        "author" : "Viet Solution Infomation System",
        "website" : "http://www.vietsolutionis.com",
        "category" : "VSIS Modules",
        "description" : """VSIS HR""",
        "depends" : ["hr","hr_contract","hr_payroll","hr_recruitment", "hr_payroll_account","hr_timesheet","hr_timesheet_sheet","hr_timesheet_invoice"],
        "init_xml" : [],
        "demo_xml" : [],
        "update_xml" : ["security/ir.model.access.csv",
                        "security/hr_security.xml",
                        "hr_config_view.xml",  
                        "hr_employee_view.xml",
                        "hr_contract_view.xml",
                        "wizard/change_company_basic_view.xml",
                        "wizard/change_history_view.xml",
                        ],
        "installable": True
}
