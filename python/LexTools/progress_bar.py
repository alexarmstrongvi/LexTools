import sys
import time

# Consider using tqdm if it is available
class ProgressBar():
    def __init__(self, total, mod=None):
        self.start = 0
        self.count = 0
        self.total = total
        self.mod   = mod if mod else 1 if total < 100 else total//100
        
    def begin(self):
        self.start = time.perf_counter()
        return self

    def reset(self):
        self.start = 0
        self.count = 0
        
    def update(self):
        if not self.start:
            self.begin()
        self.count += 1
        
        if (self.count % self.mod) and (self.count < self.total):
            return
        
        time_elapsed = time.perf_counter() - self.start
        minutes, sec = divmod(time_elapsed, 60)
        time_str = f'{minutes: >2.0f}min {sec:02.3f}s'
        
        rate = self.count/time_elapsed if time_elapsed > 0 else 1
        remaining_time = ((self.total-self.count)/rate)/60
        
        sys.stdout.write(
            f'{self.count/self.total:4.0%} Done; '
            f'({self.count:>4}/{self.total}) {time_str} elapsed '
            f'[~{round(remaining_time)}min remaining]    \r'
        )
        sys.stdout.flush()
        
        if self.count == self.total:
            print()

if __name__ == '__main__':
    N = 13579
    pbar = ProgressBar(N)
    for _ in range(N):
        time.sleep(0.01)
        pbar.update()

