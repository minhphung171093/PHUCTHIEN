# -*- encoding: utf-8 -*-
##############################################################################
#
#
##############################################################################
{
	"name" : "General Account Regularizations",
	"version" : "6.1",
	"author" : "Le Truong Thanh <thanh.lt1689@gmail.com>",
	"license" : "GPL-3",
	"category" : "General 70",
	"description" : """ This module creates a new object in accounting, 
	very similar to the account models named account.regularization. 
	Within this object you can define regularization moves, 
	This is, accounting moves that will automatically calculate the balance of a set of accounts, 
	Set it to 0 and transfer the difference to a new account. This is used, for example with tax declarations or in some countries to create the 'Profit and Loss' regularization
""",
	"depends" : ["account","account_accountant"],
	"demo_xml" : [],
	"update_xml" : [
		"account_regularization_view.xml",
		"security/ir.model.access.csv",
		'wizard/account_regularization.xml',
		
		"menu.xml",
	],
	"active": False,
	"installable": True,

}
