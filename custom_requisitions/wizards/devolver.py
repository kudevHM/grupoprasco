# -*- coding: utf-8 -*-
from odoo.exceptions import Warning, UserError
from odoo import models, fields, _, api
class ReqModelWizard(models.TransientModel):
    _name='devolver.wizard'

    accumulated_qty = fields.Integer(string='Cantidad Acumulada')
    qty = fields.Integer(string='Cantidad a devolver')
    rec_id = fields.Many2one('req.model.lines',string='Rec lines')
    line_id = fields.Char(string='id')

    def devolver(self):
        model_lines = self.env["req.model.lines"].search([('id','=',self.line_id)])
        model_lines_qty = model_lines.acumulacion - self.qty
        model_lines.write({'acumulacion':model_lines_qty})
        
        job_line_id = self.env["job.cost.line"].search(
                [("id", "=", model_lines.linea_id.id)])
            
        if job_line_id:
            job_line_qty = job_line_id.product_qty + self.qty
            job_line_id.sudo().write({
                "product_qty": job_line_qty
            })
        
        
