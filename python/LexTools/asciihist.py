import numpy as np
def ascii_hist(it, 
               bins=10,
               minmax=None, 
               scale_output=30, 
               str_tag='', 
               generate_only=False
) -> str:
    """Create an ASCII histogram from an iterable of numbers.

    Author: Boris Gorelik boris@gorelik.net. based on  http://econpy.googlecode.com/svn/trunk/pytrix/pytrix.py
    License: MIT
    
    Arguments:
        it     -- iterable of numbers
        bins   -- number of histogram bins
        minmax -- y-range. Default is full range. 'auto' uses 5th to 95th percentile.  
        str_tag        -- print prefix for each output line
        scale_output   -- number of markers in max bin
        generate_only  -- do not print to stdout
    """
    ret = []
    itarray = np.asanyarray(it)
    if minmax == 'auto':
        minmax = np.percentile(it, [5, 95])
        if minmax[0] == minmax[1]:
            # for very ugly distributions
            minmax = None
    if minmax is not None:
        # discard values that are outside minmax range
        mn = minmax[0]
        mx = minmax[1]
        itarray = itarray[itarray >= mn]
        itarray = itarray[itarray <= mx]
    if itarray.size:
        total = len(itarray)
        counts, cutoffs = np.histogram(itarray, bins=bins)
        cutoffs = cutoffs[1:]
        if str_tag:
            str_tag = '%s ' % str_tag
        else:
            str_tag = ''
        if scale_output is not None:
            scaled_counts = counts.astype(float) / counts.max() * scale_output
        else:
            scaled_counts = counts

        if minmax is not None:
            ret.append('Trimmed to range (%s - %s)' % (str(minmax[0]), str(minmax[1])))
        for cutoff, original_count, scaled_count in zip(cutoffs, counts, scaled_counts):
            ret.append("{:s}{:>8.2f} |{:<7,d} | {:s}".format(
                str_tag,
                cutoff,
                original_count,
                "*" * int(round(scaled_count)))
                       )
        ret.append(
            "{:s}{:s} |{:s} | {:s}".format(
                str_tag,
                '-' * 8,
                '-' * 7,
                '-' * 7
            )
        )
        ret.append(
            "{:s}{:>8s} |{:<7,d}".format(
                str_tag,
                'N=',
                total
            )
        )
    else:
        ret = []
    if not generate_only:
        for line in ret:
            print(line)
    ret = '\n'.join(ret)
    return ret


if __name__ == '__main__':
    np.random.seed(11)
    ascii_hist(np.random.randn(10000), minmax='auto', str_tag='Normal');
