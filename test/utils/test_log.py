from jupyterMagicCommands.utils.log import getLogger


class TestGetLogger:

    def test_same_name_returns_same_logger(self):
        logger1 = getLogger("test.duplicate")
        logger2 = getLogger("test.duplicate")
        assert logger1 is logger2

    def test_no_duplicate_handlers(self):
        getLogger("test.nodup")
        logger = getLogger("test.nodup")
        assert len(logger.handlers) == 1

    def test_has_stream_handler(self):
        import logging
        logger = getLogger("test.hashandler")
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
