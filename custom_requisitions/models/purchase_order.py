# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    req_id = fields.Char(string='Requisición', readonly=True)
    name = fields.Char(string='Nombre')
    project_id = fields.Many2one('job.costing', string='Proyecto',required=True)
    #orden de trabajo falta
    client_id = fields.Many2one("res.partner", "Cliente")
    Responsible = fields.Many2one('res.users','Responsable', required=True)

    
    

class PurchaseOrderLinesInherit(models.Model):
    _inherit = 'purchase.order.line'
    
    req_model_line_id = fields.Many2one(comodel_name='req.model.lines', string='req model line')
    req_labores_line_id = fields.Many2one(comodel_name='req.labores.lines', string='req model line')
    req_subcontrataciones_line_id = fields.Many2one(comodel_name='req.subcontrataciones.lines', string='req model line')
    price_after = fields.Float(string='Nuevo Precio', required=True)

    

