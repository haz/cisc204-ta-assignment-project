
from itertools import combinations

from people import STUDENTS, PROFS, PROF_ASSIGNMENTS, GRADS
from courses import COURSES, GRAD_COUNT
LEVELS = [1,2,3,4,5]

from bauhaus import Encoding, proposition, constraint, Or, And
from bauhaus.utils import count_solutions, likelihood

import tabulate

# These two lines make sure a faster SAT solver is used.
from nnf import config
config.sat_backend = "kissat"

# Encoding that will store all of your constraints
E = Encoding()

class Hashable:
    def __hash__(self):
        return hash(str(self))

    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)

    def __repr__(self):
        return str(self)



@proposition(E)
class Assigned(Hashable):
    def __init__(self, student, course) -> None:
        self.student = student
        self.course = course

    def __str__(self) -> str:
        return f"({self.student} @ {self.course})"


@proposition(E)
class StudentPref(Hashable):
    def __init__(self, student, course, level) -> None:
        self.student = student
        self.course = course
        self.level = level

    def __str__(self) -> str:
        return f"(student {self.student} has a preference of {self.level} for course {self.course})"


@proposition(E)
class ProfPref(Hashable):
    def __init__(self, prof, student, course, level) -> None:
        self.prof = prof
        self.student = student
        self.course = course
        self.level = level

    def __str__(self) -> str:
        return f"({self.prof} prefers student {self.student} for course {self.course} at level {self.level})"

assigned_props = []
for s in STUDENTS:
    for c in COURSES:
        assigned_props.append(Assigned(s, c))

student_pref_props = []
for s in STUDENTS:
    for c in COURSES:
        for l in LEVELS:
            student_pref_props.append(StudentPref(s, c, l))

prof_pref_props = []
for p in PROFS:
    for s in STUDENTS:
        for c in COURSES:
            for l in LEVELS:
                prof_pref_props.append(ProfPref(p, s, c, l))

# It shouldn't be the case that there is an assignment swap where the stduents would both prefer it
def ensure_student_nash():
    for s1 in STUDENTS:
        for s2 in STUDENTS:
            for c1 in COURSES:
                for c2 in COURSES:
                    if (s1 != s2) and (c1 != c2):

                        assigned = Assigned(s1, c1) & Assigned(s2, c2)

                        options_s1 = []
                        options_s2 = []
                        for l1 in LEVELS:
                            for l2 in LEVELS:
                                if l2 > l1:
                                    options_s1.append(StudentPref(s1,c2,l2) & StudentPref(s1,c1,l1))
                                    options_s2.append(StudentPref(s2,c1,l2) & StudentPref(s2,c2,l1))
                        s1prefc2 = Or(options_s1)
                        s2prefc1 = Or(options_s2)

                        E.add_constraint(assigned >> ~(s1prefc2 & s2prefc1))



def build_theory():

    # For every student X and pair of courses Y1 and Y2 (that are unique), we have ~(Assigned_X_Y1 /\ Assigned_X_Y2)
    for s in STUDENTS:
        for c1 in COURSES:
            for c2 in COURSES:
                if c1 != c2:
                    E.add_constraint(~(Assigned(s, c1) & Assigned(s, c2)))

    # For every student, they aren't assigned a course that they rank as 1
    for s in STUDENTS:
        for c in COURSES:
            E.add_constraint(StudentPref(s,c,1) >> ~Assigned(s,c))

    # For every student and course, they have exactly one preference level
    for s in STUDENTS:
        for c in COURSES:
            constraint.add_exactly_one(E, [StudentPref(s, c, l) for l in LEVELS])

    # Make the official professor assignments
    for p in PROFS:
        for c in COURSES:
            if c in PROF_ASSIGNMENTS[p]:
                # exactly one preference level for every student
                for s in STUDENTS:
                    constraint.add_exactly_one(E, [ProfPref(p, s, c, l) for l in LEVELS])
            else:
                # no preference levels for every student
                for s in STUDENTS:
                    E.add_constraint(And([~ProfPref(p, s, c, l) for l in LEVELS]))

    # Students must have at least two rank 5 courses
    for s in STUDENTS:
        options = []
        for c1 in COURSES:
            for c2 in COURSES:
                if c1 != c2:
                    options.append(StudentPref(s, c1, 5) & StudentPref(s, c2, 5))
        # E.add_constraint(Or(options))

    # Course needs K=2 TAs
    for c in COURSES:
        options = []
        for s1 in STUDENTS:
            for s2 in STUDENTS:
                if s1 != s2:
                    options.append(And([Assigned(s1, c), Assigned(s2, c)] + \
                                       [~Assigned(s, c) for s in STUDENTS \
                                        if s != s1 and s != s2]))
        E.add_constraint(Or(options))

    # Courses have a required number of grad students
    for c in COURSES:
        options = []
        for choice in combinations(GRADS, GRAD_COUNT[c]):
            options.append(And([Assigned(s, c) for s in choice]))
        E.add_constraint(Or(options))

    # Prof must have 2 TAs with a rank of 3 or higher
    for p in PROFS:
        for c in COURSES:
            if c in PROF_ASSIGNMENTS[p]:
                options = []
                for s in STUDENTS:
                    options.extend([ProfPref(p, s, c, l) for l in LEVELS if l >= 3])
                E.add_constraint(Or(options))

    # No violations of nash equilibrium
    ensure_student_nash()

    return E


def display_solution(sol):
    import pprint
    # pprint.pprint(sol)
    display_assignment(sol)
    display_prof_prefs(sol)
    display_student_prefs(sol)


def display_assignment(sol):
    print("\nAssigned TAs:")

    for c in COURSES:
        print(f"\n{c} ({GRAD_COUNT[c]} grads):")
        for s in STUDENTS:
            if sol[Assigned(s,c)]:
                print(f" - {s}")

def display_student_prefs(sol):
    print("\nStudent Preferences:")

    course2id = {}
    for i,c in enumerate(COURSES):
        course2id[c] = i+1
    data = [[''] + COURSES]
    for s in STUDENTS:
        data.append([s] + ['' for _ in range(len(COURSES))])
        for c in COURSES:
            pref = ''
            for l in LEVELS:
                if sol[StudentPref(s,c,l)]:
                    assert pref == ''
                    pref += f'{l}'
            # if this student is assigned to the course, colour it green
            if sol[Assigned(s,c)]:
                pref = f'\033[92m{pref}\033[0m'
            data[-1][course2id[c]] = pref

    print(tabulate.tabulate(data, headers='firstrow', tablefmt='fancy_grid',
                            colalign=['center']*(len(COURSES)+1)))

def display_prof_prefs(sol):
    print("\nProf Preferences:")
    for p in PROFS:
        print(f"\n{p}:")
        for c in COURSES:
            if c in PROF_ASSIGNMENTS[p]:
                print(f"\n\t{c}:")
                for s in STUDENTS:
                    for l in LEVELS:
                        if sol[ProfPref(p,s,c,l)]:
                            if sol[Assigned(s,c)]:
                                print(f"\t\t{s} at level {l} (assigned)")
                            else:
                                print(f"\t\t{s} at level {l}")

if __name__ == "__main__":

    T = build_theory()
    # Don't compile until you're finished adding all your constraints!
    T = T.compile()
    # After compilation (and only after), you can check some of the properties
    # of your model:
    print("\nSatisfiable: %s" % T.satisfiable())
    # print("# Solutions: %d" % count_solutions(T))
    print("   Solution:")
    sol = T.solve()
    display_solution(sol)

    # print("\nVariable likelihoods:")
    # for v,vn in zip([w,x,y,z], 'wxyz'):
    #     # Ensure that you only send these functions NNF formulas
    #     # Literals are compiled to NNF here
    #     print(" %s: %.2f" % (vn, likelihood(T, v)))
    print()
