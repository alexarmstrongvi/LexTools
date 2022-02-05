import sys
from datetime import datetime

class LoadingBar():
    def __init__(self, total, mod=None):
        self.start = None
        self.count = 0
        self.total = total
        self.mod   = mod if mod else 1 if total < 100 else total//100
        
    def begin(self):
        self.start = datetime.now()
        return self
        
    def update(self):
        if not self.start:
            self.begin()
        self.count += 1
        
        time_elapsed = (datetime.now()-self.start).seconds
        minutes, sec = divmod(time_elapsed, 60)
        time_str = f'{minutes: >2}min {sec:02}s'
        
        rate = self.count/time_elapsed if time_elapsed > 0 else 1
        remaining_time = ((self.total-self.count)/rate)/60
        
        if (self.count % self.mod) and (self.count < self.total):
            return
        
        print(f'{self.count/self.total:4.0%} Done; ({self.count:>4}/{self.total}) {time_str} elapsed [~{round(remaining_time)}min remaining]    \r', end='')
        sys.stdout.flush()
        
        if self.count == self.total:
            print()
