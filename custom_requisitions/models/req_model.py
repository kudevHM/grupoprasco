# -*- coding: utf-8 -*-

from datetime import datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, _, api
import logging
import xlrd
import tempfile
import binascii
_logger = logging.getLogger(__name__)


class ReqModel(models.Model):
    _name = "req.model"
    _rec_name = "p_order"


    name = fields.Char(string="Nombre")
    admin_user = fields.Integer('Admin User', default=2)
    p_order = fields.Char(string='Proyecto', store=True)
    p_order2 = fields.Many2one('job.costing', string='Proyecto',
                               required=True, domain="[('has_req', '!=', True  )]")
    job_name = fields.Char(string="Nombre de Proyecto", related='p_order2.name' )       
    requisition_wiz = fields.One2many(
        comodel_name='requisition.purchase.wizard', inverse_name='rec_model', string='Materiales')                   
    employee_id = fields.Many2one(
        'res.partner', string='Empleado', required=True)
    date = fields.Date(string='Fecha de Creación')
    Responsible = fields.Many2one(
        'res.users', string='Responsable', required=True)
    req_lines_ids = fields.One2many(
        comodel_name='req.model.lines', inverse_name='req_id', string='Materiales')
    req_labores_ids = fields.One2many(
        comodel_name='req.labores.lines', inverse_name='req_id', string='Requisiciones')
    req_subcontrataciones_ids = fields.One2many(
        comodel_name='req.subcontrataciones.lines', inverse_name='req_id', string='Requisiciones')
    req_canalizaciones_ids = fields.One2many(
        comodel_name='req.canalizaciones.lines', inverse_name='req_id', string='Requisiciones')        
    req_cableado_ids = fields.One2many(
        comodel_name='req.cableado.lines', inverse_name='req_id', string='Requisiciones')    
    req_accesoriado_ids = fields.One2many(
        comodel_name='req.accesoriado.lines', inverse_name='req_id', string='Requisiciones')            
    torres_departamento = fields.Boolean(string='Torres de departamento')
    state = fields.Selection([('draft', 'Borrador'),('valid', 'Validado'),('finished', 'Terminado'),('cancel', 'Cancelado')],default="draft")
    
    purchase_count = fields.Integer(
        string="Purchases count", compute="_compute_purchase_count", readonly=True
    )
    requisition_count = fields.Integer(
        string="Purchases count", compute="_compute_requisition_count", readonly=True
    )
    @api.depends("req_lines_ids")
    def _compute_purchase_count(self):
        self.purchase_count = len(self.mapped("req_lines_ids.purchase_lines.order_id"))

    @api.depends("req_lines_ids")
    def _compute_requisition_count(self):
        self.requisition_count = len(self.mapped("req_lines_ids.purchase_request_lines.wiz_id"))    


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'req.model.sec') or 'New'
        result = super(ReqModel, self).create(vals)
        return result

    def action_view_purchase_order(self):
        action = self.env.ref("purchase.purchase_rfq").read()[0]
        lines = self.mapped("req_lines_ids.purchase_lines.order_id")
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [
                (self.env.ref("purchase.purchase_order_form").id, "form")
            ]
            action["res_id"] = lines.id
        return action

    @api.multi
    def action_view_requisition_order(self):
        action = self.env.ref("custom_requisitions.action_requisition_purchase_wizard").read()[0]
        lines = self.mapped("requisition_wiz.req_lines_ids.wiz_id")
        if len(lines) > 1:
            action["domain"] = [("id", "in", lines.ids)]
        elif lines:
            action["views"] = [
                (self.env.ref("custom_requisitions.requisition_purchase_wizard_form").id, "form")
            ]
            action["res_id"] = lines.id
        return action


    @api.multi
    def action_open_import_wizard(self):
       # new = view_id.create()
        return {
            'type': 'ir.actions.act_window',
            'context': {'torres_departamento': self.torres_departamento, 'req_id':self.id},
            'name': 'A continuación, agregue las plantillas para importar los datos',
            'res_model': 'req.model.wizard',
            'view_type': 'form',
            'view_mode': 'form',
          #  'res_id'    : self.id,
            'view_id': self.env.ref('custom_requisitions.req_model_wizard').id,
            'target': 'new',
        }

    def validate_pr(self):
        self.state= "valid"

    def purchase_request_line_finished(self):
        self.state= "finished"
    def validar(self):
        p_order_id = self.env['purchase.order'].search(
            [("req_id", "=", self.p_order2.number)])
        if len(p_order_id) == 0:
            res = self.env['purchase.order'].create({'partner_id': self.employee_id.id,
                                                     'date_order': datetime.today(),
                                                     'req_id': self.p_order2.number,
                                                     'project_id': self.p_order2.id,
                                                     'Responsible':self.Responsible.id
                                                     })
            purchase_order_id = self.env['purchase.order'].search(
                [("id", "=", res.id)])
        else:
            p_order_id.write({'partner_id': self.employee_id.id,
                              'date_order': datetime.today(),
                              'req_id': self.p_order2.number
                              })
            purchase_order_id = self.env['purchase.order'].search(
                [("id", "=", p_order_id.id)])
            res = False


        for item in self.req_lines_ids:
            p_order_line = self.env['purchase.order.line'].search(
                [("req_model_line_id", "=", item.id)])
            vals = {}
            vals["product_id"] = item.products.id
            vals["name"] = item.description
            vals["product_qty"] = item.acumulacion
            vals["price_unit"] = item.linea_id.cost_price or 0 
            vals["product_uom"] = item.products.uom_id.id
            vals["date_planned"] = item.req_date
            vals["order_id"] = purchase_order_id.id
            vals["price_after"] = item.linea_id.cost_price or 0
            vals["req_model_line_id"] = item.id           
            if len(p_order_line) == 0:
                self.env["purchase.order.line"].create(vals)
            else:
                p_order_line.write(vals)
        for item in self.req_labores_ids:
            p_order_line = self.env['purchase.order.line'].search(
                [("req_labores_line_id", "=", item.id)])
            vals = {}
            vals["product_id"] = item.products.id
            vals["name"] = item.description
            vals["product_qty"] = item.acumulacion
            vals["price_unit"] = item.products.lst_price
            vals["product_uom"] = item.products.uom_id.id
            vals["date_planned"] = item.req_date
            vals["order_id"] = purchase_order_id.id
            vals["req_labores_line_id"] = item.id
            vals["price_after"] = item.products.lst_price

            if len(p_order_line) == 0:
                self.env["purchase.order.line"].create(vals)
            else:
                p_order_line.write(vals)
        for item in self.req_subcontrataciones_ids:
            p_order_line = self.env['purchase.order.line'].search(
                [("req_subcontrataciones_line_id", "=", item.id)])
            vals = {}
            vals["product_id"] = item.products.id
            vals["name"] = item.description
            vals["product_qty"] = item.acumulacion
            vals["price_unit"] = item.products.lst_price
            vals["product_uom"] = item.products.uom_id.id
            vals["date_planned"] = item.req_date
            vals["order_id"] = purchase_order_id.id
            vals["req_subcontrataciones_line_id"] = item.id
            vals["price_after"] = item.products.lst_price

            if len(p_order_line) == 0:
                self.env['purchase.order.line'].create(vals)
            else:
                p_order_line.write(vals)
        return {
            'name': _("Purchase Order"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'purchase.order',
            'res_id': res.id if res else p_order_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
        
    def purchase_request_line_make_purchase_order(self):

        data = []
        view = self.env.ref('custom_requisitions.requisition_purchase_wizard_form')
        
        name = self.p_order2.number + "/"+ str(self.requisition_count)
        purchase_order = self.env['requisition.purchase.wizard'].create({
            'supplier_id':self.employee_id.id,
            'job_id':self.p_order2.id,
            'rec_model':self.id,
            'responsible':self.Responsible.id,
            'name':name
        })

        for line in self.req_lines_ids:
            vals = {}
            vals['product_id'] = line.products.id
            vals['wiz_id'] = purchase_order.id
            vals['name'] = line.description
            vals["price_unit"] = line.linea_id.cost_price or 0 
            vals["price_after"] = line.linea_id.cost_price or 0
            vals["product_uom_id"] = line.products.uom_id.id
            vals["req_model_line_id"] = line.id
            vals['date_planned'] = line.req_date
            vals['available_qty'] = line.available_qty
            vals['qty_expected'] = line.qty_expected
            data.append(vals)
        print("#@@@@@@data:",data)    
        line = self.env['requisition.purchase.line.wizard'].create(data)
        print("####",purchase_order)
        # print("####",line.product_id.name)


        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Orden de Compra',
            'res_model': 'requisition.purchase.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': purchase_order.id,
            'context': self.env.context,
        }

    def cancelar(self):
        for item in self.req_lines_ids:
            item.acumulacion=0
            job_line_id = self.env["job.cost.line"].search(
                [("id", "=", item.linea_id.id)])
            
            if job_line_id:
                job_line_id.sudo().write({
                    "product_qty": item.product_qty
                })
            
    
    @api.multi
    def unlink(self):
        job_id = self.env["job.costing"].search(
            [("id", "=", self.p_order2.id)])
        job_id.write({
            "has_req": False
        })
        return super(ReqModel, self).unlink()

    @api.onchange('p_order2')
    def changePorder(self):
        self.req_lines_ids = [(5, _, _)]
        material_line = self.env["job.cost.line"].search(
            [("direct_id", "=", self.p_order2.id)])
        result = []
        result2 = []
        result3 = []
        for item in material_line:
            if item.job_type == 'material':
                _logger.info('==== %s', item)
                vals = {}
                vals["linea_id"] = item.id
                vals["products"] = item.product_id.id
                vals["description"] = item.description
                vals["qty"] = 0
                vals["req_date"] = item.date
                vals["req_id"] = self.id
                result.append((1, item.id, vals))
            if item.job_type == 'labour':
                _logger.info('==== %s', item)
                vals = {}
                vals["linea_id"] = item.id
                vals["products"] = item.product_id.id
                vals["description"] = item.description
                vals["qty"] = 0
                vals["req_date"] = item.date
                vals["req_id"] = self.id
                result2.append((1, item.id, vals))
            if item.job_type == 'overhead':
                _logger.info('==== %s', item)
                vals = {}
                vals["linea_id"] = item.id
                vals["products"] = item.product_id.id
                vals["description"] = item.description
                vals["qty"] = 0
                vals["req_date"] = item.date
                vals["req_id"] = self.id
                result3.append((1, item.id, vals))
        if self.req_lines_ids:
            self.req_lines_ids = result
        if self.req_labores_ids:
            self.req_labores_ids = result2
        if self.req_subcontrataciones_ids:
            self.req_subcontrataciones_ids = result3

    @api.multi
    def write(self, values):
        res = super(ReqModel, self).write(values)
        # Materiales
        for item in self.req_lines_ids:
            item.changed = False
            job_line_id = self.env["job.cost.line"].search(
                [("id", "=", item.linea_id.id)])
            if job_line_id.product_qty >= item.qty:
                job_line_id.sudo().write({
                    "product_qty": job_line_id.product_qty - item.qty
                })
                acumulado = item.qty + item.acumulacion
                move = self.env['stock.quant'].search(
                    [("product_id", "=", item.products.id), ("company_id", "!=", ''), ("quantity", ">", 0)], limit=1)
                move.sudo().write({
                    'quantity': move.quantity - item.qty
                })
                item.write({'acumulacion': acumulado, 'qty': 0})

            else:
                raise UserError(
                    _('No puede retirar mas productos de lo que hay'))

        # Labores
        for item in self.req_labores_ids:
           #       if item.changed:
            labor = self.env['req.labores.lines'].search(
                [("id", "=", item.id)])
            job_line_id = self.env["job.cost.line"].search(
                [("id", "=", labor.linea_id.id)])
            if job_line_id.cost_price >= item.qty:
                job_line_id.sudo().write({
                    "cost_price": job_line_id.cost_price - item.qty
                })
                acumulado = item.qty + item.acumulacion
                item.write({'acumulacion': acumulado, 'qty': 0})
            else:
                raise UserError(
                    _('No puede consumir mas horas de las programadas'))
            # Subcontratacioens
        for item in self.req_subcontrataciones_ids:
            subcontratacion = self.env['req.subcontrataciones.lines'].search(
                [("id", "=", item.id)])
            job_line_id = self.env["job.cost.line"].search(
                [("id", "=", subcontratacion.linea_id.id)])

            if job_line_id.cost_price >= item.qty:
                job_line_id.sudo().write({
                    "cost_price": job_line_id.cost_price - item.qty
                })
                acumulado = item.qty + item.acumulacion
                move = self.env['stock.quant'].search(
                    [("product_id", "=", item.products.id), ("company_id", "!=", ''), ("quantity", ">", 0)], limit=1)
                move.sudo().write({
                    'cost_price': move.quantity - item.qty
                })
                item.write({'acumulacion': acumulado, 'qty': 0})
            else:
                raise UserError(
                    _('No puede retirar mas productos de lo que hay'))
        return res


class ReqModelLines(models.Model):
    _name = "req.model.lines"

    linea_id = fields.Many2one(
        comodel_name='job.cost.line', string='Jobs Line')
    number = fields.Integer(string='Numero')
    description = fields.Char(string='Descripción')
    qty = fields.Integer(string='Cantidad a retirar')
    req_date = fields.Date(string='Fecha de retiro')
    req_id = fields.Many2one(comodel_name='req.model', string='Requisición')
    products = fields.Many2one(
        'product.product', string='Product', required=True)
    changed = fields.Boolean(string='cambio?')
    acumulacion = fields.Integer(string='Cantidad acumulada')
    # p_order_line_id = fields.One2many(comodel_name='purchase.order.line', inverse_name='req_model_line_id', string='Purchase line')
    available_qty = fields.Integer(string='Cantidad Disponible',  compute="_compute_available_qty")
    qty_expected  = fields.Integer(string='Cantidad Prevista', compute="_compute_purchased_qty") 
    product_qty = fields.Integer(string='Cantidad Planificada')
    purchased_qty = fields.Float(
        string="Cantidad Retirada",
        compute="_compute_purchased_qty",
       
    )
    job_type_id = fields.Many2one('job.type', string='Tipo de trabajo',related='linea_id.job_type_id' )
    reference = fields.Char(string="Referencia",related='linea_id.reference' )


    purchase_lines = fields.Many2many(
        comodel_name="purchase.order.line",
        relation="purchase_request_purchase_order_line_rel",
        column1="purchase_request_line_id",
        column2="purchase_order_line_id",
        string="Purchase Order Lines",
        readonly=True,
        copy=False,
    )
    # purchase_request_lines = fields.Many2many(
    #     comodel_name="requisition.purchase.line.wizard",
    #     relation="requisition_purchase_wizard_order_line_rel",
    #     column1="requisition_purchase_wizard_line_id",
    #     column2="requisition_purchase_line_wizard_line_id",
    #     string="Purchase Order Lines",
    #     readonly=True,
    #     copy=False,
    # )
    purchase_request_lines = fields.One2many(comodel_name='requisition.purchase.line.wizard', inverse_name='req_model_line_id', string='requisition wiz Line')
    
    def _compute_available_qty(self):
        for rec in self:
            rec.available_qty = 0.0
            for line in rec.linea_id:
                rec.available_qty = line.product_qty - line.withdrawn_qty

    def _compute_purchased_qty(self):
        for rec in self:
            rec.purchased_qty = 0.0
            rec.qty_expected = 0.0
            print("####buena",rec.purchase_request_lines)
            for line in rec.purchase_lines.filtered(lambda x: x.state != "cancel"):
                print("####buena")
                rec.purchased_qty += line.product_qty
            for line in rec.purchase_request_lines:
                print("####buena!!!!!!!!!!!!!!")
                rec.qty_expected += line.qty
            qty_expected = self.env['requisition.purchase.line.wizard'].search([('req_labores_line_id','=',rec.id)])
            print("######testtttttt",qty_expected)


    def devolver(self):
        return {
            'type': 'ir.actions.act_window',
            'context': {'default_accumulated_qty': self.acumulacion, 'default_req_id':self.id,'default_line_id':self.id},
            'name': 'Devolucion',
            'res_model': 'devolver.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('custom_requisitions.req_model_devolver_wizard').id,
            'target': 'new',
        }



class ReqLaboresLines(models.Model):
    _name = "req.labores.lines"
    linea_id = fields.Many2one(
        comodel_name='job.cost.line', string='Jobs Line')
    description = fields.Char(string='Descripción')
    qty = fields.Integer(string='Cantidad a descontar')
    req_date = fields.Date(string='Fecha de retiro')
    req_id = fields.Many2one(comodel_name='req.model', string='Requisición')
    products = fields.Many2one(
        'product.product', string='Product', required=True)
    changed = fields.Boolean(string='cambio?', readonly=True)
    acumulacion = fields.Integer(string='Cantidad descontadas')
    p_order_line_id = fields.One2many(comodel_name='purchase.order.line', inverse_name='req_labores_line_id', string='Purchase line')


class ReqsubcontratacionesLines(models.Model):
    _name = "req.subcontrataciones.lines"
    linea_id = fields.Many2one(
        comodel_name='job.cost.line', string='Jobs Line')
    description = fields.Char(string='Descripción')
    qty = fields.Integer(string='Cantidad a descontar')
    req_date = fields.Date(string='Fecha de retiro')
    req_id = fields.Many2one(comodel_name='req.model', string='Requisición')
    products = fields.Many2one(
        'product.product', string='Product', required=True)
    changed = fields.Boolean(string='cambio?', readonly=True)
    acumulacion = fields.Integer(string='Cantidad descontada')
    p_order_line_id = fields.One2many(comodel_name='purchase.order.line', inverse_name='req_subcontrataciones_line_id', string='Purchase line')

class CanalizacionLines(models.Model):
    _name = "req.canalizaciones.lines"

    linea_id = fields.Many2one('job.canalizaciones.lines', string='Jobs Line')
    number = fields.Integer(string='Numero')
    description = fields.Char(string='Descripción')
    qty = fields.Integer(string='Cantidad a retirar')
    req_date = fields.Date(string='Fecha de retiro')
    req_id = fields.Many2one(comodel_name='req.model', string='Requisición')
    products = fields.Many2one(
        'product.product', string='Product', required=True, domain=[('cat_id.name','=', 'Canalización')])
    changed = fields.Boolean(string='cambio?')
    acumulacion = fields.Integer(string='Cantidad retirada')
    p_order_line_id = fields.One2many(comodel_name='purchase.order.line', inverse_name='req_model_line_id', string='Purchase line')
    available_qty = fields.Integer(string='Cantidad Disponible')

class CableadoLines(models.Model):
    _name = "req.cableado.lines"

    # linea_id = fields.Many2one(
    #     comodel_name='job.cableado.lines', string='Jobs Line')
    number = fields.Integer(string='Numero')
    description = fields.Char(string='Descripción')
    qty = fields.Integer(string='Cantidad a retirar')
    req_date = fields.Date(string='Fecha de retiro')
    req_id = fields.Many2one(comodel_name='req.model', string='Requisición')
    products = fields.Many2one(
        'product.product', string='Product', required=True, domain=[('cat_id.name','=', 'Cableado')])
    changed = fields.Boolean(string='cambio?')
    acumulacion = fields.Integer(string='Cantidad retirada')
    p_order_line_id = fields.One2many(comodel_name='purchase.order.line', inverse_name='req_model_line_id', string='Purchase line')
    available_qty = fields.Integer(string='Cantidad Disponible')

class AccesoriadoLines(models.Model):
    _name = "req.accesoriado.lines"

    # linea_id = fields.Many2one(
    #     comodel_name='job.accesoriado.lines', string='Jobs Line')
    number = fields.Integer(string='Numero')
    description = fields.Char(string='Descripción')
    qty = fields.Integer(string='Cantidad a retirar')
    req_date = fields.Date(string='Fecha de retiro')
    req_id = fields.Many2one(comodel_name='req.model', string='Requisición')
    products = fields.Many2one(
        'product.product', string='Product', required=True, domain=[('cat_id.name','=', 'Accesoriado')])
    changed = fields.Boolean(string='cambio?')
    acumulacion = fields.Integer(string='Cantidad retirada')
    p_order_line_id = fields.One2many(comodel_name='purchase.order.line', inverse_name='req_model_line_id', string='Purchase line')
    available_qty = fields.Integer(string='Cantidad Disponible')
