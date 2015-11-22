#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import os

###############################################################################


class PBar:

    def __init__(self, text, max_value):
        self.text = text
        self.max_value = max_value
        self.value = 0
        self.started = arrow.now()
        self.width = 40
        os.system('setterm -cursor off')

    def update(self):
        self.value += 1
        print(self._line() + '\r', end='')

    def _line(self):
        percentage = round(100 * self.value / self.max_value)
        filled = round(self.width * self.value / self.max_value)
        empty = self.width - filled
        minutes, seconds = divmod((arrow.now() - self.started).seconds, 60)
        return '{} |{}{}| {:>3}% ({:02}:{:02})'.format(
            self.text, '█' * filled, ' ' * empty, percentage, minutes, seconds)

    def finish(self):
        self.value = self.max_value
        print(self._line())
        os.system('setterm -cursor on')
