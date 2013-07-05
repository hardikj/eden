
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

from s3rest import S3Method
from gluon import *
import uuid
import urllib
import sys


class S3WorkflowExitNode(object):
    """
        The S3 Worfklow Exit Node class
    """
    def __init__(self, 
                 controller = None, 
                 function = None, 
                 args = None):

        self.status = "Completed"

        if controller:
            self.controller = controller
        else:
            self.controller = "default"
        if function:
            self.function = function
        else:
            self.function = "index"
        if args:
            self.args	= args
        else:
            self.args = []

    # ----------------------------------------------------------------------
    def __call__(self, request):
        """
            Executes the Exit Node
            @param request: The S3 Reuqest 
        """
        
        current.reaponse.flash = "You have completed the workflow"
        request.vars.wf_id = None
        redirect(URL(c = self.controller,
                     f = self.function,
                     args = self.args))        


# ==========================================================================

class S3Workflow(object):
    """
        Class to Execute the workflow
    """

    def __init__(self, 
                 status = None, 
                 display_text = None, 
                 postp = None, 
                 prep = None,
                 **attr):
        """
            Node Constuctor
            @param status = Node's status
            @param postp = postp for Node
            @param prep = prep for Node
            @param display_text = text to diplay in the as information
        """

        self.actions = []
        self.status = status
        self.prep = prep
        self.postp = postp
        if display_text:
            self.text = display_text
        else:
            self.text = status
        if attr:
            self.attr = attr

    # ----------------------------------------------------------------------
    def node(self, left = None, op = None, right = None):
        """
            Workflow Constructor
            @param left = left object
            @param right = right object
            @param op = oprator 
        """

        self.left = left
        self.op = op
        self.right = right

        return self

    # ----------------------------------------------------------------------
    def __and__(self, other):
        """ AND """

        return S3Workflow().node(self, "and", other)
   
    # ----------------------------------------------------------------------
    def __or__(self, other):
        """ OR """

        return S3Workflow().node(self, "or", other)

    # ----------------------------------------------------------------------
    def __call__(self, r):
        """
            Excutes the Node 
            @param r: The S3 Request
        """
     	pass   

    # ----------------------------------------------------------------------
    def execute(self, request, errors = False):
        """
            Reads the workflow configration and executes the workflow
            @param request: The S3 Request
            @param errors = used to check if form has errors
        """

        uid = None
        s3db = current.s3db
        T = current.T
        db = current.db
        table = s3db.workflow_status
        winsert = table.insert
        wstatus = None
        response = current.response
        c = request.controller
        f = request.function
        m = request.method
        theme = current.deployment_settings.get_theme()
        s3 = response.s3

        w = request.get_vars.wf_id.split(":")
        if len(w)>1:
            uid = w[1]
            wf_id = request.vars.wf_id = "%s:%s"%(w[0], uid)

        if request.vars.wf_uid:
            if uid is list():
                uid = request.vars.wf_uid[0].split(":")[1]
            else:
                uid = request.vars.wf_uid.split(":")[1]
            wf_id  = "%s:%s"%(w[0], uid)
            request.vars.wf_id = wf_id
            request.get_vars.wf_id = wf_id

        # Get workflow configration and store it in database
        name = w[0]
        module_name = "applications.%s.private.templates.%s.workflow" \
        % (request.application, theme)
        try: 
            __import__(module_name)
        except ImportError:
            return
        mymodule = sys.modules[module_name]
        S3WorkflowConfig = mymodule.S3WorkflowConfig()
        if hasattr(S3WorkflowConfig, name):
            workflow = getattr(S3WorkflowConfig, name)()
        else:
            current.response.flash("Invalid Workflow Name: %s" % name)
            return None 

        # If not found assign new one
        if uid is None:
            # Register new workflow in database
            winsert(status=None, data=None, name = name)
            db.commit()
            wstatus = None
            query = (table.user_id == current.auth.user_id) & \
                    (table.name == name)
            uid = db(query).select().last().uuid
            uid = uid.split(":")[2] 
            wf_id = request.vars.wf_id = "%s:%s"%(w[0], uid)

        # Get current status
        if uid is not None and errors is False:
            query = table.uuid == "urn:uuid:"+uid
            row = db(query).select().first()
            request.old_status = row.status
            wstatus = row.status 

        elif errors is True:
            wstatus = request.old_status

        # Get current node
        cnode = self.get_node(workflow, wstatus)        

        match = False

        if isinstance(cnode, S3WorkflowExitNode):
            request = cnode(request)
            return request

        # Match the current action
        if cnode.status: 
            (match,action) = self.match_action(cnode, request, workflow)
        else:
            # Match nodes combinations like (N() | N() | N()) with correct event
            cnode = self.match_node(cnode, request )
            if cnode:
                match = True

        if errors is True:
            match = False

        if match:
            db(query).update(status = action["next_status"])
            db.commit()
            # override postprocess and preprocess
            if self.prep:
                s3.wf_prep = self.prep
                
        if match:
            next_status = action["next_status"]
            nnode = self.get_node(workflow, next_status)
        else:
            nnode = cnode

        if action:
            s3.wf_postp = self.postp_wrapper

        nnode.workflow = workflow
        nnode.wf_id = wf_id
        nnode.name = name
        cnode.match = match
        request.workflow_cnode = nnode
        self.__call__(request)

    # -----------------------------------------------------------------------
    def postp_wrapper(self, request, output):
        
        cnode = request.workflow_cnode
        if cnode.postp:
            postp = cnode.postp
            output = postp(request, output)


        links = current.response.s3.actions
        if links is not None:
            for link in links:
                link["url"] += "?wf_id="+cnode.wf_id

        return output

    # -----------------------------------------------------------------------
    def match_action(self, cnode, r, workflow):
        """
            Function to determine wheather the current action will 
            update the status
            @param cnode = current workflow node 
            @param r = current.request
            
        """

        http = r.http
        match = False
        iactions = []
        factions = []
        node =  cnode.get_parent_node(workflow, cnode)
        if node.op == "or":
            if node.right is cnode:
                onode = node.left
            else:
                onode = node.right

            for o in onode.actions:
                if o["show_ad"] is True:
                    iactions.append(o)

        if cnode.actions:
            factions = iactions +  cnode.actions
            for action in factions:
                d = action
                if "controller" in d:
                    if r.controller == d["controller"]:
                        match = True
                if r.function == d["function"]:
                    match = True
                else:
                    match = False
                if "m" in d and (d["m"]) != r.method:
                    match = False
                if r.args and "rno" in d:
                    if d["rno"] and str(d["rno"]) != str(r.args[0]):
                        match = False
                if "http" in d:
                    if d["http"] != http:
                        match = False
                if match:
                    break

        else:
            action = None

        return (match,action)

    # -----------------------------------------------------------------------
    def match_node(self, root, r, mnode = None):
        """
            Recursive function match nodes combinations like (N() | N() | N())
            with current event
            @param root = the root node
            @param r = current request
            @param mnode = node that got matched
        """

        if hasattr(root, "right") and hasattr(root, "left"):

            mnode = self.match_node(root.left, r, mnode)
            mnode = self.match_node(root.right, r, mnode)

        elif root.status:
                http = r.http
                match = False

                for action in root.actions:
                    d = action
                    if (d["m"] ) == (r.method):
                        match = True
                    if r.args and "rno" in d:
                        if d["rno"] and str(d["rno"]) != str(r.args[0]):
                            match = False 
                    if "http" in d:
                        if d["http"] is not http:
                            match = False
                    if "resource" in d:
                        rname = r.resource.prefix +"_"+ r.resource.name
                        if rname != d["resource"]:
                            match = False
                    if match:
                        break

                if match is True: 
                    mnode = root
 
        return mnode 

    # -----------------------------------------------------------------------
    def handle(self,
               controller = None,
	       function = None,
               args = None,
               next_status = None,
               http = None,
               action_text = None,
               show_ad = False,
               ):
        """
            Contain current action, prep and pop
            @param args = request args
            @param status = status of the current node
            @param http = http method
            @param controller = controller
            @param function = function
            @param show_ad = show this action on adjcent node
        """

        action = dict()

        if next_status:
            action["next_status"] = next_status
        if http:
            action["http"] = http
        if controller and not function:
            action["controller"] = controller
            action["function"] = "index"
        else:
            action["controller"] = controller
            action["function"] = function
        if type(args) is list:
            if len(args) >= 2:
                action["rno"] = args[0]
                action["m"] = args[1]
            else:
                action["m"] = args[0]
        elif args:
            action["rno"] = None
            action["m"] = args
        if action_text:
            action["action_text"] = action_text
        else:
            action["action_text"] = next_status

        if show_ad is True:
            action["show_ad"] = True
        else:
            action["show_ad"] = False

        if action:
            self.actions.append(action)
        

        return self

    # ----------------------------------------------------------------------- 
    def get_current_node(self, root, status, cnode=None, fnode=False):
        """
            Recursive function that returns current node from the 
            workflow configuration
            @param root = root node
            @param status = current workflow status
        """

        if hasattr(root, "left") and hasattr(root, "right"):
            if fnode is True:
                if root.op is not "or":
                    cnode = self.get_current_node(root.left, status, cnode, fnode=True)
                else:
                    cnode = root
            elif fnode is False:
                if root.left.status == status:
                    cnode = root
                elif root.right.status == status:
                    cnode = root
                else:
                    cnode = self.get_current_node(root.left, status, cnode)
                    cnode = self.get_current_node(root.right, status, cnode)
        elif fnode is True :
            cnode = root
        return cnode

    # -----------------------------------------------------------------------
    def get_node(self, root, status):
        """
            Returns next node from the workflow configuration
            @param root = workflow configuration
            @param status = current status
        """

        if status is None:
            cnode = self.get_current_node(root, status, fnode=True) 
            status = cnode.status
            return cnode

        pcnode = self.get_current_node(root, status)

        #TODO - workflow ends if pcnode in None
 

        if pcnode.left.status == status:
            cnode = pcnode.left
        else:
            cnode = pcnode.right

        return cnode

    # -----------------------------------------------------------------------
    def get_node_actions(self, r):
        """
            Function to fetch all the action needed to update staus 
            from current node.Currently used to generate href 
            for next button.
            @param r = S3request
        """
       
        action = self.actions 
        wf_id  = self.wf_id
        links = []

        for a in action:
            c = a.get("controller")
            f = a.get("function")
            m = a.get("m")
            rno = a.get("rno")
            if m or rno:
                if not rno:
                    args = [m]
                elif not m:
                    args  = [rno]
                else:
                    args = [rno, m]
            else:
                args = []
            show_ad = a.get("show_ad", False)
            action_text  = a.get("action_text")
            next_status = a.get("next_status")
            link = URL(c = c, f = f, args = args, vars = {"wf_id" : wf_id})

            if action_text: 
                links.append({"href":link, "show_ad":show_ad, "action_text":action_text})
            elif next_status:
                links.append({"href":link, "show_ad":show_ad, "action_text":next_status})
            else:
                links.append({"href":link, "show_ad":show_ad})

        return links
 
    # -----------------------------------------------------------------------
    def calculate_total(self, root, count):
        if hasattr(root, "left") and hasattr(root, "right"):
            if root.op == "and":
                count = count + 1
                count = self.calculate_total(root.right, count)
                count = self.calculate_total(root.left, count)
            elif root.op == "or":
                pass
        return count

    # -----------------------------------------------------------------------
    def get_current_progress(self, root, status, count, pcount, nocount=False):
        """
           Utility function to find user progress
           @param root = workflow instance
           @param = current status
           @count = count of recursive nodes
           @pcount = progress
        """

        if hasattr(root, "left") and hasattr(root, "right"):
            if root.op == "and":
                if nocount is False:
                    count = count + 1
                pcount = self.get_current_progress(root.right, status, count, pcount) 
                pcount = self.get_current_progress(root.left, status, count, pcount)
            elif root.op == "or":    
                pcount = self.get_current_progress(root.right, status, count, pcount, nocount = True) 
                pcount = self.get_current_progress(root.left, status, count, pcount, nocount = True)
        elif root.status == status:
            pcount = count

        return pcount
 
    # -----------------------------------------------------------------------
    def get_progress(self, r):
        """
            Function that return current workflow progress.
            @param r = S3Request
        """

        cnode = r.workflow_cnode
        total = self.calculate_total(self.workflow, 0)
        total = total
        status = cnode.status
        progress = self.get_current_progress(cnode.workflow, status, count = 0, pcount = 0) - 1
        progress = total - (progress)
        progress = float(progress)/float(total) * 100
        return progress 

    # -----------------------------------------------------------------------
    def get_parent_node(self, root, node, rnode=None):
        """
            recursive function that returns parent instance of the current node
            @param root = root node
            @param node = node whose parent instance will be returned
        """

        if hasattr(root, "left") and hasattr(root, "right"):
            if root.left and root.left is node:
                rnode = root
            elif root.right is node:
                rnode = root
            else:
                rnode = self.get_parent_node(root.left, node, rnode)
                rnode = self.get_parent_node(root.right, node, rnode)
        return rnode



    # -----------------------------------------------------------------------
    def __repr__(self):
        
        r = ""
        def addnode(root, r):

            if hasattr(root, "left") and hasattr(root, "right"):
                if root.op is "and":
                    op = "& "
                    r = addnode(root.left, r)
                    r = r + "%s "%op
                    r = addnode(root.right, r)
                elif root.op is "or":
                    op = "| "
                    r += "( " 
                    r = addnode(root.left, r)
                    r = r + "%s "%op
                    r = addnode(root.right, r)
                    r += ") " 
            elif hasattr(root, "status"):
                    r = r + "%s(%s) "%(root.__class__.__name__, root.status)
            else:
                    r = r + "%s()"%root.__class__.__name__
            return r
        r = addnode(self, r)
        rep = "<%s { %s }>"%(self.__class__.__name__, r) 
        return rep

# =========================================================================

class S3WorkflowHeader(object):
    """
        Default wheader for the workflows
    """
    def __call__(self, r):
        """
          @param r =  S3request 
        """

        # Add Next Button
        T = current.T
        cnode = r.workflow_cnode
        s3 = current.response.s3
        wheader = None
        node = cnode.get_parent_node(cnode.workflow, cnode)
        if node.left is cnode:
            onode = node.right
        else:
            onode = node.left 
         
        onode.wf_id = cnode.wf_id
        ol = DIV()

        if cnode:
            links = cnode.get_node_actions(r)
            if links:
                if node.op == "or":
                     olinks = onode.get_node_actions(r)
                     for l in olinks:
                         at = l.get("action_text", "Next")
                         if l["show_ad"] is True:
                             ol.append(A(T(at), _href=l["href"], _class = "workflow_btns"))
                    
                if len(links) < 2:
                    href = links[0]["href"]
                    at = links[0].get("action_text", "Next")
                    if r.http=="GET" and r.method in ["create"] or r.werror is True: 
                        wheader = DIV(DIV(A(T(at) ,_class = "workflow_non_active_btn"), ol, _class = "workflow_btns_container")) 
                    else:
                        wheader = DIV(A(T(at), _href=href, _class = "workflow_btns" ), ol, _class = "workflow_btns_container")
                else:
                    href = links
                    btn = DIV(_class = "workflow_btns_container")
                    for l in href:
                        at = l.get("action_text", "Next")
                        if r.http=="GET" and r.method=="create":
                            btn.append(DIV(T(at), _class = "workflow_non_active_btn"))
                        else:
                            btn.append(A(T(at), _href=l["href"], _class = "workflow_btns"))
                    if node.op == "or":
                        btn.append(ol)
                    wheader = DIV() 
                    wheader.append(btn)
            
            ad = DIV(_id="attr_contents")
            if hasattr(cnode, "attr"):
                for i in cnode.attr:
                    ad.append(DIV(cnode.attr[i], _id=i))

            exit_btn = DIV(A(T("Exit"), _href=URL("default","index") ), _id="workflow_exit_btn" )
            

            # Add workflow information div
            wi = DIV("%s"%(cnode.text),_id="workflow_info")

            # Adding Progress Bar
            pb = S3WorkflowProgressBarWidget() 
            pbar = pb(r)
             
            if wheader:
               wheader = DIV(pbar, exit_btn, wheader, wi, ad, _id = "workflow_header") 
            else: 
               wheader = DIV(pbar, exit_btn , wi, _id = "workflow_header")

            return wheader
            
        return None

# =========================================================================

class S3WorkflowProgressBarWidget(object):
    def __call__(self, r):

        s3 = current.response.s3
        cnode = r.workflow_cnode 
        T = current.T

        progress = cnode.get_progress(r)

        s3.stylesheets.append("jquery-ui/jquery.ui.progressbar.css")
        s3.stylesheets.append("S3/s3workflow.css")
        s3.scripts.append("/%s/static/scripts/jquery.ui.progressbar.js" % \
        current.request.application)
        s3.jquery_ready.append(
'''$(function() {$( "#progressbar" ).progressbar({value: %s});});'''%progress)
        
        pb =  DIV( DIV("Progress", _id="progress_btn", _class = "ui-progressbar-value ui-widget-header ui-corner-left"), 
                   DIV(DIV(T("Workflow - %s"%cnode.name), _id="progress-label"), _id="progressbar"), _id="pb_container")
        return pb
# END ======================================================================
