# Write over the default nbgrader export.py file
# This way, it will choose the "default" exporter, which
# is replaced with the Canvas custom exporter

from traitlets import Unicode, List

from .base import BasePlugin
from ..api import MissingEntry


class ExportPlugin(BasePlugin):
    """Base class for export plugins."""

    to = Unicode("", help="destination to export to").tag(config=True)

    student = List([],
        help="list of students to export").tag(config=True)

    assignment = List([],
        help="list of assignments to export").tag(config=True)

    def export(self, gradebook):
        """Export grades to another format.

        This method MUST be implemented by subclasses. Users should be able to
        pass the ``--to`` flag on the command line, which will set the
        ``self.to`` variable. By default, this variable will be an empty string,
        which allows you to specify whatever default you would like.

        Arguments
        ---------
        gradebook: :class:`nbgrader.api.Gradebook`
            An instance of the gradebook

        """
        raise NotImplementedError


class CsvExportPlugin(ExportPlugin):
    """ Default CSV exporter plugin """

    def export(self, gradebook):
        if self.to == "":
            dest = "grades.csv"
        else:
            dest = self.to

        if len(self.student) == 0:
            allstudents = []
        else:
            # make sure studentID(s) are a list of strings
            allstudents = [str(item) for item in self.student]

        if len(self.assignment) == 0:
            allassignments = []
        else:
            # make sure assignment(s) are a list of strings
            allassignments = [str(item) for item in self.assignment]

        self.log.info("Exporting grades to %s", dest)
        if allassignments:
            self.log.info("Exporting only assignments: %s", allassignments)

        if allstudents:
            self.log.info("Exporting only students: %s", allstudents)

        fh = open(dest, "w")
        keys = [
            "assignment",
            "duedate",
            "timestamp",
            "student_id",
            "last_name",
            "first_name",
            "email",
            "raw_score",
            "late_submission_penalty",
            "score",
            "max_score"
        ]
        fh.write(",".join(keys) + "\n")
        fmt = ",".join(["{" + x + "}" for x in keys]) + "\n"

        # Loop over each assignment in the database
        for assignment in gradebook.assignments:

            # only continue if assignment is required
            if allassignments and assignment.name not in allassignments:
                continue

            # Loop over each student in the database
            for student in gradebook.students:

                # only continue if student is required
                if allstudents and student.id not in allstudents:
                    continue

                # Create a dictionary that will store information 
                # about this student's submitted assignment
                score = {}
                score['assignment'] = assignment.name
                score['duedate'] = assignment.duedate
                score['student_id'] = student.id
                score['last_name'] = student.last_name
                score['first_name'] = student.first_name
                score['email'] = student.email
                score['max_score'] = assignment.max_score

                # Try to find the submission in the database. If it
                # doesn't exist, the `MissingEntry` exception will be
                # raised, which means the student didn't submit 
                # anything, so we assign them a score of zero.
                try:
                    submission = gradebook.find_submission(
                        assignment.name, student.id)
                except MissingEntry:
                    score['timestamp'] = ''
                    score['raw_score'] = 0.0
                    score['late_submission_penalty'] = 0.0
                    score['score'] = 0.0
                else:
                    penalty = submission.late_submission_penalty
                    score['timestamp'] = submission.timestamp
                    score['raw_score'] = submission.score
                    score['late_submission_penalty'] = penalty
                    score['score'] = max(0.0, submission.score - penalty)

                for key in score:
                    if score[key] is None:
                        score[key] = ''
                    if not isinstance(score[key], str):
                        score[key] = str(score[key])

                fh.write(fmt.format(**score))

        fh.close()

        self.CanvasExport(gradebook)

    """Export grades to Canvas format"""
    def CanvasExport(self, gradebook):
        if self.to == "":
            dest = "canvas_grades.csv"
        else:
            dest = self.to

        if len(self.student) == 0:
            allstudents = []
        else:
            # make sure studentID(s) are a list of strings
            allstudents = [str(item) for item in self.student]

        if len(self.assignment) == 0:
            allassignments = []
        else:
            # make sure assignment(s) are a list of strings
            allassignments = [str(item) for item in self.assignment]

        self.log.info("Exporting grades to %s", dest)
        
        if allassignments:
            self.log.info("Exporting only assignments: %s", allassignments)

        if allstudents:
            self.log.info("Exporting only students: %s", allstudents)

        fh = open(dest, "w")
        keys = [
            "Student",
            "ID",
            "SIS User ID",
            "SIS Login ID",
            "Section"
        ]
        
        # Add Assignments to keys
        for assignment in reversed(gradebook.assignments):
            keys.append(assignment.name)
            
        fh.write(",".join(keys) + "\n")
        fmt = ",".join(["{" + x + "}" for x in keys])# + "\n"
        
        # Loop over each student in the database
        for student in gradebook.students:

            # only continue if student is required
            if allstudents and student.id not in allstudents:
                continue
        
            # Create a dictionary that will store information 
            # about this student's submitted assignment
            score = {}
            score['Student'] = ''
            score['ID'] = ''
            score['SIS User ID'] = ''
            score['SIS Login ID'] = student.id
            score['Section'] = ''
                
            # Loop over each assignment in the database
            for assignment in gradebook.assignments:
                score[assignment.name] = ''
                
                # only continue if assignment is required
                if allassignments and assignment.name not in allassignments:
                    continue

                # Try to find the submission in the database. If it
                # doesn't exist, the `MissingEntry` exception will be
                # raised, which means the student didn't submit 
                # anything, so we assign them a score of zero.
                try:
                    submission = gradebook.find_submission(
                        assignment.name, student.id)
                except MissingEntry:
                    score[assignment.name] = 0.0
                    
                else:
                    score[assignment.name] = submission.score


                for key in score:
                    if score[key] is None:
                        score[key] = ''
                    if not isinstance(score[key], str):
                        score[key] = str(score[key])
            fh.write(fmt.format(**score)+"\n")

        fh.close()