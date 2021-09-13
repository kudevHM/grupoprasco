from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    job_responsible_ids = fields.Many2many(
        string="Job costing",
        comodel_name="job.costing",
        relation="responsible_job_res_partner_rel",
        column1="res_ursers_id",
        column2="job_costing_id",
        copy=False
    )