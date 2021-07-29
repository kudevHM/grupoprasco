# -*- coding: utf-8 -*-
from odoo.exceptions import Warning, UserError
from odoo import models, fields, _, api
from datetime import datetime, date
class ReqModelWizard(models.TransientModel):
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
    responsible = fields.Many2one('res.users',string='Responsable')   
    
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
            "Responsible":line.wiz_id.responsible.id,
            'date_order': datetime.today(),
        }
        return data







    @api.model
    def _get_purchase_line_onchange_fields(self):
        return ["product_uom", "price_unit", "name", "taxes_id"]

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
            "product_qty": item.qty,
            # "account_analytic_id": item.line_id.analytic_account_id.id,
            "purchase_request_lines": [(4, item.req_model_line_id.id)],
            "date_planned": datetime(
                date_required.year, date_required.month, date_required.day
            ),
            # "move_dest_ids": [(4, x.id) for x in item.line_id.move_dest_ids],
        }
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
                    raise UserError(_("Enter a positive quantity."))
                if not purchase:
                    po_data = self._prepare_purchase_order(line)
                    purchase = purchase_obj.create(po_data)
                print("##############prq",purchase)
                po_line_data = self._prepare_purchase_order_line(purchase, line)
                po_line = po_line_obj.create(po_line_data)
                new_pr_line = True
                # new_qty = pr_line_obj._calc_new_qty(
                #     line, po_line=po_line, new_pr_line=new_pr_line
                # )
                res.append(purchase.id)

        return {
            "domain": [("id", "in", res)],
            "name": _("RFQ"),
            "view_mode": "tree,form",
            "res_model": "purchase.order",
            "view_id": False,
            "context": False,
            "type": "ir.actions.act_window",
        }

class ReqModelWizard(models.TransientModel):
    _name='requisition.purchase.line.wizard'
    
    
    product_id =  fields.Many2one(
        'product.product',
        string='Producto',
        )
    qty = fields.Integer(string='Cantidad a retirar')    
    available_qty = fields.Integer(string='Cantidad Disponible')
    wiz_id = fields.Many2one(
        "requisition.purchase.wizard",
        string="Wizard",
    )
    pr_active = fields.Boolean("Activo", defaul=False)
    name = fields.Char("Nombre")
    price_unit = fields.Float("precio")
    price_after = fields.Float("precio Anterior")
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom", string="UoM", required=True
    )
    req_model_line_id = fields.Many2one(comodel_name='req.model.lines', string='req model line')
    req_labores_line_id = fields.Many2one(comodel_name='req.labores.lines', string='req model line')
    req_subcontrataciones_line_id = fields.Many2one(comodel_name='req.subcontrataciones.lines', string='req model line')
    date_planned = fields.Datetime("Date planned")

    @api.onchange('qty')
    def onchange_field(self):
        self.pr_active = True
    