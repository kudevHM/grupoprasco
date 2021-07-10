# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, _, api
import logging
import xlrd
import tempfile
import binascii
_logger = logging.getLogger(__name__)
class ReqModelWizard(models.TransientModel):
    _name='req.model.wizard'

    material_data = fields.Binary('Importar Materiales')
    labores_data = fields.Binary('Importar labores')    
    subcontrataciones_data = fields.Binary('Importar Subcontrataciones')    
    canalizacion_data = fields.Binary('Import Canalizacion')
    cableado_data = fields.Binary('Import Cableado')
    accesoriado_data = fields.Binary('Import Accesoriado')
    torres_departamento = fields.Boolean(string='Torres de departamento', default=lambda self: self._get_default_status())

    @api.model 
    def _get_default_status(self): 
        if self.env.context.get('torres_departamento'): 
            return self.env.context.get('torres_departamento')


    def import_data_from_excel(self, datos, modelo):
        fp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        fp.write(binascii.a2b_base64(datos)) # self.xls_file is your binary field
        fp.seek(0)
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = (map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                arreglo = list(line)
                producto_tmpl = self.env['product.template'].search([("name", "=", str(arreglo[0],'utf-8'))], limit=1)
                producto = self.env['product.product'].search([('product_tmpl_id', '=', producto_tmpl.id)], limit=1)
                obj={
                    "products":producto.id,
                    "description":arreglo[1],
                    "available_qty":int(float(arreglo[2])),
                    "qty":int(float(arreglo[3])),
                    # "req_date":fecha,
                    "acumulación":int(float(arreglo[5])),
                    "req_id":self.env.context.get('req_id')                 
                }
                self.env[modelo].sudo().create(obj)   

    def import_all(self):
        if self.material_data:
            self.import_data_from_excel(self.material_data, 'req.model.lines')
        if self.labores_data:
            self.import_data_from_excel(self.labores_data, 'req.labores.lines')
        if self.subcontrataciones_data:
            self.import_data_from_excel(self.subcontrataciones_data, 'req.subcontrataciones.lines')                                        
        if self.canalizacion_data:
            self.import_data_from_excel(self.canalizacion_data, 'req.canalizaciones.lines')
        if self.cableado_data:
            self.import_data_from_excel(self.cableado_data, 'req.cableado.lines') 
        if self.accesoriado_data:    
            self.import_data_from_excel(self.accesoriado_data, 'req.accesoriado.lines')     

    # def import_button_materiales(self):
    #     self.import_data_from_excel(self.material_data, 'req.model.lines')
    # def import_button_labores(self):
    #     self.import_data_from_excel(self.labores_data, 'req.labores.lines')
    # def import_button_subcontrataciones(self):
    #     self.import_data_from_excel(self.subcontrataciones_data, 'req.subcontrataciones.lines')                                        
    # def import_button_cana(self):
    #     self.import_data_from_excel(self.canalizacion_data, 'req.canalizaciones.lines')
    # def import_button_cabl(self):
    #     self.import_data_from_excel(self.cableado_data, 'req.cableado.lines') 
    # def import_button_acce(self):
    #     self.import_data_from_excel(self.accesoriado_data, 'req.accesoriado.lines')     