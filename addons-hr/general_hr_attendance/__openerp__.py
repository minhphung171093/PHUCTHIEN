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
        "description" : """HR Attendance""",
        "depends" : ["resource","general_hr","hr_timesheet_sheet"],
        "init_xml" : [],
        "demo_xml" : [],
        "update_xml" : [
                        "hr_attendance_config_view.xml",
                        "hr_attendance_view.xml",
                        "wizard/hr_attendance_wizard.xml", 
                        "report/hr_attendance_report.xml"
                        ],
        "installable": True
}
