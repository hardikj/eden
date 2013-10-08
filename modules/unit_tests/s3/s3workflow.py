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

class S3WorkflowEngineModelTests(unittest.TestCase):
    """
        Test Workflow Engine Models
    """
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

    # -------------------------------------------------------------------- 
    def testWorkflowModel(self):

        s3db = current.s3db
        UUID = "workflow_status.uuid"
        uids = ["WF1", "WF2", "WF3"]
        test_fields = ["id", "uuid", "name", "status"]
 
 
        resource = s3db.resource("workflow_status",
                                  uid=uids)
        result = resource.select(test_fields)["rows"]

        # Test workflow_status table
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

# =============================================================================
class S3WorkflowConfigurationTests(unittest.TestCase):

    def setUp(self):
        # Define test workflow
        w = S3Workflow("test workflow", "test resource")
        w.transition("status1", "status2")
        w.transition("status2", ["status3", "status4"])
        w.transition("status3", ["status5", "status6"])
        w.transition("status6", "status4")
        w.transition("status5", "status4")
        w.transition("status2", ["status4", "status7"])
        self.w = w

    # -------------------------------------------------------------------- 
    def test_functions(self):
        # Test workflow functions
        w = self.w
        t1 = w.transitions[0]
        t2 = w.transitions[2] 

        # Test the Configuration attributes
        self.assertEqual(w.name, "test workflow")
        self.assertEqual(w.resource, "test resource")
        self.assertEqual(t1.status, "status1")
        self.assertEqual(t2.next, ["status5","status6"])

        # Test get_all_status function
        statuses = w.get_all_status()
        self.assertSetEqual(statuses, set(["status1", "status2", "status3",
                                     "status4", "status7", "status5",
                                     "status6"]))

        # Test get_next_statuses function
        statuses = w.get_next_status("status2")
        self.assertListEqual(statuses, ["status4", "status7", "status3"])

        # Test get_previous_status function
        statuses = w.get_previous_status("status3")
        self.assertEqual(statuses, set(["status2"]))

        # Test same status condition
        #tnext = w.get_next_status("status2")

# =============================================================================

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

    run_suite( S3WorkflowEngineModelTests,
    		   S3WorkflowConfigurationTests)

# END =========================================================================