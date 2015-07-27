# -*- encoding: utf-8 -*-
##############################################################################
#
#    Viet Solution Infomation System, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://vietsolutionis.com>). All Rights Reserved
#
##############################################################################

{
        "name" : "VSIS HR Attendance",
        "version" : "1.0",
        "author" : "Viet Solution Infomation System",
        "website" : "http://www.vietsolutionis.com",
        "category" : "VSIS Modules",
        "description" : """VSIS HR""",
        "depends" : ["hr_holidays",'hr','hr_attendance','hr_timesheet_sheet'],
        "init_xml" : [],
        "demo_xml" : [],
        "update_xml" : [
                        'vsis_hr_attendance_view.xml',
                        'wizard/vsis_hr_attendance_wizard.xml',
                        'report/hr_attendance_report.xml',
                        ],
        "installable": True
}
