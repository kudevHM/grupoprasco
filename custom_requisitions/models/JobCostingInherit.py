# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError

import logging
_logger = logging.getLogger(__name__)

class JobCostingInherit(models.Model):
    _inherit = 'job.costing'
    admin_user = fields.Integer('Admin User', default=2)
    current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)
    Responsible = fields.Many2one('res.users','esponsable', )
    # Responsible = fields.Many2many(comodel_name='res.users', relation='responsible_job_res_partner_rel',  column1='job_responsible_ids',column2='Responsible_ids',string='Responsable', required=True)
   
    Responsible = fields.Many2many(
        'res.users',
        string='Responsables',
    )
    req_id = fields.One2many(comodel_name='req.model', inverse_name="p_order2")
    has_req = fields.Boolean(string='tiene requisición?')
    labour_discount = fields.Float(string='Descuento por Labores', readonly=True, compute='_compute_dscto_labour', store=True)
    subc_discount = fields.Float(string='Descuento por Subcontrataciones', readonly=True, compute='_compute_dscto_subc', store=True)
    torres_departamento = fields.Boolean(string='Torres de departamento')
    niveles = fields.Char(string='Niveles')
    rango = fields.Char(string='Rango de departamentos')
    job_canalizaciones_ids = fields.One2many(
        'job.canalizaciones.lines',
        'job_costing_id',
        string='Direct Materials',
        copy=False,
    )
    job_cableado_ids = fields.One2many(
        'job.cableado.lines',
        'job_costing_id',
        string='Direct Materials',
        copy=False,
    )
    job_accesorio_ids = fields.One2many(
        'job.accesoriado.lines',
        'job_costing_id',
        string='Direct Materials',
        copy=False,
        
    )
    @api.depends(
        'job_labour_line_ids',
        'job_labour_line_ids.hours',
        'job_labour_line_ids.cost_price'
    )
    def _compute_labor_total(self):
        for rec in self:
            rec.labor_total = sum([(p.hours * (p.cost_price - p.dcto)) for p in rec.job_labour_line_ids])

    @api.depends(
        'job_overhead_line_ids',
        'job_overhead_line_ids.product_qty',
        'job_overhead_line_ids.cost_price'
    )
    def _compute_overhead_total(self):
        for rec in self:
            rec.overhead_total = sum([(p.product_qty *(p.cost_price - p.dcto)) for p in rec.job_overhead_line_ids])

    @api.depends(
        'job_labour_line_ids',
        'job_labour_line_ids.hours',
        'job_labour_line_ids.cost_price',
    )
    def _compute_dscto_labour(self):
        for rec in self:
            rec.labour_discount = sum([(p.dcto) for p in rec.job_labour_line_ids])        

    @api.depends(
        'job_overhead_line_ids',
        'job_overhead_line_ids.product_qty',
        'job_overhead_line_ids.cost_price',
    )
    def _compute_dscto_subc(self):
        for rec in self:
            rec.subc_discount = sum([(p.dcto) for p in rec.job_overhead_line_ids])   

    @api.multi
    def action_report_requisition(self):
        active_id = self._context.get('active_id', False)
        job_id = self.env['job.costing'].browse(active_id)
       
        view_id = self.env.ref('custom_requisitions.requisition_report_wizard_form').id
      
        return {
            'type': 'ir.actions.act_window',
            'context': {'default_job_id': job_id.id},
            'name': 'Report',
            'res_model': 'requisition.report.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': view_id,
            'target': 'new',
        }
        

    # @api.multi
    # def action_show_requisitions(self):
    #     self.ensure_one()
    #     s_order = self.number
    #     context = self._context
    #     current_uid = context.get('uid')
    #     _logger.info('current user ============%s',current_uid )
    #     _logger.info('admin user============%s',self.admin_user)

    #     return {
    #         'name':_("Requisitions to Process"),
    #         'view_mode':'tree,form',
    #         #'view_id': False,
    #         'view_type': 'form',
    #         'res_model': 'req.model',
    #         #'res_id': req_id,
    #         'type': 'ir.actions.act_window',
    #         #'nodestroy': True,
    #         'target': 'main',
    #         'clear_bredcrumb':True,
    #         #'domain': '[]',
    #         'context': {'default_p_order': s_order},
    #         'flags': {'mode': 'edit'},
    #         'domain':['|',('Responsible','=',current_uid), ("admin_user", "=",current_uid)]
    #     }
    @api.multi
    def action_show_requisitions(self):
        action = self.env.ref("custom_requisitions.action_open_requisitions").read()[0]
        lines = self.mapped("req_id.req_lines_ids.req_id")
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [
                (self.env.ref("custom_requisitions.req_form_view").id, "form")
            ]
            action["res_id"] = lines.id
        return action

    @api.multi
    def write(self, values):
        res = super(JobCostingInherit, self).write(values)
        req_id=self.env["req.model"].search([("p_order", "=", self.number)], limit=1)
        #Busca Materiales
        for item in self.job_cost_line_ids:
            req_line_ids =self.env["req.model.lines"].search([("linea_id","=", item.id)], limit=1)
            if req_line_ids:
                req_line_ids.write({"products": item.product_id.id,"description":item.description,"available_qty":item.product_qty,"qty": 0,"req_date" :item.date,"req_id": req_id.id})
            # else:
            #     self.env["req.model.lines"].create({"linea_id":item.id,"products": item.product_id.id,"description":'',"qty": 0,"req_date" :item.date,"req_id": req_id.id})
        #Busca Labores
        for item in self.job_labour_line_ids:
            req_labores_ids =self.env["req.labores.lines"].search([("linea_id","=", item.id)])
            if req_labores_ids:
                req_labores_ids.write({"products": item.product_id.id,"description":item.description,"qty": 0,"req_date" :item.date,"req_id": req_id.id})
            # else:
            #     self.env["req.labores.lines"].create({"linea_id":item.id,"products": item.product_id.id,"description":item.description,"qty": 0,"req_date" :item.date,"req_id": req_id.id})
        #Busca Subcontrataciones
        for item in self.job_overhead_line_ids:
            req_subcon_ids =self.env["req.subcontrataciones.lines"].search([("linea_id","=", item.id)])
            if req_subcon_ids:
                req_subcon_ids.write({"products": item.product_id.id,"description":item.description,"qty": 0,"req_date" :item.date,"req_id": req_id.id})
            # else:
            #     self.env["req.subcontrataciones.lines"].create({"linea_id":item.id,"products": item.product_id.id,"description":item.description,"qty": 0,"req_date" :item.date,"req_id": req_id.id})                                  
        #buscar canalizacion
        for item in self.job_canalizaciones_ids:
            req_line_ids =self.env["req.canalizaciones.lines"].search([("linea_id","=", item.id)], limit=1)
           
            if req_line_ids:
                req_line_ids.write({"products": item.product_id.id,"description":item.description,"available_qty":item.product_qty,"qty": 0,"req_date" :item.date,"req_id": req_id.id})
        #buscar cableado
        for item in self.job_cableado_ids:
            req_line_ids =self.env["req.cableado.lines"].search([("linea_id","=", item.id)], limit=1)
            if req_line_ids:
                req_line_ids.write({"products": item.product_id.id,"description":item.description,"available_qty":item.product_qty,"qty": 0,"req_date" :item.date,"req_id": req_id.id})
        #buscar accesorio
        for item in self.job_accesorio_ids:
            req_line_ids =self.env["req.accesoriado.lines"].search([("linea_id","=", item.id)], limit=1)
            if req_line_ids:
                req_line_ids.write({"products": item.product_id.id,"description":item.description,"available_qty":item.product_qty,"qty": 0,"req_date" :item.date,"req_id": req_id.id})
        
        return res

    
    @api.multi
    def action_confirm(self):
        req_model = self.env['req.model']
        req_model.sudo().create(
            {   "employee_id":self.partner_id.id,
                "p_order":self.number,
                "p_order2":self.id,
                "Responsible": [(6, 0,self.Responsible.ids)],
                "torres_departamento":self.torres_departamento,
                "state": 'draft'
            }
        )
        id_req_model = self.env['req.model'].search([("p_order2", "=", self.id)], limit=1)
        req_labores = self.env['req.labores.lines']
        req_subcontrataciones = self.env['req.subcontrataciones.lines']
        req_material = self.env['req.model.lines']
        req_canalizacion = self.env['req.canalizaciones.lines']
        req_cable = self.env['req.cableado.lines']
        req_accesorios = self.env['req.accesoriado.lines']

        for item in self.job_cost_line_ids:
            job_id = item.id
            _logger.info('JOB_ID %s', job_id)
            vals={}
            vals["linea_id"]=job_id
            vals["products"]=item.product_id.id
            vals["description"]=item.description
            vals["qty"]=0
            vals["req_date"]=item.date
            vals["req_id"]=id_req_model.id
            vals["product_qty"]=item.product_qty
            _logger.info('OBJETO %s', vals)

            req_material.create(vals)
        for item2 in self.job_labour_line_ids:
            job_id = item2.id
            vals={}
            vals["linea_id"]=job_id
            vals["products"]=item2.product_id.id
            vals["description"]=item2.description
            vals["qty"]=0
            vals["req_date"]=item.date
            vals["req_id"]=id_req_model.id
            req_labores.create(vals)

        for item3 in self.job_overhead_line_ids:
            job_id = item3.id
            vals={}
            vals["number"]=1
            vals["linea_id"]=job_id
            vals["products"]=item3.product_id.id
            vals["description"]=item3.description
            vals["qty"]=0
            vals["req_date"]=item.date
            vals["req_id"]=id_req_model.id
            req_subcontrataciones.create(vals)    
        for item4 in self.job_canalizaciones_ids:
            job_id = item4.id
     
            vals={}
            vals["linea_id"]=item4.id
            vals["products"]=item4.product_id.id
            vals["description"]=item4.description
            vals["qty"]=0
            vals["available_qty"] = item4.product_qty
            vals["req_date"]=item4.date
            vals["req_id"]=id_req_model.id
            req_canalizacion.create(vals)     
        for item5 in self.job_cableado_ids:
            job_id = item5.id
            vals={}
            vals["linea_id"]=job_id
            vals["products"]=item5.product_id.id
            vals["description"]=item5.description
            vals["qty"]=0
            vals["available_qty"] = item5.product_qty
            vals["req_date"]=item5.date
            vals["req_id"]=id_req_model.id
            req_cable.create(vals) 
        for item6 in self.job_accesorio_ids:
            job_id = item6.id
            vals={}
            vals["linea_id"]=job_id
            vals["products"]=item6.product_id.id
            vals["description"]=item6.description
            vals["qty"]=0
            vals["available_qty"] = item6.product_qty
            vals["req_date"]=item6.date
            vals["req_id"]=id_req_model.id
            req_accesorios.create(vals)                             
        for rec in self:
            rec.write({
                'has_req' :True,
                'state' : 'confirm',
            })
            rec.create_sale_order()
            rec.add_items_project_task()  
      
        return super(JobCostingInherit, self).action_confirm()

    @api.multi
    def action_open_import_wizard_job(self):
     # new = view_id.create()
        return {
             'type': 'ir.actions.act_window',
             'context': {'torres_departamento': self.torres_departamento, 'req_id':self.id},
             'name': 'A continuación, agregue las plantillas para importar los datos',
             'res_model': 'job.costing.wizard',
             'view_type': 'form',
            'view_mode': 'form',
         #  'res_id'    : self.id,
             'view_id': self.env.ref('custom_requisitions.budget_wizard').id,
             'target': 'new',
          }      


class JobCostingLineInherit(models.Model):
    _inherit = 'job.cost.line'

    dcto = fields.Float(string='Descuento', readonly=True, stored=True)
    dcto_sub = fields.Float(string='Descuento', readonly=True)
    req_linea_ids = fields.One2many(comodel_name='req.model.lines', inverse_name='linea_id', string='Req Line')
    req_labores_ids = fields.One2many(comodel_name='req.labores.lines', inverse_name='linea_id', string='lab Line')
    req_subcontrataciones_ids = fields.One2many(comodel_name='req.subcontrataciones.lines', inverse_name='linea_id', string='sub Line')
    withdrawn_qty = fields.Float(string="Cantidad Retirada", compute="_compute_withdrawn_qty")



    def _compute_withdrawn_qty(self):
        for rec in self:
            rec.withdrawn_qty = 0.0
            for line in rec.req_linea_ids:
                rec.withdrawn_qty = line.requisition_line_qty

    @api.onchange('cost_price')
    def onchange_listPrice(self):
        if self.job_type != 'material':
            if self.cost_price < 500000:
                self.dcto = self.cost_price*(0.05)
            else:
                self.dcto = self.cost_price*(0.15)
            if self.job_type == 'labour':
                self.total_cost = (self.cost_price - self.dcto)*self.hours
            else:
                self.total_cost = (self.cost_price - self.dcto)*self.product_qty

    @api.onchange('hours')
    def onchange_hour(self):
        if self.job_type != 'material':
            if self.cost_price < 500000:
                self.dcto = self.cost_price*(0.05)
            else:
                self.dcto = self.cost_price*(0.15)
            if self.job_type == 'labour':
                self.total_cost = (self.cost_price - self.dcto)*self.hours
            else:
                self.total_cost = (self.cost_price - self.dcto)*self.product_qty

    @api.depends('product_qty','hours','cost_price','direct_id')
    def _compute_total_cost(self):
        for rec in self:
            req_line_ids = rec.env["req.model.lines"].search([("linea_id","=", rec.id)], limit=1)
            if req_line_ids:
                req_line_ids.write({"available_qty":rec.product_qty})
            if rec.job_type == 'labour':
                rec.product_qty = 0.0
                rec.total_cost = rec.hours * (rec.cost_price - rec.dcto)
            else:
                rec.hours = 0.0
                rec.total_cost = rec.product_qty * (rec.cost_price - rec.dcto)   
            

    @api.onchange('product_qty')
    def onchange_product_qty(self):
        if self.job_type != 'material':
            if self.cost_price < 500000:
                self.dcto = self.cost_price*(0.05)
            else:
                self.dcto = self.cost_price*(0.15)
            if self.job_type == 'labour':
                self.total_cost = (self.cost_price - self.dcto)*self.hours
            else:
                self.total_cost = (self.cost_price - self.dcto)*self.product_qty

class ResUserInherit(models.Model):

    _inherit = 'res.users'

    req_id = fields.One2many(comodel_name='req.model', inverse_name='Responsible', string='Requisition')

class JobCanalizacionLines(models.Model):
    _name = "job.canalizaciones.lines"

    req_linea_ids = fields.One2many('req.canalizaciones.lines','linea_id', string='Req Line')
    description = fields.Char(string='Descripción')
    date = fields.Date(string='Fecha ')
    job_costing_id = fields.Many2one(comodel_name='job.costing', string='Job cost')
    product_id = fields.Many2one(
        'product.product', string='Product', required=True, domain=[('cat_id.name','=', 'Canalización')])
    product_qty = fields.Integer(string='Cantidad Planificada')

class JobCableadoLines(models.Model):
    _name = "job.cableado.lines"
    # req_linea_ids = fields.One2many(comodel_name='req.cableado.lines', inverse_name='linea_id', string='Req Line')
    description = fields.Char(string='Descripción')
    date = fields.Date(string='Fecha')
    job_costing_id = fields.Many2one(comodel_name='job.costing', string='Job cost')
    product_id = fields.Many2one('product.product', string='Product', required=True, domain=[('cat_id.name','=', 'Cableado')])
    product_qty = fields.Integer(string='Cantidad Planificada')

class JobAccesoriadoLines(models.Model):
    _name = "job.accesoriado.lines"

    # req_linea_ids = fields.One2many(comodel_name='req.accesoriado.lines', inverse_name='linea_id', string='Req Line')
    description = fields.Char(string='Descripción')
    date = fields.Date(string='Fecha')
    job_costing_id = fields.Many2one(comodel_name='job.costing', string='Job cost')
    product_id = fields.Many2one(
        'product.product', string='Product', required=True, domain=[('cat_id.name','=', 'Accesoriado')])
    product_qty = fields.Integer(string='Cantidad Planificada')    

