'''
Tool for profiling code execution

How to use: (see __main__ below)
'''

from time import perf_counter, sleep
import logging

log = logging.getLogger(__name__)

class Stopwatch():
    def __init__(self):
        self.prec   = 3
        self.timers = {}

    def start(self, key):
        if not self.timers:
            self.timers['TOTAL_START'] = perf_counter()
            self.timers['TOTAL'] = 0
        self.timers[key] = self.timers.get(key, 0)
        self.timers[f'{key}_START'] = perf_counter()

    def stop(self, key):
        try:
            self.timers[key] += perf_counter() - self.timers[f'{key}_START']
            del self.timers[f'{key}_START']
        except KeyError:
            log.warning('Attempting to stop timer that never started: %s', key)

    def clear(self):
        self.timers = {}

    def summary(self):
        # TODO: Allow summary() to be called multiple times
        # Currently summary() is meant to be called after all stopwatches are stopped
        if not self.timers:
            return 'Stopwatch not used'
        self.stop('TOTAL')
        for key in tuple(self.timers.keys()):
            if key.endswith('_START'):
                base_key = key.rstrip('_START')
                log.warning('Stopwatch timer not stopped : %s', base_key)
                self.stop(base_key)
        s = f'Total Time : {self.timers["TOTAL"]:.{self.prec}f}s\n'
        s += self._to_string(self._nested_timers(), self.timers["TOTAL"])
        return s

    def _nested_timers(self):
        nested = {}
        for key, timer in self.timers.items():
            if '/' in key or key == 'TOTAL':
                continue
            sub_timers = self._get_subtimers(key)
            nested[key] = (timer, sub_timers)
        return nested

    def _get_subtimers(self, parent_key):
        sub_timers = {}
        for key, timer in self.timers.items():
            if key.startswith(parent_key+'/') and '/' not in key[len(parent_key)+1:]:
                sub_timers[key[len(parent_key)+1:]] = (timer, self._get_subtimers(key))
        return sub_timers

    def _to_string(self, times, parent_time, tabs='\t'):
        s = ''
        buff = max([len(k) for k in times])
        for key, val in times.items():
            subtotal, subtimers = val
            try:
                percent = subtotal / parent_time
            except ZeroDivisionError:
                percent = 0

            if subtotal == parent_time:
                p_str = '100%'
            elif subtotal == 0:
                p_str = '  0%'
            elif percent > 0.995:
                p_str = '>99%'
            elif percent < 0.01:
                p_str = '< 1%'
            else:
                p_str = f'{percent:4.0%}'

            s += f'{tabs}{key:{buff}} : {subtotal:{self.prec+3}.{self.prec}f}s [{p_str}]\n'

            if subtimers:
                s += self._to_string(subtimers, subtotal, tabs+'\t')
        return s

stopwatch = Stopwatch()

if __name__ == '__main__':
    for _ in range(5):
        ########################################
        stopwatch.start('my_timer1')
        ####################
        stopwatch.start('my_timer1/subtimer1')
        sleep(0.1)
        ##########
        stopwatch.start('my_timer1/subtimer1/subsubtimer')
        sleep(0.1)
        stopwatch.stop('my_timer1/subtimer1/subsubtimer')
        stopwatch.stop('my_timer1/subtimer1')

        ####################
        stopwatch.start('my_timer1/subtimer2')
        sleep(0.0001)
        stopwatch.stop('my_timer1/subtimer2')

        stopwatch.stop('my_timer1')

        ########################################
        stopwatch.start('my_timer2')
        sleep(.1)
        stopwatch.stop('my_timer2')
    print(stopwatch.summary())
