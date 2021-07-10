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
    admin_user = fields.Integer('Admin User', default=2)
    p_order = fields.Char(string='Proyecto', store=True)
    p_order2 = fields.Many2one('job.costing', string='Proyecto',
                               required=True, domain="[('has_req', '!=', True  )]")
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
    state = fields.Selection([
        ('new', 'Nuevo'),
        ('draft', 'Borrador')],
        default="new",
        track_visibility='onchange',
    )

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
            vals["price_unit"] = item.products.lst_price
            vals["product_uom"] = item.products.uom_id.id
            vals["date_planned"] = item.req_date
            vals["order_id"] = purchase_order_id.id
            vals["price_after"] = item.products.lst_price
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
    acumulacion = fields.Integer(string='Cantidad retirada')
    p_order_line_id = fields.One2many(comodel_name='purchase.order.line', inverse_name='req_model_line_id', string='Purchase line')
    available_qty = fields.Integer(string='Cantidad Disponible')

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

    linea_id = fields.Many2one(
        comodel_name='job.cost.line', string='Jobs Line')
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

    linea_id = fields.Many2one(
        comodel_name='job.cost.line', string='Jobs Line')
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

    linea_id = fields.Many2one(
        comodel_name='job.cost.line', string='Jobs Line')
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
