

from people import STUDENTS, PROFS
from courses import COURSES
LEVELS = [1,2,3,4,5]

from bauhaus import Encoding, proposition, constraint
from bauhaus.utils import count_solutions, likelihood

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

def example_theory():

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

    # E.add_constraint(w >> x)

    return E


def display_solution(sol):
    import pprint
    pprint.pprint(sol)

def display_assignment(sol):
    print("\nAssigned TAs:")

    for c in COURSES:
        print(f"\n{c}:")
        for s in STUDENTS:
            if sol[Assigned(s,c)]:
                print(f" - {s}")


if __name__ == "__main__":

    T = example_theory()
    # Don't compile until you're finished adding all your constraints!
    T = T.compile()
    # After compilation (and only after), you can check some of the properties
    # of your model:
    print("\nSatisfiable: %s" % T.satisfiable())
    print("# Solutions: %d" % count_solutions(T))
    print("   Solution:")
    sol = T.solve()
    display_solution(sol)
    display_assignment(sol)

    # print("\nVariable likelihoods:")
    # for v,vn in zip([w,x,y,z], 'wxyz'):
    #     # Ensure that you only send these functions NNF formulas
    #     # Literals are compiled to NNF here
    #     print(" %s: %.2f" % (vn, likelihood(T, v)))
    print()
