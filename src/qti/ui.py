import importlib
import os

UI_TYPE = os.environ.get('UI', 'qt')
DEBUG = os.environ.get('DEBUG')

CLASSES = {
    'app': 'app.App',
    'image': 'image.Image',
    'browser': 'browser.BrowserWidget',
    'grid': 'grid.GridWidget',
    'viewer': 'viewer.ViewerWidget',
    'pathbar': 'pathbar.PathbarWidget',
    'status_bar': 'status_bar.StatusBarWidget',
    'bulk_edit_dialog': 'dialogs.bulk_edit.BulkEditDialogWidget',
    'field_dialog': 'dialogs.common.FieldDialogWidget',
    'choice_dialog': 'dialogs.choice.ChoiceDialogWidget',
    'field_group': 'dialogs.fields.FieldGroupWidget',
    'field': 'dialogs.fields.FieldWidget',
    'text_field': 'dialogs.fields.TextFieldWidget',
    'set_field': 'dialogs.fields.SetFieldWidget',
    'validated_text_field': 'dialogs.fields.ValidatedTextFieldWidget',
    'color_field': 'dialogs.fields.ColorFieldWidget',
    'enum_field': 'dialogs.fields.EnumFieldWidget',
    'importer_dialog': 'dialogs.importer.ImporterDialogWidget',
    'key_config_dialog': 'dialogs.key_config.KeybindDialogWidget',
    'key_chooser': 'dialogs.key_config.KeyChooserWidget',
    'macro_dialog': 'dialogs.macros.MacroDialogWidget',
    'metadata_editor_dialog': 'dialogs.metadata_editor.MetadataEditorDialogWidget',
    'search_dialog': 'dialogs.search.SearchDialogWidget',
    'label_dialog': 'dialogs.simple.LabelDialogWidget',
    'line_edit_dialog': 'dialogs.simple.LineEditDialogWidget',
}


def cls(name):
    path = CLASSES[name.lower()]
    module_suffix, class_name = path.rsplit('.', 1)
    module_name = 'qti.%s.%s' % (UI_TYPE, module_suffix)
    try:
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except (ModuleNotFoundError, AttributeError):
        if DEBUG:
            print("WARNING: failed to import %s.%s" % (module_name, class_name))
        def _fail(*args, **kwargs):
            raise Exception("Failed to import %s.%s" % (module_name, class_name))
        return _fail
