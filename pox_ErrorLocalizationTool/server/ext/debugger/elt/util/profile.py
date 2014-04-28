import cProfile


i = 0


def profile(func):
    """Decorator for run function profile"""
    def wrapper(*args, **kwargs):
        global i
        profile_filename = 'profile/' + func.__name__ + '%06d' % i + '.prof'
        i += 1
        profiler = cProfile.Profile()
        result = profiler.runcall(func, *args, **kwargs)
        profiler.dump_stats(profile_filename)
        return result
    return wrapper
