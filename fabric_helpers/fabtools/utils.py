import fabric


class RequiredDictKeysMixin:

    """Use this mixin to require an option dict with required keys.

    Gives a helpful errorback for class implementations requiring a dict with
    specific keys, here is what you must do to implement:

    1. Subclass RequiresKeysMixin
    2. Call __init__ for RequiresKeysMixin in the classes __init__
    3. Specific a list of keys option_keys class variable

    Like this::

        class MyClass(RequiresKeysMixin):  # you can add other classes too

            option_keys = [  # required to have a list of keys
                'required_key1',
                'required_key2'
            ]

            def __init__(self, options, *args, **kwargs):  # use any signature.
                # as long as you pass the dict to RequiresKeysMixin
                RequiredDictKeysMixin.__init__(self, options)
                # Do whatever else you want
                super(MyClass, self).__init__(*args, **kwargs)
    """

    def __init__(self, options):
        if not all(k in options for k in self.option_keys):
            # if not, let user implementing know what options were missing
            fabric.utils.abort(
                'Missing keys in options: \n - {}'.format(
                    '\n - '.join(k for k in self.option_keys if k not in options)
                )
            )
