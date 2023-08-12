from jupyterMagicCommands.outputters.interactive_outputter import InteractiveOutputter


import asyncio


class AsyncInteractiveOutputter(InteractiveOutputter):

    @staticmethod
    def wait_for_change(widget, value):
        future = asyncio.Future()
        def getvalue(change):
            # make the new value available
            future.set_result(change.new)
            widget.unobserve(getvalue, value)
        widget.observe(getvalue, value)
        return future

    async def on_read(self):
        while True:
            x = await self.wait_for_change(self.text, 'value')
            self.read_cb(x)