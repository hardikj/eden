# -*- coding: utf-8 -*-
#
# Workflow Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3workflow.py
#

import unittest
import datetime
from gluon import *
from gluon.storage import Storage
from gluon.dal import Row
from s3.s3resource import *
from s3.s3workflow import *

class S3WorkflowEngineTests(unittest.TestCase):
    """ Test for S3 Workflow Engine"""

    @classmethod
    def setUp(self):

        xmlstr = """
<s3xml>
    <resource name = "workflow_status" uuid = "WF1">
        <data field = "name">WF1</data>
        <data field = "status">test status1</data>
    </resource>
    <resource name = "workflow_status" uuid = "WF2">
        <data field = "name">WF2</data>
        <data field = "status">test status2</data>
    </resource>
    <resource name = "workflow_status" uuid = "WF3">
        <data field = "name">WF3</data>
        <data field = "status">test status3</data>
    </resource>
</s3xml>
"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        current.auth.override = True
        resource = current.s3db.resource("workflow_status")
        resource.import_xml(xmltree)

    # ------------------------------------------------------------------   
    def testWorkflowModel(self):

        s3db = current.s3db
        UUID = "workflow_status.uuid"
        uids = ["WF1", "WF2", "WF3"]
        test_fields = ["id", "uuid", "name", "status"]
 
        resource = s3db.resource("workflow_status",
                                  uid=uids)
        result = resource.select(test_fields)["rows"]

        counter = 1
        for record in result:
            if record[UUID] == "WF"+str(counter):
                self.assertEqual(record["workflow_status.name"], "WF"+str(counter))
                self.assertEqual(record["workflow_status.name"], "WF"+str(counter))
            counter = counter+1


    # -------------------------------------------------------------------- 
    def tearDown(self):

        current.auth.override = False
        current.db.rollback()

# =======================================================================

class TestS3WorkflowConfiguration(unittest.TestCase):
    """
        Test Workflow Configuration
    """

    def setUp(self):

        s3db = current.s3db
        N = S3Workflow
        Exit = S3WorkflowExitNode
        self.configuration1 = N("new").handle(controller = "org",
                                              function = "organisation",
                                              args = "create", 
                                              next_status = "add organisation get", 
                                              http = "GET") & \
                              N("add organisation get").handle(controller = "org", 
                                                               function = "organisation", 
                                                               args = "create", 
                                                               next_status = "add organisation post", 
                                                               http = "POST") & \
                              N("add organisation post").handle(controller = "org", 
                                                                function = "office", 
                                                                args = [1,"update"], 
                                                                next_status = "add office")\
                                                        .handle(controller = "org", 
                                                                function = "facility", 
                                                                args = "create", 
                                                                next_status = "add facility") & \
                              ( N("add office").handle(controller = "hrm", 
                                                       function = "staff", 
                                                       args = "create", 
                                                       next_status = "add staff") | \
                                N("add facility").handle(controller = "hrm", 
                                                         function = "staff", 
                                                         args = "create", 
                                                         next_status = "add staff") ) & \
                              Exit() 




    # ---------------------------------------------------------------------- 
    def test_configuration(self):
 
        self.assertTrue(isinstance(self.configuration1.left, S3Workflow))
        self.assertTrue(isinstance(self.configuration1.left.left, S3Workflow))
        self.assertTrue(isinstance(self.configuration1.left.left.right, S3Workflow))
        self.assertEqual(self.configuration1.left.right.op, "or")
        self.assertEqual(self.configuration1.left.left.op, "and")
        self.assertFalse(hasattr(self.configuration1.left.left.right,"op"))
        self.assertEqual(self.configuration1.left.left.left.left.actions[0]["http"], "GET")
        self.assertEqual(self.configuration1.left.right.left.status, "add office")
        self.assertEqual(self.configuration1.left.right.left.actions[0]["next_status"], "add staff")


# =========================================================================
class TestS3WorkflowHeader(unittest.TestCase):
    """
        Test Workflow Header class
    """

    def setUp(self):
        N = S3Workflow
        Exit = S3WorkflowExitNode
        self.configuration1 = N("new").handle(controller = "org",
                                              function = "organisation",
                                              args = "create",
                                              next_status = "add organisation get",
                                              http = "GET") & \
                              N("add organisation get").handle(controller = "org",
                                                               function = "organisation",
                                                               args = "create",
                                                               next_status = "add organisation post",
                                                               http = "POST") & \
                              N("add organisation post").handle(controller = "org",
                                                                function = "office",
                                                                args = [1,"update"],
                                                                next_status = "add office")\
                                                        .handle(controller = "org",
                                                                function = "facility",
                                                                args = "create",
                                                                next_status = "add facility") & \
                              ( N("add office").handle(controller = "hrm",
                                                       function = "staff",
                                                       args = "create",
                                                       next_status = "add staff") | \
                                N("add facility").handle(controller = "hrm",
                                                         function = "staff",
                                                         args = "create",
                                                         next_status = "add staff") ) & \
                              Exit()

        wf = S3Workflow()
        cnode1 = wf.get_node(self.configuration1, "add organisation get")
        cnode1.wf_id = "orgmanagement%3A80de1d95-c0c0-4489-8ad4-ecd35e02e333"
        self.r1 = Storage(
                         workflow_cnode = cnode1
                        )

    def testDefaultWorkflowHeader(self):

        wheader = S3WorkflowHeader()
        wheader1 = wheader(self.r1)
        awheader1 = """<div><div class="workflow_btns"><a href="eden/default/index">Exit</a></div>\
                       <div class="workflow_btns" id="wf_dropdown">\
                       <a href="/eden/org/organisation/create?wf_id=\
                       orgmanagement%253A80de1d95-c0c0-4489-8ad4-ecd35e02e333">NEXT</a></div></div>"""
        self.assertEqual(wheader1.xml(), awheader1)

# =========================================================================
class TestS3WorkflowSupporterFunctions(unittest.TestCase):
    """
        Test Worlflow Supporter functions
    """

    def setUp(self):
        N = S3Workflow
        Exit = S3WorkflowExitNode
        self.configuration1 = N("new").handle(controller = "org",
                                              function = "organisation",
                                              args = "create",
                                              next_status = "add organisation get",
                                              http = "GET") & \
                              N("add organisation get").handle(controller = "org",
                                                               function = "organisation",
                                                               args = "create",
                                                               next_status = "add organisation post",
                                                               http = "POST") & \
                              N("add organisation post").handle(controller = "org",
                                                                function = "office",
                                                                args = [1,"update"],
                                                                next_status = "add office")\
                                                        .handle(controller = "org",
                                                                function = "facility",
                                                                args = "create",
                                                                next_status = "add facility") & \
                              ( N("add office").handle(controller = "hrm",
                                                       function = "staff",
                                                       args = "create",
                                                       next_status = "add staff") | \
                                N("add facility").handle(controller = "hrm",
                                                         function = "staff",
                                                         args = "create",
                                                         next_status = "add staff") ) & \
                              Exit()




        # create fake request
        self.r = Storage(http = "POST",
                         controller = "org",
                         function = "office",
                         method = "update",
                         args = [1,"update"], 
                        )

    # ---------------------------------------------------------------------- 
    def test_functions(self):

        wf = S3Workflow()

        # test get_current_node function
        cpnode = wf.get_current_node(self.configuration1, "add office")
        self.assertEqual(cpnode, self.configuration1.left.right)

        # test get_node funcion
        cnode =  wf.get_node(self.configuration1, None)
        self.assertEqual(cnode, self.configuration1.left.left.left.left)

        cnode =  wf.get_node(self.configuration1, "add organisation post")
        self.assertEqual(cnode, self.configuration1.left.left.right)

        # test match_action function
        (match,action) = wf.match_action(cnode, self.r)

        self.assertTrue(match, True)
        self.assertEqual(action["controller"], "org")
        self.assertEqual(action["function"], "office")
        self.assertEqual(action["m"], "update")



# ======================================================================== 
def run_suite(*test_classes):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner(verbosity=2).run(suite)
    return

if __name__ == "__main__":

    run_suite( S3WorkflowEngineTests,
               TestS3WorkflowConfiguration,
               TestS3WorkflowSupporterFunctions,
               TestS3WorkflowHeader
    )

