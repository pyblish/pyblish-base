"""An asynchronous, stateful scripting engine to Pyblish

This engine is designed for graphical user interfaces
who need access to data with more diagnostic ability and
up-front information.

Dependencies:

        _____________
       |             |
       |  engine.py  |
       |_____________|
              |
              |
              | uses
              |
     ________ v_________
    |                   |
    |      api.py       |
    |___________________|
              |
              |
              |
              |
   ___________v____________
  |                        |
  |     implementation     |
  |________________________|


Usage:
    >>> count = {"#": 0}
    >>> def on_reset():
    ...   count["#"] += 1
    ...
    >>> engine = create_default()
    >>> engine.was_reset.connect(on_reset)
    >>> engine.reset()
    >>> count["#"]
    1

"""

import sys
import traceback

from . import api, logic, plugin, lib


class TemplateSignal(object):
    """Placeholder signal

    This signal is used as an indicator of where to install signals.
    The instantiator of AbstractEngine later replaces these with
    supplied signals, either DefaultSignal or QtCore.Signal.

    """

    def __init__(self, *args):
        self.args = args
        
    def connect(self, *args):
        pass
    
    def emit(self, *args):
        pass


class AbstractEngine(object):
    """Asynchronous, stateful scripting engine"""

    # Emitted when the GUI is about to start processing;
    # e.g. resetting, validating or publishing.
    about_to_process = TemplateSignal(object, object)

    # Optional outlet for observers
    warned = TemplateSignal(str)
    logged = TemplateSignal(str)

    # Emitted for each process
    was_processed = TemplateSignal(dict)

    was_discovered = TemplateSignal()
    was_reset = TemplateSignal()
    was_collected = TemplateSignal()
    was_validated = TemplateSignal()
    was_extracted = TemplateSignal()
    was_integrated = TemplateSignal()
    was_published = TemplateSignal()
    was_acted = TemplateSignal()

    # Emitted when processing has finished
    finished = TemplateSignal()

    @property
    def context(self):
        return self._context

    @property
    def plugins(self):
        return self._plugins

    def __init__(self):
        super(AbstractEngine, self).__init__()

        self.asynchronous = True
        self.is_running = False

        self._context = api.Context()
        self._plugins = list()

        # Transient state used during publishing.
        self.pair_generator = None        # Active producer of pairs
        self.current_pair = (None, None)  # Active pair
        self.current_error = None

        # This is used to track whether or not to continue
        # processing when, for example, validation has failed.
        self.processing = {
            "nextOrder": None,
            "ordersWithError": set()
        }

        # Signals
        #
        #     /     \
        #    ( ( o ) )
        #     \  |  /
        #        |
        #       / \
        #      /   \
        #     /     \
        #    /       \
        #
        # Install class attributes as instance attributes
        for attr in dir(self):
            signal = getattr(self, attr)
            if isinstance(signal, DefaultSignal):
                setattr(self, attr, DefaultSignal(*signal._args))

    def defer(self, delay, func):
        """Virtual

        This method is overridden by factory function :func:`engine`

        """

    def stop(self):
        self.is_running = False

    def reset(self):
        """Discover plug-ins and run collection"""
        self._context = api.Context()
        self._plugins[:] = api.discover()

        self.was_discovered.emit()

        self.pair_generator = None
        self.current_pair = (None, None)
        self.current_error = None

        self.processing = {
            "nextOrder": None,
            "ordersWithError": set()
        }

        self._load()

        self.was_reset.emit()

    def collect(self):
        """Run until and including Collection"""
        self._run(until=api.CollectorOrder,
                  on_finished=self.was_collected.emit)

    def validate(self):
        """Run until and including Validation"""
        self._run(until=api.ValidatorOrder,
                  on_finished=self.was_validated.emit)

    def extract(self):
        """Run until and including Extraction"""
        self._run(until=api.ExtractorOrder,
                  on_finished=self.was_extracted.emit)

    def integrate(self):
        """Run until and including Integration"""
        self._run(until=api.IntegratorOrder,
                  on_finished=self.was_integrated.emit)

    def publish(self):
        """Run until there are no more plug-ins"""
        self._run(on_finished=self.was_published.emit)

    def act(self, plug, action):
        context = self._context

        def on_next():
            result = plugin.process(plug, context, None, action.id)
            self.was_processed.emit(result)
            self.defer(500, lambda: self.was_acted.emit())

        self.is_running = True
        self.defer(100, on_next)

    def cleanup(self):
        """Forcefully delete objects from memory

        In an ideal world, this shouldn't be necessary. Garbage
        collection guarantees that anything without reference
        is automatically removed.

        However, because this application is designed to be run
        multiple times from the same interpreter process, extra
        case must be taken to ensure there are no memory leaks.

        Explicitly deleting objects shines a light on where objects
        may still be referenced in the form of an error. No errors
        means this was uneccesary, but that's ok.

        """

        for instance in self._context:
            del(instance)

        for plug in self._plugins:
            del(plug)

    def _load(self):
        """Initiate new generator and load first pair"""
        self.is_running = True
        self.pair_generator = self._iterator(self._plugins, self._context)
        self.current_pair = next(self.pair_generator, (None, None))
        self.current_error = None
        self.is_running = False

    def _run(self, until=float("inf"), on_finished=lambda: None):
        """Process current pair and store next pair for next process

        Arguments:
            until (api.Order, optional): Keep fetching next()
                until this order, default value is infinity.
            on_finished (callable, optional): What to do when finishing,
                defaults to doing nothing.

        """

        def on_next():
            if self.current_pair == (None, None):
                self.is_running = False
                return self.defer(100, on_finished)

            # The magic number 0.5 is the range between
            # the various CVEI processing stages;
            order = self.current_pair[0].order
            if order > (until + 0.5):
                self.is_running = False
                return self.defer(100, on_finished)

            self.about_to_process.emit(*self.current_pair)

            self.defer(10, on_process)

        def on_process():
            try:
                result = self._process(*self.current_pair)
                if result["error"] is not None:
                    self.current_error = result["error"]

                self.was_processed.emit(result)

            except Exception as e:
                stack = traceback.format_exc(e)
                return self.defer(
                    500, lambda: on_unexpected_error(error=stack))

            # Now that processing has completed, and context potentially
            # modified with new instances, produce the next pair.
            #
            # IMPORTANT: This *must* be done *after* processing of
            # the current pair, otherwise data generated at that point
            # will *not* be included.
            try:
                self.current_pair = next(self.pair_generator)

            except StopIteration:
                # All pairs were processed successfully!
                self.current_pair = (None, None)
                self.is_running = False
                return self.defer(500, on_finished)

            except Exception as e:
                # This is a bug
                stack = traceback.format_exc(e)
                self.current_pair = (None, None)
                return self.defer(
                    500, lambda: on_unexpected_error(error=stack))

            self.defer(10, on_next)

        def on_unexpected_error(error):
            self.is_running = False
            self.warned.emit(str(error))
            return self.defer(500, on_finished)

        self.is_running = True
        self.defer(10, on_next)

    def _iterator(self, plugins, context):
        """Yield next plug-in and instance to process.

        Arguments:
            plugins (list): Plug-ins to process
            context (api.Context): Context to process

        """

        test = logic.registered_test()

        for plug, instance in logic.Iterator(plugins, context):
            if not plug.active:
                continue

            if instance is not None and instance.data.get("publish") is False:
                continue

            self.processing["nextOrder"] = plug.order

            if not self.is_running:
                raise StopIteration("Stopped")

            if test(**self.processing):
                raise StopIteration("Stopped due to %s" % test(
                    **self.processing))

            yield plug, instance

    def _process(self, plug, instance=None):
        """Produce `result` from `plugin` and `instance`

        :func:`_process` shares state with :func:`_iterator` such that
        an instance/plugin pair can be fetched and processed in isolation.

        Arguments:
            plug (api.Plugin): Produce result using plug-in
            instance (optional, api.Instance): Process this instance,
                if no instance is provided, context is processed.

        """

        self.processing["nextOrder"] = plug.order

        try:
            result = plugin.process(plug, self._context, instance)

        except Exception as e:
            raise Exception("Unknown error: %s" % e)

        else:
            # Make note of the order at which the
            # potential error occured.
            has_error = result["error"] is not None
            if has_error:
                self.processing["ordersWithError"].add(plug.order)

        return result


def default_defer(self, delay, func):
    """Append artificial delay to `func`

    This aids in keeping the GUI responsive, but complicates logic
    when producing tests. To combat this, the environment variable ensures
    that every operation is synchonous.

    This function is designed to be overridden in the implementation
    of your graphical user engine.

    Arguments:
        delay (float): Delay multiplier; default 1, 0 means no delay
        func (callable): Any callable

    """

    return func()


class DefaultSignal(object):
    def __init__(self, *args):
        self._args = args
        self._observers = list()

    def connect(self, func):
        reference = lib.WeakRef(func)
        if reference not in self._observers:
            self._observers.append(reference)

    def disconnect(self, func):
        self._observers.remove(lib.WeakRef(func))

    def emit(self, *args):
        for observer in self._observers:
            try:
                observer()(*args)
            except ReferenceError:
                pass
            except Exception as e:
                sys.stderr.write(str(e))


def create(signal, defer, base=object):
    """Instantiate an isolated engine with supplied internals

    Arguments:
        signal (func):
        defer (func):

    """

    body = {"defer": defer}

    for attr in dir(AbstractEngine):
        prop = getattr(AbstractEngine, attr)
        if isinstance(prop, TemplateSignal):
            body[attr] = signal(*prop.args)

    cls = type("Engine", (AbstractEngine, base), body)

    return cls()


# Default slots
def _on_warned(message):
    sys.stderr.write(message + "\n")


def _on_processed(result):
    for record in result["records"]:
        print(record.msg)


def create_default():
    """Instantiate an engine with blocking signals"""
    default = create(DefaultSignal, default_defer)

    default.warned.connect(_on_warned)
    default.was_processed.connect(_on_processed)

    return default
