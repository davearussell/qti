from PySide6.QtWidgets import QDialogButtonBox, QRadioButton

from .common import DialogWidget


class ChoiceDialogWidget(DialogWidget):
    def __init__(self, choices, **kwargs):
        super().__init__(**kwargs)
        self.add_radio_buttons(choices)
        self.add_action_buttons()

    def selected_choice(self):
        for i, button in enumerate(self.radio_buttons):
            if button.isChecked():
                return self.choices[i]

    def add_radio_buttons(self, choices):
        self.choices = []
        self.radio_buttons = []
        for choice, shortcut, label in choices:
            self.choices.append(choice)
            if shortcut and shortcut in label:
                label = label.replace(shortcut, '&' + shortcut, 1)
            button = QRadioButton(label)
            self.layout().addWidget(button)
            if shortcut:
                button.setShortcut(shortcut)
            self.radio_buttons.append(button)
        self.radio_buttons[0].setChecked(True)
