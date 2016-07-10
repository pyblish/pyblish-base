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

    def disconnect(self, *args):
        pass

    def emit(self, *args):
        pass


class AbstractEngine(object):
    """Asynchronous, stateful scripting engine"""

    # Emitted when the GUI is about to start processing;
    # e.g. resetting, validating or publishing.
    about_to_process = TemplateSignal(object, object)

    # Emitted for each process
    was_processed = TemplateSignal(dict)  # dict=result

    was_discovered = TemplateSignal()
    was_reset = TemplateSignal()
    was_collected = TemplateSignal()
    was_validated = TemplateSignal()
    was_extracted = TemplateSignal()
    was_integrated = TemplateSignal()
    was_published = TemplateSignal()
    was_acted = TemplateSignal()

    # Emitted when processing has finished
    was_finished = TemplateSignal()

    # Informational outlets for observers
    warned = TemplateSignal(str)  # str=message
    logged = TemplateSignal(str)  # str=message

    @property
    def context(self):
        return self._context

    @property
    def plugins(self):
        return self._plugins

    @property
    def is_running(self):
        return self._is_running

    @property
    def current_error(self):
        return self._current_error

    def dispatch(self, func, *args, **kwargs):
        """External functionality

        This is an optional overridable for services that implement their own
        client-side proxies to the supplied functionality.

        For example, in pyblish-qml, these functions are provided as a
        wrapper to functionality running remotely.

        Arguments:
            func (str): Name of external function
            args (list, optional): Arguments passed to `func`
            kwargs (dict, optional): Keyword arguments passed to `func`

        Raises:
            KeyError on missing functionality and
            whatever exception raised by target function.

        """

        raise NotImplementedError

    def defer(self, delay, func):
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

        raise NotImplementedError

    def __init__(self):
        super(AbstractEngine, self).__init__()

        self._is_running = False

        self._context = self.dispatch("Context")
        self._plugins = list()

        # Transient state used during publishing.
        self._pair_generator = None        # Active producer of pairs
        self._current_pair = (None, None)  # Active pair
        self._current_error = None

        # This is used to track whether or not to continue
        # processing when, for example, validation has failed.
        self._processing = {
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

    def stop(self):
        self._is_running = False

    def reset(self):
        """Discover plug-ins and run collection"""
        self._context = self.dispatch("Context")
        self._plugins[:] = self.dispatch("discover")

        self.was_discovered.emit()

        self._pair_generator = None
        self._current_pair = (None, None)
        self._current_error = None

        self._processing = {
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
            result = self.dispatch("process", plug, context, None, action.id)
            self.was_processed.emit(result)
            self.defer(500, on_finished)

        def on_finished():
            self.was_acted.emit()
            self._is_running = False

        self._is_running = True
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

        while self._context:
            self._context.pop(0)

        while self._plugins:
            self._plugins.pop(0)

        self._context = []
        self._plugins = []

        try:
            self._pair_generator.close()
        except AttributeError:
            pass

        self._pair_generator = None
        self._current_pair = ()
        self._current_error = None

    def _load(self):
        """Initiate new generator and load first pair"""
        self._is_running = True
        self._pair_generator = self._iterator(self._plugins, self._context)
        self._current_pair = next(self._pair_generator, (None, None))
        self._current_error = None
        self._is_running = False

    def _run(self, until=float("inf"), on_finished=lambda: None):
        """Process current pair and store next pair for next process

        Arguments:
            until (api.Order, optional): Keep fetching next()
                until this order, default value is infinity.
            on_finished (callable, optional): What to do when finishing,
                defaults to doing nothing.

        """

        def on_next():
            if self._current_pair == (None, None):
                return finished(100)

            # The magic number 0.5 is the range between
            # the various CVEI processing stages;
            order = self._current_pair[0].order
            if order > (until + 0.5):
                return finished(100)

            self.about_to_process.emit(*self._current_pair)

            self.defer(10, on_process)

        def on_process():
            try:
                result = self._process(*self._current_pair)
                if result["error"] is not None:
                    self._current_error = result["error"]

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
                self._current_pair = next(self._pair_generator)

            except StopIteration:
                # All pairs were processed successfully!
                self._current_pair = (None, None)
                return finished(500)

            except Exception as e:
                # This is a bug
                stack = traceback.format_exc(e)
                self._current_pair = (None, None)
                return self.defer(
                    500, lambda: on_unexpected_error(error=stack))

            self.defer(10, on_next)

        def on_unexpected_error(error):
            self.warned.emit(str(error))
            return finished(500)

        def finished(delay):
            self._is_running = False
            self.was_finished.emit()
            return self.defer(delay, on_finished)

        self._is_running = True
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

            self._processing["nextOrder"] = plug.order

            if not self._is_running:
                raise StopIteration("Stopped")

            if test(**self._processing):
                raise StopIteration("Stopped due to %s" % test(
                    **self._processing))

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

        self._processing["nextOrder"] = plug.order

        try:
            result = self.dispatch("process", plug, self._context, instance)

        except Exception as e:
            raise Exception("Unknown error: %s" % e)

        else:
            # Make note of the order at which the
            # potential error occured.
            has_error = result["error"] is not None
            if has_error:
                self._processing["ordersWithError"].add(plug.order)

        return result


def default_defer(self, delay, func):
    """Synchronous, non-deferring"""
    return func()


def default_dispatch(self, func, *args, **kwargs):
    """Use local library"""
    return {
        "Context": api.Context,
        "Instance": api.Instance,
        "discover": api.discover,
        "process": plugin.process,
    }[func](*args, **kwargs)


class DefaultSignal(object):
    """Simple, but capable signal

    Handles garbage collection of connected observers
    via weak referencing. Runs in the emitting thread.

    """

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


def create(signal=DefaultSignal,
           defer=default_defer,
           base=object,
           dispatch=default_dispatch):
    """Instantiate an independent engine of supplied internals

    Arguments:
        signal (class, optional): Must implement the interface
            of TemplateSignal. Defaults to `DefaultSignal`
        defer (callable, optional): Must implement the interface
            of `default_defer`. Defaults to `default_defer`
        base (class, optional): Baseclass of AbstractEngine,
            defaults to `object`.
        dispatch (callable, optional): Must implement the interface
            of `default_dispatch`, defaults to `default_dispatch`.

    """

    body = {
        "defer": defer,
        "dispatch": dispatch
    }

    # Replace TemplateSignal with provided mechanism
    for attr in dir(AbstractEngine):
        prop = getattr(AbstractEngine, attr)
        if isinstance(prop, TemplateSignal):
            body[attr] = signal(*prop.args)

    cls = type("Engine", (AbstractEngine, base), body)

    return cls()
