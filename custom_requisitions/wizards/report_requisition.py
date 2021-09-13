from odoo import models, fields, api

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
class RequisitionReportWizard(models.TransientModel):

    _name = 'requisition.report.wizard'
    _description = 'requisition report wizard'

    date_start = fields.Date(string="Start Date", required=True, default=fields.Date.today)
    date_end = fields.Date(string="End Date", required=True, default=fields.Date.today)
    job_id = fields.Many2one(
        'job.costing',
        string='Proyecto',
        )


    def get_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
                'job_id': self.job_id.id,

            },
        }

        return self.env.ref('custom_requisitions.requisition_report').report_action(self, data=data)


class RequisitionReport(models.AbstractModel):
    _name = 'report.custom_requisitions.report_template_requisition'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)

        active_job_id = data['form']['job_id']


        docs = []
        # PROJECT MODEL DATA 
        job_id = self.env['job.costing'].browse(active_job_id)

        # REQUISITION LINE MODEL DATA 
        requisition = self.env['requisition.purchase.wizard'].search([
                ('job_id','=',job_id.id),
                # ('pr_active','=','True'),
                ('create_date', '>=', date_start_obj.strftime(DATETIME_FORMAT)),
                ('create_date', '<=', date_end_obj.strftime(DATETIME_FORMAT))], order='name asc')

        purchase = self.env['purchase.order'].search([
                ('project_id','=',job_id.id),
                ('date_order', '>=', date_start_obj.strftime(DATETIME_FORMAT)),
                ('date_order', '<=', date_end_obj.strftime(DATETIME_FORMAT))], order='name asc')

        # req_model = self.env['req.model'].search([
        #         ('p_order2','=',job_id.id)
        #         ('invoice_date', '>=', date_start_obj.strftime(DATETIME_FORMAT)),
        #         ('invoice_date', '<=', date_end_obj.strftime(DATETIME_FORMAT))], order='name asc')        

        
        # for invoice in account_move_ids:
        #     amount_by_group= ""
        #     for line in invoice.amount_by_group:
        #         amount_by_group = line[0] and line[3]
        #     docs.append({
        #         'invoice_date': invoice.invoice_date,
        #         'name': invoice.name,
        #         'invoice_user_id': invoice.invoice_user_id.name,
        #         'amount_untaxed':invoice.amount_untaxed,
        #         'amount_by_group':amount_by_group,
        #         'amount_total':invoice.amount_total,
        #         'currency_id':invoice.currency_id.symbol
        #     })

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'docs': job_id,
            'requisition':requisition,
            'purchase':purchase
        }