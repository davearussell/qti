from xui.widgets import FieldDialog, TypedField, ColorField

from ..settings import Color, Size

FIELD_TYPES = {
    Color: ColorField,
    Size:  TypedField,
    str:   TypedField,
    int:   TypedField,
    float: TypedField,
}


class AppSettingsDialog(FieldDialog):
    title = 'App settings'

    def __init__(self):
        super().__init__()
        self.init_fields(self.choose_fields())

    def choose_fields(self):
        return [
            FIELD_TYPES[type(value)](key, value)
            for key, value in self.app.settings.to_dict().items()
        ]

    def apply_field_update(self, field, value):
        self.app.settings.set(field.key, str(value))

    def post_commit_cb(self):
        super().post_commit_cb()
        self.app.apply_settings()
        super().post_commit_cb()
