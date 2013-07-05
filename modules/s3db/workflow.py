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

from gluon import *
from gluon.storage import Storage
from ..s3 import *

__all__ = ["S3WorkflowModel"]

class S3WorkflowModel(S3Model):

    name = ["workflow_status"]

    def model(self):

        auth = current.auth
        define_table = self.define_table
        db = current.db
        tablename = "workflow_status"
        table = define_table(tablename,
                             Field("user_id", "reference auth_user", 
                                   default = auth.user_id,
                                   readable = False,
                                   writable = False),
                             Field("name"),
                             Field("status"),
                             Field("data","json"),
                             *s3_meta_fields()
                            )
        return Storage()  


