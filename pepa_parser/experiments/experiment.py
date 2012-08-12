#!/usr/bin/env python


def get_rate_from_actset(action, actset):
    """ Returns rate from actset returned from solver """
    for act in actset:
        if act[0] == action:
            return float(act[1])


def rate_experiment(rate_x, var_rate, rate_y, pepa_model):
    """ var_rate is a generator
        rate_y is the resulting rate on the Y axis
    """
    rate_ys = []
    rate_xs = []
    rates = pepa_model.get_rates()
    for i in var_rate():
            rates[rate_x] = str(i)
            rate_xs.append(float(i))
            pepa_model.recalculate(rates)
            pepa_model.steady_state()
            rate_ys.append( get_rate_from_actset(rate_y, pepa_model.get_throughoutput()))
    return (rate_xs, rate_ys)


def range_maker(low, hi, step):
    """
    Returns a generator function
    """
    def counter():
        nonlocal low
        nonlocal hi
        nonlocal step
        cur = low
        while cur <= hi:
            yield cur
            cur += step
    return counter
