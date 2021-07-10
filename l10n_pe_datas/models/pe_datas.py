# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PeDatas(models.Model):
    _name = 'pe.datas'
    _description = 'datas'

    name = fields.Char("Name", required=True)
    company_id = fields.Many2one("res.company", "Company")
    code = fields.Char("Code", required=True)
    un_ece_code = fields.Char("UN/ECE Code")
    table_code = fields.Char("Table Code", required=True)
    active= fields.Boolean("Active", default=True)
    description = fields.Text("Description")
    value = fields.Float('Value', digits=(12, 6))
    un_ece_code_5305 = fields.Char("UN/ECE Code 5305")
    
    _sql_constraints = [
        ('table_code_uniq', 'unique(code, table_code)', 'The code of the table must be unique by table code !')
    ]
    
    @api.model
    def get_selection(self, table_code):
        res=[]
        datas=self.search([('table_code', '=', table_code)])
        if datas:
            res = [(data.code,data.name) for data in datas]
        return res

    @api.model
    def get_name_item_by_table(self, table_code, item_code):
        res=[]
        datas=self.search([('table_code', '=', table_code), ('code', '=', item_code)])
        if datas:
            res = datas['name']
        return res

    @api.model
    def get_name_item_by_table_pe_doc_type(self, item_code):
        res = []
        datas = self.search([('table_code', '=', 'PE.DOC.TYPE'), ('code', '=', item_code)])
        if datas:
            res = datas['name']
        return res
        