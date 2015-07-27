# Embedded file name: D:\Working\Version_7.0\OpenERPV7\addons_hr\general_hr\hr_holidays.py
from functools import partial
import logging
from lxml import etree
from lxml.builder import E
from datetime import datetime, timedelta
import openerp
import time
from openerp import SUPERUSER_ID
from openerp import pooler, tools
import openerp.exceptions
from openerp.osv import fields, osv
from openerp.osv.orm import browse_record
from openerp.tools.translate import _
import datetime
from openerp.tools import append_content_to_html
_logger = logging.getLogger(__name__)

class hr_holidays_status(osv.osv):
    _inherit = 'hr.holidays.status'
    _columns = {'ratio': fields.float('Ratio', required=True)}
    _defaults = {'ratio': 1}


hr_holidays_status()