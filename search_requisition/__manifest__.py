#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Search Requisition",
    'version': '12.0.1.0.0',
    'description': "Search in one2many field",
    'summary': 'This module helps to search records easily in one2many field.',
    'category': 'Web',
    'license': "AGPL-3",
    'depends': ['web','custom_requisitions'],
    'data': [
        'views/assets.xml',
    ],
    'installable': True,
}
