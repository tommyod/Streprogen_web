# -*- coding: utf-8 -*-

from __future__ import division
from collections import defaultdict
import random
import math


class DynamicExercise(object):
    """
    Object for Dynamic Exercises.
    """
    def __init__(self, name, current_max, desired_max, low_reps, high_reps):
        self.name = name
        self.current_max = int(current_max)
        self.desired_max = int(desired_max)
        self.low_reps = int(low_reps)
        self.high_reps = int(high_reps)

    def __repr__(self):
        return str(self.__dict__)


class StaticExercise(object):
    """
    Object for Static Exercises.
    """
    def __init__(self, name, scheme):
        self.name = name
        self.scheme = scheme

    def __repr__(self):
        return str(self.__dict__)


class Day(object):
    """
    Object for Days.
    """
    def __init__(self):
        self.main_exercises = []
        self.extra_exercises = []

    def __repr__(self):
        return str(self.__dict__)

    def add_main(self, exercise):
        self.main_exercises.append(exercise)

    def add_extra(self, exercise):
        self.extra_exercises.append(exercise)


class Program(object):
    """
    Object for the Program.
    """

    def __init__(self, name, units, round, duration, nonlinearity, intensity_list, intensity_model,
                 reps_list, reps_model, reps_per_week, reps_RM):
        self.name = name
        self.units = units
        self.round = float(round)
        self.duration = int(duration)
        self.nonlinearity = int(nonlinearity)
        if float(self.nonlinearity) == 0:
            self.k = 0.001
        else:
            self.k = 0.1 * float(nonlinearity)
        self.intensity_list = to_list(intensity_list)
        self.intensity_model = intensity_model
        self.reps_list = to_list(reps_list)
        self.k_list = [S(self.k, w, 100, 0, 1, self.duration) for w in range(1,self.duration+1)]
        self.reps_model = reps_model
        self.reps_per_week = float(reps_per_week)
        self.reps_RM_model = reps_RM.lower()
        reps_RM = reps_RM.lower()
        if reps_RM == 'normal':
            self.reps_RM = [None] + [97.5, 92.5, 87.5, 82.5, 77.5, 72.5, 67.5, 62.5, 57.5, 52.5]
        if reps_RM == 'relaxed':
            self.reps_RM = [None] + [97.5, 91.9, 86.3, 80.6, 75.0, 69.4, 63.8, 58.1, 52.5, 46.9]
        if reps_RM == 'tight':
            self.reps_RM = [None] + [97.5, 93.1, 88.8, 84.4, 80.0, 75.6, 71.3, 66.9, 62.5, 58.1]


        self.days = []
        self.rendered = False

    def _set_maxima(self):
        """
        Sets the maximum intensity (lowest number of repetitions).
        This is done prior to rendering the program, and it is done
        to ensure some variety in the minimum number of repetitions,
        along with consistency depending on the mode.
        For instance, working up to the same number of repetitions
        two weeks in a row is not possible.

        See list_of_random.
        """
        self.maxima = dict()

        # If the mode is weekly, work up to the same intensity for the entire week
        if self.mode == 'week':
            ex = self.days[0].main_exercises[0]
            values = list_of_random(ex.low_reps, 5, self.duration)
            for ex in self.iter_exercises():
                    self.maxima[ex] = values

        # If the mode is day, work up to the same intensity for the day
        if self.mode == 'day':
            for day in self.days:
                ex = day.main_exercises[0]
                values = list_of_random(ex.low_reps, 5, self.duration)
                for ex in day.main_exercises:
                    self.maxima[ex] = values

        # If the mode is exercise, go it for every exercise
        for ex in self.iter_exercises():
            self.maxima[ex] = list_of_random(ex.low_reps, 5, self.duration)


    def render(self):
        """
        Render the program.
        Prior to rendering, set the mode automatically and set the maxima (max intensity).
        """
        self.mode = self._mode()
        self._set_maxima()
        self.rendered = [defaultdict(int) for i in range(self.duration*2)]

        for week in range(1, self.duration+1):
            self.rendered[week] = defaultdict(int)
            for i, day in enumerate(self.days):
                for mainex in day.main_exercises:
                    reps, intensity, weights = render(mainex, self, week)
                    self.rendered[week][mainex] = (' | '.join([str(r)+' x '+str(w)+self.units for r, w in zip(reps, weights)]),
                                                   (reps, intensity, weights))


    def _stats_total_lifted(self, day):
        """
        Return statistics of total weight lifted.
        """
        return_list = []
        for week in range(1, self.duration+1):
            lifted = 0
            for mainex in day.main_exercises:
                reps = self.rendered[week][mainex][1][0]
                weights = self.rendered[week][mainex][1][2]
                lifted += sum([i*j for i, j in zip(reps, weights)])
            return_list.append(lifted)
        return return_list

    def _stats_reps_heaviest(self, exercise):
        """
        Return statistics on the number of reps on the heaviest set.
        """
        return_list = []
        for week in range(1, self.duration+1):
            reps = self.rendered[week][exercise][1][0][-1]
            return_list.append(reps)
        return return_list



    def print_it(self):
        """
        Debugging function.
        """
        print('printing')
        for week in range(1, self.duration+1):
            print('Week {}'.format(week))
            for i, day in enumerate(self.days):
                print('Day {}'.format(i))
                for mainex in day.main_exercises:
                    print(self.rendered[week][mainex][0])



    def __repr__(self):
        """
        Representation of a program. For debugging.
        """
        return str(self.__dict__)

    def iter_exercises(self):
        """
        Generator yielding the exercises.
        """
        for day in self.days:
            for mainex in day.main_exercises:
                yield mainex

    def _mode(self):
        """
        Determine the mode. Either 'week', 'day' or 'exercise'.
        """
        container = []
        for day in self.days:
            for ex in day.main_exercises:
                container.append(ex.low_reps)
        if len(list(set(container))) == 1:
            return 'week'

        for day in self.days:
            container = []
            for ex in day.main_exercises:
                container.append(ex.low_reps)
            if len(list(set(container))) != 1:
                return 'exercise'
        return 'day'



def render(exercise, program, week):
    """
    Stand-alone function for rendering.
    """
    low_reps = program.maxima[exercise][week-1]
    high_reps = exercise.high_reps
    reps_total = int(program.reps_per_week * (program.reps_list[week-1]/100))
    desired_MI = program.intensity_list[week-1]

    suggestions = []
    render_times = 25
    # Going from render_times = 1 to render_times = 10 halves the total error,
    # going to 25 seems to be a reasonable compromise.
    for s in range(render_times):
        reps = create_reps(low_reps, high_reps, reps_total)
        intensity = [program.reps_RM[rep] for rep in reps]
        error = abs(get_MI(reps, intensity) - desired_MI) + 5*loss_measure(reps)
        suggestions.append((reps, intensity, error))

    suggestions.sort(key=lambda a:a[2])

    chosen = suggestions[0]# random.choice(suggestions[0:10])

    reps, intensity, error = chosen

    current_max = S(program.k, week, exercise.desired_max, exercise.current_max, 1, 8)
    weights = [round_to_nearest((inten/100)*current_max, program.round) for inten in intensity]

    return reps, intensity, weights








































def loss_measure(someList):
    """
    Measures spread. The lower the better. Between 0 and 1.
    """
    diff = [(someList[i] - someList[i + 1]) ** 2 for i in range(len(someList) - 1)]
    worst = (max(someList) - min(someList)) ** 2
    if worst == 0:
        return 1
    return sum(diff) / worst



def to_list(inputvalue):
    """
    Takes a string to a list, separated by commas.
    """
    return [float(i) for i in inputvalue.split(',')]

def get_MI(reps, intensities):
    upper = sum([i*j for i, j in zip(reps, intensities)])
    return upper/sum(reps)

def S(k, t, S_m, S_i, t_i, t_m):
    """
    Returns the current strength level from linearly adjusted differential eq.
    """
    a = (t_i - t) / (t_m - t_i)
    return (S_i - S_m) * math.exp(a * k) + S_m + a * (S_i - S_m) * math.exp(-k)


def round_to_nearest(number, nearest):
    """
    Rounds to nearest. Returns integer if it's an integer.
    """
    rounded = round(number / nearest) * nearest
    if rounded % 1 == 0:
        return int(rounded)
    else:
        return rounded


def list_of_random(low, high, num):
    if abs(low-high) < 1:
        return [low for i in range(num)]
    return_list = [random.randint(low, high)]
    i = 0
    for i in range(num-1):
        try_value = random.randint(low, high)
        while try_value == return_list[i]:
            try_value = random.randint(low, high)
        return_list.append(try_value)
    return return_list

def create_reps(low, high, num):
    return_list = []
    taken = 0
    while True:
        if (num - taken) <= high and (num - taken) >= low:
            return_list.append(num - taken)
            break
        new = random.randint(low, high)
        taken += new
        return_list.append(new)
        if taken > num:
            break

    return_list.sort(reverse=True)
    return return_list