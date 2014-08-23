import re

import publish.plugin


class ValidateNamingConvention(publish.plugin.Validator):
    """Ensure each included node ends with a three-letter, upper-case type

    Example:
        clavicle_CTL <- Good
        shoulder <- Bad

    Raises:
        ValueError with an added .nodes attribute for each node
            found to be misnamed.

    """

    families = ['model', 'animation', 'animRig']
    hosts = ['maya']
    version = (0, 1, 0)

    pattern = re.compile("^\w+_\w{3}(Shape)?$")

    def process(self, context):
        """Allow nodes of appropriate names through

        Example:
            >>> # These are fine
            >>> inst = publish.plugin.Instance('doctest')
            >>> inst.add('clavicle_CTL')
            >>> inst.add('Peter_AST')
            >>> inst.add('Body_PLYShape')

            >>> ctx = publish.plugin.Context()
            >>> ctx.add(inst)

            >>> validator = ValidateNamingConvention()
            >>> value, exc = next(validator.process(ctx))
            >>> assert exc is None

            >>> # But these are invalid
            >>> inst.add('misnamed')
            >>> inst.add('missing_suffix')

            >>> value, exc = next(validator.process(ctx))
            >>> assert isinstance(exc, ValueError)

        """

        for instance in context:
            mismatches = list()
            for node in instance:
                if not self.pattern.match(node):
                    mismatches.append(node)

            if mismatches:
                msg = "The following nodes were misnamed\n"
                for node in mismatches:
                    msg += "\t{0}\n".format(node)

                exc = ValueError(msg)
                exc.nodes = mismatches

                yield instance, exc

            yield instance, None


if __name__ == '__main__':
    import doctest
    doctest.testmod()
