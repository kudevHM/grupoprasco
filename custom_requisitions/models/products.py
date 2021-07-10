# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError

import logging
_logger = logging.getLogger(__name__)

class ProductInherit(models.Model):
    _inherit = 'product.template'

    cat_id = fields.Many2one(comodel_name='material.categoria', string='Categoria')        
    subcat_id = fields.Many2one(comodel_name='material.subcategoria', string='SubCategoria')        
