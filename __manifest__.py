# -*- coding: utf-8 -*-
{
    'name': "Smart Medical",
    'summary': """Smart Medical""",
    'description': """Medical """,
    'author': "Black Belts Egypt",
    'website': "www.blackbelts-egypt.com",
    'category': 'Medical',
    'version': '0.1',
    'license': 'AGPL-3',
    # any module necessary for this one to work correctly
    'depends': ['base','helpdesk_inherit','arope-conf'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/medical_helpdesk.xml',
        'views/setup.xml',
        'views/covers.xml',

        'views/menu_item.xml',


    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
