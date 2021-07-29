# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    @api.depends('project_id')
    def compute_project_name(self):
        for rec in self:
            rec.project_name = rec.project_id.name
            
    req_id = fields.Char(string='Requisición', readonly=True)
    name = fields.Char(string='Nombre')
    project_id = fields.Many2one('job.costing', string='Proyecto')
    #orden de trabajo falta
    client_id = fields.Many2one("res.partner", "Cliente")
    Responsible = fields.Many2one('res.users','Responsable', )
    project_name = fields.Char(string='Nombre de Proyecto',compute=compute_project_name)

    
    

class PurchaseOrderLinesInherit(models.Model):
    _inherit = 'purchase.order.line'
    
    req_model_line_id = fields.Many2one(comodel_name='req.model.lines', string='req model line')
    req_labores_line_id = fields.Many2one(comodel_name='req.labores.lines', string='req model line')
    req_subcontrataciones_line_id = fields.Many2one(comodel_name='req.subcontrataciones.lines', string='req model line')
    price_after = fields.Float(string='Nuevo Precio', )
    purchase_request_lines = fields.Many2many(
        comodel_name="purchase.request.line",
        relation="purchase_request_purchase_order_line_rel",
        column1="purchase_order_line_id",
        column2="purchase_request_line_id",
        string="Purchase Request Lines",
        readonly=True,
        copy=False,
    )

    @api.onchange('price_after')
    def onchange_field(self):
        if self.price_after > self.price_unit:
            raise Warning(_("El Nuevo Precio no puede ser mayor al Precio Anterior."))
 

    

