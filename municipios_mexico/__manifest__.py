# -*- coding: utf-8 -*-
{
    'name': "Municipios México",

    'summary': "",

    'description': "Módulo que agrega los municipios de Mexico al momento de crear clientes y/o proveedores",

    'author': "Luis Enrique Alva Villena",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': '',
    'version': '2.0.0',

    # any module necessary for this one to work correctly
    'depends': ['l10n_pe_toponyms'],

    # always loaded
    'data': [
        'data/provincias.xml',
        #'data/distritos.xml',
        'views/partner.xml'
        ],
    # only loaded in demonstration mode
    'demo': [],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    'auto_install': False,
    'application': True,
    'installable': True,
}
