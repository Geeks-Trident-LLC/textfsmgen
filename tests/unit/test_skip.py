import textfsmgen.__main__ as mod__main__
import textfsmgen.main as mode_main
import textfsmgen.application as mod_application
import textfsmgen.ui.about as mod_ui_about
import textfsmgen.ui.builder as mod_ui_builder
import textfsmgen.ui.common as mod_ui_common
import textfsmgen.ui.callback as mod_ui_callback
import textfsmgen.ui.controls as mod_ui_controls
import textfsmgen.ui.menu as mod_ui_menu
import textfsmgen.ui.settings as mod_ui_settings
import textfsmgen.ui.suggester as mod_ui_suggester
import textfsmgen.ui.textfsm_tester as mod_textfsm_tester
import textfsmgen.ui.usage as mod_ui_usage

import pytest


@pytest.mark.parametrize(
    "mod_class_or_func",
    [
        mod__main__, mode_main, mod_application.Application,
        mod_ui_about, mod_ui_builder, mod_ui_common,
        mod_ui_callback, mod_ui_controls, mod_ui_menu,
        mod_ui_settings, mod_ui_suggester, mod_textfsm_tester, mod_ui_usage,
    ]
)
def test(mod_class_or_func):
    assert mod_class_or_func is not None
