import re

import publish.abstract


class ValidateNamingConvention(publish.abstract.Validator):
    """Ensure each included node ends with a three-letter, upper-case type

    Example:
        clavicle_CTL <- Good
        shoulder <- Bad

    Raises:
        ValueError with an added .nodes attribute for each node
            found to be misnamed.

    """

    @property
    def families(self):
        return ['model', 'animation', 'animRig']

    @property
    def hosts(self):
        return ['maya']

    @property
    def version(self):
        return (0, 1, 0)

    pattern = re.compile("^\w+_\w{3}(Shape)?$")

    def process(self):
        """Allow nodes of appropriate names through

        Example:
            >>> # These are fine
            >>> instance = {'clavicle_CTL',
            ...             'Peter_AST',
            ...             'body_GEO'}
            >>> validator = ValidateNamingConvention(instance)
            >>> assert validator.process() == None

            >>> # But these are invalid
            >>> instance = {'misnamed',
            ...             'missing_suffix',
            ...             '_GEO_wrong'}
            >>> validator = ValidateNamingConvention(instance)
            >>> try:
            ...     validator.process()
            ... except ValueError as e:
            ...     assert len(e.nodes) == 3

        """

        mismatches = list()
        for node in self.instance:
            print "node %r" % node
            if not self.pattern.match(node):
                mismatches.append(node)

        if mismatches:
            msg = "The following nodes were misnamed\n"
            for node in mismatches:
                msg += "\t{0}\n".format(node)

            exc = ValueError(msg)
            exc.nodes = mismatches
            raise exc

    def fix(self):
        pass


if __name__ == '__main__':
    import doctest
    doctest.testmod()
