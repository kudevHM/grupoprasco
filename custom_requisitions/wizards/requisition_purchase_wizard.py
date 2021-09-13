# -*- coding: utf-8 -*-
from odoo.exceptions import Warning, UserError
from odoo import models, fields, _, api
from datetime import datetime, date

class ReqModelWizard(models.Model):
    _name='requisition.purchase.wizard'


    def _default_picking_type(self):
        type_obj = self.env["stock.picking.type"]
        company_id = self.env.context.get("company_id") or self.env.user.company_id
        types = type_obj.search(
            [("code", "=", "incoming"), ("warehouse_id.company_id", "=", company_id.id)]
        )
        if not types:
            types = type_obj.search(
                [("code", "=", "incoming"), ("warehouse_id", "=", False)]
            )
        return types[:1]
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        required=True,
        copy=True,
    )
    admin_user = fields.Integer('Admin User', default=2)
    name = fields.Char(string="Nombre")
    state = fields.Selection([('draft', 'Borrador'),('vobo', 'Vobo'),('valid','Validar'),('finished', 'Terminado'),('cancel', 'Cancelado')],default="draft")
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Picking Type",
        required=True,
        default=_default_picking_type,
    )    
    job_id = fields.Many2one(
        'job.costing',
        string='Proyecto',
        )
    job_name = fields.Char(string="Nombre de Proyecto", related='job_id.name' ) 
    supplier_id =  fields.Many2one(
        'res.partner',
        string='Provedor',
        )   

    req_lines_ids = fields.One2many(
        comodel_name='requisition.purchase.line.wizard', inverse_name='wiz_id', string='Materiales')

    rec_model = fields.Many2one(
        'req.model',
        string='rec model',
        )
    responsible = fields.Many2many(
        'res.users',
        string='Responsables',
    )   
    total = fields.Float("total", compute="_compute_total")

    def _compute_total(self):
        for rec in self:
            rec.total= 0
            rec.total= sum(rec.req_lines_ids.mapped('subtotal'))
        
    @api.model
    def _prepare_purchase_order(self, line):
        if not self.supplier_id:
            raise UserError(_("Enter a supplier."))
        supplier = self.supplier_id
        data = {

            "partner_id": self.supplier_id.id,
            "fiscal_position_id": supplier.property_account_position_id
            and supplier.property_account_position_id.id
            or False,
            "picking_type_id": line.wiz_id.picking_type_id.id,
            "company_id": line.wiz_id.company_id.id,
            "project_id":line.wiz_id.job_id.id,
            "req_id": self.name,
            "Responsible":[(6, 0,line.wiz_id.responsible.ids)],
            'date_order': datetime.today(),
        }
        return data


    @api.multi
    def write(self, values):
        res = super(ReqModelWizard, self).write(values)
        if self.state=="draft":
            for line in self.req_lines_ids:
                if line.qty < 0.0:
                    raise UserError(_("Ingrese una cantidad positiva."))
                if line.qty > line.available_qty :
                    raise UserError(_("La cantidad a retirar debe ser menor o igual a la cantidad disponible."))
                if not line.pr_active :
                    line.unlink()

            self.state = "vobo"
        return res

    def validate_vobo(self):
        self.state= "valid"

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft') :
                raise Warning(_('Solo puede eliminar la requisición en estado borrador'))
             
        return super(ReqModelWizard, self).unlink()

    @api.model
    def _get_purchase_line_onchange_fields(self):
        return ["product_uom", "name", "taxes_id"]

    @api.model
    def _execute_purchase_line_onchange(self, vals):
        cls = self.env["purchase.order.line"]
        onchanges_dict = {
            "onchange_product_id": self._get_purchase_line_onchange_fields()
        }
        for onchange_method, changed_fields in onchanges_dict.items():
            if any(f not in vals for f in changed_fields):
                obj = cls.new(vals)
                getattr(obj, onchange_method)()
                for field in changed_fields:
                    vals[field] = obj._fields[field].convert_to_write(obj[field], obj)


    @api.model
    def _prepare_purchase_order_line(self, po, item):
        if not item.product_id:
            raise UserError(_("Please select a product for all lines"))
        product = item.product_id

        
        date_required = item.date_planned
        vals = {
            "name": product.name,
            "order_id": po.id,
            "product_id": product.id,
            "product_uom": product.uom_po_id.id or product.uom_id.id,
            "price_unit": item.price_unit,
            "price_after":item.price_unit,
            "product_qty": item.qty,
            # "account_analytic_id": item.line_id.analytic_account_id.id,
            "purchase_request_lines": [(4, item.req_model_line_id.id)],
            "date_planned": datetime(
                date_required.year, date_required.month, date_required.day
            ),
            # "move_dest_ids": [(4, x.id) for x in item.line_id.move_dest_ids],
        }
        #se comento debido a que ejecuta el metdo de obtencion de precion segun configuracion del producto
        self._execute_purchase_line_onchange(vals)
        return vals



    def create_purchase_order(self):
        res = []
        purchase_obj = self.env["purchase.order"]
        po_line_obj = self.env["purchase.order.line"]
        pr_line_obj = self.env["req.model.lines"]
        purchase = False

        for line in self.req_lines_ids:
            # line = item.line_id
            if line.pr_active == True:
                if line.qty <= 0.0:
                    raise UserError(_("Ingrese una cantidad positiva."))
                if line.qty > line.available_qty :
                    raise UserError(_("La cantidad a retirar debe ser menor o igual a la cantidad disponible.")) 
                if not purchase:
                    po_data = self._prepare_purchase_order(line)
                    purchase = purchase_obj.create(po_data)
                po_line_data = self._prepare_purchase_order_line(purchase, line)
                po_line = po_line_obj.create(po_line_data)
                # new_pr_line = True
                # new_qty = pr_line_obj._calc_new_qty(
                #     line, po_line=po_line, new_pr_line=new_pr_line
                # )
                res.append(purchase.id)

        self.state = "finished"
       

class ReqModelWizardLine(models.Model):
    _name='requisition.purchase.line.wizard'
    
    
    product_id =  fields.Many2one(
        'product.product',
        string='Producto',
        )
    qty = fields.Integer(string='Cantidad a retirar')  
    qty_expected  = fields.Integer(string='Cantidad Prevista')  
    available_qty = fields.Integer(string='Cantidad Disponible')
    wiz_id = fields.Many2one(
        "requisition.purchase.wizard",
        string="Wizard",
    )
    pr_active = fields.Boolean("Activo", defaul=False)
    name = fields.Char("Descripción")
    price_unit = fields.Float("precio")
    price_after = fields.Float("precio Anterior")
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom", string="UoM", required=True
    )
    subtotal = fields.Float("sub_total", compute="_compute_subtotal")
    req_model_line_id = fields.Many2one(comodel_name='req.model.lines', string='req model line')
    req_labores_line_id = fields.Many2one(comodel_name='req.labores.lines', string='req model line')
    req_subcontrataciones_line_id = fields.Many2one(comodel_name='req.subcontrataciones.lines', string='req model line')
    date_planned = fields.Datetime("Fecha",default=datetime.today())
    planned_quantity = fields.Integer(string='Cantidad Planificada', compute="_compute_planned_quantity")
    # req_model_line_id = fields.Many2many(
    #     comodel_name="req.model.lines",
    #     relation="requisition_purchase_wizard_order_line_rel",
    #     column1="requisition_purchase_line_wizard_line_id",
    #     column2="requisition_purchase_wizard_line_id",
    #     string="Purchase Request Lines",
    #     readonly=True,
    #     copy=False,
    # )
    job_type_id = fields.Many2one('job.type', string='Tipo de trabajo',related='req_model_line_id.job_type_id' )
    reference = fields.Char(string="Referencia",related='req_model_line_id.reference' )

    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.price_unit * rec.qty
    def _compute_planned_quantity(self):
        for rec in self:
            rec. planned_quantity= 0
            for line in rec.req_model_line_id:
                rec.planned_quantity = line.planned_quantity

    @api.onchange('qty')
    def onchange_field(self):
        self.pr_active = True
    