# -*- encoding: utf-8 -*-
from PIL import Image
import requests
import pytesseract
from bs4 import BeautifulSoup
from bs4 import Comment
from lxml import etree
from io import StringIO , BytesIO
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from collections import OrderedDict
import re
import logging
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    @staticmethod
    def _get_captcha(type, countdown):
        s = requests.Session()
        if type.upper() == 'R':
            # Solo para consulta de RUC el countdown sera de 2 intentos para resolver el captcha
            if countdown > 0:
                try:
                    r = s.get('http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/captcha?accion=image&nmagic=0')
                    if r.status_code != 200:
                        return (False, r)
                #except s.exceptions .RequestException as e:
                except s.exceptions.RequestException as e:
                    if countdown > 0:
                        consulta, captcha_val = cls._get_captcha("R", countdown - 1)
                        return (consulta, captcha_val)
                    else:
                        return (False, e)
                try:
                    img = Image.open(BytesIO(r.content))

                except Exception as e:

                    return (False, e)

                captcha_val = pytesseract.image_to_string(img)
                captcha_val = captcha_val.strip().upper()
                return (s, captcha_val)
            else:
                return (False, e)

    @classmethod
    def _get_sunat_getRepLeg(cls, desRuc, vat):
        _logger.info("_get_sunat_getRepLeg - l10n_pe_vat")
        vals = []
        if not cls.validate_ruc(vat):
            raise UserError(_('the RUC entered is incorrect'))
        for i in range(10):
            consulta, captcha_val = cls._get_captcha("R", 1)
            if not consulta:
                raise UserError(_('El servidor de consulta no está en linea, por favor reitentelo más tarde.'))
            if captcha_val.isalpha():
                break
        payload = OrderedDict()
        payload['accion'] = 'getRepLeg'
        payload['desRuc'] = desRuc
        payload['nroRuc'] = vat
        post = consulta.post("http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias", params=payload)
        if post.status_code != 200:
            raise UserError(_('El servidor de consulta no está en linea, por favor reitentelo más tarde.'))
        texto_error = 'Surgieron problemas al procesar la consulta'
        texto_consulta = post.text

        if texto_error in (texto_consulta):
            raise UserError(_('El servidor de consulta no responde, por favor reintentelo más tarde'))

        texto_consulta = texto_consulta.replace('<br>', '\n')
        texto_consulta = re.sub("(<!--.*?-->)", "", texto_consulta, flags=re.MULTILINE)

        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(texto_consulta), parser)
        j=0
        vals_cabecera = {}
        for _th in tree.findall("//th[@class='beta']"):
            if _th.attrib['class'] == 'beta':
                vals_cabecera[j] = [_th.text.strip()]
                j += 1

        # Busqueda de datos
        item = {}
        i = 0
        for _td in tree.findall("//td[@class='bg']"):
            if i % j == 0 and i != 0:
                vals.append(item)
                item = {}
                i = 0
            if _td.attrib['class'] == 'bg':
                item[vals_cabecera[i][0]] = _td.text.strip()
                i += 1
        vals.append(item)
        return vals

    @classmethod
    def _get_sunat_details(cls, vat):
        _logger.info("_get_sunat_details - l10n_pe_vat")
        vals = {}
        con_error = False
        if not cls.validate_ruc(vat):
            raise UserError(_('the RUC entered is incorrect'))
        for i in range(10):
            consulta, captcha_val = cls._get_captcha("R", 1)
            if not consulta:
                raise UserError(_('El servidor de consulta no está en linea, por favor reitentelo más tarde.'))
            if captcha_val.isalpha():
                break
        payload = OrderedDict()
        payload['accion'] = 'consPorRuc'
        payload['razSoc'] = ''
        payload['nroRuc'] = vat
        payload['nrodoc'] = ''
        payload['contexto'] = 'ti-it'
        payload['tQuery'] = 'on'
        payload['search1'] = vat
        payload['codigo'] = captcha_val
        payload['tipdoc'] = '1'
        payload['search2'] = ''
        payload['coddpto'] = ''
        payload['codprov'] = ''
        payload['coddist'] = ''
        payload['search3'] = ''
        post = consulta.post("http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias", params=payload)
        if post.status_code != 200:
            raise UserError(_('El servidor de consulta no está en linea, por favor reitentelo más tarde.'))
        texto_error = 'Surgieron problemas al procesar la consulta'
        texto_error_codigo_error = 'El codigo ingresado es incorrecto'
        texto_consulta = post.text

        if texto_error in (texto_consulta) or texto_error_codigo_error in (texto_consulta):
            con_error = True
            raise UserError(_('El servidor de consulta no responde, por favor reintentelo más tarde'))

        texto_consulta = texto_consulta.replace('<br>', '\n')
        texto_consulta = re.sub("(<!--.*?-->)", "", texto_consulta, flags=re.MULTILINE)
        # parser = etree.HTMLParser()
        # tree   = etree.parse(StringIO(texto_consulta), parser)
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(texto_consulta), parser)
        flag_nombre = False
        flag_comercial = False
        flag_tipo_contrib = False
        flag_sistema_emision = False
        flag_sistema_conta = False
        flag_direccion = False
        flag_estado = False
        flag_condicion = False
        flag_padrones = False
        flag_ciu = False

        flag_reg_date = False
        flag_start_date = False
        flag_export = False
        flag_esystem = False
        flag_esystem_from = False
        flag_esystem_receipts = False
        flag_ple_from = False
        #vals['legal_name'] = None
        # Busqueda de datos
        for _td in tree.findall("//div[@id='print']/table//td"):
            if _td.attrib['class'] == 'bgn':
                if re.findall(re.compile('N.mero.de RUC.'), _td.text):
                    flag_nombre = True
                elif re.findall(re.compile('Nombre Comercial.'), _td.text):
                    flag_comercial = True
                elif re.findall(re.compile('Tipo Contribuyente.'), _td.text):
                    flag_tipo_contrib = True
                elif re.findall(re.compile('Sistema de Emisi.n de Comprobante.'), _td.text):
                    flag_sistema_emision = True
                elif re.findall(re.compile('Sistema de Contabilidad.'), _td.text):
                    flag_sistema_conta = True
                elif re.findall(re.compile('Direcci.n.'), _td.text):
                    flag_direccion = True
                elif re.findall(re.compile('Estado.'), _td.text):
                    flag_estado = True
                elif re.findall(re.compile('Condici.n.'), _td.text):
                    flag_condicion = True
                elif re.findall(re.compile('Padrones.'), _td.text):
                    flag_padrones = True
                elif re.findall(re.compile('Actividad.es. Econ.mica.s.'), _td.text):
                    flag_ciu = True
                elif re.findall(re.compile('Fecha de Inscripci.n.'), _td.text):
                    flag_reg_date = True
                elif re.findall(re.compile('Fecha de Inicio.'), _td.text):
                    flag_start_date = True
                elif re.findall(re.compile('Actividad de Comercio Exterior.'), _td.text):
                    flag_export = True
                elif re.findall(re.compile('Sistema de Emision.'), _td.text):
                    flag_esystem = True
                elif re.findall(re.compile('Emisor electr.nico.'), _td.text):
                    flag_esystem_from = True
                elif re.findall(re.compile('Comprobantes Electr.nicos.'), _td.text):
                    flag_esystem_receipts = True
                elif re.findall(re.compile('Afiliado al PLE desde.'), _td.text):
                    flag_ple_from = True
            elif _td.attrib['class'] == 'bg':
                if flag_nombre:
                    flag_nombre = False
                    vals['company_type'] = 'company'
                    # vals['legal_name'] = _td.text.split(' - ')[1]
                    legal_names = _td.text.split('-')
                    var_name = ""
                    for i in range(1, len(legal_names)):
                        var_name += legal_names[i]
                    vals['legal_name'] = var_name.strip()
                    vals['name'] = vals['legal_name']
                if flag_comercial:
                    flag_comercial = False
                    vals['commercial_name'] = _td.text
                elif flag_direccion:
                    flag_direccion = False
                    street = _td.text.strip().split('-')
                    if not street:
                        street = _td.text.strip().split(' ')

                    for i in range(len(street)):
                        street[i] = street[i].strip()
                    if len(street) >= 3:
                        if street[-1]:
                            district = street[-1]
                            if district.find('('):
                                district = district[:district.find("(")].strip()
                            vals['district'] = district
                            vals['zip'] = vals['district']
                        if street[-2]:
                            vals['province'] = street[-2].strip()
                            vals['city'] = vals['province']
                        if len(street[-3].split(' ')) > 1:
                            vals['region'] = street[-3].split(' ')[-1]

                    vals['street'] = " ".join(street)
                elif flag_tipo_contrib:
                    flag_tipo_contrib = False
                    vals['type_taxpayer'] = _td.text
                elif flag_sistema_emision:
                    flag_sistema_emision = False
                    vals['emission_system'] = _td.text
                elif flag_sistema_conta:
                    flag_sistema_conta = False
                    vals['accounting_system'] = _td.text
                elif flag_estado:
                    flag_estado = False
                    vals['state'] = _td.text
                elif flag_condicion:
                    flag_condicion = False
                    vals['condition'] = _td.text.strip()
                elif flag_padrones:
                    flag_padrones = False
                    if re.findall(re.compile('.Agentes de Retenci.n de IGV.'), _td.text):
                        if len(_td.text.split('(')) > 1:
                            string_res = _td.text.split('(')[1]
                            if len(string_res.split(')')) > 1:
                                resol_val = string_res.split(')')[0]
                                vals['retention_agent_resolution'] = resol_val
                                string_date = _td.text.strip()[-10:]
                                vals['retention_agent_from'] = datetime.strptime(string_date, "%d/%m/%Y").strftime(
                                    "%Y-%m-%d")
                                vals['retention_agent'] = True

                elif flag_ciu:
                    flag_ciu = False
                    ciu_ids = []
                    if _td.text:
                        cius = _td.text.strip().split("\n")
                        for ciu in cius:
                            if ciu.strip():
                                ciu_sunat = ciu.strip().split("-")
                                element = {}
                                element['code'] = ciu_sunat[1].strip()
                                element['name'] = ciu_sunat[2].strip()
                                ciu_ids.append(element)
                    vals['activities'] = ciu_ids

                elif flag_reg_date:
                    flag_reg_date = False
                    if _td.text.strip() != "-":
                        vals['registration_date'] = datetime.strptime(_td.text.strip(' '), "%d/%m/%Y").strftime(
                            "%Y-%m-%d")
                elif flag_start_date:
                    flag_start_date = False
                    if _td.text.strip() != "-":
                        vals['started_activity_date'] = datetime.strptime(_td.text.strip(' '), "%d/%m/%Y").strftime(
                            "%Y-%m-%d")
                elif flag_export:
                    flag_export = False
                    vals['foreign_trade_activity'] = _td.text.strip()
                elif flag_esystem:
                    flag_esystem = False
                    vals['electronic_system'] = _td.text.strip()
                elif flag_esystem_from:
                    flag_esystem_from = False
                    if _td.text.strip() != "-":
                        vals['electronic_system_from'] = datetime.strptime(_td.text.strip(' '), "%d/%m/%Y").strftime(
                            "%Y-%m-%d")
                elif flag_esystem_receipts:
                    flag_esystem_receipts = False
                    vals['electronic_system_receipts'] = _td.text.strip()
                elif flag_ple_from:
                    flag_ple_from = False
                    if _td.text.strip() != "-":
                        vals['ple_from'] = datetime.strptime(_td.text.strip(' '), "%d/%m/%Y").strftime("%Y-%m-%d")

        # Busqueda del TELEFONO
        soup = BeautifulSoup(post.text, 'html.parser')
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        flag_temp = 0
        html_coment = ""
        for c in comments:
            if flag_temp == 1:
                html_coment = html_coment + c
            if c.find("PAS20134EA20000207") >= 0:
                flag_temp += 1
            if flag_temp == 1 and c.find("</tr>") >= 0:
                flag_temp += 1
        if flag_temp >= 2:
            newsoup = BeautifulSoup(html_coment, 'html.parser')
            table_td = newsoup.find_all('td')
            vals['phone_sunat'] = table_td[1].get_text().strip()
            vals['fax_sunat'] = table_td[3].get_text().strip()

        if not con_error and vals['legal_name']:
            #Busqueda de representantes
            vals ['representatives']= cls._get_sunat_getRepLeg(vals['legal_name'], vat)

        return vals

    @staticmethod
    def validate_ruc(vat):
        factor = '5432765432'
        sum = 0
        dig_check = False
        if len(vat) != 11:
            return False
        try:
            int(vat)
        except ValueError:
            return False
        for f in range(0, 10):
            sum += int(factor[f]) * int(vat[f])
        subtraction = 11 - (sum % 11)
        if subtraction == 10:
            dig_check = 0
        elif subtraction == 11:
            dig_check = 1
        else:
            dig_check = subtraction
        if not int(vat[10]) == dig_check:
            return False
        return True

    def buscar_mintra(self, nro_documento):
        str_parse = "|"
        reponse = False

        url = 'http://extranet.trabajo.gob.pe/extranet/web/citas/validarDNI'
        req = {'dni': nro_documento}
        try:
            reponse = requests.post(url, req, timeout=300)
        except Exception:
            reponse = False
        if reponse and reponse.status_code == 200 and reponse.text != "-2":
            _logger.info("respuesta %s" % reponse.text)
            str = reponse.text.split(str_parse)
            respuesta = {
                'detail': 'found',
                'paternal_surname': str[1],
                'maternal_surname': str[2],
                'name': str[3],
                'sexo': str[4],
                'company_type': 'person',
                'fecha_nacimiento': str[5][:4] + '/' + str[5][4:6] + '/' + str[5][6:8]
            }
        else:
            respuesta = {'detail': "Not found."}
        return respuesta

    @api.multi
    def buscar_dni(self, nro_dni):
        respuesta = self.buscar_mintra(nro_dni)
        return respuesta

    @api.model
    def _get_pe_doc_type(self):
        res = []
        res.append(('0', 'DOC.TRIB.NO.DOM.SIN.RUC'))
        res.append(('1', 'DOCUMENTO NACIONAL DE IDENTIDAD (DNI)'))
        res.append(('4', 'CARNET DE EXTRANJERIA'))
        res.append(('6', 'REGISTRO ÚNICO DE CONTRIBUYENTES'))
        res.append(('7', 'PASAPORTE'))
        res.append(('A', 'CÉDULA DIPLOMÁTICA DE IDENTIDAD'))
        res.append(('B', 'DOC.IDENT.PAIS.RESIDENCIA-NO.D'))
        res.append(('C', 'Tax Identifi cation Number - TIN – Doc Trib PP.NN'))
        res.append(('D', 'Identifi cation Number - IN – Doc Trib PP. JJ'))
        return res

    doc_type= fields.Selection(selection=_get_pe_doc_type, string="Document Type")
    doc_number= fields.Char("Document Number")
    commercial_name = fields.Char("Commercial Name", default="-", help='If you do not have a commercial name, put "-" without quotes')
    legal_name = fields.Char("Legal Name", default="-", help='If you do not have a legal name, put "-" without quotes')
    
    state = fields.Selection([('ACTIVO', 'ACTIVO'),
                            ('BAJA DE OFICIO', 'BAJA DE OFICIO'),
                            ('BAJA DEFINITIVA', 'BAJA DEFINITIVA'),
                            ('BAJA PROVISIONAL', 'BAJA PROVISIONAL'),
                            ('BAJA PROV. POR OFICIO', 'BAJA PROV. POR OFICIO'),
                            ('SUSPENSION TEMPORAL', 'BAJA PROVISIONAL'),
                            ('INHABILITADO-VENT.UN', 'INHABILITADO-VENT.UN'),
                            ('BAJA MULT.INSCR. Y O', 'BAJA MULT.INSCR. Y O'),
                            ('PENDIENTE DE INI. DE', 'PENDIENTE DE INI. DE'),
                            ('OTROS OBLIGADOS', 'OTROS OBLIGADOS'),
                            ('NUM. INTERNO IDENTIF', 'NUM. INTERNO IDENTIF'),
                            ('ANUL.PROVI.-ACTO ILI', 'ANUL.PROVI.-ACTO ILI'),
                            ('ANULACION - ACTO ILI', 'ANULACION - ACTO ILI'),
                            ('BAJA PROV. POR OFICI', 'BAJA PROV. POR OFICI'),
                            ('ANULACION - ERROR SU', 'ANULACION - ERROR SU')], "State", default="ACTIVO")
    condition = fields.Selection([('HABIDO', 'HABIDO'),
                                ('NO HABIDO', 'NO HABIDO'),
                                ('NO HALLADO', 'NO HALLADO'),
                                ('PENDIENTE', 'PENDIENTE'),
                                ('NO HALLADO SE MUDO D', 'NO HALLADO SE MUDO D'),
                                ('NO HALLADO NO EXISTE', 'NO HALLADO NO EXISTE'),
                                ('NO HALLADO FALLECIO', 'NO HALLADO FALLECIO'),
                                ('-', 'NO HABIDO'),
                                ('NO HALLADO OTROS MOT','NO HALLADO OTROS MOT'),
                                ('NO APLICABLE', 'NO APLICABLE'),
                                ('NO HALLADO NRO.PUERT', 'NO HALLADO NRO.PUERT'),
                                ('NO HALLADO CERRADO', 'NO HALLADO CERRADO'),
                                ('POR VERIFICAR', 'POR VERIFICAR'),
                                ('NO HALLADO DESTINATA', 'NO HALLADO DESTINATA'),
                                ('NO HALLADO RECHAZADO', 'NO HALLADO RECHAZADO')], 'Condition', default="HABIDO")
    
    activities_ids = fields.Many2many("pe.datas", string= "Economic Activities", domain=[('table_code', '=', 'PE.CIIU')])
    main_activity = fields.Many2one("pe.datas", string= "Main Economic Activity", domain=[('table_code', '=', 'PE.CIIU')])
    retention_agent = fields.Boolean("Is Agent")
    retention_agent_from = fields.Date("From")
    retention_agent_resolution = fields.Char("Resolution")
    is_validate= fields.Boolean("Is Validated")
    type_taxpayer = fields.Char("Type Taxpayer")
    emission_system = fields.Char("Emission System")
    accounting_system = fields.Char("Accounting System")
    last_update = fields.Datetime("Last Update")
    representative_ids = fields.One2many("res.partner.representative", "partner_id", "Representatives")
    
    @api.constrains("doc_number")
    def check_doc_number(self):
        for partner in self:
            if not partner.doc_type and not partner.doc_number:
                continue
            elif partner.doc_type=="0":
                continue
            elif not partner.doc_type and partner.doc_number:
                raise ValidationError(_("Select a document type"))
            elif partner.doc_type and not partner.doc_number:
                raise ValidationError(_("Enter the document number"))
            vat = partner.doc_number
            if partner.doc_type == '6':
                check = self.validate_ruc(vat)
                if not check:
                    _logger.info("The RUC Number [%s] is not valid !" % vat)
                    raise ValidationError(_('the RUC entered is incorrect'))
            if self.search_count([('company_id','=', partner.company_id.id),
                                  ('doc_type', '=', partner.doc_type), ('doc_number', '=', partner.doc_number)])>1:
                raise ValidationError(_('Document Number already exists and violates unique field constrain'))

    @api.onchange('company_type')
    def onchange_company_type(self):
        self.doc_type= self.company_type == 'company' and "6" or "1"
        super(Partner, self).onchange_company_type()
        
    @staticmethod
    def validate_ruc(vat):
        factor = '5432765432'
        sum = 0
        dig_check = False
        if len(vat) != 11:
            return False
        try:
            int(vat)
        except ValueError:
            return False 
        for f in range(0,10):
            sum += int(factor[f]) * int(vat[f])
        subtraction = 11 - (sum % 11)
        if subtraction == 10:
            dig_check = 0
        elif subtraction == 11:
            dig_check = 1
        else:
            dig_check = subtraction
        if not int(vat[10]) == dig_check:
            return False
        return True
    
    @api.onchange("doc_number", "doc_type")
    @api.depends("doc_type", "doc_number")
    def _doc_number_change(self):
        vat=self.doc_number
        if vat and self.doc_type:
            vat_type = self.doc_type
            if vat_type == '0':
                self.vat="%s%s"%("PEO", self.doc_number)
            elif vat_type == '1':
                if len(vat) != 8:
                    raise UserError(
                        _('the DNI entered is incorrect'))
                respuesta = self.buscar_dni(self.doc_number.strip())
                if respuesta and respuesta['detail'] != 'Not found.':
                    self.name = "%s %s %s" % ((respuesta['name'] or ''), (respuesta['paternal_surname'] or ''),
                                              (respuesta['maternal_surname'] or ''))
                    self.company_type = "person"
                    self.is_validate = True
                    self.vat = "%s%s" % ("PED", vat)
                else:
                    raise UserError(_('El Numero de DNI ingresado es incorrecto o no existe'))
            elif vat_type == '4':
                self.vat="%s%s"%("PEE", self.doc_number)
            elif vat_type=="6":
                vals = self._get_sunat_details(vat)
                _logger.info("vals: %s" % vals)
                #if response and response.status_code!=200:
                #    vals= self._get_sunat_details(vat)
                #else:
                #vals = response and response.json() or {'detail':"Not found."}
                #    if vals.get('detail', '') == "Not found.":
                #        vals= self._get_sunat_details(vat)
                if vals:
                    self.commercial_name = vals.get('commercial_name')
                    self.legal_name = vals.get('legal_name')
                    self.name = vals.get('legal_name') or vals.get('legal_name')
                    self.street = vals.get('street', False)
                    self.company_type="company"
                    self.state = vals.get('state', False)
                    self.condition = vals.get('condition')
                    self.type_taxpayer = vals.get('type_taxpayer')
                    self.emission_system = vals.get('emission_system')
                    self.accounting_system = vals.get('accounting_system')
                    self.last_update = vals.get('last_update') and fields.Datetime.context_timestamp(self, datetime.strptime(vals.get('last_update'), '%Y-%m-%dT%H:%M:%S.%fZ')) or False
                    self.is_validate = True
                    if vals.get('activities'):
                        activities_ids = []
                        for activity in  vals.get('activities'):
                            ciiu = self.env['pe.datas'].search([('code', '=', activity.get('code')),('table_code', '=', 'PE.CIIU')], limit=1)
                            if ciiu:
                                activities_ids.append(ciiu.id)
                            else:
                                activity['table_code']='PE.CIIU'
                                ciiu = self.env['pe.datas'].sudo().create(activity)
                                activities_ids.append(ciiu.id)
                        if activities_ids:
                            self.main_activity = activities_ids[-1]
                            if self.activities_ids:
                                self.activities_ids = [(6, None, activities_ids)]
                            else:
                                act=[]
                                for activity_id in activities_ids:
                                    act.append((4,activity_id))
                                self.activities_ids = act
                    if vals.get('representatives'):
                        representatives=[]
                        contacts = []
                        for rep in vals.get('representatives'):
                            representative = {}
                            representative['name'] =  rep.get('Nombre')
                            representative['position'] = rep.get('Cargo')
                            representative['doc_number'] = rep.get('Nro. Documento')
                            representative['doc_type'] = rep.get('Documento')
                            if rep.get('Fecha Desde'):
                                try:
                                    fecha = rep.get('Fecha Desde').split('/')
                                    representative['date_from'] = date(int(fecha[2]), int(fecha[1]), int(fecha[0]))
                                except:
                                    pass
                            representatives.append((0, None,representative))
                            if rep.get('Cargo'): #in ["GERENTE GENERAL", "TITULAR-GERENTE", "GERENTE"]:
                                contact={}
                                list_doc = {}
                                list_doc['DNI'] = '1'
                                list_doc['RUC'] = '6'
                                list_doc['C. EXT.'] = '4'
                                contact['name']= rep.get('Nombre')
                                if self.search_count([('name', '=', contact['name']), ('parent_id', '=', self.id)])==0:
                                    try:
                                        contact['function'] = rep.get('Cargo')
                                        contact['type']='contact'
                                        contact['doc_number'] = rep.get('Nro. Documento')
                                        contact['function'] = rep.get('Cargo')

                                        if rep.get('Documento'):
                                            contact['doc_type'] = list_doc[rep.get('Documento')]
                                        contact['parent_id']=self.id
                                        contacts.append((0, None, contact))
                                    except:
                                        _logger.error("error ")
                                        pass
                        if self.representative_ids:
                            self.representative_ids.unlink()
                        self.representative_ids = representatives
                        self.child_ids = contacts
                    self.retention_agent = vals.get('retention_agent', False)
                    self.retention_agent_from = vals.get('retention_agent_from', False)
                    self.retention_agent_resolution = vals.get('retention_agent_resolution', False)
                    if vals.get('district') and vals.get('province'):
                        district = self.env['res.country.district'].search([('name','ilike', vals.get('district')),
                                                                               ('province_id.name','ilike', vals.get('province'))])
                        if len(district)==1:
                            self.district_id=district.id
                        elif len(district)==0:
                            province = self.env['res.country.province'].search([('name','ilike', vals.get('province'))])
                            if len(province)==1:
                                self.province_id=province.id
                        else:
                            province = self.env['res.country.province'].search([('name','ilike', vals.get('province'))])
                            if len(province)==1:
                                self.province_id=province.id

                self.vat= "PER%s"% vat
            elif vat_type == '7':
                prefix="CC"
                if self.country_id:
                    prefix=self.country_id.code
                self.vat="%s%s"%(prefix, self.doc_number)
            elif vat_type == 'A':
                self.vat="%s%s"%("PEA", self.doc_number)
            elif vat_type == 'B':
                self.vat="%s%s"%("PEB", self.doc_number)
            elif vat_type == 'C':
                self.vat="%s%s"%("PEC", self.doc_number)
            elif vat_type == 'D':
                self.vat="%s%s"%("PEI", self.doc_number)
        self._vat_change()

    @api.onchange('vat')
    def _vat_change(self):
        if self.vat:
            prefix=len(self.vat)>=2 and self.vat[0:2] or False
            vat =len(self.vat)>=2 and self.vat[2:] or ""
            if prefix:
                if not self.country_id:
                    country_id=self.env['res.country'].search([("code","=", prefix.upper())], limit=1)
                    self.country_id=country_id.id
            if prefix and prefix.upper()== "PE": 
                doc_type = len(vat)>0 and vat[0:1] or False
                doc_number = len(vat)>0 and vat[1:] or False
                if doc_type and doc_type.upper()=="O":
                    self.doc_type="0"
                elif doc_type and doc_type.upper()=="D":
                    if len(doc_number)!=8:
                            raise UserError(_('El número de DNI ingresado es incorrecto'))
                    self.doc_type="1"
                elif doc_type and doc_type.upper()=="E":
                    self.doc_type="4"
                elif doc_type and doc_type.upper()=="R":
                    if not self.validate_ruc(doc_number):
                            raise UserError(_('El número de DNI ingresado es incorrecto'))
                    self.doc_type="6"
                elif doc_type and doc_type.upper()=="A":
                    self.doc_type="A"
                if self.doc_number != doc_number:    
                    self.doc_number= doc_number
            else:
                self.doc_type="7"
                if self.doc_number != vat:
                    self.doc_number = vat
        

    def check_vat_pe(self, vat):
        vat_type, doc = vat and len(vat) >= 2 and (vat[0], vat[1:]) or (False, False)
        if vat_type.upper() in ['A', 'O', 'E', 'B', 'C', 'D', 'I']:
            return True
        return super(Partner, self).check_vat_pe(vat)    

    @api.multi
    def change_commercial_name(self):
        partner_ids=self.search([('commercial_name', '!=', '-'), ('doc_type', '=', '6')])
        for partner_id in partner_ids:
            partner_id.update_document()

    @api.one
    def update_document(self):
        self._doc_number_change()


    @api.model
    def update_partner_datas(self):
        partner_ids = self.search([('doc_type', '=', '6')])
        for partner in partner_ids:
            partner.name = partner.commercial_name

class PartnerRepresentative(models.Model):
    _description = "Partner Representative"
    _name = "res.partner.representative"

    name = fields.Char("Name")
    doc_type = fields.Char("Document Type")
    doc_number = fields.Char("Document Number")
    position = fields.Char("Position")
    date_from = fields.Date("Date From")
    partner_id = fields.Many2one("res.partner", "Partner")
    
