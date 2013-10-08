
""" S3 Workflow

    @copyright: 2009-2013 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""


from gluon import *
import itertools
import sys
import uuid

class S3Workflow(object):

    """
    	Class to create the workflow
    """

    def __init__(self, name, resource):

        """
            @param name = name of the worklfow
            @param resource = S3resource name
        """
        self.name = name
        self.resource = resource
        self.transitions = []

    # -------------------------------------------------------------------- 
    def transition(self, status, next):
        """
           Function to define transition
           @param status = status of the transition
           @param next =  next possible statses
        """

        if isinstance(next, basestring):
            if status == next:
                return

        # check if transition has same satus
        # just append the extra next satus.
        next_list = set([])
        for t in self.transitions:
            if t.status == status:
                for i,j in itertools.izip_longest(t.next, next):
                    if i is None or j is None:
                        pass
                    if i not in next_list:
                        next_list.add(i)
                    if j not in next_list:
                        next_list.add(j)
                t.next = list(next_list)
                return

        t1 = S3WorkflowTransitionRule(status, next)
        self.transitions.append(t1)

    # -------------------------------------------------------------------- 
    def get_previous_status(self, status):
        """
            Function to get all previous statuses of current status.
            @param status = current status
        """

        # validate all transitions
        validated = self.validate_transitions()
        if validated is False:
            return None

        pstatus = set([])
        for t in self.transitions:
            if t.status != status:
                for n in t.next:
                    if n == status:
                        pstatus.add(t.status)

        if not pstatus:
            pstatus = None

        return pstatus

    # -------------------------------------------------------------------- 
    def validate_transitions(self):
        """
            Function to validate all transition rules defined for a workflow
        """

        if self.transitions is None:
            return False
            
        if len(self.transitions) == 1:
            return False

    # -------------------------------------------------------------------- 
    def get_next_status(self, status):
        """
            Function to get all possible next statuses of current status,
            It also find all the possible status between the current status 
            and end_status.
            @param status = current status
        """

        # validate all transitions
        validated = self.validate_transitions()
        if validated is False:
            return None

        #Todo - Implement hill climbing
        next_list = None

        for t in self.transitions:
            if t.status == status:
                next_list =  t.next

        return next_list

    # -------------------------------------------------------------------- 
    def get_all_status(self):
        """
            Function to get all the status of the workflow.
        """

        # validate all transitions
        validated = self.validate_transitions()
        if validated is False:
            return None

        status_list = set([])
        for t in self.transitions:
            if t.status not in status_list:
                status_list.add(t.status)
            for n in t.next:
                if n not in status_list:
                    status_list.add(n)

        return status_list

# ============================================================================
class S3WorkflowTransitionRule(object):
    """
        Class to define Workflow transition rules
    """
    def __init__(self, status, next):
        """
            @param status = status of the transition
            @param next = the next possible statuses
        """

        self.status = status
        if isinstance(next, list):
            self.next = next
        else:
            self.next = [next]

# END =========================================================================