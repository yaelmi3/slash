import slash
from slash import plugins
from slash.plugins import PluginInterface
from slash import hooks

from .utils import TestCase


def test_hook__test_interrupt(populated_suite, request, checkpoint):
    request.addfinalizer(
        hooks.test_interrupt.register(checkpoint)
        .unregister)

    test_index = int(len(populated_suite) / 2)
    for index, test in enumerate(populated_suite):
        if index == test_index:
            test.interrupt()
        elif index > test_index:
            test.expect_deselect()
    populated_suite.run(expect_interruption=True)
    assert checkpoint.called

def test_hook__test_failure_without_exception(populated_suite, request, checkpoint, suite_test):
    request.addfinalizer(
        hooks.test_failure.register(checkpoint)
        .unregister)

    suite_test.inject_line('slash.add_failure("failure")')
    suite_test.expect_failure()

    populated_suite.run()
    assert checkpoint.called



#### Older tests below, need modernizing ####

class HookCallingTest(TestCase):

    def setUp(self):
        super(HookCallingTest, self).setUp()
        self.plugin1 = make_custom_plugin("plugin1", self)
        self.plugin2 = make_custom_plugin("plugin2", self, hook_names=["session_start", "after_session_start"])
        self.addCleanup(plugins.manager.uninstall, self.plugin1)
        self.addCleanup(plugins.manager.uninstall, self.plugin2)

    def test_hook_calling_order(self):
        # expect:
        with self.forge.any_order():
            self.plugin1.activate()
            self.plugin2.activate()

        with self.forge.any_order():
            self.plugin1.session_start()
            self.plugin2.session_start()


        with self.forge.any_order():
            self.plugin1.after_session_start()
            self.plugin2.after_session_start()

        self.plugin1.session_end()

        self.forge.replay()
        # get:

        plugins.manager.install(self.plugin1, activate=True)
        plugins.manager.install(self.plugin2, activate=True)

        with slash.Session() as s:
            with s.get_started_context():
                pass


def make_custom_plugin(name, test, hook_names=None):

    class CustomPlugin(PluginInterface):
        def get_name(self):
            return name

    CustomPlugin.__name__ = name

    if hook_names is None:
        hook_names = [name for name, _ in slash.hooks.get_all_hooks()]

    for hook_name in hook_names:
        setattr(CustomPlugin, hook_name, test.forge.create_wildcard_function_stub(name=hook_name))

    setattr(CustomPlugin, "activate", test.forge.create_wildcard_function_stub(name="activate"))

    return CustomPlugin()
