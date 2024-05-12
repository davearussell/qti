from .common import FieldDialog
from .fields import TypedField, ColorField
from settings import Color, Size

FIELD_TYPES = {
    Color: ColorField,
    Size:  TypedField,
    str:   TypedField,
    int:   TypedField,
    float: TypedField,
}


class AppSettingsDialog(FieldDialog):
    title = 'App settings'

    def __init__(self, app):
        self.app = app
        fields = [FIELD_TYPES[type(value)](key, value)
                  for key, value in self.app.settings.to_dict().items()]
        super().__init__(app.window, fields)

    def apply_field_update(self, field, value):
        self.app.settings.set(field.key, str(value))

    def post_commit_cb(self):
        self.app.apply_settings()
        super().post_commit_cb()
