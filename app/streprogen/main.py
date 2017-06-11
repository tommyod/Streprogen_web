# -*- coding: utf-8 -*-

# Imports
from __future__ import division
from collections import defaultdict
import random
import math
import warnings


class DynamicExercise(object):
    """
    Object for Dynamic Exercises.
    """
    def __init__(self, name, current_max, desired_max, 
                 low_reps = 3, high_reps = 8, reps = None):
        """
        Initalize a new dynamic exercise.
        
        Parameters
        ----------
        name : Name of the exercise.
        current_max : Current maximum.
        desired_max : Desired maximum.
        low_reps : Lowest number of reps.
        high_reps : Highest number of reps.
        reps : Total reps, if None global from program is used.
        """
        self.name = name
        self.current_max = int(current_max)
        self.desired_max = int(desired_max)
        self.low_reps = int(low_reps)
        self.high_reps = int(high_reps)
        self.reps = reps

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
        if isinstance(exercise, list):
            self.main_exercises += exercise
        else:
            self.main_exercises.append(exercise)

    def add_extra(self, exercise):
        self.extra_exercises.append(exercise)


class Program(object):
    """
    Object for the Program.
    """
    
    _latex_template_path = 'latex_template.txt'

    def __init__(self, name, units = 'kg', round_to = 2.5, weeks = 6, 
                 nonlinearity = 0.1, intensity_list = None, 
                 intensity_model = None, reps_list = None, reps_model = None, 
                 reps_per_exercise = 25, reps_RM = 'tight'):
        """
        Initalize a new training program.
        
        Parameters
        ----------
        name : Name of the program.
        units : Units, using ´kg´ og ´lbs´ makes sense.
        round_to : Round to this number, e.g. 2.5.
        weeks : Number of weeks.
        nonlinearity : Number between 0 and 0.2
        intensity_list : List of intensities, should be of length ´week´
                            with average value at around 75.
        intensity_model : Deprecated.
        reps_list : List of factors to scale the reps. Of length ´week´,
                    where each entry should be close to 100.
        reps_model : Deprecated.
        reps_per_exercise : Repetitions per exercise.
        reps_RM : normal, relaxed or ´tight´
        """
        self.name = name
        self.units = units
        self.round = float(round_to)
        self.duration = int(weeks)
        self.nonlinearity = int(nonlinearity)
        
        if float(self.nonlinearity) == 0:
            self.k = 0.001
        else:
            self.k = 0.1 * float(nonlinearity)
            
        if intensity_list is None:
            self.intensity_list = [random.randint(70,80) for i in range(self.duration)]
        else:
            self.intensity_list = to_list(intensity_list)
        self.intensity_model = intensity_model
        self.reps_list = to_list(reps_list)
        self.k_list = [S(self.k, w, 100, 0, 1, self.duration) for w in range(1,self.duration+1)]
        self.reps_model = reps_model
        self.reps_per_exercise = float(reps_per_exercise)
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
        
    def add_day(self, day):
        if isinstance(day, list):
            self.days += day
        else:
            self.days.append(day)

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
                    reps, intensity, weights = type(self).render_dynamic_exericse(mainex, self, week)
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
        print('Printing: "{}"'.format(self.name))
        for week in range(1, self.duration+1):
            print('Week {}'.format(week))
            for i, day in enumerate(self.days):
                print('Day {}'.format(i+1))
                for mainex in day.main_exercises:
                    print(mainex.name, self.rendered[week][mainex][0])
            print('')



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
    
    def to_latex(self):
        SEP = '&'
        return_string = ''
    
        # ------------
        # -- HEADER
        # ------------
        return_string += '\section*{' + self.name +'}\n'
    
        return_string += '\\begin{tabular}{l|llll} \n \
        \\textbf{Exercise} & \\textbf{Initial} & \\textbf{Final} \
        & \\textbf{Low} & \\textbf{High} \\\ \hline \n'
    
        for i, day in enumerate(self.days):
            for mainex in day.main_exercises:
                return_string += '&'.join([str(j) for j in 
                                          [mainex.name, 
                                          mainex.current_max, 
                                          mainex.desired_max, 
                                          mainex.low_reps, 
                                          mainex.high_reps]]) + '\\\ \n'
        
    
    
        return_string += '\end{tabular} \n'
        
        # ------------
        # -- Body
        # ------------
        
        for week in range(1, self.duration+1):
            return_string += '\section*{Week ' + str(week) + '}\n'
        
            for i, day in enumerate(self.days):
                return_string += '\subsection*{Day ' + str(i+1) + '}\n'
                table_width = max(self.rendered[week][mainex][0].count('|')
                for mainex in day.main_exercises) + 1
                
                if table_width >= 7:
                    warnings.warn('Table width may overflow in LaTeX.')
                    
                return_string += '\\begin{tabular}{l|' + 'l'*table_width + '}\n \\textbf{Exercise} & \\textbf{Reps} \\\ \hline \n'
            
                for mainex in day.main_exercises:
                    missing = table_width - self.rendered[week][mainex][0].count('|') -1
                    return_string += (mainex.name + SEP + 
                                      self.rendered[week][mainex][0].replace('|', SEP) + SEP*missing + '\\\ \n')
                    
                return_string += '\end{tabular} \n'
           
            
        with open(self._latex_template_path, 'r', encoding = 'utf-8') as file:
            latex_code = '\n'.join(list(line.strip() for line in file))
            return_string = return_string.replace(self.units, '')
            return latex_code.replace('CONTENTHERE', return_string)
        print (return_string.replace(self.units, ''))
        


    @staticmethod
    def render_dynamic_exericse(exercise, program, week):
        """
        Stand-alone function for rendering.
        
        Renders a dynamic exercise, return three lists of
        reps, intensities and weights for a given dynamic
        exercise in a given week.
        """
        low_reps = program.maxima[exercise][week-1]
        high_reps = exercise.high_reps
        
        # Set the reps based on the exercise, or globally fromt he program
        if exercise.reps is None:
            reps_total = int(program.reps_per_exercise * (program.reps_list[week-1]/100))
        else:
            reps_total = int(exercise.reps * (program.reps_list[week-1]/100))
        desired_MI = program.intensity_list[week-1]
    
        suggestions = []
        render_times = 25
        # Going from render_times = 1 to render_times = 10 halves the total error,
        # going to 25 seems to be a reasonable compromise.
        for s in range(render_times):
            reps = create_reps(low_reps, high_reps, reps_total)
            intensity = [program.reps_RM[rep] for rep in reps]
            err_1 = abs(get_MI(reps, intensity) - desired_MI) # Deviation from MI
            err_2 = 100*loss_measure(reps) # Spread of the reps
            err_3 = abs(low_reps - min(reps)) # Punishes staying away from low reps
            error = err_1 + err_2 + err_3
            suggestions.append((reps, intensity, error))
    
        # Choose the rep string with the minimum error
        reps, intensity, error = min(suggestions, key=lambda a:a[2])
    
        current_max = S(program.k, week, exercise.desired_max, 
                        exercise.current_max, 1, program.duration)
        weights = [round_to_nearest((inten/100)*current_max, program.round) for inten in intensity]

        return reps, intensity, weights








































def loss_measure(iterable):
    """
    Measures spread. The lower the better. Between 0 and 1.
    """
    diff = [(iterable[i] - iterable[i + 1]) ** 2 for i in range(len(iterable) - 1)]
    worst = (max(iterable) - min(iterable)) ** 2
    if worst == 0:
        return 1
    return sum(diff) / worst



def to_list(inputvalue):
    """
    Takes a string to a list, separated by commas.
    """
    if isinstance(inputvalue, list):
        return inputvalue
    return [float(i) for i in inputvalue.split(',')]

def get_MI(reps, intensities):
    """
    Return the average intensity.
    """
    return sum([i*j for i, j in zip(reps, intensities)])/sum(reps)

def S(k, t, S_m, S_i, t_i, t_m, sine_wave = False):
    """
    Returns the current strength level from linearly adjusted differential eq.
    """
    a = (t_i - t) / (t_m - t_i)
    ans = (S_i - S_m) * math.exp(a * k) + S_m + a * (S_i - S_m) * math.exp(-k)
    if not sine_wave:
        return ans
    return (1 + 0.025* math.sin(t*2*math.pi/(t_m-t_i))) * ans


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
    """
    Create a list with NUM integers between LOW and HIGH,
    such that no two adjacent numbers are the same.
    """
    if abs(low-high) < 1:
        return [low for i in range(num)]
    return_list = [random.randint(low, high)]

    for i in range(num-1):
        try_value = random.randint(low, high)
        while try_value == return_list[i]:
            try_value = random.randint(low, high)
        return_list.append(try_value)
    
    return return_list


def create_reps(low, high, num):
    """
    Return a sorted list of NUM repetitions between LOW and HIGH.
    """
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
    

    
if __name__ == '__main__':
    # ----------------------------------------------------------------
    # ---------------- Web driven test
    # ----------------------------------------------------------------
    ex = DynamicExercise('Benkpress', 100, 200, 1, 8)
    d = Day()
    program = Program(name='test',
                      units = 'kg', 
                      round_to = 2.5, 
                      weeks = 8, 
                      nonlinearity = 0.1, 
                      intensity_list = '70,70,70,70,70,70,70,70', 
                      intensity_model = 'none', 
                      reps_list = '70,70,70,70,70,70,70,70', 
                      reps_model = 'none', 
                      reps_per_exercise = 30, 
                      reps_RM = 'tight')
    
    d.add_main(ex)
    program.days = [d]
    program.render()
    program.print_it()
    print('')
    
    # ----------------------------------------------------------------
    # ---------------- Local LaTeX rendering
    # ----------------------------------------------------------------
    program = Program(name='TommyJuni17',
                      units = 'kg', 
                      round_to = 2.5, 
                      weeks = 8, 
                      nonlinearity = 0.1, 
                      intensity_list = [68,72,74,71,68,73,71,75], 
                      intensity_model = 'none', 
                      reps_list = '70,70,70,70,70,70,70,70', 
                      reps_model = 'none', 
                      reps_per_exercise = 35, 
                      reps_RM = 'tight')
    
    day1 = Day()
    ex1 = DynamicExercise('Tung bøy', 100, 120, 3, 6)
    ex2 = DynamicExercise('Smalbenk', 130, 140, 2, 7)
    ex3 = DynamicExercise('Militærpress', 60, 80, 4, 8)
    day1.add_main([ex1, ex2, ex3])
    
    day2 = Day()
    ex1 = DynamicExercise('Lett bøy', 80, 100, 5, 8)
    ex2 = DynamicExercise('Chin ups', 95+50, 95+65, 3, 8)
    ex3 = DynamicExercise('Benkpress', 135, 145, 2, 6)
    day2.add_main([ex1, ex2, ex3])
    
    
    program.days = [day1, day2]
    program.render()
    program.print_it()
    print('--')
    latex_code = program.to_latex()
    print(latex_code)
    
    
    # A simple program
    program = Program(name='simple_test',
                      units = 'kg', 
                      round_to = 2.5, 
                      weeks = 4, 
                      nonlinearity = 0.1, 
                      intensity_list = [68,72,74,71,68,73,71,70], 
                      intensity_model = 'none', 
                      reps_list = '100,100,100,100', 
                      reps_model = 'none', 
                      reps_per_exercise = 20, 
                      reps_RM = 'tight')
    
    day1 = Day()
    ex1 = DynamicExercise('Tung bøy', 100, 120, 2, 5)
    day1.add_main(ex1)
    
    program.add_day(day1)
    program.render()
    program.print_it()
    
    
    
    
    
    
    
    
    
    
    
    
    
