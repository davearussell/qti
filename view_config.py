from dialog import FieldDialog
from fields import SetField, TextField, LineEdit
import expr
import keys


class ExprEdit(LineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textChanged.connect(self.check_valid)

    def is_valid(self, value):
        try:
            expr.parse_expr(value)
            return True
        except expr.BadExpr:
            return False

    def normalise(self, value):
        try:
            return str(expr.parse_expr(value))
        except expr.BadExpr:
            return ''

    def check_valid(self, value):
        self.setProperty("valid", self.is_valid(value))
        self.setStyleSheet("/* /") # force stylesheet recalc

    def keyPressEvent(self, event):
        if keys.get_action(event) == 'select':
            self.setText(self.normalise(self.text()))
        super().keyPressEvent(event)


class ExprField(TextField):
    edit_cls = ExprEdit


def normalize_expr(text):
    return str(expr.parse_expr(text)) if text else text


class ViewConfigDialog(FieldDialog):
    title = "Config"

    def __init__(self, app, library, config):
        super().__init__(app)
        self.library = library
        self.config = config
        self.init_fields(self.choose_fields())

    def choose_fields(self):
        all_tags = set()
        for _set in self.library.sets.values():
            all_tags |= _set
        sort_types = self.library.sort_types()
        config = self.config.copy()
        return [
            SetField("group_by", config.group_by, self.library.groupable_keys(), keybind='G'),
            SetField("order_by", config.order_by, sort_types, keybind='O'),
            SetField('include_tags', config.include_tags, all_tags, keybind='I'),
            SetField('exclude_tags', config.exclude_tags, all_tags, keybind='X'),
            ExprField('custom_expr', config.custom_expr, keybind='U'),
        ]

    def field_committed(self, field, value):
        self.need_reload = True
        assert field.key in self.config.defaults, (field.key, value)
        setattr(self.config, field.key, value)
        super().field_committed(field, value)
