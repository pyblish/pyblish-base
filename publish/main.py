from __future__ import absolute_import

# Standard library
import logging

# Local library
import publish.plugin
import publish.config
import publish.domain

log = logging.getLogger('publish')


def publish_all():
    """Convenience function of the above"""

    # parse context
    context = publish.domain.select()

    if not context:
        log.info("No instances found")
        return

    # Validate
    publish.domain.process('validators', context)

    if context.has_errors:
        log.error("There were ({n}) errors "
                  "during validation:".format(n=len(context.errors)))

        for error in context.errors:
            log.error("({n}): {error}".format(
                n=context.errors.index(error) + 1,
                error=error))
        return

    # Extract
    publish.domain.process('extractors', context)

    if context.has_errors:
        log.error("There were ({n}) errors "
                  "during extraction:".format(n=len(context.errors)))

        for error in context.errors:
            log.error("({n}): {error}".format(
                n=context.errors.index(error) + 1,
                error=error))


def validate_all():
    """Convenience function for selecting and validating"""
    # parse context
    context = publish.domain.select()

    if not context:
        log.info("No instances found")
        return

    # Validate
    publish.domain.process('validators', context)

    if context.has_errors:
        log.error("There were ({n}) errors "
                  "during validation:".format(n=len(context.errors)))

        for error in context.errors:
            log.error("({n}): {error}".format(
                n=context.errors.index(error) + 1,
                error=error))
        return

    log.info("Passed")
