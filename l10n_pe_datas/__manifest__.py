# -*- coding: utf-8 -*-
{
    'name': "Peruvian Datas Management",

    'summary': """
        Peruvian Datas Management
        """,

    'description': """
        Peruvian Datas Management
        Para configurar IBCPE https://www.youtube.com/watch?v=GbabOa_tlPw&t=7s
    """,

    'author': "techruna",
    'website': "http://www.techruna.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    # configurar IBCPE https://www.youtube.com/watch?v=GbabOa_tlPw&t=7s
    'category': 'Localization/Peruvian',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'account',
    ],

    # always loaded
    'data': [
        'data/pe.datas.csv',
        'security/pe_datas_security.xml',
        'security/ir.model.access.csv',
        'views/pe_datas_view.xml',
        'data/pe_datas.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}