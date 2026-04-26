import logging

from application.webhook_fetch import handle_webhook


logger = logging.getLogger(__name__)


def process_webhook(payload):
    try:
        result, error = handle_webhook(payload)

        if error:
            logger.warning(
                "PRClosure webhook background processing completed with error: %s",
                error,
            )
            return

        logger.info(
            "PRClosure webhook background processing completed successfully"
        )

        return result

    except Exception:
        logger.exception(
            "PRClosure webhook background processing failed"
        )
        return None
