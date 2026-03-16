import logging
import sys
import structlog

def _setup_logging():
    def abbreviate_level(logger, method_name, event_dict):
        lvl = event_dict.get("level")
        if not lvl:
            return event_dict

        # structlog.stdlib.add_log_level produces lowercase strings like "info", "error", "warn"
        mapping = {
            "critical":  " crit",
            "exception": "excep",
            "error":     "error",
            "warning":   " warn",
            "info":      " info",
            "debug":     "debug",
            "notset":    " none",
        }
        event_dict["level"] = mapping.get(lvl)
        return event_dict

    level_styles={
        # keep built‑in coloring behavior, only override the displayed text
        " crit":      structlog.dev.RED + structlog.dev.BRIGHT,
        "excep":      structlog.dev.RED + structlog.dev.BRIGHT,
        "error":      structlog.dev.RED + structlog.dev.BRIGHT,
        " warn":   structlog.dev.YELLOW + structlog.dev.BRIGHT,
        " info":    structlog.dev.GREEN + structlog.dev.BRIGHT,
        "debug":      structlog.dev.DIM,
        " none": structlog.dev.RED_BACK,
    }

    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=logging.INFO)
    # logging.basicConfig(stream=sys.stdout, format="%(message)s", level=logging.DEBUG)
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            # structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            abbreviate_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(colors=True, level_styles=level_styles, pad_level=False),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )