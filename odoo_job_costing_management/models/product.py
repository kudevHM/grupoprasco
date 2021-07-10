# -*- coding: utf-8 -*-

from odoo import models, fields

class Product(models.Model):
    _inherit = 'product.product'
    
    boq_type = fields.Selection([
        ('eqp_machine', 'Machinery / Equipment'),
        ('worker_resource', 'Worker / Resource'),
        ('work_cost_package', 'Work Cost Package'),
        ('subcontract', 'Subcontract')], 
        string='BOQ Type', 
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    #type = fields.Selection([('consu', 'Consumable'),('service', 'Service')], string='Product Type', default='service', required=True,help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n''A consumable product is a product for which stock is not managed.\n''A service is a non-material product you provide.')