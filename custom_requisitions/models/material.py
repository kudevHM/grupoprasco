# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError

import logging
_logger = logging.getLogger(__name__)

class MaterialesCategoria(models.Model):
    _name = 'material.categoria'
    name = fields.Char(string='Nombre de Categoria')
    subcat_id = fields.One2many(comodel_name='material.subcategoria', inverse_name='cat_id', string='Subcategoria_id')
    product_id = fields.One2many(comodel_name='product.product', inverse_name='cat_id', string='product_id')
    
    # material_cat = fields.Selection(string="Categoria de Material", selection=[('canalizacion', 'Canalización'), ('cableado', 'Cableado'), ('accesoriado', 'Accesoriado')])
    # material_subcat = fields.Selection(string="Subcategoria de Material", selection=[('sub1', 'ILUMINACIÓN EN LOSA O SOBRE PLAFON'), ('sub2', 'VOZ Y DATOS EN LOSA O SOBRE PLAFON'), ('sub3', 'AIRE ACONDICIONADO EN LOSA O SOBRE PLAFON')])
    
class MaterialesSubcategoria(models.Model):
    _name = 'material.subcategoria'
    name = fields.Char(string='Nombre de Subcategoria')
    cat_id = fields.Many2one(comodel_name='material.categoria', string='Categoria')        
    product_id = fields.One2many(comodel_name='product.product', inverse_name='subcat_id', string='product_id')
