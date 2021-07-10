# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    district_mex = fields.Char(string='Distritos')
    