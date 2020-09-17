from odoo import models, tools, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime


class Notes(models.Model):
    _name = 'medical.notes'
    _rec_name = 'note'

    note = fields.Text('Note')
    ar_note = fields.Text('Arabic Note')
    package = fields.Selection([('individual', 'Individual'),
                                ('sme', 'SME'), ('all', 'All')],
                               'Note For',
                               default='individual')
    sort = fields.Integer('Sort')


class MedicalPriceTable(models.Model):
    _name = 'medical.price'
    _description = 'Set up Price tables'
    _rec_name = 'product_name'
    package = fields.Selection([('individual', 'Individual'),
                             ('sme', 'SME'),],
                            'Package For',
                            default='individual')

    product_name = fields.Char(string='Product Name')
    sort = fields.Integer('Sort')


    price_lines = fields.One2many('medical.price.line','price_id',string='Prices')
    cover_lines = fields.One2many('medical.cover','cover_id',string='Covers')
    # internal_lines = fields.One2many('medical.internal.hospital.treatment', 'internal_id', string='Internal Hospital Treatment')
    # outpatient_lines = fields.One2many('medical.outpatient.services', 'outpatient_id', string='Outpatient Services')

    # @api.multi
    def price(self):
        self.env['medical.api'].get_price({'type':'individual','dob':['1999-5-4'], 'lang':'en'})

class MedicalPriceTableLines(models.Model):
    _name = 'medical.price.line'

    from_age = fields.Float('From Age')
    to_age = fields.Float('To Age')
    price = fields.Float('Price')
    price_id = fields.Many2one('medical.price', ondelete='cascade')

class MedicalCoversType(models.Model):
    _name = 'medical.covers.type'
    _rec_name = 'type'

    type = fields.Char('Type')
    ar_type = fields.Char('Arabic Type')

class MedicalCovers(models.Model):
      _name = 'medical.cover'

      benefit = fields.Text(string='Benefit')
      value = fields.Text(string='Value')
      en_benefit = fields.Text(string='English Benefit')
      en_value = fields.Text(string='English Value')
      type = fields.Many2one('medical.covers.type', 'Type')
      sort = fields.Integer('Sort')
      cover_id = fields.Many2one('medical.price', ondelete='cascade')

#
# class InternalHospitalTreatment(models.Model):
#     _name = 'medical.internal.hospital.treatment'
#
#     benefit = fields.Text(string='Benefit')
#     value = fields.Text(string='Value')
#     en_benefit = fields.Text(string='English Benefit')
#     en_value = fields.Text(string='English Value')
#     sort = fields.Integer('Sort')
#     internal_id = fields.Many2one('medical.price', ondelete='cascade')
#
# class OutpatientServices(models.Model):
#     _name = 'medical.outpatient.services'
#
#     benefit = fields.Text(string='Benefit')
#     value = fields.Text(string='Value')
#     en_benefit = fields.Text(string='English Benefit')
#     en_value = fields.Text(string='English Value')
#     sort = fields.Integer('Sort')
#     outpatient_id = fields.Many2one('medical.price', ondelete='cascade')


class MedicalApi(models.Model):
    _name = 'medical.api'

    def calculate_age(self, DOB):
        ages = []
        for rec in DOB:
            today = datetime.today().date()
            DOB = datetime.strptime(rec, '%Y-%m-%d').date()+timedelta(days=15)
            difference = relativedelta(today, DOB)
            age = difference.years
            months = difference.months
            days = difference.days
            if months or days != 0:
                age += 1
            ages.append(age)
        return ages

    def calc_age(self,data):
        ages = []
        for rec in data.get('DOB'):
            today = datetime.strptime(data.get('issue'), '%Y-%m-%d').date()
            DOB = datetime.strptime(rec, '%Y-%m-%d').date()
            difference = relativedelta(today, DOB)
            age = difference.years
            months = difference.months
            days = difference.days
            if months or days != 0:
                age += 1
            ages.append(age)
        return ages

    def calculate_price(self,data):
        dprice = {}
        if data.get('type') == 'individual':
            # ndata = {'DOB': data.get('dob'),'issue': data.get('issue')}
            age = self.calculate_age(data.get('dob'))
            for record in self.env['medical.price'].search([('package', '=', data.get('type'))]):
                for rec in record.price_lines:
                    if rec.from_age <= age[0] and rec.to_age >= age[0]:
                        dprice.update({'cover': 'price', record.product_name: 'EGP ' + str(rec.price)})
            return dprice
        elif data.get('type') == 'family':
            # ndata = {'DOB': data.get('dob'), 'issue': data.get('issue')}
            for record in self.env['medical.price'].search([('package', '=', 'individual')]):
                price = 0.0
                for age in self.calculate_age(data.get('dob')):
                    for rec in record.price_lines:
                        if rec.from_age <= age and rec.to_age >= age:
                            price += rec.price
                            dprice.update({'cover': 'price', record.product_name: 'EGP ' + str(price)})
            return dprice
        else:
            for record in self.env['medical.price'].search([('package', '=', 'sme')]):
                price = 0.0
                for age in data.get('dob'):
                    for rec in record.price_lines:
                        if rec.from_age <= age['age'] and rec.to_age >= age['age']:
                            price += rec.price * age['num']
                            dprice.update({'cover': 'price', record.product_name: 'EGP ' + str(price)})
            return dprice

    @api.model
    def get_products(self, data):
        products = []
        if data.get('type') == 'individual' or data.get('type') == 'family':
            for record in self.env['medical.price'].search([('package', '=', 'individual')]):
                products.append(record.product_name)
            print(products)
            return products
        else:
            for record in self.env['medical.price'].search([('package', '=', data.get('type'))]):
                products.append(record.product_name)
            print(products)
            return products

    @api.model
    def get_price(self, data):
        main = []
        result = []
        res=[]
        dprice = self.calculate_price(data)
        main.append(dprice)
        products = []
        if data.get('type') == 'individual' or data.get('type') == 'family':
            package = 'individual'
        else:
            package = 'sme'
        for type in self.env['medical.covers.type'].search([]):
            maindic = {}
            for cover in self.env['medical.cover'].search([('cover_id.package','=',package),('type', '=', type.id)],order='sort asc'):
                # print(cover.benefit_key)

                res = []
                if data.get('lang') == 'ar':
                    for rec in self.env['medical.price'].search([('package', '=', package)],order='sort asc'):
                        products.append(rec.product_name)
                        # print(rec.product_name)

                        for covers in rec.cover_lines:
                                if covers.benefit == cover.benefit:
                                    val = covers.value
                                    res.append({rec.product_name: val})
                    if cover.benefit not in maindic.keys():
                        maindic[cover.benefit] = res

                elif data.get('lang') == 'en':
                    for rec in self.env['medical.price'].search([('package', '=', package)],order='sort asc'):
                        products.append(rec.product_name)
                        print(rec.product_name)

                        for covers in rec.cover_lines:
                                if covers.en_benefit == cover.en_benefit:
                                    val = covers.en_value
                                    res.append({rec.product_name: val})
                    if cover.en_benefit not in maindic.keys() and cover.en_benefit != False:
                        maindic[cover.en_benefit] = res
            d={}
            for key, val in maindic.items():
                for rec in val:
                    for k,v in rec.items():
                        d['cover']=key
                        d[k]=v
                main.append(d)
                d={}

            if data.get('lang') == 'ar':
                result.append({'name': type.ar_type, 'plans': main})
            elif data.get('lang') == 'en':
                result.append({'name': type.type, 'plans': main})
            main = []
        for rec in result:
            if len(rec['plans']) == 0:
                result.remove(rec)
        columns = list(dict.fromkeys(products))

        print(result)
        return {'data': result, 'column': columns}

    @api.model
    def create_medical_ticket(self, data):
        if data.get('type') == 'individual':
            name = 'Individual Medical Ticket'
        elif data.get('type') == 'family':
            name = 'Family Medical Ticket'
        elif data.get('type') == 'medicalCorporate':
            name = 'Corporate Medical Ticket'
        else:
            name = 'SMEs Medical Ticket'
        type = 'medical'
        ids = self.env['medical.price'].search([('product_name', '=', data.get('product'))])
        ticket = self.env['quoate'].create(
            {'name': name, 'contact_name': data.get('name'), 'phone': data.get('phone'),
             'email_from': data.get('mail'), 'medical_product': ids.id, 'ticket_type': type})
        return ticket.id

    @api.model
    def get_notes(self,data):
        result = []
        if data.get('type') == 'individual' or data.get('type') == 'family':
            package = ['individual', 'all']
        else:
            package = ['sme', 'all']
        for rec in self.env['medical.notes'].search([('package', 'in', package)],order='sort asc'):
            if data.get('lang') == 'ar':
                result.append(rec.ar_note)
            else:
                result.append(rec.note)
        result = list(dict.fromkeys(result))
        return result
        # for cover in self.env['medical.internal.hospital.treatment'].search([('internal_id.package','=',package)],order='sort asc'):
        #     print(cover.benefit)
        #     res = []
        #     if data.get('lang') == 'ar':
        #         for rec in self.env['medical.price'].search([('package', '=', package)]):
        #             print(rec.product_name)
        #             for covers in rec.internal_lines:
        #                 if covers.benefit == cover.benefit:
        #                     val = covers.value
        #                     res.append({rec.product_name: val})
        #         if cover.benefit not in internaldic.keys():
        #             internaldic[cover.benefit] = res
        #     elif data.get('lang') == 'en':
        #         for rec in self.env['medical.price'].search([('package', '=', package)]):
        #             print(rec.product_name)
        #             for covers in rec.internal_lines:
        #                 if covers.en_benefit == cover.en_benefit:
        #                     val = covers.en_value
        #                     res.append({rec.product_name: val})
        #         if cover.en_benefit not in internaldic.keys() and cover.en_benefit != False:
        #             internaldic[cover.en_benefit] = res
        # print(internaldic)
        # d={}
        # for key, val in internaldic.items():
        #     for rec in val:
        #         for k,v in rec.items():
        #             d['cover']=key
        #             d[k]=v
        #     internal.append(d)
        #     d={}
        #
        # for cover in self.env['medical.outpatient.services'].search([('outpatient_id.package','=',package)],order='sort asc'):
        #     print(cover.benefit)
        #     res = []
        #     if data.get('lang') == 'ar':
        #         for rec in self.env['medical.price'].search([('package', '=', package)]):
        #             print(rec.product_name)
        #             for covers in rec.outpatient_lines:
        #                 if covers.benefit == cover.benefit:
        #                     val = covers.value
        #                     res.append({rec.product_name: val})
        #         if cover.benefit not in outpatientdic.keys():
        #             outpatientdic[cover.benefit] = res
        #     elif data.get('lang') == 'en':
        #         for rec in self.env['medical.price'].search([('package', '=', package)]):
        #             print(rec.product_name)
        #             for covers in rec.outpatient_lines:
        #                 if covers.en_benefit == cover.en_benefit:
        #                     val = covers.en_value
        #                     res.append({rec.product_name: val})
        #         if cover.en_benefit not in outpatientdic.keys() and cover.en_benefit != False:
        #             outpatientdic[cover.en_benefit] = res
        # print(outpatientdic)
        # d={}
        # for key, val in outpatientdic.items():
        #     for rec in val:
        #         for k,v in rec.items():
        #             d['cover']=key
        #             d[k]=v
        #     outpatient.append(d)
        #     d={}
        # if data.get('lang') == 'ar':
        #     result.append({'name': 'main', 'plans': main})
        #     result.append({'name': 'العلاج الداخلي بالمستشفيـات', 'plans': internal})
        #     result.append({'name': ' خدمات العيادات الخارجية', 'plans': outpatient})
        #     print(result)
        #     return result
        # else:
        #     result.append({'name': 'main', 'plans': main})
        #     result.append({'name': 'Internal Hospital Treatment', 'plans': internal})
        #     result.append({'name': ' Outpatient Services', 'plans': outpatient})
        #     print(result)
        #     return result
class aropeHelpDesk(models.Model):
    _inherit = 'quoate'
    medical_product = fields.Many2one('medical.price', string="Medical Product", ondelete='cascade')








            # for product in self.env['medical.price'].search([('package', '=', data.get('type'))]):
            #     benefit = []
            #     internals = []
            #     outpatients = []
            #     price = product.price_lines.search([('from_age','>=',age[0]),('to_age','<=',age[0])]).price
            #     for cover in product.cover_lines:
            #         benefit.append({'cover': cover.benefit, product.product_name: cover.value, })
            #     for record in product.internal_lines:
            #         internals.append({'cover': record.benefit, 'value': record.value})
            #     for rec in product.outpatient_lines:
            #         outpatients.append({'cover': rec.benefit, 'value': rec.value})
            #
            #     result.append({'name': product.product_name, 'price': price, 'plan':[{'main':benefit,'Internal Hospital Treatment': internals, 'Outpatient Services': outpatients}]})
            #     res = sorted(result, key=lambda i: i['price'], reverse=True)
            # return res
