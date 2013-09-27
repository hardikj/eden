"""
   This file is used to define the configration of the workflows
   for the workflow engine.
   
   @copyright: 2012-13 (c) Sahana Software Foundation
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

from s3.s3resource import *
from s3.s3workflow import S3Workflow, S3WorkflowExitNode

class S3WorkflowConfig(object):

    def orgmanagement(self):
        N = S3Workflow
        Exit = S3WorkflowExitNode
        s3db = current.s3db
        s3 = current.response.s3

        def postp(r, output):
            if r.interactive:
                s3.actions =[
                    dict(url = URL(c="req", f="req"),
                        _class = "action-btn",
                        label = str("go to req/req")
                        )
                    ]
            return output

 
        return N("new", display_text = "wrlcome to the org management workflow" ).handle(controller = "org", 
                               function = "organisation", 
                               args = "create", 
                               next_status = "add organisation get", 
                               http = "GET",
                               ) & \
               N("add organisation get", display_text = "please enter organisation record").handle(controller = "org", 
                                                function = "organisation", 
                                                args = "create", 
                                                next_status = "add organisation post", 
                                                http = "POST",
                                                action_text = "Please fill the form to proceed"
                                                ) & \
               N("add organisation post", display_text = "you just added an organisation record",
                 a_text = "next" ).handle(controller = "org",
                                                 function = "office", 
                                                 args = ["create"], 
                                                 next_status = "add office")\
                                         .handle(controller = "org",
                                                 function = "facility",
                                                 next_status = "add facility", 
                                                 ) & \
               ( N("add office", display_text = "please update the office details").handle(controller = "hrm", 
                                        function = "staff", 
                                        args = ["1","update"], 
                                        next_status = "add staff"
                                        ).handle(next_status = "add office",
                                                 controller = "org", function = "office", args = ["create"],
                                                 action_text = "Add more office", show_ad = True) | \
                 N("add facility", postp = postp, display_text = "please add one facility").handle(controller = "hrm", 
                                          function = "staff", 
                                          args = "create", 
                                          next_status = "add staff").handle(controller = "org",
                                                 function = "facility",
                                                  action_text = "Add more facility", 
                                                  next_status = "add facility", 
                                                  show_ad = True
                                                 ) ) & \
               N("add staff") & \
               Exit() 


    # ==========================================================================================

    def reqmanagement(self):

        N = S3Workflow
        Exit = S3WorkflowExitNode
        s3db = current.s3db
        s3 = current.response.s3


    return N("new", display_text = "welcome to request management workflow").handle(controller="req",
                                                                                    function="req",
                                                                                    action_text="asv")
