# -*- encoding: utf-8 -*-
##############################################################################
#
#    Viet Solution Infomation System, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://vietsolutionis.com>). All Rights Reserved
#
##############################################################################

{
        "name" : "VSIS HR",
        "version" : "1.0",
        "author" : "Viet Solution Infomation System",
        "website" : "http://www.vietsolutionis.com",
        "category" : "VSIS Modules",
        "description" : """VSIS HR""",
        "depends" : ["vsis_hr"],
        "init_xml" : [],
        "demo_xml" : [],
        "update_xml" : [
                        "security/ir.model.access.csv",
                        "wizard/change_structure_view.xml",
                        "wizard/change_calendar_view.xml",
                        "wizard/hr_payroll_manual_rule_view.xml",  
                        "wizard/hr_payroll_view.xml",  
#                        "hr_holidays_view.xml",
                        "hr_payroll_config_view.xml",  
                        "hr_payroll_view.xml",
                        "wizard/template_view.xml",
                        "hr_payroll_account_view.xml",
                        "hr_payroll_data.xml",                 
                        ],
        "installable": True
}
