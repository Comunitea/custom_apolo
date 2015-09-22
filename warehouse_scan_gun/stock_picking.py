
    'stock.task'
    @api.one
    def finish_partial_task(self):
        if self.type != 'picking':
            pick_objs = list(set([x.picking_id for x in self.operation_ids]))
            for pick in pick_objs:
                pick.approve_pack_operations2(self.id)
        else:
            for picking in self.wave_id.picking_ids:
                if picking.state not in ['done', 'draft', 'cancel']:
                    picking.approve_pack_operations()
            self.wave_id.done()

        duration = datetime.now() - \
            datetime.strptime(self.date_start, DEFAULT_SERVER_DATETIME_FORMAT)
        vals = {
            'date_end': time.strftime("%Y-%m-%d %H:%M:%S"),
            'duration': duration.seconds / float(60),
            'state': 'done'}
        return self.write(vals)



    'stock.task'
    @api.cr_uid_ids_context
    def approve_pack_operations(self, cr, uid, ids, context=None):
        """
        Aprove the pack operations, put the pick in done.
        Also calculate the operations for the next picking.
        In this moment we calculate the final location of each operation
        """
        if context is None:
            context = {}
        for pick in self.browse(cr, uid, ids, context=context):
            for op in pick.pack_operation_ids:
                op.write({
                    'qty_done': op.product_qty,
                    'processed': 'true'})
        self.do_transfer(cr, uid, ids, context=context)
        return True