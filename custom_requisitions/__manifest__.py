# -*- coding: utf-8 -*-
{
    'name': "Custom Requisitions",

    'summary': "",

    'description': "",

    'author': "Digilab Soluciones",
    'contributors': [
        'Omar Barron<omar.barron@digilab.pe>',
        'Luis Alva<luis.alva@digilab.pe>'
    ],
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': '',
    'version': '4.0.1',

    # any module necessary for this one to work correctly
    'depends': ['odoo_job_costing_management','hr_expense', 'material_purchase_requisitions'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/wizard.xml',
        'views/budget_wizard.xml',
        'data/categorias.xml',
        'data/productos.xml',
        'views/menu_items.xml',
      #  "views/product_views.xml",
        "views/requisition_view.xml",
        "wizards/devolver.xml",
        "report/report.xml",
        "views/purchase_order.xml",

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
