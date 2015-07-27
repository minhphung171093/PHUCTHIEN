# -*- encoding: utf-8 -*-
##############################################################################
#
#    General Solutions, Open Source Management Solution
#    Copyright (C) 2009 General Solutions (<http://gscom.vn>). All Rights Reserved
#
##############################################################################

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
_logger = logging.getLogger(__name__)

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
